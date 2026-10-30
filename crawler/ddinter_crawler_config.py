"""
Load and validate config.json (shared by the download, merge and crawl scripts).

Keys (all optional, defaults below):
    start_id, end_id        inclusive interaction_id range to crawl
    workers                 number of threads; each owns one proxy at a time
    delay_seconds           sleep per worker after each ID (politeness delay)
    timeout_seconds, retries, backoff_seconds   per-ID HTTP request / retry policy
    max_consecutive_errors  errors in a row on one proxy that count as "blocked"
    progress_every          print progress every N finished IDs
    save_every              rewrite the final CSV every N finished IDs (and at the end)
    use_proxy, proxy_file   proxy settings
    downloads_dir, merged_file, final_file, unmatched_file, crawl_output_dir
                            paths (relative to the crawler workspace folder)
"""

import json
from pathlib import Path
from types import SimpleNamespace

# The crawler folder is a self-contained workspace: relative paths resolve against it
WORKSPACE_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = WORKSPACE_ROOT / "config.json"

DEFAULTS = {
    "start_id": 1,
    # Highest existing ID found by bisection on 2026-10-30 (IDs may have gaps)
    "end_id": 302665,
    "workers": 4,
    "delay_seconds": 0.2,
    "timeout_seconds": 30,
    "retries": 3,
    "backoff_seconds": 2.0,
    "max_consecutive_errors": 5,
    "progress_every": 500,
    "save_every": 2000,
    "use_proxy": True,
    "proxy_file": "proxy.txt",
    "downloads_dir": "data/downloads",
    "merged_file": "data/ddinter_interactions_merged.csv",
    "final_file": "data/ddinter_interactions_final.csv",
    "unmatched_file": "data/ddinter_interactions_unmatched.csv",
    "crawl_output_dir": "data/crawled",
}
PATH_KEYS = ("proxy_file", "downloads_dir", "merged_file", "final_file", "unmatched_file", "crawl_output_dir")
POSITIVE_INT_KEYS = (
    "start_id", "end_id", "workers", "retries", "max_consecutive_errors", "progress_every", "save_every",
)
NON_NEGATIVE_NUMBER_KEYS = ("delay_seconds", "timeout_seconds", "backoff_seconds")


def load_crawler_config(config_path: Path = DEFAULT_CONFIG_PATH) -> SimpleNamespace:
    """Return config with defaults applied and paths resolved; raise ValueError if invalid."""
    with config_path.open(encoding="utf-8") as f:
        user_config = json.load(f)

    unknown = set(user_config) - set(DEFAULTS)
    if unknown:
        raise ValueError(f"Unknown config keys: {sorted(unknown)}")
    config = {**DEFAULTS, **user_config}

    for key in POSITIVE_INT_KEYS:
        if not isinstance(config[key], int) or isinstance(config[key], bool) or config[key] < 1:
            raise ValueError(f"'{key}' must be a positive integer")
    for key in NON_NEGATIVE_NUMBER_KEYS:
        if not isinstance(config[key], (int, float)) or config[key] < 0:
            raise ValueError(f"'{key}' must be a number >= 0")
    if not isinstance(config["use_proxy"], bool):
        raise ValueError("'use_proxy' must be true or false")
    if config["end_id"] < config["start_id"]:
        raise ValueError("'end_id' must be >= 'start_id'")

    for key in PATH_KEYS:
        path = Path(config[key])
        config[key] = path if path.is_absolute() else WORKSPACE_ROOT / path
    return SimpleNamespace(**config)
