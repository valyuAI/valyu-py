"""
Tests for DeepResearch report editing (no network): the request the SDK
sends, how 200/202/error/decline responses parse, wait_for_edit polling, and
reading a report version through status().
"""

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from valyu.deepresearch_client import DeepResearchClient
from valyu.types.deepresearch import DeepResearchEditFocus, DeepResearchEditStatus

BASE = "https://api.example.com"


def _make_client():
    session = MagicMock()
    parent = SimpleNamespace(base_url=BASE, headers={}, _session=session)
    return DeepResearchClient(parent), session


def _response(status_code=200, body=None, headers=None):
    response = MagicMock()
    response.status_code = status_code
    response.ok = status_code < 400
    response.text = json.dumps(body)
    response.json.side_effect = lambda: dict(body)
    response.headers = {"content-type": "application/json", **(headers or {})}
    return response


def _record(status, **extra):
    return {
        "edit_id": "ed_1",
        "deepresearch_id": "dr_1",
        "status": status,
        "target": {"kind": "report"},
        "base_version": 1,
        "created_at": "2026-11-19T14:20:00.000Z",
        **extra,
    }


APPLIED = _record(
    "applied",
    version=2,
    summary="Condensed the summary.",
    changes=[{"section": "Executive Summary", "description": "3 bullets"}],
    unapplied=[],
    stats={"replacements": 1},
    warnings=[{"type": "deliverables_stale", "message": "Files were not changed."}],
    pdf_url="https://api.example.com/report.pdf?version=2",
)


class TestEditRequest(unittest.TestCase):
    def test_sends_only_set_fields_and_key_as_header(self):
        """The endpoint rejects unknown or null fields with 400, so a bare
        edit must send only the instruction, and the idempotency key must
        travel as a header rather than in the body."""
        client, session = _make_client()
        session.post.return_value = _response(202, _record("running", retry_after_seconds=3))

        client.edit("dr_1", "Fix the Q3 figure", idempotency_key="key-1")

        call = session.post.call_args
        self.assertEqual(call.args[0], f"{BASE}/deepresearch/tasks/dr_1/edit")
        self.assertEqual(call.kwargs["json"], {"instruction": "Fix the Q3 figure"})
        self.assertEqual(call.kwargs["headers"], {"Idempotency-Key": "key-1"})

    def test_optional_fields_serialize_without_nulls(self):
        """Models and dicts with None values must not leak null keys."""
        client, session = _make_client()
        session.post.return_value = _response(200, APPLIED)

        client.edit(
            "dr_1",
            "Soften this claim",
            target={"kind": "deliverable", "deliverable_id": "f_01"},
            focus=DeepResearchEditFocus(start_char=10, end_char=20, scope="strict"),
            base_version=1,
            citations="compact",
            wait_seconds=15,
        )
        client.edit("dr_1", "x", focus={"section": "Outlook", "text": None})

        first = session.post.call_args_list[0].kwargs["json"]
        self.assertEqual(
            first,
            {
                "instruction": "Soften this claim",
                "target": {"kind": "deliverable", "deliverable_id": "f_01"},
                "focus": {"start_char": 10, "end_char": 20, "scope": "strict"},
                "base_version": 1,
                "citations": "compact",
                "wait_seconds": 15,
            },
        )
        self.assertEqual(
            session.post.call_args_list[1].kwargs["json"]["focus"], {"section": "Outlook"}
        )

    def test_focus_offsets_must_pair(self):
        with self.assertRaises(ValueError):
            DeepResearchEditFocus(start_char=5)
        with self.assertRaises(ValueError):
            DeepResearchEditFocus(start_char=5, end_char=5)


class TestEditResponses(unittest.TestCase):
    def test_applied_record_parses(self):
        client, session = _make_client()
        session.post.return_value = _response(200, APPLIED)

        edit = client.edit("dr_1", "Fix it", wait_seconds=15)

        self.assertTrue(edit.success)
        self.assertEqual(edit.status, DeepResearchEditStatus.APPLIED)
        self.assertTrue(edit.is_terminal)
        self.assertEqual(edit.version, 2)
        self.assertEqual(edit.warnings[0].type, "deliverables_stale")

    def test_decline_and_failure_are_successful_requests(self):
        """A declined or failed edit is an outcome, not a request error, and
        a failed edit's code is reachable as error_code."""
        client, session = _make_client()
        session.get.side_effect = [
            _response(200, _record("declined", decline={
                "code": "edit.out_of_evidence",
                "message": "Needs facts the task did not gather.",
                "suggestion": "Start a new task.",
            })),
            _response(200, _record("failed", error={
                "code": "edit.interrupted", "message": "Interrupted", "retryable": True,
            })),
        ]

        declined = client.get_edit("dr_1", "ed_1")
        failed = client.get_edit("dr_1", "ed_1")

        self.assertTrue(declined.success)
        self.assertEqual(declined.decline.code, "edit.out_of_evidence")
        self.assertTrue(failed.success)
        self.assertEqual(failed.error.code, "edit.interrupted")
        self.assertTrue(failed.error.retryable)
        self.assertEqual(failed.error_code, "edit.interrupted")

    def test_http_errors_surface_code_and_candidates(self):
        client, session = _make_client()
        session.post.side_effect = [
            _response(422, {
                "error": "Focus text matched 2 places",
                "code": "focus.ambiguous",
                "candidates": [
                    {"start_char": 10, "end_char": 20, "section": "Outlook"},
                    {"start_char": 90, "end_char": 100, "section": "Risks"},
                ],
            }),
            _response(409, {"error": "Another edit is running", "code": "edit.in_progress"}),
        ]

        ambiguous = client.edit("dr_1", "Fix it", focus={"text": "growth"})
        busy = client.edit("dr_1", "Fix it")

        self.assertFalse(ambiguous.success)
        self.assertEqual(ambiguous.error_code, "focus.ambiguous")
        self.assertEqual(ambiguous.status_code, 422)
        self.assertEqual([c.start_char for c in ambiguous.candidates], [10, 90])
        self.assertEqual(busy.error_code, "edit.in_progress")
        self.assertEqual(busy.error, "Another edit is running")


@patch("valyu.deepresearch_client.time.sleep")
class TestWaitForEdit(unittest.TestCase):
    def test_polls_through_transient_errors_using_the_hint(self, sleep):
        """wait_for_edit keeps polling a running edit, rides out a 503 and
        returns the finished record, sleeping for retry_after_seconds."""
        client, session = _make_client()
        session.get.side_effect = [
            _response(200, _record("running", retry_after_seconds=2)),
            _response(503, {"error": "unavailable"}),
            _response(200, APPLIED),
        ]

        edit = client.wait_for_edit("dr_1", "ed_1")

        self.assertEqual(edit.status, DeepResearchEditStatus.APPLIED)
        self.assertEqual(session.get.call_count, 3)
        self.assertEqual(sleep.call_args_list[0].args[0], 2)
        session.get.assert_called_with(f"{BASE}/deepresearch/tasks/dr_1/edits/ed_1")

    def test_definitive_error_raises(self, sleep):
        client, session = _make_client()
        session.get.return_value = _response(404, {"error": "Edit not found"})

        with self.assertRaises(ValueError):
            client.wait_for_edit("dr_1", "ed_missing")
        sleep.assert_not_called()

    def test_times_out(self, sleep):
        client, session = _make_client()
        session.get.return_value = _response(200, _record("running"))

        with self.assertRaises(TimeoutError):
            client.wait_for_edit("dr_1", "ed_1", max_wait_time=-1)


class TestVersions(unittest.TestCase):
    def test_list_and_restore(self):
        client, session = _make_client()
        session.get.return_value = _response(200, {
            "deepresearch_id": "dr_1",
            "head": 2,
            "versions": [
                {"version": 1, "kind": "original", "created_at": "t", "is_head": False},
                {"version": 2, "kind": "edit", "created_at": "t", "is_head": True,
                 "edit_id": "ed_1", "instruction": "Fix it", "target": {"kind": "report"}},
            ],
        })
        session.post.return_value = _response(200, {"version": 3, "restored_from": 1})

        versions = client.list_versions("dr_1")
        restored = client.restore_version("dr_1", 1)

        self.assertEqual(versions.head, 2)
        self.assertEqual([v.kind for v in versions.versions], ["original", "edit"])
        self.assertEqual(
            session.post.call_args.args[0],
            f"{BASE}/deepresearch/tasks/dr_1/versions/1/restore",
        )
        self.assertEqual((restored.version, restored.restored_from), (3, 1))

    def test_status_version_cannot_be_passed_positionally(self):
        """status(task_id, 2) must not be read as a version request: the
        second positional argument is max_attempts, so version is keyword-only
        and a positional version fails loudly instead of returning the head."""
        client, session = _make_client()
        session.get.return_value = _response(200, {"deepresearch_id": "dr_1", "status": "completed"})

        client.status("dr_1", 2)
        self.assertNotIn("params", session.get.call_args.kwargs)
        with self.assertRaises(TypeError):
            client.status("dr_1", 5, 2)

    def test_status_version_is_not_served_from_the_head_cache(self):
        """status(version=N) sends ?version=N and must not send the current
        report's ETag, or a 304 would hand back the wrong version."""
        client, session = _make_client()
        head = {"deepresearch_id": "dr_1", "status": "completed", "output": "v2",
                "editable": True, "version": 2, "version_count": 2}
        old = {"deepresearch_id": "dr_1", "status": "completed", "output": "v1",
               "version": 1, "is_latest": False}
        session.get.side_effect = [
            _response(200, head, {"ETag": '"head"'}),
            _response(200, old),
        ]

        current = client.status("dr_1")
        first = client.status("dr_1", version=1)

        self.assertTrue(current.editable)
        self.assertEqual((first.output, first.is_latest), ("v1", False))
        call = session.get.call_args_list[1]
        self.assertEqual(call.kwargs.get("params"), {"version": 1})
        self.assertNotIn("headers", call.kwargs)


if __name__ == "__main__":
    unittest.main()
