"""
Tests for HTTP 429 (rate limit) handling: the structured `rate_limit` detail
attached to error responses, the automatic retry on `search()`, `contents()`,
`answer()`, `deepresearch.create()`, `batch.create()`, and `batch.add_tasks()`,
and `RateLimitError` raised by `deepresearch.get_assets()`.
"""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from valyu import RateLimitError, Valyu
from valyu.batch_client import BatchClient
from valyu.deepresearch_client import DeepResearchClient


def _response(status_code, body=None, headers=None):
    """A requests-style response."""
    response = MagicMock()
    response.status_code = status_code
    response.ok = status_code < 400
    response.headers = headers or {}
    response.text = "" if body is None else json.dumps(body)
    response.json.return_value = body
    return response


def _search_ok():
    return _response(
        200,
        {
            "success": True,
            "error": None,
            "tx_id": "tx_test",
            "query": "q",
            "results": [],
            "results_by_source": {"web": 0, "proprietary": 0},
            "total_deduction_dollars": 0.0,
            "total_characters": 0,
        },
    )


RICH_429_BODY = {
    "error": "rate_limited",
    "message": (
        "Search rate limit reached: your Pay-as-you-go plan allows 5 "
        "requests per second. Retry after 2 seconds. Upgrade to "
        "Ridiculously Cheap for 10 requests per second: "
        "https://platform.valyu.ai/user/account/billing?tab=plan"
    ),
    "retry_after": 2,
    "plan": "Pay-as-you-go",
    "limit": {"endpoint": "search", "requests_per_second": 5},
    "upgrade_url": "https://platform.valyu.ai/user/account/billing?tab=plan",
}

GENERIC_429_BODY = {
    "error": "rate_limited",
    "message": "Too many requests; retry after 3 seconds",
    "retry_after": 3,
}

ENTERPRISE_429_BODY = {
    "error": "rate_limited",
    "message": "Search rate limit reached: contact us to raise your limit.",
    "retry_after": 1,
    "plan": "Enterprise",
    "limit": {"endpoint": "search", "requests_per_second": 50},
    "contact_url": "https://www.valyu.ai/contact",
}


class SearchRateLimitDetailTest(unittest.TestCase):
    """`search()` surfaces the structured 429 detail without ever raising."""

    def test_rich_429_body_populates_structured_fields(self):
        client = Valyu(api_key="val_test", max_rate_limit_retries=0)
        client._session.post = MagicMock(return_value=_response(429, RICH_429_BODY))

        response = client.search("q")

        self.assertFalse(response.success)
        self.assertIsNotNone(response.rate_limit)
        self.assertEqual(response.rate_limit.retry_after, 2)
        self.assertEqual(response.rate_limit.plan, "Pay-as-you-go")
        self.assertEqual(response.rate_limit.limit.endpoint, "search")
        self.assertEqual(response.rate_limit.limit.requests_per_second, 5)
        self.assertEqual(
            response.rate_limit.upgrade_url,
            "https://platform.valyu.ai/user/account/billing?tab=plan",
        )
        self.assertIsNone(response.rate_limit.contact_url)
        # Never phrased as a billing/credit problem.
        self.assertNotIn("credit", response.error.lower())
        self.assertNotIn("billing", response.error.lower())

    def test_generic_429_body_leaves_structured_fields_none(self):
        """An older server sending only the generic shape must not crash."""
        client = Valyu(api_key="val_test", max_rate_limit_retries=0)
        client._session.post = MagicMock(return_value=_response(429, GENERIC_429_BODY))

        response = client.search("q")

        self.assertFalse(response.success)
        self.assertIsNotNone(response.rate_limit)
        self.assertEqual(response.rate_limit.retry_after, 3)
        self.assertIsNone(response.rate_limit.plan)
        self.assertIsNone(response.rate_limit.limit)
        self.assertIsNone(response.rate_limit.upgrade_url)
        self.assertIsNone(response.rate_limit.contact_url)

    def test_enterprise_tier_gets_contact_url_not_upgrade_url(self):
        client = Valyu(api_key="val_test", max_rate_limit_retries=0)
        client._session.post = MagicMock(
            return_value=_response(429, ENTERPRISE_429_BODY)
        )

        response = client.search("q")

        self.assertIsNone(response.rate_limit.upgrade_url)
        self.assertEqual(response.rate_limit.contact_url, "https://www.valyu.ai/contact")

    def test_bare_429_with_no_body_fields_and_no_header_uses_default(self):
        client = Valyu(api_key="val_test", max_rate_limit_retries=0)
        client._session.post = MagicMock(return_value=_response(429, {}))

        response = client.search("q")

        self.assertIsNotNone(response.rate_limit)
        self.assertEqual(response.rate_limit.retry_after, 1)

    def test_non_429_error_has_no_rate_limit_detail(self):
        client = Valyu(api_key="val_test", max_rate_limit_retries=0)
        client._session.post = MagicMock(
            return_value=_response(500, {"error": "internal_error"})
        )

        response = client.search("q")

        self.assertIsNone(response.rate_limit)


class SearchRateLimitRetryTest(unittest.TestCase):
    """`search()` automatically retries a 429, honoring its retry hint."""

    @patch("valyu._rate_limit.time.sleep")
    def test_retries_until_success_and_honors_retry_after(self, sleep):
        client = Valyu(api_key="val_test")
        client._session.post = MagicMock(
            side_effect=[
                _response(429, {"retry_after": 5}),
                _search_ok(),
            ]
        )

        response = client.search("q")

        self.assertTrue(response.success)
        self.assertEqual(client._session.post.call_count, 2)
        sleep.assert_called_once_with(5)

    @patch("valyu._rate_limit.time.sleep")
    def test_retry_after_header_used_when_body_has_no_retry_after(self, sleep):
        client = Valyu(api_key="val_test")
        client._session.post = MagicMock(
            side_effect=[
                _response(429, {}, headers={"Retry-After": "7"}),
                _search_ok(),
            ]
        )

        client.search("q")

        sleep.assert_called_once_with(7)

    @patch("valyu._rate_limit.time.sleep")
    def test_wait_is_capped_at_60_seconds(self, sleep):
        client = Valyu(api_key="val_test")
        client._session.post = MagicMock(
            side_effect=[
                _response(429, {"retry_after": 600}),
                _search_ok(),
            ]
        )

        client.search("q")

        sleep.assert_called_once_with(60)

    @patch("valyu._rate_limit.time.sleep")
    def test_max_retries_is_enforced_not_infinite(self, sleep):
        client = Valyu(api_key="val_test", max_rate_limit_retries=2)
        always_429 = _response(429, {"retry_after": 0})
        client._session.post = MagicMock(return_value=always_429)

        response = client.search("q")

        self.assertFalse(response.success)
        self.assertIsNotNone(response.rate_limit)
        # Original attempt + 2 retries = 3 calls total; sleep called twice.
        self.assertEqual(client._session.post.call_count, 3)
        self.assertEqual(sleep.call_count, 2)

    @patch("valyu._rate_limit.time.sleep")
    def test_max_rate_limit_retries_zero_disables_retry(self, sleep):
        client = Valyu(api_key="val_test", max_rate_limit_retries=0)
        client._session.post = MagicMock(return_value=_response(429, {"retry_after": 1}))

        response = client.search("q")

        self.assertFalse(response.success)
        self.assertEqual(client._session.post.call_count, 1)
        sleep.assert_not_called()


class ContentsRateLimitTest(unittest.TestCase):
    def test_contents_429_populates_rate_limit_and_retries(self):
        client = Valyu(api_key="val_test")
        ok = _response(
            200,
            {
                "success": True,
                "error": None,
                "tx_id": "tx_1",
                "urls_requested": 1,
                "urls_processed": 1,
                "urls_failed": 0,
                "results": [],
                "total_cost_dollars": 0.0,
                "total_characters": 0,
            },
        )
        with patch("valyu._rate_limit.time.sleep") as sleep:
            client._session.post = MagicMock(
                side_effect=[_response(429, RICH_429_BODY), ok]
            )
            response = client.contents(["https://example.com"])

        self.assertTrue(response.success)
        sleep.assert_called_once_with(2)

    def test_contents_429_without_retry_reports_structured_error(self):
        client = Valyu(api_key="val_test", max_rate_limit_retries=0)
        client._session.post = MagicMock(return_value=_response(429, RICH_429_BODY))

        response = client.contents(["https://example.com"])

        self.assertFalse(response.success)
        self.assertEqual(response.rate_limit.plan, "Pay-as-you-go")
        self.assertNotIn("credit", response.error.lower())


class AnswerRateLimitTest(unittest.TestCase):
    def _stream_response(self, status_code, body, headers=None):
        response = MagicMock()
        response.status_code = status_code
        response.ok = status_code < 400
        response.headers = headers or {}
        response.json.return_value = body
        response.iter_lines.return_value = iter([])
        return response

    def test_answer_429_populates_rate_limit(self):
        client = Valyu(api_key="val_test", max_rate_limit_retries=0)
        client._session.post = MagicMock(
            return_value=self._stream_response(429, RICH_429_BODY)
        )

        response = client.answer("q")

        self.assertFalse(response.success)
        self.assertIsNotNone(response.rate_limit)
        self.assertEqual(response.rate_limit.plan, "Pay-as-you-go")
        self.assertNotIn("credit", response.error.lower())
        self.assertNotIn("billing", response.error.lower())

    @patch("valyu._rate_limit.time.sleep")
    def test_answer_retries_on_429(self, sleep):
        client = Valyu(api_key="val_test")
        done_response = self._stream_response(200, {})
        done_response.ok = True
        done_response.iter_lines.return_value = iter(
            [
                'data: {"success": true, "tx_id": "tx_1", "contents": "answer", '
                '"search_metadata": {"tx_ids": [], "number_of_results": 0, "total_characters": 0}, '
                '"ai_usage": {"input_tokens": 1, "output_tokens": 1}, '
                '"cost": {"total_deduction_dollars": 0, "search_deduction_dollars": 0, "ai_deduction_dollars": 0}}'
            ]
        )
        client._session.post = MagicMock(
            side_effect=[
                self._stream_response(429, {"retry_after": 4}),
                done_response,
            ]
        )

        response = client.answer("q")

        self.assertTrue(response.success)
        sleep.assert_called_once_with(4)


def _dr_client():
    session = MagicMock()
    parent = SimpleNamespace(base_url="https://api.example.com", headers={}, _session=session)
    return DeepResearchClient(parent), session


def _batch_client():
    session = MagicMock()
    parent = SimpleNamespace(base_url="https://api.example.com", headers={}, _session=session)
    return BatchClient(parent), session


class DeepResearchCreateRateLimitTest(unittest.TestCase):
    def test_create_429_populates_rate_limit(self):
        client, session = _dr_client()
        client._max_rate_limit_retries = 0
        session.post.return_value = _response(429, RICH_429_BODY)

        result = client.create(query="q", mode="fast")

        self.assertFalse(result.success)
        self.assertEqual(result.rate_limit.plan, "Pay-as-you-go")
        self.assertNotIn("credit", result.error.lower())

    @patch("valyu._rate_limit.time.sleep")
    def test_create_retries_on_429_and_exposes_queued_message(self, sleep):
        client, session = _dr_client()
        queued = _response(
            201,
            {
                "success": True,
                "deepresearch_id": "dr_1",
                "status": "queued",
                "message": "Queued: your plan runs a limited number of "
                "DeepResearch tasks at once.",
            },
        )
        session.post.side_effect = [_response(429, {"retry_after": 2}), queued]

        result = client.create(query="q", mode="standard")

        self.assertTrue(result.success)
        self.assertEqual(result.deepresearch_id, "dr_1")
        self.assertIn("Queued", result.message)
        sleep.assert_called_once_with(2)

    @patch("valyu._rate_limit.time.sleep")
    def test_create_max_retries_enforced(self, sleep):
        client, session = _dr_client()
        session.post.return_value = _response(429, {"retry_after": 0})
        client._max_rate_limit_retries = 1

        result = client.create(query="q", mode="fast")

        self.assertFalse(result.success)
        self.assertEqual(session.post.call_count, 2)
        self.assertEqual(sleep.call_count, 1)


class BatchRateLimitTest(unittest.TestCase):
    def test_batch_create_429_populates_rate_limit(self):
        client, session = _batch_client()
        client._max_rate_limit_retries = 0
        session.post.return_value = _response(429, RICH_429_BODY)

        result = client.create(name="b")

        self.assertFalse(result.success)
        self.assertEqual(result.rate_limit.plan, "Pay-as-you-go")

    @patch("valyu._rate_limit.time.sleep")
    def test_batch_create_retries_on_429(self, sleep):
        client, session = _batch_client()
        ok = _response(200, {"success": True, "batch_id": "batch_1", "message": "ok"})
        session.post.side_effect = [_response(429, {"retry_after": 1}), ok]

        result = client.create(name="b")

        self.assertTrue(result.success)
        self.assertEqual(result.batch_id, "batch_1")
        sleep.assert_called_once_with(1)

    def test_add_tasks_429_populates_rate_limit(self):
        client, session = _batch_client()
        client._max_rate_limit_retries = 0
        session.post.return_value = _response(429, ENTERPRISE_429_BODY)

        result = client.add_tasks("batch_1", [{"input": "q"}])

        self.assertFalse(result.success)
        self.assertEqual(result.rate_limit.contact_url, "https://www.valyu.ai/contact")
        self.assertIsNone(result.rate_limit.upgrade_url)

    @patch("valyu._rate_limit.time.sleep")
    def test_add_tasks_retries_on_429_and_exposes_message(self, sleep):
        client, session = _batch_client()
        ok = _response(
            200,
            {
                "success": True,
                "batch_id": "batch_1",
                "added": 1,
                "message": "Queued: tasks added but delayed by plan concurrency.",
            },
        )
        session.post.side_effect = [_response(429, {"retry_after": 1}), ok]

        result = client.add_tasks("batch_1", [{"input": "q"}])

        self.assertTrue(result.success)
        self.assertIn("Queued", result.message)
        sleep.assert_called_once_with(1)


class GetAssetsRateLimitErrorTest(unittest.TestCase):
    def test_get_assets_raises_rate_limit_error_on_429(self):
        client, session = _dr_client()
        response = MagicMock()
        response.ok = False
        response.status_code = 429
        response.headers = {"content-type": "application/json", "Retry-After": "9"}
        response.json.return_value = RICH_429_BODY
        session.get.return_value = response

        with self.assertRaises(RateLimitError) as ctx:
            client.get_assets("dr_1", "asset_1")

        err = ctx.exception
        self.assertEqual(err.retry_after, 2)
        self.assertEqual(err.plan, "Pay-as-you-go")
        self.assertEqual(
            err.upgrade_url, "https://platform.valyu.ai/user/account/billing?tab=plan"
        )
        # The server's own message is passed through as-is; only check that
        # the SDK itself never *authors* a credit/billing framing for a 429.
        self.assertNotIn("credit", str(err).lower())

    def test_get_assets_still_raises_http_error_for_other_statuses(self):
        import requests

        client, session = _dr_client()
        response = MagicMock()
        response.ok = False
        response.status_code = 404
        response.headers = {"content-type": "application/json"}
        response.json.return_value = {"error": "not_found"}
        response.text = '{"error": "not_found"}'
        session.get.return_value = response

        with self.assertRaises(requests.HTTPError):
            client.get_assets("dr_1", "asset_1")


if __name__ == "__main__":
    unittest.main()
