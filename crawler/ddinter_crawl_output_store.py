"""
Thread-safe, resumable output files for the DDInter interaction crawler.

Files inside output_dir:
    ddinter_interactions_detail.csv  - raw log, one row per crawled interaction (appended,
                                       flushed per row; source of truth for the final table)
    missing_interaction_ids.txt      - IDs the site reports as non-existent (appended)
    failed_interaction_ids.csv       - IDs that failed after all retries in the last run (rewritten)
    blocked_proxies.txt              - dead proxies (ProxyError), written by ProxyPool, skipped next run
IDs already in the first two files are skipped on the next run, failed IDs are retried.
"""

import csv
import threading
from pathlib import Path

from ddinter_interaction_page_parser import RECORD_FIELDS

RECORDS_FILE = "ddinter_interactions_detail.csv"
MISSING_FILE = "missing_interaction_ids.txt"
FAILED_FILE = "failed_interaction_ids.csv"
BLOCKED_PROXIES_FILE = "blocked_proxies.txt"


class CrawlOutputStore:
    def __init__(self, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)
        self.records_path = output_dir / RECORDS_FILE
        self.missing_path = output_dir / MISSING_FILE
        self.failed_path = output_dir / FAILED_FILE
        self._lock = threading.Lock()
        self.failed = []

        write_header = not self.records_path.exists() or self.records_path.stat().st_size == 0
        self._records_file = self.records_path.open("a", encoding="utf-8", newline="")
        self._records_writer = csv.DictWriter(self._records_file, fieldnames=RECORD_FIELDS)
        if write_header:
            self._records_writer.writeheader()
            self._records_file.flush()
        self._missing_file = self.missing_path.open("a", encoding="utf-8")

    def iter_records(self):
        """Yield previously crawled records (dicts with RECORD_FIELDS)."""
        with self.records_path.open(encoding="utf-8", newline="") as f:
            yield from (row for row in csv.DictReader(f) if row.get("InteractionID"))

    def load_done_ids(self) -> set:
        """IDs already crawled or known missing (used to resume)."""
        done = {int(row["InteractionID"]) for row in self.iter_records()}
        with self.missing_path.open(encoding="utf-8") as f:
            done.update(int(line) for line in f if line.strip().isdigit())
        return done

    def add_record(self, record: dict):
        with self._lock:
            self._records_writer.writerow(record)
            self._records_file.flush()

    def add_missing(self, interaction_id: int):
        with self._lock:
            self._missing_file.write(f"{interaction_id}\n")
            self._missing_file.flush()

    def add_failed(self, interaction_id: int, error: str):
        with self._lock:
            self.failed.append((interaction_id, error))

    def close(self):
        """Close append files and rewrite the failed-IDs file for this run."""
        self._records_file.close()
        self._missing_file.close()
        with self.failed_path.open("w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["InteractionID", "Error"])
            writer.writerows(sorted(self.failed))
