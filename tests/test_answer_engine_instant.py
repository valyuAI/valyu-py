"""
Tests for answer(engine="deepresearch_instant"): the opt-in path that runs a DeepResearch
`instant` task and adapts it into the Answer API's response shape. The default engine
is untouched by this file.
"""

import unittest
from unittest.mock import patch

from valyu import Valyu
from valyu.types.answer import AnswerErrorResponse, AnswerSuccessResponse
from valyu.types.deepresearch import DeepResearchCreateResponse, DeepResearchStatusResponse, DeepResearchSource


def _client():
    return Valyu(api_key="test-key")


def _completed_status(**overrides):
    defaults = dict(
        success=True,
        deepresearch_id="dr_1",
        status="completed",
        query="what is the capital of australia",
        output="Canberra is the capital of Australia.",
        sources=[
            DeepResearchSource(title="Capital cities", url="https://example.com/a", snippet="Canberra...", source="web"),
        ],
        cost=0.07,
    )
    defaults.update(overrides)
    return DeepResearchStatusResponse(**defaults)


class AnswerDeepResearchInstantTest(unittest.TestCase):
    def test_validates_unsupported_params_before_creating_a_task(self):
        client = _client()
        with patch.object(client.deepresearch, "create") as create:
            with self.assertRaises(ValueError):
                client.answer("q", engine="deepresearch_instant", data_max_price=1.0)
            with self.assertRaises(ValueError):
                client.answer("q", engine="deepresearch_instant", fast_mode=True)
            with self.assertRaises(ValueError):
                client.answer("q", engine="deepresearch_instant", search_type="news")
            create.assert_not_called()

    def test_fetch_adapts_a_completed_instant_task(self):
        client = _client()
        with patch.object(client.deepresearch, "create") as create, patch.object(client.deepresearch, "wait") as wait:
            create.return_value = DeepResearchCreateResponse(success=True, deepresearch_id="dr_1", status="queued")
            wait.return_value = _completed_status()

            result = client.answer("What is the capital of Australia?", engine="deepresearch_instant")

            create.assert_called_once()
            self.assertEqual(create.call_args.kwargs.get("mode"), "instant")
            self.assertIsInstance(result, AnswerSuccessResponse)
            self.assertEqual(result.tx_id, "dr_1")
            self.assertIn("Canberra", result.contents)
            self.assertEqual(len(result.search_results), 1)
            self.assertEqual(result.cost.total_deduction_dollars, 0.07)

    def test_fetch_returns_error_response_on_failed_task(self):
        client = _client()
        with patch.object(client.deepresearch, "create") as create, patch.object(client.deepresearch, "wait") as wait:
            create.return_value = DeepResearchCreateResponse(success=True, deepresearch_id="dr_1", status="queued")
            wait.return_value = DeepResearchStatusResponse(
                success=True, deepresearch_id="dr_1", status="failed", error_message="research.no_evidence"
            )

            result = client.answer("q", engine="deepresearch_instant")

            self.assertIsInstance(result, AnswerErrorResponse)
            self.assertIn("research.no_evidence", result.error)

    def test_streaming_emits_synthetic_search_results_content_metadata_done(self):
        client = _client()
        with patch.object(client.deepresearch, "create") as create, patch.object(client.deepresearch, "wait") as wait:
            create.return_value = DeepResearchCreateResponse(success=True, deepresearch_id="dr_1", status="queued")
            wait.return_value = _completed_status()

            chunks = list(client.answer("q", engine="deepresearch_instant", streaming=True))

            self.assertEqual([c.type for c in chunks], ["search_results", "content", "metadata", "done"])
            self.assertEqual(len(chunks[0].search_results), 1)
            self.assertIn("Canberra", chunks[1].content)
            self.assertEqual(chunks[2].tx_id, "dr_1")

    def test_create_failure_surfaces_as_error_response_not_an_exception(self):
        client = _client()
        with patch.object(client.deepresearch, "create") as create:
            create.return_value = DeepResearchCreateResponse(success=False, error="credits.insufficient")
            result = client.answer("q", engine="deepresearch_instant")
            self.assertIsInstance(result, AnswerErrorResponse)
            self.assertIn("credits.insufficient", result.error)

    def test_streaming_create_error_yields_one_error_chunk(self):
        client = _client()
        with patch.object(client.deepresearch, "create") as create:
            create.side_effect = ValueError("boom")
            chunks = list(client.answer("q", engine="deepresearch_instant", streaming=True))
            self.assertEqual([c.type for c in chunks], ["error"])
            self.assertIn("boom", chunks[0].error)

    def test_default_engine_is_unchanged(self):
        """engine defaults to 'default': no behavior change for existing callers who never pass it."""
        client = _client()
        with patch.object(client, "_fetch_answer") as fetch, patch.object(client.deepresearch, "create") as create:
            fetch.return_value = AnswerErrorResponse(error="irrelevant - just proving the default path is still hit")
            client.answer("q")
            fetch.assert_called_once()
            create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
