import json
import unittest
from unittest.mock import MagicMock

from valyu import ResponseWarning, Valyu
from valyu.types.deepresearch import DeepResearchStatusResponse
from valyu.types.response import SearchResponse

WARNING = {
    "type": "datasets_not_in_plan",
    "message": "Your plan doesn't include valyu/valyu-biorxiv, so it was skipped.",
    "detail": {
        "upgrade_url": "https://platform.valyu.ai/user/account/billing?tab=plan"
    },
}

SEARCH_BODY = {
    "success": True,
    "tx_id": "tx_test",
    "query": "q",
    "results": [],
    "results_by_source": {"web": 0, "proprietary": 0},
    "total_deduction_dollars": 0.0,
    "total_characters": 0,
}


def _response(**body):
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = body
    response.iter_lines.return_value = [f"data: {json.dumps(body)}", "data: [DONE]"]
    return response


def _client(response):
    client = Valyu(api_key="val_test")
    client._session.post = MagicMock(return_value=response)
    return client


class ResponseWarningsTest(unittest.TestCase):
    def test_object_warning_parses(self):
        response = SearchResponse(**SEARCH_BODY, warnings=[WARNING])
        self.assertEqual(response.warnings, [ResponseWarning(**WARNING)])

    def test_string_warning_normalises(self):
        response = DeepResearchStatusResponse(
            success=True, warnings=["Skipped a dataset"]
        )
        self.assertEqual(
            response.warnings,
            [ResponseWarning(type="warning", message="Skipped a dataset")],
        )

    def test_absent_is_none(self):
        self.assertIsNone(SearchResponse(**SEARCH_BODY).warnings)

    def test_junk_entries_are_dropped(self):
        response = SearchResponse(
            **SEARCH_BODY, warnings=[42, None, {"type": "x"}, "kept", WARNING]
        )
        self.assertEqual(
            [w.message for w in response.warnings], ["kept", WARNING["message"]]
        )
        self.assertIsNone(SearchResponse(**SEARCH_BODY, warnings="oops").warnings)

    def test_search_passes_warnings_through(self):
        client = _client(_response(**SEARCH_BODY, warnings=[WARNING]))
        self.assertEqual(client.search("q").warnings[0].type, "datasets_not_in_plan")

    def test_search_with_no_results_and_error_keeps_warnings(self):
        body = {**SEARCH_BODY, "error": "No results", "warnings": [WARNING]}
        client = _client(_response(**body))
        self.assertEqual(client.search("q").warnings[0].type, "datasets_not_in_plan")

    def test_answer_passes_warnings_through(self):
        body = {
            "success": True,
            "tx_id": "tx_a",
            "contents": "hi",
            "warnings": [WARNING],
        }
        answer = _client(_response(**body)).answer("q")
        self.assertEqual(answer.warnings[0].detail, WARNING["detail"])

    def test_answer_stream_metadata_carries_warnings(self):
        body = {"success": True, "tx_id": "tx_a", "warnings": ["Skipped a dataset"]}
        chunks = list(_client(_response(**body)).answer("q", streaming=True))
        self.assertEqual(chunks[0].type, "metadata")
        self.assertEqual(chunks[0].warnings[0].message, "Skipped a dataset")


if __name__ == "__main__":
    unittest.main()
