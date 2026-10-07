"""
Live check of conditional DeepResearch polling against a real API.

Skipped unless VALYU_LIVE_TESTS=1. Uses VALYU_API_KEY (or VALYU_STAGE_KEY) and VALYU_BASE_URL
(e.g. https://stage.api.valyu.ai/v1). Creates one instant and one fast task,
waits for both through the SDK, and reports how many status polls were full
200 responses against 304 Not Modified, with the bytes the 304s saved.

    VALYU_LIVE_TESTS=1 VALYU_BASE_URL=https://stage.api.valyu.ai/v1 \\
        python3 -m pytest tests/test_deepresearch_polling_live.py -v -s
"""

import os
import time
import unittest

import requests

from valyu import Valyu
from valyu.types.deepresearch import DeepResearchStatus

LIVE = os.getenv("VALYU_LIVE_TESTS") == "1"


class PollCounter:
    """Counts status responses per task through a requests response hook."""

    def __init__(self):
        self.tasks = {}

    def __call__(self, response, *args, **kwargs):
        path = response.request.path_url
        if not path.rstrip("/").endswith("/status"):
            return response
        task_id = path.rstrip("/").split("/")[-2]
        stats = self.tasks.setdefault(
            task_id,
            {"200": 0, "304": 0, "other": 0, "bytes": 0, "saved": 0, "last": 0,
             "etag_sent": 0},
        )
        if "If-None-Match" in response.request.headers:
            stats["etag_sent"] += 1
        size = len(response.content)
        stats["bytes"] += size
        if response.status_code == 200:
            stats["200"] += 1
            stats["last"] = size
        elif response.status_code == 304:
            stats["304"] += 1
            # A 304 stands in for the full body it would have resent.
            stats["saved"] += stats["last"]
        else:
            stats["other"] += 1
        return response


@unittest.skipUnless(LIVE, "set VALYU_LIVE_TESTS=1 to run against a live API")
class ConditionalPollingLiveTest(unittest.TestCase):
    def setUp(self):
        self.counter = PollCounter()
        session = requests.Session()
        session.hooks["response"].append(self.counter)
        self.valyu = Valyu(
            api_key=os.getenv("VALYU_API_KEY") or os.getenv("VALYU_STAGE_KEY"),
            base_url=os.getenv("VALYU_BASE_URL", "https://api.valyu.ai/v1"),
            session=session,
        )

    def _run(self, mode, query):
        task = self.valyu.deepresearch.create(query=query, mode=mode)
        self.assertTrue(task.success, task.error)
        task_id = task.deepresearch_id
        progress_calls = []

        started = time.time()
        result = self.valyu.deepresearch.wait(
            task_id,
            max_wait_time=1800,
            on_progress=lambda s: progress_calls.append(s.status.value),
        )
        elapsed = time.time() - started

        stats = self.counter.tasks[task_id]
        print(f"\n{'=' * 60}")
        print(f"Mode: {mode}  Task: {task_id}")
        print(f"Query: {query}")
        print(f"Status: {result.status.value}  in {elapsed:.0f}s  cost: {result.cost}")
        print(
            f"Polls: {stats['200']} x 200, {stats['304']} x 304, "
            f"{stats['other']} other; If-None-Match sent {stats['etag_sent']} times"
        )
        print(
            f"Bytes received: {stats['bytes']:,}; saved by 304s: {stats['saved']:,}"
        )
        print(f"on_progress calls: {len(progress_calls)} (one per changed response)")
        output = result.output if isinstance(result.output, str) else str(result.output)
        print(f"Output ({len(output)} chars): {output[:400]}...")

        self.assertEqual(result.status, DeepResearchStatus.COMPLETED)
        self.assertTrue(output.strip())
        self.assertLessEqual(len(progress_calls), stats["200"])
        return stats

    def test_instant_task(self):
        self._run("instant", "What is the boiling point of water at the top of Mount Everest?")

    def test_fast_task(self):
        stats = self._run(
            "fast", "What are the main differences between PostgreSQL 16 and 17?"
        )
        # A running v2 task is polled faster than it changes, so some polls
        # must come back 304.
        self.assertGreater(stats["304"], 0)


if __name__ == "__main__":
    unittest.main()
