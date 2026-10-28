import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from valyu import AsyncValyu, Valyu
from valyu.types.contents import ContentsResponse


def _contents_response(results=None):
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "error": None,
        "tx_id": "tx_test",
        "urls_requested": 1,
        "urls_processed": 1,
        "urls_failed": 0,
        "results": results or [],
        "total_cost_dollars": 0.0,
        "total_characters": 0,
    }
    return response


class MaxAgeSyncTest(unittest.TestCase):
    def _payload(self, **kwargs):
        client = Valyu(api_key="val_test")
        client._session.post = MagicMock(return_value=_contents_response())
        client.contents(["https://example.com"], **kwargs)
        return client._session.post.call_args.kwargs["json"]

    def test_omitted_by_default(self):
        self.assertNotIn("max_age", self._payload())

    def test_zero_is_sent(self):
        self.assertEqual(self._payload(max_age=0)["max_age"], 0)

    def test_value_is_sent(self):
        self.assertEqual(self._payload(max_age=3600)["max_age"], 3600)


class MaxAgeAsyncTest(unittest.TestCase):
    def _payload(self, **kwargs):
        client = AsyncValyu(api_key="val_test")
        client._post = AsyncMock(return_value=_contents_response())
        asyncio.run(client.contents(["https://example.com"], **kwargs))
        return client._post.call_args.args[1]

    def test_omitted_by_default(self):
        self.assertNotIn("max_age", self._payload())

    def test_zero_is_sent(self):
        self.assertEqual(self._payload(max_age=0)["max_age"], 0)


class CacheFieldsTest(unittest.TestCase):
    def test_result_exposes_cache_fields(self):
        row = {
            "url": "https://example.com", "status": "success", "title": "T",
            "content": "text", "length": 4, "source": "web",
            "cache_state": "stale", "crawled_at": "2026-10-28T10:00:00+00:00",
        }
        result = ContentsResponse(**_contents_response([row]).json.return_value).results[0]
        self.assertEqual(result.cache_state, "stale")
        self.assertEqual(result.crawled_at, "2026-10-28T10:00:00+00:00")

    def test_fields_are_optional(self):
        row = {
            "url": "https://example.com", "status": "success", "title": "T",
            "content": "text", "length": 4, "source": "web",
        }
        result = ContentsResponse(**_contents_response([row]).json.return_value).results[0]
        self.assertIsNone(result.cache_state)
        self.assertIsNone(result.crawled_at)


if __name__ == "__main__":
    unittest.main()
