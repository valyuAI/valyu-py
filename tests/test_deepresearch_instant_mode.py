"""
Tests for the "instant" DeepResearch mode.

An instant task's create and status responses carry the mode as
``research_mode`` and leave out ``mode``; the SDK exposes ``research_mode``
and fills ``mode`` from it.
"""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from valyu.deepresearch_client import DeepResearchClient
from valyu.types.deepresearch import (
    DeepResearchCreateResponse,
    DeepResearchMode,
    DeepResearchStatus,
    DeepResearchStatusResponse,
)
from valyu.types.workflows import ResolvedWorkflowTemplate


def _make_client():
    session = MagicMock()
    parent = SimpleNamespace(
        base_url="https://api.example.com", headers={}, _session=session
    )
    return DeepResearchClient(parent), session


def _response(status_code, body):
    response = MagicMock()
    response.status_code = status_code
    response.ok = status_code < 400
    response.text = json.dumps(body)
    response.json.side_effect = lambda: dict(body)
    response.headers = {"content-type": "application/json"}
    return response


# Shapes observed from the API for an instant task (trimmed).
INSTANT_CREATE = {
    "deepresearch_id": "dr_1",
    "status": "queued",
    "created_at": "2026-10-20T10:22:34.486Z",
    "metadata": {},
    "public": False,
    "research_mode": "instant",
    "warnings": [],
}
INSTANT_COMPLETED = {
    "deepresearch_id": "dr_1",
    "status": "completed",
    "query": "What is the capital of Australia?",
    "output_formats": ["markdown"],
    "progress": {"current_step": 2, "total_steps": 1},
    "output": "Canberra.",
    "output_type": "markdown",
    "cost": 0.05,
    "cost_breakdown": {"task": 0.05},
    "research_mode": "instant",
}


class InstantModeTest(unittest.TestCase):
    def test_enum_has_instant(self):
        self.assertEqual(DeepResearchMode("instant"), DeepResearchMode.INSTANT)
        self.assertEqual(DeepResearchMode.INSTANT.value, "instant")

    def test_create_sends_instant_and_reads_research_mode(self):
        client, session = _make_client()
        session.post.return_value = _response(202, INSTANT_CREATE)

        task = client.create(query="What is the capital of Australia?", mode="instant")

        self.assertEqual(session.post.call_args.kwargs["json"]["mode"], "instant")
        self.assertTrue(task.success)
        self.assertEqual(task.deepresearch_id, "dr_1")
        self.assertEqual(task.research_mode, "instant")
        self.assertEqual(task.mode, DeepResearchMode.INSTANT)

    def test_create_accepts_enum_member(self):
        client, session = _make_client()
        session.post.return_value = _response(202, INSTANT_CREATE)

        client.create(query="q", mode=DeepResearchMode.INSTANT)

        self.assertEqual(session.post.call_args.kwargs["json"]["mode"], "instant")

    @patch("valyu.deepresearch_client.time.sleep")
    def test_status_without_mode(self, _sleep):
        client, session = _make_client()
        session.get.return_value = _response(200, INSTANT_COMPLETED)

        status = client.wait("dr_1")

        self.assertTrue(status.success)
        self.assertEqual(status.status, DeepResearchStatus.COMPLETED)
        self.assertEqual(status.mode, DeepResearchMode.INSTANT)
        self.assertEqual(status.research_mode, "instant")
        self.assertEqual(status.cost, 0.05)

    def test_mode_wins_over_research_mode(self):
        status = DeepResearchStatusResponse(
            success=True, mode="fast", research_mode="instant"
        )
        self.assertEqual(status.mode, DeepResearchMode.FAST)
        self.assertEqual(status.research_mode, "instant")

    def test_neither_mode_nor_research_mode(self):
        created = DeepResearchCreateResponse(success=True, deepresearch_id="dr_1")
        self.assertIsNone(created.mode)
        self.assertIsNone(created.research_mode)

    def test_workflow_resolved_instant(self):
        self.assertEqual(ResolvedWorkflowTemplate(mode="instant").mode, "instant")


if __name__ == "__main__":
    unittest.main()
