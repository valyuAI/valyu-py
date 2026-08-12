import unittest
from unittest.mock import MagicMock

from valyu import Valyu
from valyu._request_builders import build_search_payload


def _search_response():
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "error": None,
        "tx_id": "tx_test",
        "query": "cancer immunotherapy",
        "results": [],
        "results_by_source": {"web": 0, "proprietary": 0},
        "total_deduction_dollars": 0.0,
        "total_characters": 0,
    }
    return response


class IncludeAbstractsTest(unittest.TestCase):
    def test_sync_search_forwards_include_abstracts(self):
        client = Valyu(api_key="val_test")
        client._session.post = MagicMock(return_value=_search_response())

        client.search("cancer immunotherapy", include_abstracts=True)

        payload = client._session.post.call_args.kwargs["json"]
        self.assertIs(payload["include_abstracts"], True)

    def test_async_payload_builder_defaults_include_abstracts_to_false(self):
        payload = build_search_payload(
            query="cancer immunotherapy",
            search_type="proprietary",
            max_num_results=10,
            is_tool_call=True,
            relevance_threshold=0.5,
            max_price=None,
            included_sources=["valyu/valyu-pubmed"],
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

        self.assertIs(payload["include_abstracts"], False)


if __name__ == "__main__":
    unittest.main()
