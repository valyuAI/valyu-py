"""Search scope_policy / hls_coverage, source_scope, datasource search and new typed fields."""
import unittest
from unittest.mock import MagicMock

from valyu import Valyu
from valyu._request_builders import build_search_payload
from valyu.types.contents import ContentsResultSuccess
from valyu.types.datasources import Datasource, DatasourcesResponse
from valyu.types.deepresearch import DeepResearchSource, SearchConfig
from valyu.types.response import SearchResponse

_BASE = {
    "success": True,
    "error": None,
    "tx_id": "tx_test",
    "query": "q",
    "results": [],
    "results_by_source": {"web": 0, "proprietary": 0},
    "total_deduction_dollars": 0.0,
    "total_characters": 0,
}


def _http(body):
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = body
    return response


class SearchParamsTest(unittest.TestCase):
    def test_sync_search_sends_scope_policy_and_hls_coverage(self):
        client = Valyu(api_key="val_test")
        client._session.post = MagicMock(return_value=_http(_BASE))
        client.search(
            "q",
            included_sources=["valyu/valyu-arxiv"],
            scope_policy="strict",
            hls_coverage="increased_coverage",
            max_price=6.25,
        )
        payload = client._session.post.call_args.kwargs["json"]
        self.assertEqual(payload["scope_policy"], "strict")
        self.assertEqual(payload["hls_coverage"], "increased_coverage")
        self.assertEqual(payload["max_price"], 6.25)

    def test_omitted_params_are_absent(self):
        client = Valyu(api_key="val_test")
        client._session.post = MagicMock(return_value=_http(_BASE))
        client.search("q")
        payload = client._session.post.call_args.kwargs["json"]
        self.assertNotIn("scope_policy", payload)
        self.assertNotIn("hls_coverage", payload)

    def test_builder_carries_params(self):
        kwargs = dict(
            query="q", search_type="all", max_num_results=10, is_tool_call=True,
            relevance_threshold=0.5, max_price=None, included_sources=None,
            excluded_sources=None, country_code=None, response_length=None,
            category=None, start_date=None, end_date=None, fast_mode=False,
            url_only=False, source_biases=None, instructions=None,
        )
        self.assertNotIn("scope_policy", build_search_payload(**kwargs))
        payload = build_search_payload(**kwargs, scope_policy="advisory", hls_coverage="hls")
        self.assertEqual(payload["scope_policy"], "advisory")
        self.assertEqual(payload["hls_coverage"], "hls")


class ResponseModelsTest(unittest.TestCase):
    def test_source_scope_and_crawl_date_parse(self):
        result = {
            "title": "t", "url": "https://a.test", "content": "c", "source": "web",
            "price": 0.0, "length": 1, "crawl_date": "2024-06-16T08:12:45Z",
        }
        body = dict(_BASE, results=[result], source_scope={
            "policy": "strict",
            "allowed_dataset_ids": ["valyu/valyu-arxiv"],
            "selected_dataset_ids": ["valyu/valyu-arxiv"],
            "returned_dataset_ids": [],
            "omitted_dataset_ids": [],
            "coverage": "unknown",
            "exhaustive": False,
            "errors": [{"code": "source_execution_error"}],
        })
        response = SearchResponse(**body)
        self.assertEqual(response.source_scope.policy, "strict")
        self.assertEqual(response.source_scope.selected_dataset_ids, ["valyu/valyu-arxiv"])
        self.assertFalse(response.source_scope.exhaustive)
        self.assertEqual(response.results[0].crawl_date, "2024-06-16T08:12:45Z")
        self.assertIsNone(SearchResponse(**_BASE).source_scope)

    def test_contents_result_new_fields(self):
        result = ContentsResultSuccess(
            url="https://a.test", status="success", title="t", content="c", length=1,
            source="web", id="10.1/x", doi="10.1/x", authors=["A"], citation_count=3,
            structured_metadata={"k": "v"},
        )
        self.assertEqual(result.structured_metadata, {"k": "v"})
        self.assertEqual(result.citation_count, 3)

    def test_datasource_new_fields(self):
        ds = Datasource(
            id="valyu/valyu-arxiv", name="arXiv", description="d", category="research",
            required_plan={"id": "tier_1", "name": "Ridiculously Cheap", "price": "$29/mo"},
            access_modes=["search"], geography={"x": 1}, capabilities={"y": 2},
            data_source={"provider": "p", "license": "l"},
        )
        self.assertEqual(ds.required_plan["id"], "tier_1")
        self.assertEqual(DatasourcesResponse(success=True, datasources=[ds], total_count=1).total_count, 1)

    def test_deepresearch_fields(self):
        config = SearchConfig(reference_date="2026-07-31", historical_cache_strict="only")
        dumped = config.model_dump(exclude_none=True)
        self.assertEqual(dumped, {"reference_date": "2026-07-31", "historical_cache_strict": "only"})
        source = DeepResearchSource(
            title="t", url="https://a.test",
            locations=[{"excerpt": "x", "page": 3, "piece": 1}],
        )
        self.assertEqual(source.locations[0]["page"], 3)


class DatasourcesSearchTest(unittest.TestCase):
    def test_datasources_search(self):
        client = Valyu(api_key="val_test")
        client._session.get = MagicMock(return_value=_http({
            "success": True, "query": "FDA drug label", "search_mode": "semantic",
            "total_count": 1,
            "results": [{
                "id": "valyu/valyu-drug-labels", "name": "FDA Drug Labels",
                "category": "healthcare", "description": "d", "relevance_score": 0.79,
            }],
        }))
        response = client.datasources_search("FDA drug label", limit=5)
        call = client._session.get.call_args
        self.assertTrue(call.args[0].endswith("/datasources/search"))
        self.assertEqual(call.kwargs["params"], {"q": "FDA drug label", "limit": 5})
        self.assertTrue(response.success)
        self.assertEqual(response.search_mode, "semantic")
        self.assertEqual(response.results[0].relevance_score, 0.79)

    def test_datasources_search_error(self):
        client = Valyu(api_key="val_test")
        bad = _http({"error": "bad"})
        bad.ok = False
        bad.status_code = 400
        client._session.get = MagicMock(return_value=bad)
        response = client.datasources_search("x")
        self.assertFalse(response.success)
        self.assertEqual(response.error, "bad")
        self.assertNotIn("limit", client._session.get.call_args.kwargs["params"])


if __name__ == "__main__":
    unittest.main()
