import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from valyu import AsyncValyu, Valyu
from valyu._request_builders import build_contents_payload, build_search_payload


def _search_response():
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "error": None,
        "tx_id": "tx_test",
        "query": "q",
        "results": [],
        "results_by_source": {"web": 0, "proprietary": 0},
        "total_deduction_dollars": 0.0,
        "total_characters": 0,
    }
    return response


def _contents_response():
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
        "results": [],
        "total_cost_dollars": 0.0,
        "total_characters": 0,
    }
    return response


def _search_kwargs(**extra):
    kwargs = dict(
        query="q",
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
        end_date=None,
        fast_mode=False,
        url_only=False,
        source_biases=None,
        instructions=None,
    )
    kwargs.update(extra)
    return kwargs


def _contents_kwargs(**extra):
    kwargs = dict(
        urls=["https://example.com"],
        summary=None,
        extract_effort=None,
        response_length=None,
        max_price_dollars=None,
        screenshot=False,
        async_mode=False,
        webhook_url=None,
    )
    kwargs.update(extra)
    return kwargs


class IncludeImageLinksBuilderTest(unittest.TestCase):
    def test_search_omits_field_by_default(self):
        self.assertNotIn("include_image_links", build_search_payload(**_search_kwargs()))

    def test_search_omits_field_when_true(self):
        payload = build_search_payload(**_search_kwargs(include_image_links=True))
        self.assertNotIn("include_image_links", payload)

    def test_search_sends_field_when_false(self):
        payload = build_search_payload(**_search_kwargs(include_image_links=False))
        self.assertIs(payload["include_image_links"], False)

    def test_contents_omits_field_by_default(self):
        self.assertNotIn(
            "include_image_links", build_contents_payload(**_contents_kwargs())
        )

    def test_contents_omits_field_when_true(self):
        payload = build_contents_payload(**_contents_kwargs(include_image_links=True))
        self.assertNotIn("include_image_links", payload)

    def test_contents_sends_field_when_false(self):
        payload = build_contents_payload(**_contents_kwargs(include_image_links=False))
        self.assertIs(payload["include_image_links"], False)


class IncludeImageLinksSyncTest(unittest.TestCase):
    def _client(self, response):
        client = Valyu(api_key="val_test")
        client._session.post = MagicMock(return_value=response)
        return client

    def _payload(self, client):
        return client._session.post.call_args.kwargs["json"]

    def test_search_default_omits_field(self):
        client = self._client(_search_response())
        client.search("q")
        self.assertNotIn("include_image_links", self._payload(client))

    def test_search_true_omits_field(self):
        client = self._client(_search_response())
        client.search("q", include_image_links=True)
        self.assertNotIn("include_image_links", self._payload(client))

    def test_search_false_sends_field(self):
        client = self._client(_search_response())
        client.search("q", include_image_links=False)
        self.assertIs(self._payload(client)["include_image_links"], False)

    def test_contents_default_omits_field(self):
        client = self._client(_contents_response())
        client.contents(["https://example.com"])
        self.assertNotIn("include_image_links", self._payload(client))

    def test_contents_false_sends_field(self):
        client = self._client(_contents_response())
        client.contents(["https://example.com"], include_image_links=False)
        self.assertIs(self._payload(client)["include_image_links"], False)


class IncludeImageLinksAsyncTest(unittest.TestCase):
    def _run(self, method, response, **kwargs):
        client = AsyncValyu(api_key="val_test")
        client._post = AsyncMock(return_value=response)
        arg = "q" if method == "search" else ["https://example.com"]
        asyncio.run(getattr(client, method)(arg, **kwargs))
        return client._post.call_args.args[1]

    def test_search_default_omits_field(self):
        self.assertNotIn("include_image_links", self._run("search", _search_response()))

    def test_search_false_sends_field(self):
        payload = self._run("search", _search_response(), include_image_links=False)
        self.assertIs(payload["include_image_links"], False)

    def test_contents_default_omits_field(self):
        self.assertNotIn(
            "include_image_links", self._run("contents", _contents_response())
        )

    def test_contents_false_sends_field(self):
        payload = self._run("contents", _contents_response(), include_image_links=False)
        self.assertIs(payload["include_image_links"], False)


if __name__ == "__main__":
    unittest.main()
