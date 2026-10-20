"""
Tests that response parsing fails in the right way, or not at all:

- a status body that doesn't match the model fails fast instead of being
  retried as a network error until wait() times out;
- a successful create never loses the task ID;
- a ``success`` key in a batch or workflow body doesn't break the call;
- wait() answers each HITL interaction once;
- enum values newer than the SDK are kept as strings.
"""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from valyu.batch_client import BatchClient
from valyu.deepresearch_client import DeepResearchClient
from valyu.types.deepresearch import (
    BatchStatus,
    DeepResearchBatch,
    DeepResearchMode,
    DeepResearchStatus,
    DeepResearchStatusResponse,
    InteractionType,
)
from valyu.workflows_client import WorkflowsClient


def _parent():
    return SimpleNamespace(
        base_url="https://api.example.com", headers={}, _session=MagicMock()
    )


def _response(status_code, body):
    response = MagicMock()
    response.status_code = status_code
    response.ok = status_code < 400
    response.text = json.dumps(body)
    response.json.side_effect = lambda: json.loads(json.dumps(body))
    response.headers = {"content-type": "application/json"}
    return response


def _interaction(interaction_id):
    return {
        "interaction_id": interaction_id,
        "type": "plan_review",
        "data": {"plan": "1. Search 2. Write"},
        "created_at": 1760000000000,
        "timeout_ms": 600000,
    }


def _paused(interaction_id):
    return _response(
        200,
        {
            "deepresearch_id": "dr_1",
            "status": "paused",
            "interaction": _interaction(interaction_id),
        },
    )


def _status(status):
    return _response(200, {"deepresearch_id": "dr_1", "status": status})


@patch("valyu.deepresearch_client.random.random", return_value=0.0)
@patch("valyu.deepresearch_client.time.sleep")
class StatusValidationFailsFastTest(unittest.TestCase):
    # created_at must be a string; a number cannot be parsed.
    BAD = {"deepresearch_id": "dr_1", "status": "running", "created_at": 1760000000}

    def test_status_returns_error_without_retrying(self, sleep, _random):
        parent = _parent()
        parent._session.get.return_value = _response(200, self.BAD)

        status = DeepResearchClient(parent).status("dr_1")

        self.assertFalse(status.success)
        self.assertFalse(status.unreachable)
        self.assertIn("Unexpected status response", status.error)
        self.assertIn("created_at", status.error)
        self.assertEqual(parent._session.get.call_count, 1)
        sleep.assert_not_called()

    def test_wait_raises_immediately(self, sleep, _random):
        parent = _parent()
        parent._session.get.return_value = _response(200, self.BAD)

        with self.assertRaises(ValueError) as ctx:
            DeepResearchClient(parent).wait("dr_1", max_wait_time=7200)

        self.assertIn("created_at", str(ctx.exception))
        self.assertEqual(parent._session.get.call_count, 1)
        sleep.assert_not_called()

    def test_stream_reports_error(self, sleep, _random):
        parent = _parent()
        parent._session.get.return_value = _response(200, self.BAD)
        errors = []

        DeepResearchClient(parent).stream("dr_1", on_error=errors.append)

        self.assertEqual(len(errors), 1)
        self.assertIn("created_at", str(errors[0]))

    def test_invalid_json_is_still_transient(self, sleep, _random):
        parent = _parent()
        broken = _response(200, {})
        broken.text = "{not json"
        broken.json.side_effect = ValueError("Expecting property name")
        parent._session.get.side_effect = [broken, _status("running")]

        status = DeepResearchClient(parent).status("dr_1")

        self.assertTrue(status.success)
        self.assertEqual(parent._session.get.call_count, 2)


class CreateKeepsTaskIdTest(unittest.TestCase):
    def test_unparseable_fields_are_dropped(self):
        parent = _parent()
        parent._session.post.return_value = _response(
            202,
            {
                "success": True,
                "deepresearch_id": "dr_1",
                "status": "queued",
                "created_at": 1760000000,
                "metadata": {"ratio": 0.5},
                "public": False,
            },
        )

        task = DeepResearchClient(parent).create(query="q", mode="fast")

        self.assertTrue(task.success)
        self.assertEqual(task.deepresearch_id, "dr_1")
        self.assertEqual(task.status, DeepResearchStatus.QUEUED)
        self.assertIs(task.public, False)
        self.assertIsNone(task.created_at)
        self.assertIsNone(task.metadata)

    def test_workflow_run_keeps_id(self):
        parent = _parent()
        parent._session.post.return_value = _response(
            202, {"deepresearch_id": "dr_2", "workflow": "not-an-object"}
        )

        task = DeepResearchClient(parent).create(workflow_id="ib-company-profile")

        self.assertTrue(task.success)
        self.assertEqual(task.deepresearch_id, "dr_2")
        self.assertIsNone(task.workflow)

    def test_error_response_is_unchanged(self):
        parent = _parent()
        parent._session.post.return_value = _response(400, {"error": "bad mode"})

        task = DeepResearchClient(parent).create(query="q", mode="fast")

        self.assertFalse(task.success)
        self.assertEqual(task.error, "bad mode")
        self.assertIsNone(task.deepresearch_id)


COUNTS = {"total": 1, "queued": 1, "running": 0, "completed": 0, "failed": 0, "cancelled": 0}


class SuccessKeyInBodyTest(unittest.TestCase):
    def _batch(self, method, body, *args, **kwargs):
        parent = _parent()
        parent._session.post.return_value = _response(200, body)
        parent._session.get.return_value = _response(200, body)
        return getattr(BatchClient(parent), method)(*args, **kwargs)

    def test_batch_create(self):
        result = self._batch(
            "create",
            {"success": True, "batch_id": "b_1", "status": "open", "mode": "fast"},
            mode="fast",
        )
        self.assertTrue(result.success, result.error)
        self.assertEqual(result.batch_id, "b_1")

    def test_batch_add_tasks(self):
        result = self._batch(
            "add_tasks",
            {
                "success": True,
                "batch_id": "b_1",
                "added": 1,
                "tasks": [{"deepresearch_id": "dr_1", "status": "queued"}],
                "counts": COUNTS,
            },
            "b_1",
            [{"query": "q"}],
        )
        self.assertTrue(result.success, result.error)
        self.assertEqual(result.added, 1)

    def test_batch_list_tasks(self):
        result = self._batch(
            "list_tasks",
            {
                "success": True,
                "batch_id": "b_1",
                "tasks": [
                    {
                        "deepresearch_id": "dr_1",
                        "query": "q",
                        "status": "queued",
                        "created_at": "2026-10-20T00:00:00Z",
                    }
                ],
                "pagination": {"count": 1, "has_more": False},
            },
            "b_1",
        )
        self.assertTrue(result.success, result.error)
        self.assertEqual(len(result.tasks), 1)

    def test_batch_cancel(self):
        result = self._batch(
            "cancel",
            {"success": True, "batch_id": "b_1", "status": "cancelled"},
            "b_1",
        )
        self.assertTrue(result.success, result.error)
        self.assertEqual(result.status, BatchStatus.CANCELLED)

    def test_workflows(self):
        parent = _parent()
        client = WorkflowsClient(parent)
        cases = [
            ("get", "list", {"success": True, "workflows": [{"slug": "a"}], "total": 1}, ()),
            ("get", "versions", {"success": True, "slug": "a", "versions": [{"version": 1}]}, ("a",)),
            ("post", "preview", {"success": True, "resolved": {"mode": "instant"}}, ("a",)),
            ("delete", "delete", {"success": True, "slug": "a"}, ("a",)),
        ]
        for verb, method, body, args in cases:
            with self.subTest(method=method):
                getattr(parent._session, verb).return_value = _response(200, body)
                result = getattr(client, method)(*args)
                self.assertTrue(result.success, result.error)


@patch("valyu.deepresearch_client.time.sleep")
class InteractionAnsweredOnceTest(unittest.TestCase):
    def _client(self, statuses, respond_ok=True):
        parent = _parent()
        parent._session.get.side_effect = statuses
        parent._session.post.return_value = (
            _response(200, {"success": True, "status": "running"})
            if respond_ok
            else _response(409, {"error": "conflict"})
        )
        return DeepResearchClient(parent), parent._session

    def test_same_interaction_answered_once(self, sleep):
        client, session = self._client(
            [_paused("i_1"), _paused("i_1"), _paused("i_1"), _status("running"), _status("completed")]
        )
        calls = []

        def on_interaction(interaction):
            calls.append(interaction.interaction_id)
            return {"approved": True}

        result = client.wait("dr_1", poll_interval=2, on_interaction=on_interaction)

        self.assertEqual(result.status, DeepResearchStatus.COMPLETED)
        self.assertEqual(calls, ["i_1"])
        self.assertEqual(session.post.call_count, 1)
        self.assertEqual(
            session.post.call_args.kwargs["json"],
            {"interaction_id": "i_1", "response": {"approved": True}},
        )
        # Every poll before the terminal one is followed by the poll interval,
        # including the one that responded.
        self.assertEqual([c.args[0] for c in sleep.call_args_list], [2, 2, 2, 2])

    def test_each_new_interaction_is_answered(self, sleep):
        client, session = self._client(
            [_paused("i_1"), _paused("i_1"), _paused("i_2"), _status("completed")]
        )
        calls = []

        def on_interaction(interaction):
            calls.append(interaction.interaction_id)
            return {"approved": True}

        client.wait("dr_1", poll_interval=1, on_interaction=on_interaction)

        self.assertEqual(calls, ["i_1", "i_2"])
        self.assertEqual(session.post.call_count, 2)

    def test_skipped_interaction_is_offered_again(self, sleep):
        client, session = self._client(
            [_paused("i_1"), _paused("i_1"), _status("completed")]
        )
        calls = []

        def on_interaction(interaction):
            calls.append(interaction.interaction_id)
            return None if len(calls) == 1 else {"approved": True}

        client.wait("dr_1", poll_interval=1, on_interaction=on_interaction)

        self.assertEqual(calls, ["i_1", "i_1"])
        self.assertEqual(session.post.call_count, 1)

    def test_failed_response_is_retried_after_interval(self, sleep):
        client, session = self._client(
            [_paused("i_1"), _paused("i_1"), _status("completed")], respond_ok=False
        )
        calls = []

        def on_interaction(interaction):
            calls.append(interaction.interaction_id)
            return {"approved": True}

        client.wait("dr_1", poll_interval=1, on_interaction=on_interaction)

        self.assertEqual(calls, ["i_1", "i_1"])
        self.assertEqual(sleep.call_count, 2)


class UnknownEnumValuesTest(unittest.TestCase):
    def test_unknown_values_kept_as_strings(self):
        status = DeepResearchStatusResponse(
            success=True,
            status="expired",
            mode="turbo",
            output_type="structured",
            output_formats=["report"],
            interaction={**_interaction("i_1"), "type": "budget_review"},
            hitl_history=[
                {
                    "interaction_id": "i_0",
                    "type": "budget_review",
                    "created_at": 1,
                    "auto_continued": True,
                }
            ],
        )
        self.assertEqual(status.status, "expired")
        self.assertEqual(status.mode, "turbo")
        self.assertEqual(status.output_type, "structured")
        self.assertEqual(status.output_formats, ["report"])
        self.assertEqual(status.interaction.type, "budget_review")
        self.assertEqual(status.hitl_history[0].type, "budget_review")

    def test_known_values_are_enum_members(self):
        status = DeepResearchStatusResponse(
            success=True,
            status="awaiting_input",
            mode="heavy",
            interaction=_interaction("i_1"),
        )
        self.assertIs(status.status, DeepResearchStatus.AWAITING_INPUT)
        self.assertIs(status.mode, DeepResearchMode.HEAVY)
        self.assertIs(status.interaction.type, InteractionType.PLAN_REVIEW)

    def test_wrong_types_still_rejected(self):
        with self.assertRaises(ValueError):
            DeepResearchStatusResponse(success=True, status=3)

    def test_batch_unknown_status_and_toon(self):
        batch = DeepResearchBatch(
            batch_id="b_1",
            status="running",
            mode="fast",
            output_formats=["toon"],
            counts=COUNTS,
            cost=0.0,
            created_at="2026-10-20T00:00:00Z",
        )
        self.assertEqual(batch.status, "running")
        self.assertIs(batch.mode, DeepResearchMode.FAST)
        self.assertEqual(batch.output_formats, ["toon"])


if __name__ == "__main__":
    unittest.main()
