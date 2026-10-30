"""
Crawl DDInter 2.0 interaction detail pages and fill the final interactions CSV.

Settings come from config.json (ID range, workers, delay, proxies, paths).
All proxies from proxy_file are loaded up front; each worker thread takes its own
proxy and keeps it until it gets blocked, then takes an unused one. Workers exit
when no unused proxy is left; the rest keep going.
Each crawled record is appended to the raw crawl log and filled into the final CSV
row with the same drug pair (final CSV is created from the merged CSV on first run).
IDs already crawled or known missing are skipped, so re-running resumes.

Usage:
    python crawl-ddinter-interactions.py [--config config.json]
"""

import argparse
import json
import queue
import sys
import threading
import time
from collections import Counter
from pathlib import Path

from ddinter_crawl_output_store import BLOCKED_PROXIES_FILE, CrawlOutputStore
from ddinter_crawl_worker import CrawlWorkerContext, run_worker
from ddinter_crawler_config import DEFAULT_CONFIG_PATH, load_crawler_config
from ddinter_final_interactions_table import FinalInteractionsTable
from ddinter_proxy_pool import ProxyPool

RECORD_KINDS = ("ok", "missing", "failed")


class ResultConsumer:
    """Main-thread consumer: writes worker results to the store / final table."""

    def __init__(self, ctx, store, table, total, worker_count):
        self.ctx, self.store, self.table, self.total = ctx, store, table, total
        self.alive = worker_count
        self.counts = Counter()
        self.started = time.time()

    def consume_until_workers_exit(self):
        while self.alive:
            try:
                kind, key, payload = self.ctx.result_queue.get(timeout=1)
            except queue.Empty:
                continue
            if kind == "worker_exit":
                self.alive -= 1
                if payload != "done":
                    print(f"worker {key} stopped: {payload}", flush=True)
            elif kind == "log":
                print(f"worker {key}: {payload}", flush=True)
            else:
                self._handle_record(kind, key, payload)

    def _handle_record(self, kind, interaction_id, payload):
        self.counts[kind] += 1
        if kind == "ok":
            self.store.add_record(payload)
            self.counts[self.table.fill(payload)] += 1
        elif kind == "missing":
            self.store.add_missing(interaction_id)
        else:
            self.store.add_failed(interaction_id, payload)

        done = sum(self.counts[k] for k in RECORD_KINDS)
        if done % self.ctx.config.save_every == 0:
            self.table.save()
        if done % self.ctx.config.progress_every == 0 or done == self.total:
            c, rate = self.counts, done / max(time.time() - self.started, 1e-9)
            print(f"[{done}/{self.total}] ok={c['ok']} missing={c['missing']} failed={c['failed']} | "
                  f"filled={c['filled']} unmatched={c['unmatched']} duplicate={c['duplicate']} "
                  f"({rate:.1f} id/s) | "
                  f"{self.ctx.pool.describe()}", flush=True)


def run(ids, pool, store, table, config):
    ctx = CrawlWorkerContext(config, pool, queue.Queue(), queue.Queue(), threading.Event())
    for interaction_id in ids:
        ctx.id_queue.put(interaction_id)

    worker_count = min(config.workers, len(pool.proxy_urls)) if config.use_proxy else config.workers
    if worker_count < config.workers:
        print(f"Only {len(pool.proxy_urls)} proxies -> running {worker_count} workers")
    for worker_no in range(1, worker_count + 1):
        threading.Thread(target=run_worker, args=(worker_no, ctx), daemon=True).start()

    consumer = ResultConsumer(ctx, store, table, len(ids), worker_count)
    try:
        consumer.consume_until_workers_exit()
    except KeyboardInterrupt:
        print("Stopping: workers finish their current ID (Ctrl+C again to abort)...", flush=True)
        ctx.stop_event.set()
        consumer.consume_until_workers_exit()

    left = 0 if ctx.stop_event.is_set() else ctx.id_queue.qsize()
    if left:
        print(f"{left} IDs not crawled: all proxies blocked. Add proxies and re-run.")
    return consumer.counts, left


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0].strip())
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    try:
        config = load_crawler_config(parser.parse_args().config)
        blocked_file = config.crawl_output_dir / BLOCKED_PROXIES_FILE
        if config.use_proxy and not config.proxy_file.exists():
            raise ValueError(f"Proxy file not found: {config.proxy_file} "
                             "(copy proxy.example.txt to proxy.txt, or set \"use_proxy\": false)")
        if not config.final_file.exists() and not config.merged_file.exists():
            raise ValueError(f"Merged file not found: {config.merged_file} "
                             "(run download-ddinter-csv.py then merge-ddinter-interactions.py)")
        pool = ProxyPool.from_file(config.proxy_file, blocked_file) if config.use_proxy else ProxyPool([])
        if config.use_proxy and not pool.proxy_urls:
            if pool.skipped_blocked:
                raise ValueError(f"All {len(pool.skipped_blocked)} proxies are listed in {blocked_file}; "
                                 "add new proxies or delete lines there to reuse them")
            raise ValueError(f"No proxies in {config.proxy_file}")
        table = FinalInteractionsTable(config.final_file, config.merged_file, config.unmatched_file)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        sys.exit(f"Startup failed: {exc}")
    if config.use_proxy:
        print(f"Loaded {len(pool.proxy_urls)} usable proxies "
              f"({len(pool.skipped_blocked)} skipped, listed in {blocked_file.name})")
    else:
        print("Direct connection (no proxy)")

    store = CrawlOutputStore(config.crawl_output_dir)
    # Sync records crawled earlier (e.g. before a crash) into the final table
    for record in store.iter_records():
        table.fill(record)
    table.save()

    done_ids = store.load_done_ids()
    ids = [i for i in range(config.start_id, config.end_id + 1) if i not in done_ids]
    total = config.end_id - config.start_id + 1
    print(f"Range {config.start_id}-{config.end_id}: {len(ids)} to crawl, {total - len(ids)} already done")
    print(f"Final table: {table.filled_count()}/{len(table.rows)} rows filled -> {config.final_file}")

    left = 0
    try:
        counts, left = run(ids, pool, store, table, config) if ids else (Counter(), 0)
        print(f"Finished: {dict(counts)}")
    finally:
        store.close()
        table.save()
        print(f"Final table: {table.filled_count()}/{len(table.rows)} rows filled")
        print(f"Not in final table: {len(table.unmatched)} pair_not_in_merged, "
              f"{len(table.duplicates)} duplicate_pair -> {config.unmatched_file}")
        if config.use_proxy:
            print(pool.describe())
        if store.failed:
            print(f"{len(store.failed)} IDs failed -> {store.failed_path} (re-run to retry)")
    if left:
        sys.exit(2)  # ran out of proxies: let scripts/schedulers notice the incomplete run


if __name__ == "__main__":
    main()
