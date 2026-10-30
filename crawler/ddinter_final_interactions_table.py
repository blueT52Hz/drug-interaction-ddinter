"""
In-memory final interactions table, matched by drug pair and saved atomically.

Final CSV columns:
    InteractionID, DDInterID_A, Drug_A, DDInterID_B, Drug_B, Level, Interaction, Management
On first use the final file is created from the merged DDInter CSV with
InteractionID / Interaction / Management left blank; crawled records then fill
those columns for the row with the same (unordered) DDInterID pair.

Crawled records that cannot go into the final table are written to the unmatched CSV:
    pair_not_in_merged  - the drug pair has no row in the merged CSV
    duplicate_pair      - the pair is already filled by a lower InteractionID (KeptInteractionID)
"""

import csv
import os
from pathlib import Path

FINAL_COLUMNS = [
    "InteractionID", "DDInterID_A", "Drug_A", "DDInterID_B", "Drug_B",
    "Level", "Interaction", "Management",
]
UNMATCHED_COLUMNS = [
    "InteractionID", "DDInterID_A", "DDInterID_B", "Reason", "KeptInteractionID",
    "Interaction", "Management",
]
FILLED_COLUMNS = ("InteractionID", "Interaction", "Management")


def pair_key(id_a: str, id_b: str):
    """Order-independent key: the site may list a pair as B/A instead of A/B."""
    return (id_a, id_b) if id_a <= id_b else (id_b, id_a)


def _read_csv(path: Path):
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _atomic_write_csv(path: Path, fieldnames, rows):
    """Write to a temp file then replace (no half-written file on crash).
    Raises PermissionError when the target is locked (e.g. open in Excel)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(".csv.tmp")
    with tmp_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp_path, path)


class FinalInteractionsTable:
    def __init__(self, final_path: Path, merged_path: Path, unmatched_path: Path):
        self.final_path = final_path
        self.unmatched_path = unmatched_path
        if final_path.exists():
            self.rows = _read_csv(final_path)
            self.dirty = False
        else:
            self.rows = [{col: row.get(col, "") for col in FINAL_COLUMNS} for row in _read_csv(merged_path)]
            self.dirty = True
            print(f"Created final table from {merged_path.name} ({len(self.rows)} rows)")
        self.index = {pair_key(r["DDInterID_A"], r["DDInterID_B"]): r for r in self.rows}
        # InteractionID -> crawled record; rebuilt every run from the raw crawl log
        self.unmatched = {}
        self.duplicates = {}

    def fill(self, record: dict) -> str:
        """
        Fill the row matching record's drug pair.
        Returns "filled" | "duplicate" (pair already has another InteractionID) | "unmatched".
        When a pair has several InteractionIDs the lowest one wins (deterministic).
        """
        new_id = int(record["InteractionID"])
        row = self.index.get(pair_key(record["DDInterID_A"], record["DDInterID_B"]))
        if row is None:
            self.unmatched[new_id] = record
            self.dirty = True
            return "unmatched"
        current = row["InteractionID"]
        if current and int(current) <= new_id:
            if int(current) == new_id:
                return "filled"
            self.duplicates[new_id] = record
            self.dirty = True
            return "duplicate"
        if current:
            # A lower ID arrived later: the previous winner becomes a duplicate
            self.duplicates[int(current)] = {col: row[col] for col in UNMATCHED_COLUMNS if col in row}
        for col in FILLED_COLUMNS:
            row[col] = str(record[col])
        self.dirty = True
        return "duplicate" if current else "filled"

    def filled_count(self) -> int:
        return sum(1 for r in self.rows if r["InteractionID"])

    def _unmatched_rows(self):
        """Unmatched + duplicate records sorted by InteractionID, in UNMATCHED_COLUMNS shape."""
        rows = [{**record, "Reason": "pair_not_in_merged", "KeptInteractionID": ""}
                for record in self.unmatched.values()]
        for record in self.duplicates.values():
            kept = self.index[pair_key(record["DDInterID_A"], record["DDInterID_B"])]["InteractionID"]
            rows.append({**record, "Reason": "duplicate_pair", "KeptInteractionID": kept})
        rows.sort(key=lambda r: int(r["InteractionID"]))
        return [{col: r.get(col, "") for col in UNMATCHED_COLUMNS} for r in rows]

    def save(self) -> bool:
        """Rewrite the final CSV and the unmatched CSV if anything changed."""
        if not self.dirty:
            return True
        try:
            _atomic_write_csv(self.final_path, FINAL_COLUMNS, self.rows)
            _atomic_write_csv(self.unmatched_path, UNMATCHED_COLUMNS, self._unmatched_rows())
        except PermissionError as exc:
            # Typically a CSV is open in Excel on Windows; keep dirty and retry on next save
            print(f"WARNING: cannot overwrite {exc.filename or 'output CSV'} (file open elsewhere?); will retry")
            return False
        self.dirty = False
        return True
