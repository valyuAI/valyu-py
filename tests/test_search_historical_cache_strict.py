"""historical_cache_strict — per-request point-in-time strictness.

The API has accepted `historical_cache_strict` (off|prefer|only) on /deepsearch and
/contents for some time, but no SDK exposed it, so a backtesting customer could not
reach strict "only" mode at all without dropping to raw HTTP. These tests pin the
wiring so it cannot silently regress to that state.
"""
import unittest
from unittest.mock import MagicMock

from valyu import Valyu
from valyu._request_builders import build_contents_payload, build_search_payload


def _search_response():
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "error": None,
        "tx_id": "tx_test",
        "query": "fed rate decision",
        "results": [],
        "results_by_source": {"web": 0, "proprietary": 0},
        "total_deduction_dollars": 0.0,
        "total_characters": 0,
    }
    return response


def _search_kwargs(**overrides):
    kwargs = dict(
        query="fed rate decision",
        search_type="all",
        max_num_results=10,
        is_tool_call=True,
        relevance_threshold=0.5,
        max_price=None,
        included_sources=None,
        excluded_sources=None,
        country_code=None,
        response_length=None,
        category=None,
        start_date=None,
        end_date="2026-07-24T04:27:00.000Z",
        fast_mode=False,
        url_only=False,
        source_biases=None,
        instructions=None,
        historical_cache=True,
    )
    kwargs.update(overrides)
    return kwargs


class HistoricalCacheStrictTest(unittest.TestCase):
    def test_sync_search_forwards_historical_cache_strict(self):
        client = Valyu(api_key="val_test")
        client._session.post = MagicMock(return_value=_search_response())

        client.search(
            "fed rate decision",
            historical_cache=True,
            end_date="2026-07-24T04:27:00.000Z",
            historical_cache_strict="only",
        )

        payload = client._session.post.call_args.kwargs["json"]
        self.assertEqual(payload["historical_cache_strict"], "only")

    def test_omitted_strict_is_absent_so_the_api_default_applies(self):
        """Never send a value the caller did not ask for — absent means the API
        picks its own default ("prefer"), which is not ours to override."""
        payload = build_search_payload(**_search_kwargs())
        self.assertNotIn("historical_cache_strict", payload)

    def test_search_payload_carries_each_accepted_mode(self):
        for mode in ("off", "prefer", "only"):
            with self.subTest(mode=mode):
                payload = build_search_payload(**_search_kwargs(historical_cache_strict=mode))
                self.assertEqual(payload["historical_cache_strict"], mode)

    def test_contents_payload_carries_strict(self):
        payload = build_contents_payload(
            urls=["https://example.test/a"],
            summary=None,
            extract_effort=None,
            response_length=None,
            max_price_dollars=None,
            screenshot=False,
            async_mode=False,
            webhook_url=None,
            historical_cache=True,
            historical_cache_strict="only",
        )
        self.assertEqual(payload["historical_cache_strict"], "only")

    def test_contents_omitted_strict_is_absent(self):
        payload = build_contents_payload(
            urls=["https://example.test/a"],
            summary=None,
            extract_effort=None,
            response_length=None,
            max_price_dollars=None,
            screenshot=False,
            async_mode=False,
            webhook_url=None,
            historical_cache=True,
        )
        self.assertNotIn("historical_cache_strict", payload)


if __name__ == "__main__":
    unittest.main()
