"""Tests for html and json deliverable types (no network)."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from valyu.deepresearch_client import DeepResearchClient
from valyu.types.deepresearch import Deliverable, DeliverableResult

SCHEMA = {"type": "object", "properties": {"x": {"type": "integer"}}}


class TestJsonDeliverable(unittest.TestCase):
    def test_schema_serializes_as_schema(self):
        d = Deliverable(type="json", description="d", schema=SCHEMA)
        out = d.model_dump(exclude_none=True, by_alias=True)
        self.assertEqual(out["schema"], SCHEMA)
        self.assertNotIn("json_schema", out)

    def test_field_name_works(self):
        d = Deliverable(type="json", description="d", json_schema=SCHEMA)
        self.assertEqual(d.json_schema, SCHEMA)

    def test_types_validate(self):
        for t in ("html", "json"):
            self.assertEqual(Deliverable(type=t, description="d").type, t)

    def test_results_parse(self):
        for t in ("html", "json"):
            r = DeliverableResult(id="a", type=t, status="completed")
            self.assertEqual(r.type, t)

    def test_request_body_has_schema(self):
        session = MagicMock()
        resp = MagicMock(ok=True, status_code=200)
        resp.json.return_value = {"success": True, "deepresearch_id": "dr_1", "status": "queued"}
        session.post.return_value = resp
        parent = SimpleNamespace(base_url="https://x", headers={}, _session=session)
        client = DeepResearchClient(parent)
        client.create(
            query="q",
            deliverables=[Deliverable(type="json", description="d", schema=SCHEMA)],
        )
        body = session.post.call_args.kwargs.get("json")
        self.assertEqual(body["deliverables"][0]["schema"], SCHEMA)


if __name__ == "__main__":
    unittest.main()
