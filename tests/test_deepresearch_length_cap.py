"""
Tests for the client-side research_strategy/report_format combined length cap
enforced by DeepResearchClient.create().
"""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from valyu.deepresearch_client import (
    DeepResearchClient,
    MAX_STRATEGY_REPORT_FORMAT_COMBINED_LENGTH,
)


def _make_client():
    """Build a DeepResearchClient with a stubbed session so no network is hit."""
    session = MagicMock()
    parent = SimpleNamespace(
        base_url="https://api.example.com",
        headers={},
        _session=session,
    )
    return DeepResearchClient(parent), session


def _ok_response():
    """A fake requests-style response representing a successful create."""
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "deepresearch_id": "dr_123",
        "status": "queued",
    }
    return response


class CombinedLengthCapTest(unittest.TestCase):
    def test_exactly_limit_passes_guard(self):
        """A combined length of exactly the limit must NOT short-circuit."""
        client, session = _make_client()
        session.post.return_value = _ok_response()

        half = MAX_STRATEGY_REPORT_FORMAT_COMBINED_LENGTH // 2
        research_strategy = "a" * half
        report_format = "b" * (MAX_STRATEGY_REPORT_FORMAT_COMBINED_LENGTH - half)
        self.assertEqual(
            len(research_strategy) + len(report_format),
            MAX_STRATEGY_REPORT_FORMAT_COMBINED_LENGTH,
        )

        result = client.create(
            query="test query",
            research_strategy=research_strategy,
            report_format=report_format,
        )

        # Guard did not fire: it reached the network layer and succeeded.
        session.post.assert_called_once()
        self.assertTrue(result.success)
        self.assertIsNone(result.error)

    def test_one_over_limit_returns_error(self):
        """One character over the limit returns the server-identical 400 error."""
        client, session = _make_client()

        combined = MAX_STRATEGY_REPORT_FORMAT_COMBINED_LENGTH + 1
        research_strategy = "a" * combined

        result = client.create(
            query="test query",
            research_strategy=research_strategy,
        )

        # Guard fired before any network call.
        session.post.assert_not_called()
        self.assertFalse(result.success)
        self.assertEqual(
            result.error,
            f"research_strategy and report_format combined length ({combined}) "
            f"exceeds 15,000 character limit",
        )

    def test_legacy_strategy_alias_counts(self):
        """The legacy `strategy` alias is counted when research_strategy is unset."""
        client, session = _make_client()

        combined = MAX_STRATEGY_REPORT_FORMAT_COMBINED_LENGTH + 1
        result = client.create(
            query="test query",
            strategy="a" * combined,
        )

        session.post.assert_not_called()
        self.assertFalse(result.success)
        self.assertEqual(
            result.error,
            f"research_strategy and report_format combined length ({combined}) "
            f"exceeds 15,000 character limit",
        )

    def test_research_strategy_wins_over_legacy_alias(self):
        """When both are sent, research_strategy takes precedence (server parity)."""
        client, session = _make_client()
        session.post.return_value = _ok_response()

        # A short research_strategy wins over a huge legacy strategy, so the
        # combined length is small and the guard does not fire.
        result = client.create(
            query="test query",
            research_strategy="short",
            strategy="a" * (MAX_STRATEGY_REPORT_FORMAT_COMBINED_LENGTH + 1),
        )

        session.post.assert_called_once()
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()
