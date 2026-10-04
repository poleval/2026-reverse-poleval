#!/usr/bin/env python3
"""Back-compat wrapper. The published example is example-submission/track-2/."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

target = Path(__file__).resolve().parents[2] / "example-submission" / "track-2" / "generate.py"
sys.argv[0] = str(target)
runpy.run_path(str(target), run_name="__main__")
