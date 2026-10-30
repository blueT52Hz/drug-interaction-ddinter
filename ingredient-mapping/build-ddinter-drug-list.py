"""
Build a unique drug/active-ingredient list from DDInter interaction files.

Reads every `ddinter_downloads_code_*.csv` in the DDInter folder (columns:
DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level), collects both sides of each
interaction pair and writes a deduplicated CSV with columns: DDInterID, Drug.

Usage:
    python ingredient-mapping/build-ddinter-drug-list.py [--input-dir DIR] [--output FILE]
    (e.g. --input-dir crawler/data/downloads after running crawler/download-ddinter-csv.py)
"""

import argparse
import csv
import sys
from pathlib import Path

from ddinter_csv_utils import (
    DDINTER_DIR,
    INPUT_PATTERN,
    ddinter_id_sort_key,
    find_input_files,
    iter_interaction_rows,
)

DEFAULT_OUTPUT = DDINTER_DIR / "ddinter_drug_list.csv"


def collect_drugs(input_files):
    """Return {DDInterID: Drug} and a dict of IDs that appear with conflicting names."""
    drugs = {}
    conflicts = {}
    for _, row in iter_interaction_rows(input_files):
        for side in ("A", "B"):
            ddinter_id = row.get(f"DDInterID_{side}", "")
            name = row.get(f"Drug_{side}", "")
            if not ddinter_id or not name:
                continue
            existing = drugs.setdefault(ddinter_id, name)
            if existing != name:
                conflicts.setdefault(ddinter_id, {existing}).add(name)
    return drugs, conflicts


def write_drug_list(drugs, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["DDInterID", "Drug"])
        for ddinter_id in sorted(drugs, key=ddinter_id_sort_key):
            writer.writerow([ddinter_id, drugs[ddinter_id]])


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("--input-dir", type=Path, default=DDINTER_DIR)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    input_files = find_input_files(args.input_dir)
    if not input_files:
        sys.exit(f"No files matching {INPUT_PATTERN} in {args.input_dir}")

    try:
        drugs, conflicts = collect_drugs(input_files)
        write_drug_list(drugs, args.output)
    except (OSError, csv.Error) as exc:
        sys.exit(f"Failed to build drug list: {exc}")

    print(f"Read {len(input_files)} files -> {len(drugs)} unique drugs -> {args.output}")
    for ddinter_id, names in sorted(conflicts.items(), key=lambda kv: ddinter_id_sort_key(kv[0])):
        print(f"WARNING: {ddinter_id} has multiple names {sorted(names)}; kept first seen")


if __name__ == "__main__":
    main()
