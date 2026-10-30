"""
Worker thread loop: owns one proxy, crawls IDs from a shared queue, and swaps to
an unused proxy when the current one is blocked.

Messages sent to ctx.result_queue (consumed by the main thread):
    ("ok", interaction_id, record) / ("missing", interaction_id, None) / ("failed", interaction_id, reason)
    ("log", worker_no, text)         proxy assignment / block notices
    ("worker_exit", worker_no, reason)  always sent exactly once per worker
"""

import queue
import random
import threading
import time
from dataclasses import dataclass

from ddinter_interaction_fetcher import PROXY_DEAD_REASON, fetch_once
from ddinter_proxy_pool import ProxyPool, mask_proxy_url


@dataclass
class CrawlWorkerContext:
    config: object
    pool: ProxyPool
    id_queue: queue.Queue
    result_queue: queue.Queue
    stop_event: threading.Event


def _crawl_id(interaction_id, worker_no, state, ctx):
    """
    Crawl one ID, switching proxies when blocked.
    Returns False if the worker must stop (no unused proxy left), True otherwise.
    """
    config = ctx.config
    for attempt in range(1, config.retries + 1):
        status, payload = fetch_once(interaction_id, state["proxy"], config.timeout_seconds)
        if status in ("ok", "missing"):
            state["errors"] = 0
            ctx.result_queue.put((status, interaction_id, payload))
            return True

        if status == "error":
            state["errors"] += 1
            if state["errors"] >= config.max_consecutive_errors:
                status, payload = "blocked", f"{state['errors']} consecutive errors (last: {payload})"
            elif attempt < config.retries:
                time.sleep(config.backoff_seconds * 2 ** (attempt - 1) + random.uniform(0, 1))
                continue

        if status == "blocked":
            state["errors"] = 0
            if config.use_proxy:
                # Only a dead proxy is blocked across runs; 403/429/error streaks are often temporary
                ctx.pool.mark_blocked(state["proxy"], payload, permanent=payload == PROXY_DEAD_REASON)
                old_proxy, state["proxy"] = state["proxy"], ctx.pool.acquire()
                next_proxy = mask_proxy_url(state["proxy"]) if state["proxy"] else "no unused proxy left"
                ctx.result_queue.put(("log", worker_no, f"proxy {mask_proxy_url(old_proxy)} blocked "
                                      f"({payload}) -> {next_proxy}"))
                if state["proxy"] is None:
                    ctx.id_queue.put(interaction_id)  # let workers that still have a proxy take it
                    return False
            elif attempt < config.retries:
                # Direct connection: nothing to switch to, just back off
                time.sleep(config.backoff_seconds * 2 ** (attempt - 1) + random.uniform(0, 1))
    ctx.result_queue.put(("failed", interaction_id, payload))
    return True


def run_worker(worker_no: int, ctx: CrawlWorkerContext):
    exit_reason = "done"
    try:
        state = {"proxy": ctx.pool.acquire() if ctx.config.use_proxy else None, "errors": 0}
        if ctx.config.use_proxy and state["proxy"] is None:
            exit_reason = "no unused proxy available"
            return
        ctx.result_queue.put(("log", worker_no, f"using {mask_proxy_url(state['proxy'])}"))
        while not ctx.stop_event.is_set():
            try:
                interaction_id = ctx.id_queue.get_nowait()
            except queue.Empty:
                break
            if not _crawl_id(interaction_id, worker_no, state, ctx):
                exit_reason = "no unused proxy left"
                return
            if ctx.config.delay_seconds:
                time.sleep(ctx.config.delay_seconds)
    except Exception as exc:  # never die silently: the main thread waits for worker_exit
        exit_reason = f"crashed: {type(exc).__name__}: {exc}"
    finally:
        ctx.result_queue.put(("worker_exit", worker_no, exit_reason))
