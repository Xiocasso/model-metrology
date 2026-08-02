"""Make the permission_bench package importable when pytest runs from the
repo root (mirrors instruments/contract_bench/conftest.py)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
