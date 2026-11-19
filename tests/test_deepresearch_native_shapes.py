"""
Proves the DeepResearch response models parse the full response shape the API can send:
longer task bodies with itemized costs, structured reports, source locations, charts and
deliverables, plus batch and error bodies.

The fixtures under tests/fixtures/native_golden/ hold real response bodies with every value
replaced by a type-preserving placeholder ("s" for string, 0 for number, and so on). We parse
each one and assert it does not raise. A parse failure here means a new or unknown value would
crash the SDK (for example, break the polling loop of wait()) instead of passing through as a
plain value.
"""

import json
import os
import unittest

from valyu.types.deepresearch import (
    BatchCreateResponse,
    BatchStatusResponse,
    DeepResearchCancelResponse,
    DeepResearchCreateResponse,
    DeepResearchStatus,
    DeepResearchStatusResponse,
)

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "native_golden")


def _load(name: str) -> dict:
    with open(os.path.join(FIXTURES_DIR, name)) as f:
        return json.load(f)


class NativeStatusShapeTest(unittest.TestCase):
    """Task status/create bodies: full task shape, field names and value domains."""

    STATUS_CASES = [
        "create.json",
        "create-instant.json",
        "status-queued.json",
        "status-queued-alt.json",
        "status-completed.json",
        "status-failed.json",
        "status-charts-deliverables.json",
        "task-cancel.json",
    ]

    def test_status_shaped_goldens_parse(self):
        for name in self.STATUS_CASES:
            golden = _load(name)
            body = dict(golden["body"])
            body.pop("success", None)
            with self.subTest(case=golden["case"]):
                status = DeepResearchStatusResponse(success=True, **body)
                self.assertTrue(status.success)
                # The placeholder status string ("s") is not one of our known members: it must
                # be kept as the raw string, not raise and not silently become None.
                self.assertIsNotNone(status.status)

    def test_create_goldens_parse_as_create_response(self):
        for name in ("create.json", "create-instant.json"):
            golden = _load(name)
            body = dict(golden["body"])
            body.pop("success", None)
            with self.subTest(case=golden["case"]):
                created = DeepResearchCreateResponse(success=True, **body)
                self.assertTrue(created.success)

    def test_cancel_golden_parses_as_cancel_response(self):
        golden = _load("task-cancel.json")
        body = dict(golden["body"])
        body.pop("success", None)
        cancelled = DeepResearchCancelResponse(success=True, **body)
        self.assertTrue(cancelled.success)

    def test_charts_and_deliverables_golden_has_pending_and_attachment_shapes(self):
        golden = _load("status-charts-deliverables.json")
        body = dict(golden["body"])
        body.pop("success", None)
        status = DeepResearchStatusResponse(success=True, **body)
        self.assertEqual(len(status.images), 3)
        self.assertEqual(len(status.deliverables), 2)
        # This body has no separate cost_detail key: the itemized bill is cost_breakdown
        # itself. effective_cost_detail() finds it either way (see cost_detail's docstring).
        self.assertIsNone(status.cost_detail)
        detail = status.effective_cost_detail()
        self.assertIsNotNone(detail)
        self.assertEqual(detail.base_usd, 0.5)
        self.assertEqual(len(detail.tools), 1)
        self.assertEqual(detail.tools[0].usd, 0.5)
        # sources[].locations round-trips (status-completed/status-charts-deliverables both
        # carry it; one entry on the golden is `{}`, i.e. an excerpt-less location).
        self.assertTrue(any(s.locations for s in status.sources))

    def test_future_status_value_is_kept_not_rejected(self):
        """The literal placeholder value in these goldens ("s") is not a real status. A status
        this SDK does not recognise must still parse — this is what keeps wait() from crashing
        on a status value introduced after this SDK shipped."""
        golden = _load("status-completed.json")
        body = dict(golden["body"])
        body.pop("success", None)
        status = DeepResearchStatusResponse(success=True, **body)
        self.assertEqual(status.status, "s")
        self.assertNotEqual(status.status, DeepResearchStatus.COMPLETED)


class NativeBatchShapeTest(unittest.TestCase):
    def test_batch_create_golden_parses(self):
        golden = _load("batch-create.json")
        created = BatchCreateResponse(success=True, **golden["body"])
        self.assertTrue(created.success)
        self.assertEqual(created.effective_mode(), "s")

    def test_batch_status_golden_parses(self):
        golden = _load("batch-status.json")
        status = BatchStatusResponse(success=True, batch=golden["body"])
        self.assertTrue(status.success)
        self.assertEqual(status.batch.effective_mode(), "s")


class NativeErrorShapeTest(unittest.TestCase):
    ERROR_CASES = [
        "error-bad-mode.json",
        "error-missing-query.json",
        "error-brand-forbidden.json",
        "task-not-found.json",
    ]

    def test_error_goldens_parse(self):
        for name in self.ERROR_CASES:
            golden = _load(name)
            with self.subTest(case=golden["case"]):
                resp = DeepResearchCreateResponse(success=False, **golden["body"])
                self.assertFalse(resp.success)
                self.assertEqual(resp.error, "s")


if __name__ == "__main__":
    unittest.main()
