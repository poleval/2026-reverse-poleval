"""Regression checks for JSON migration and response alignment."""
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
from common import load_items
from validate_format import validate_file
from sheet_export_to_json import load_pairs
import query_models


class JsonPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.items = self.root / 'items.json'

    def write(self, records):
        self.items.write_text(json.dumps(records, ensure_ascii=False), encoding='utf-8')

    def test_json_text_round_trip_and_optional_aliases(self):
        text = 'Polski tekst: „cytat”, tab\t i nowa\nlinia'
        self.write([{'input': text, 'gold': 'tak'},
                    {'input': 'drugi', 'gold': 'nie', 'aliases': ['nie.']}])
        loaded = load_items(str(self.items))
        self.assertEqual(loaded[0].input, text)
        self.assertEqual(loaded[0].aliases, [])
        self.assertEqual(loaded[1].aliases, ['nie.'])
        self.assertEqual(validate_file(str(self.items), n_min=2)[0], [])

    def test_reject_malformed_schema_and_duplicate_keys(self):
        for record in [None, {'input': 'x', 'gold': 1},
                       {'input': 'x', 'gold': 'g', 'aliases': 'g'},
                       {'input': 'x', 'gold': 'g', 'aliases': [None]},
                       {'input': 'x', 'gold': 'g', 'extra': 'ignored?'}]:
            with self.subTest(record=record):
                self.write([record])
                self.assertTrue(validate_file(str(self.items), n_min=1)[0])
        self.items.write_text('[{"input":"x","gold":"a","gold":"b"}]')
        self.assertTrue(validate_file(str(self.items), n_min=1)[0])

    def test_normalised_duplicates_alias_limits_and_budget(self):
        self.write([{'input': 'x', 'gold': 'g'}, {'input': ' x ', 'gold': 'h'}])
        self.assertTrue(validate_file(str(self.items), n_min=1)[0])
        for aliases in [[' g '], ['a', ' a '], ['a'] * 6, ['x' * 81], ['']]:
            self.write([{'input': 'x', 'gold': 'g', 'aliases': aliases}])
            self.assertTrue(validate_file(str(self.items), n_min=1)[0])
        self.write([{'input': 'x', 'gold': 'g'}])
        self.assertTrue(validate_file(str(self.items))[0])

    def test_spreadsheet_multiline_quotes_and_header(self):
        path = self.root / 'sheet.csv'
        path.write_text('input,gold\n"tekst, \\"cytat\\"\ni kolejna linia",tak\n'.replace('\\"', '""'))
        self.assertEqual(load_pairs(str(path)), [('tekst, "cytat"\ni kolejna linia', 'tak')])

    def evaluate(self):
        return subprocess.run([sys.executable, str(SCRIPTS / 'evaluate_responses.py'),
                               '--items', str(self.items), '--responses-dir', str(self.root / 'responses'),
                               '--output', str(self.root / 'matrix.json')], capture_output=True, text=True)

    def test_user_message_is_the_exact_submitted_input(self):
        text = '  Polski tekst\n\n"cytat"\t koniec  '
        response = unittest.mock.Mock()
        response.json.return_value = {'choices': [{'message': {'content': 'answer'}}]}
        with patch.object(query_models.requests, 'post', return_value=response) as post:
            query_models.query_one('http://localhost:8000/v1', 'dummy', 'model',
                                   text, 0.0, 64, 60.0, 1)
        self.assertEqual(post.call_args.kwargs['json']['messages'], [
            {'role': 'system', 'content': query_models.DEFAULT_SYSTEM_PROMPT},
            {'role': 'user', 'content': text},
        ])

    def test_query_alias_scoring_and_metric_end_to_end(self):
        self.write([{'input': 'multiline\ninput', 'gold': 'a', 'aliases': ['a.']},
                    {'input': 'other', 'gold': 'b'}])
        responses = self.root / 'responses'
        args = ['query_models.py', '--items', str(self.items), '--models', 'one', 'two',
                '--output-dir', str(responses)]
        def answer(base, key, model, prompt, *args, **kwargs):
            self.assertIn(prompt, ['multiline\ninput', 'other'])
            return ('a.' if model == 'one' else 'wrong', {})
        with patch.object(sys, 'argv', args), patch.object(query_models, 'load_dotenv', return_value=None), \
             patch.dict(os.environ, {'EVAL_API_KEY': 'dummy'}), \
             patch.object(query_models, 'query_one', side_effect=answer), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            query_models.main()
        result = self.evaluate()
        self.assertEqual(result.returncode, 0, result.stderr)
        matrix = json.loads((self.root / 'matrix.json').read_text())
        self.assertEqual(matrix['items'][0]['correct'], {'one': True, 'two': False})
        self.assertEqual(matrix['items'][1]['correct'], {'one': False, 'two': False})
        metric = subprocess.run([sys.executable, str(SCRIPTS / 'compute_metric.py'), '--matrix',
                                 str(self.root / 'matrix.json')], capture_output=True, text=True)
        self.assertEqual(metric.returncode, 0, metric.stderr)
        self.assertIn('score (', metric.stdout)
        # An unchanged run resumes without further requests.
        with patch.object(sys, 'argv', args), patch.object(query_models, 'load_dotenv', return_value=None), \
             patch.dict(os.environ, {'EVAL_API_KEY': 'dummy'}), \
             patch.object(query_models, 'query_one') as query, contextlib.redirect_stdout(io.StringIO()):
            query_models.main()
            query.assert_not_called()

    def test_reject_mismatched_duplicate_and_incomplete_responses(self):
        self.write([{'input': 'x', 'gold': 'g'}, {'input': 'y', 'gold': 'h'}])
        responses = self.root / 'responses'
        responses.mkdir()
        records = [{'idx': i, 'input': text, 'gold': gold, 'model': 'm', 'output': gold}
                   for i, (text, gold) in enumerate([('x', 'g'), ('y', 'h')])]
        bad = dict(records[0], input='another question')
        bad_alias = dict(records[0], aliases=['new answer'])
        for sample in [[bad, records[1]], [bad_alias, records[1]], records[:1], records + records[:1]]:
            (responses / 'm.jsonl').write_text(''.join(json.dumps(r) + '\n' for r in sample))
            result = self.evaluate()
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((self.root / 'matrix.json').exists())


if __name__ == '__main__':
    unittest.main()
