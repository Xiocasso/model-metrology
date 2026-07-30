"""Make the stress_probe package importable when pytest runs from the repo
root (mirrors the sys.path insertion the experiment scripts do)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
