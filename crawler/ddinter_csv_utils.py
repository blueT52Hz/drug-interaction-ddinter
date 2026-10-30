"""
Shared helpers for reading DDInter interaction CSV downloads.

Source files `ddinter_downloads_code_<ATC letter>.csv` have columns:
DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level.
"""

import csv
import re
from pathlib import Path

INPUT_PATTERN = "ddinter_downloads_code_*.csv"


def find_input_files(input_dir: Path):
    """Return sorted DDInter download files in input_dir (empty list if none)."""
    return sorted(input_dir.glob(INPUT_PATTERN))


def ddinter_id_sort_key(ddinter_id: str):
    """Sort 'DDInter12' numerically; fall back to string for unexpected formats."""
    match = re.fullmatch(r"DDInter(\d+)", ddinter_id)
    return (0, int(match.group(1)), "") if match else (1, 0, ddinter_id)


def iter_interaction_rows(input_files):
    """Yield (source_path, row_dict) with all values stripped of whitespace."""
    for path in input_files:
        with path.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                yield path, {k.strip(): (v or "").strip() for k, v in row.items() if k}
