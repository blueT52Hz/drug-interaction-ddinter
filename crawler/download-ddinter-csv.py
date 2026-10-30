"""
Download the DDInter 2.0 interaction CSV files (one per ATC group) into downloads_dir.

The DDInter download page only links 8 groups (A,B,D,H,L,P,R,V), but files for
C,G,J,M,N,S exist at the same URL pattern; all 14 are needed for a complete merge.
Existing files are skipped unless --force is given. Static files: no proxy is used.

Usage:
    python download-ddinter-csv.py [--config config.json] [--force]
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests

from ddinter_crawler_config import DEFAULT_CONFIG_PATH, load_crawler_config

DOWNLOAD_URL = "https://ddinter2.scbdd.com/static/media/download/ddinter_downloads_code_{group}.csv"
ATC_GROUPS = "ABCDGHJLMNPRSV"
EXPECTED_HEADER = b"DDInterID_A"


def download_group(group: str, target: Path, timeout: float) -> int:
    """Download one ATC group file atomically; return its size in bytes."""
    response = requests.get(DOWNLOAD_URL.format(group=group), timeout=timeout)
    response.raise_for_status()
    # A missing file may come back as an HTML error page with status 200
    if EXPECTED_HEADER not in response.content[:200]:
        raise ValueError("response is not a DDInter interaction CSV")
    tmp_path = target.with_suffix(".csv.tmp")
    tmp_path.write_bytes(response.content)
    os.replace(tmp_path, target)
    return len(response.content)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--force", action="store_true", help="re-download files that already exist")
    args = parser.parse_args()

    try:
        config = load_crawler_config(args.config)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        sys.exit(f"Invalid config: {exc}")
    config.downloads_dir.mkdir(parents=True, exist_ok=True)

    failed = []
    for group in ATC_GROUPS:
        target = config.downloads_dir / f"ddinter_downloads_code_{group}.csv"
        if target.exists() and not args.force:
            print(f"{group}: exists, skipped")
            continue
        try:
            size = download_group(group, target, config.timeout_seconds)
            print(f"{group}: {size / 1024:.0f} KB -> {target.name}")
        except (requests.RequestException, OSError, ValueError) as exc:
            failed.append(group)
            print(f"{group}: FAILED ({type(exc).__name__}: {exc})")

    if failed:
        sys.exit(f"{len(failed)} group(s) failed: {', '.join(failed)} (re-run to retry)")
    print(f"All {len(ATC_GROUPS)} groups in {config.downloads_dir}")


if __name__ == "__main__":
    main()
