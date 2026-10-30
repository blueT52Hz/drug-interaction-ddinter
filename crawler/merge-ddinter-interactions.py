"""
Merge all DDInter interaction downloads into one deduplicated CSV.

Reads every `ddinter_downloads_code_*.csv` (one file per ATC letter, so the same
pair often appears in several files, sometimes with A/B swapped) and writes one
row per unordered drug pair with columns:
DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level

Rules:
- Pair is normalized so DDInterID_A < DDInterID_B (numeric order).
- Rows with missing fields, unexpected Level values or A == B are skipped.
- If a pair has different Levels across files, the most severe is kept
  (Major > Moderate > Minor > Unknown).

Input folder and output file default to downloads_dir / merged_file in config.json.

Usage:
    python merge-ddinter-interactions.py [--config config.json] [--input-dir DIR] [--output FILE]
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

from ddinter_crawler_config import DEFAULT_CONFIG_PATH, load_crawler_config
from ddinter_csv_utils import INPUT_PATTERN, ddinter_id_sort_key, find_input_files, iter_interaction_rows

LEVEL_SEVERITY = {"Unknown": 0, "Minor": 1, "Moderate": 2, "Major": 3}
OUTPUT_COLUMNS = ["DDInterID_A", "Drug_A", "DDInterID_B", "Drug_B", "Level"]
MAX_EXAMPLES = 10


def merge_interactions(input_files):
    """
    Return (pairs, names, stats, examples).
    pairs: {(id_a, id_b): Level}; names: {DDInterID: Drug};
    examples: {issue: [str]} sample lines for skipped rows / level conflicts.
    """
    pairs, names = {}, {}
    stats = Counter()
    examples = {"invalid": [], "level_conflict": []}

    for path, row in iter_interaction_rows(input_files):
        stats["rows_read"] += 1
        id_a, drug_a = row.get("DDInterID_A", ""), row.get("Drug_A", "")
        id_b, drug_b = row.get("DDInterID_B", ""), row.get("Drug_B", "")
        level = row.get("Level", "")

        if not (id_a and drug_a and id_b and drug_b) or level not in LEVEL_SEVERITY:
            stats["skipped_invalid"] += 1
            if len(examples["invalid"]) < MAX_EXAMPLES:
                examples["invalid"].append(f"{path.name}: {row}")
            continue
        if id_a == id_b:
            stats["skipped_self_pair"] += 1
            continue

        names.setdefault(id_a, drug_a)
        names.setdefault(id_b, drug_b)
        key = tuple(sorted((id_a, id_b), key=ddinter_id_sort_key))

        existing = pairs.get(key)
        if existing is None:
            pairs[key] = level
            continue
        stats["duplicates_removed"] += 1
        if existing != level:
            # Unknown vs a known level is not a real disagreement, just missing info
            if "Unknown" not in (existing, level):
                stats["level_conflicts"] += 1
                if len(examples["level_conflict"]) < MAX_EXAMPLES:
                    examples["level_conflict"].append(f"{key}: {existing} vs {level} ({path.name})")
            if LEVEL_SEVERITY[level] > LEVEL_SEVERITY[existing]:
                pairs[key] = level

    return pairs, names, stats, examples


def pair_sort_key(pair):
    return ddinter_id_sort_key(pair[0]), ddinter_id_sort_key(pair[1])


def write_merged(pairs, names, output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(OUTPUT_COLUMNS)
        for id_a, id_b in sorted(pairs, key=pair_sort_key):
            writer.writerow([id_a, names[id_a], id_b, names[id_b], pairs[(id_a, id_b)]])


def print_report(input_files, pairs, stats, examples, output_path):
    print(f"Files read: {len(input_files)} ({', '.join(p.name for p in input_files)})")
    print(f"Rows read: {stats['rows_read']}")
    print(f"Skipped invalid rows: {stats['skipped_invalid']}")
    print(f"Skipped self pairs (A == B): {stats['skipped_self_pair']}")
    print(f"Duplicates removed: {stats['duplicates_removed']}")
    print(f"Level conflicts (resolved to most severe): {stats['level_conflicts']}")
    print(f"Unique pairs written: {len(pairs)} -> {output_path}")
    for level, count in Counter(pairs.values()).most_common():
        print(f"  {level}: {count}")
    for issue, lines in examples.items():
        for line in lines:
            print(f"EXAMPLE {issue}: {line}")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--input-dir", type=Path, help="default: downloads_dir from config")
    parser.add_argument("--output", type=Path, help="default: merged_file from config")
    args = parser.parse_args()

    try:
        config = load_crawler_config(args.config)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        sys.exit(f"Invalid config: {exc}")
    input_dir = args.input_dir or config.downloads_dir
    output_path = args.output or config.merged_file

    input_files = find_input_files(input_dir)
    if not input_files:
        sys.exit(f"No files matching {INPUT_PATTERN} in {input_dir} (run download-ddinter-csv.py first)")

    try:
        pairs, names, stats, examples = merge_interactions(input_files)
        write_merged(pairs, names, output_path)
    except (OSError, csv.Error) as exc:
        sys.exit(f"Failed to merge interactions: {exc}")

    print_report(input_files, pairs, stats, examples, output_path)


if __name__ == "__main__":
    main()
