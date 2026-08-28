"""Tests for ads_megalib.

Run from the repo root:

    python -m unittest discover -s tests -t . -v
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
root = str(ROOT)
if root not in sys.path:
    sys.path.insert(0, root)
