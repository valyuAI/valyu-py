"""
Tests for conditional DeepResearch status polling: ETag / If-None-Match,
304 reuse, Retry-After, and backoff on 429/5xx.
"""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from valyu.deepresearch_client import DeepResearchClient
from valyu.types.deepresearch import DeepResearchMode, DeepResearchStatus

URL = "https://api.example.com/deepresearch/tasks/dr_1/status"


def _make_client():
    session = MagicMock()
    parent = SimpleNamespace(
        base_url="https://api.example.com",
        headers={},
        _session=session,
    )
    return DeepResearchClient(parent), session


def _response(status_code=200, body=None, headers=None):
    """A requests-style response. ``body=None`` means an empty body."""
    import json

    response = MagicMock()
    response.status_code = status_code
    response.ok = status_code < 400
    response.text = "" if body is None else json.dumps(body)
    response.json.side_effect = (
        (lambda: dict(body)) if body is not None else ValueError("empty body")
    )
    all_headers = {"content-type": "application/json"} if body is not None else {}
    all_headers.update(headers or {})
    response.headers = all_headers
    return response


def _running(step=1, etag=None, retry_after=None):
    headers = {}
    if etag:
        headers["ETag"] = etag
    if retry_after is not None:
        headers["Retry-After"] = str(retry_after)
    return _response(
        200,
        {
            "success": True,
            "deepresearch_id": "dr_1",
            "status": "running",
            "progress": {"current_step": step, "total_steps": 5},
        },
        headers,
    )


def _completed(etag=None):
    return _response(
        200,
        {
            "success": True,
            "deepresearch_id": "dr_1",
            "status": "completed",
            "output": "the report",
        },
        {"ETag": etag} if etag else {},
    )


def _not_modified(retry_after=None):
    headers = {"Retry-After": str(retry_after)} if retry_after is not None else {}
    return _response(304, None, headers)


def _sent_if_none_match(call):
    return (call.kwargs.get("headers") or {}).get("If-None-Match")


@patch("valyu.deepresearch_client.random.random", return_value=0.0)
@patch("valyu.deepresearch_client.time.sleep")
class ConditionalPollingTest(unittest.TestCase):
    def test_etag_round_trip(self, sleep, _random):
        client, session = _make_client()
        session.get.side_effect = [
            _running(etag='W/"dr_1:1:running"'),
            _running(step=2, etag='W/"dr_1:2:running"'),
            _not_modified(),
        ]

        client.status("dr_1")
        client.status("dr_1")
        client.status("dr_1")

        calls = session.get.call_args_list
        self.assertIsNone(_sent_if_none_match(calls[0]))
        self.assertEqual(_sent_if_none_match(calls[1]), 'W/"dr_1:1:running"')
        # The newest ETag replaces the old one.
        self.assertEqual(_sent_if_none_match(calls[2]), 'W/"dr_1:2:running"')

    def test_304_reuses_cached_response(self, sleep, _random):
        client, session = _make_client()
        not_modified = _not_modified()
        session.get.side_effect = [_running(step=3, etag='W/"e1"'), not_modified]

        first = client.status("dr_1")
        second = client.status("dr_1")

        self.assertTrue(second.success)
        self.assertEqual(second.status, DeepResearchStatus.RUNNING)
        self.assertEqual(second.progress.current_step, 3)
        self.assertEqual(second, first)
        # The 304's empty body is never parsed, and no retry happens.
        not_modified.json.assert_not_called()
        self.assertEqual(session.get.call_count, 2)
        sleep.assert_not_called()

    def test_cache_is_per_task(self, sleep, _random):
        client, session = _make_client()
        session.get.side_effect = [_running(etag='W/"e1"'), _running(etag='W/"e2"')]

        client.status("dr_1")
        client.status("dr_2")

        self.assertIsNone(_sent_if_none_match(session.get.call_args_list[1]))

    def test_no_etag_keeps_plain_polling(self, sleep, _random):
        client, session = _make_client()
        session.get.side_effect = [_running(), _running(step=2), _completed()]

        result = client.wait("dr_1")

        self.assertEqual(result.status, DeepResearchStatus.COMPLETED)
        for call in session.get.call_args_list:
            self.assertEqual(call.args, (URL,))
            self.assertNotIn("headers", call.kwargs)
        # The default 5s interval, as before.
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [5, 5])

    def test_retry_after_sets_poll_interval(self, sleep, _random):
        client, session = _make_client()
        session.get.side_effect = [
            _running(etag='W/"e1"', retry_after=7),
            _not_modified(retry_after=7),
            _completed(etag='W/"e2"'),
        ]

        client.wait("dr_1")

        self.assertEqual([c.args[0] for c in sleep.call_args_list], [7, 7])

    def test_retry_after_is_clamped(self, sleep, _random):
        client, session = _make_client()
        session.get.side_effect = [
            _running(etag='W/"e1"', retry_after=0),
            _running(step=2, etag='W/"e2"', retry_after=600),
            _completed(),
        ]

        client.wait("dr_1")

        self.assertEqual([c.args[0] for c in sleep.call_args_list], [1, 30])

    def test_user_poll_interval_wins_over_retry_after(self, sleep, _random):
        client, session = _make_client()
        session.get.side_effect = [
            _running(etag='W/"e1"', retry_after=7),
            _completed(),
        ]

        client.wait("dr_1", poll_interval=2)

        self.assertEqual([c.args[0] for c in sleep.call_args_list], [2])

    def test_on_progress_fires_only_on_change(self, sleep, _random):
        client, session = _make_client()
        session.get.side_effect = [
            _running(step=1, etag='W/"e1"'),
            _not_modified(),
            _not_modified(),
            _running(step=2, etag='W/"e2"'),
            _completed(etag='W/"e3"'),
        ]
        seen = []

        client.wait("dr_1", on_progress=lambda s: seen.append(s.status.value))

        self.assertEqual(seen, ["running", "running", "completed"])

    def test_on_progress_skips_identical_body_without_etag(self, sleep, _random):
        client, session = _make_client()
        session.get.side_effect = [_running(), _running(), _completed()]
        seen = []

        client.wait("dr_1", on_progress=lambda s: seen.append(s.status.value))

        self.assertEqual(seen, ["running", "completed"])

    def test_stream_progress_fires_only_on_change(self, sleep, _random):
        client, session = _make_client()
        session.get.side_effect = [
            _running(step=1, etag='W/"e1"', retry_after=4),
            _not_modified(retry_after=4),
            _completed(etag='W/"e2"'),
        ]
        progress, done = [], []

        client.stream(
            "dr_1",
            on_progress=lambda cur, total: progress.append(cur),
            on_complete=done.append,
        )

        self.assertEqual(progress, [1])
        self.assertEqual(len(done), 1)
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [4, 4])

    def test_backoff_on_429_and_503(self, sleep, _random):
        client, session = _make_client()
        session.get.side_effect = [
            _response(429, {"error": "rate limited"}),
            _response(503, None),
            _response(502, None),
            _running(etag='W/"e1"'),
        ]

        status = client.status("dr_1")

        self.assertTrue(status.success)
        # Exponential: 1, 2, 4 seconds (jitter patched to zero).
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [1, 2, 4])

    def test_backoff_is_jittered(self, sleep, _random):
        _random.return_value = 0.5
        client, session = _make_client()
        session.get.side_effect = [_response(503, None), _running()]

        client.status("dr_1")

        self.assertEqual(sleep.call_args_list[0].args[0], 1.5)

    def test_backoff_honours_longer_retry_after_on_429(self, sleep, _random):
        client, session = _make_client()
        session.get.side_effect = [
            _response(429, {"error": "slow down"}, {"Retry-After": "12"}),
            _running(),
        ]

        client.status("dr_1")

        self.assertEqual(sleep.call_args_list[0].args[0], 12)

    def test_unrequested_304_is_retried_not_parsed(self, sleep, _random):
        client, session = _make_client()
        stray = _not_modified()
        session.get.side_effect = [stray, _running()]

        status = client.status("dr_1")

        self.assertTrue(status.success)
        stray.json.assert_not_called()
        self.assertEqual(session.get.call_count, 2)

    def test_mutating_a_result_does_not_touch_the_cache(self, sleep, _random):
        client, session = _make_client()
        session.get.side_effect = [_running(etag='W/"e1"'), _not_modified()]

        first = client.status("dr_1")
        first.status = DeepResearchStatus.FAILED
        second = client.status("dr_1")

        self.assertEqual(second.status, DeepResearchStatus.RUNNING)


class InstantModeTest(unittest.TestCase):
    def test_instant_is_a_mode(self):
        self.assertEqual(DeepResearchMode("instant"), DeepResearchMode.INSTANT)

    def test_create_sends_instant(self):
        client, session = _make_client()
        session.post.return_value = _response(
            200, {"success": True, "deepresearch_id": "dr_1", "status": "queued"}
        )

        result = client.create(query="What is the capital of France?", mode="instant")

        self.assertTrue(result.success)
        self.assertEqual(session.post.call_args.kwargs["json"]["mode"], "instant")

    def test_status_parses_instant_task(self):
        client, session = _make_client()
        session.get.return_value = _response(
            200,
            {
                "success": True,
                "deepresearch_id": "dr_1",
                "status": "running",
                "mode": "instant",
            },
        )

        status = client.status("dr_1")

        self.assertTrue(status.success)
        self.assertEqual(status.mode, DeepResearchMode.INSTANT)

    def test_lite_still_maps_to_standard(self):
        client, session = _make_client()
        session.post.return_value = _response(
            200, {"success": True, "deepresearch_id": "dr_1", "status": "queued"}
        )

        client.create(query="q", mode="lite")

        self.assertEqual(session.post.call_args.kwargs["json"]["mode"], "standard")


if __name__ == "__main__":
    unittest.main()
