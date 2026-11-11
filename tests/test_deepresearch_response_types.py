"""DeepResearch status response parsing: old, full and unknown-value shapes."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from valyu.deepresearch_client import DeepResearchClient
from valyu.types.deepresearch import DeepResearchStatusResponse


class ResponseParsingTest(unittest.TestCase):
    def test_minimal_old_response(self):
        r = DeepResearchStatusResponse(
            **{
                "success": True,
                "deepresearch_id": "dr_1",
                "status": "completed",
                "cost": 1.5,
                "cost_breakdown": {"task": 1.5},
                "images": [
                    {
                        "image_id": "i1",
                        "image_type": "chart",
                        "title": "t",
                        "image_url": "https://x/i.png",
                        "created_at": 1,
                    }
                ],
                "deliverables": [
                    {
                        "id": "d1",
                        "request": "r",
                        "type": "csv",
                        "status": "completed",
                        "title": "a.csv",
                        "url": "https://x/a.csv",
                        "s3_key": "k",
                        "created_at": 5,
                    }
                ],
            }
        )
        self.assertEqual(r.cost_breakdown.task, 1.5)
        self.assertIsNone(r.cost_credits)
        self.assertIsNone(r.cost_detail)
        self.assertIsNone(r.pending_deliverables)
        self.assertIsNone(r.error_code)
        self.assertIsNone(r.images[0].chart_kind)

    def test_full_response(self):
        r = DeepResearchStatusResponse(
            **{
                "success": True,
                "status": "completed",
                "mode": "standard",
                "research_mode": "standard",
                "output_formats": ["markdown"],
                "research_output_formats": ["markdown", {"type": "object"}],
                "cost": 2.0,
                "cost_credits": 320.0,
                "cost_breakdown": {
                    "task": 1.0,
                    "screenshots": 0.1,
                    "code_execution": 0.1,
                    "deliverables": 0.1,
                    "datasets": 0.1,
                    "x_search": 0.1,
                    "browse": 0.1,
                    "ocr": 0.1,
                    "urls": 0.1,
                    "other_tools": 0.1,
                },
                "cost_breakdown_credits": {"task": 160, "ocr": 16},
                "cost_detail": {
                    "base_usd": 1.0,
                    "tools": [
                        {
                            "item": "browse",
                            "label": "Browse",
                            "pricing": "per_unit",
                            "unit": "page",
                            "units": 12,
                            "free_units": 10,
                            "billed_units": 2,
                            "unit_price_usd": 0.05,
                            "usd": 0.1,
                            "credits": 16,
                        }
                    ],
                    "datasets": [{"source": "s", "rows": 3, "usd": 0.2, "credits": 32}],
                    "total_usd": 2.0,
                    "base_credits": 160,
                    "total_credits": 320,
                },
                "images": [
                    {
                        "image_id": "i1",
                        "image_type": "chart",
                        "chart_type": "bar",
                        "chart_kind": "slope",
                        "title": "t",
                        "image_url": "https://x/i.png",
                        "created_at": 1700000000000,
                    }
                ],
                "deliverables": [],
                "pending_deliverables": [
                    {"id": "d2", "type": "pdf", "status": "pending", "created_at": 1}
                ],
                "error_code": "some_code",
            }
        )
        self.assertEqual(r.cost_credits, 320.0)
        self.assertEqual(r.cost_breakdown.x_search, 0.1)
        self.assertEqual(r.cost_breakdown_credits.ocr, 16)
        self.assertEqual(r.cost_detail.tools[0].billed_units, 2)
        self.assertEqual(r.cost_detail.datasets[0].source, "s")
        self.assertEqual(r.cost_detail.total_credits, 320)
        self.assertEqual(r.images[0].chart_kind, "slope")
        self.assertEqual(r.images[0].created_at, 1700000000000)
        self.assertEqual(r.pending_deliverables[0].status, "pending")
        self.assertEqual(r.research_output_formats[1], {"type": "object"})
        self.assertEqual(r.error_code, "some_code")

    def test_unknown_values_and_fields(self):
        r = DeepResearchStatusResponse(
            **{
                "success": True,
                "status": "brand_new_status",
                "mode": "brand_new_mode",
                "output_formats": ["brand_new_format"],
                "future_field": {"a": 1},
                "cost_breakdown": {"task": 1.0, "future_tool": 0.25},
                "cost_detail": {"future": 1, "tools": [{"item": "x", "extra": 1}]},
                "images": [
                    {
                        "image_id": "i",
                        "image_type": "hologram",
                        "chart_type": "sankey",
                        "chart_kind": "sunburst",
                        "title": "t",
                        "image_url": "u",
                        "extra": 1,
                    }
                ],
                "deliverables": [
                    {
                        "id": "d",
                        "request": "r",
                        "type": "mp3",
                        "status": "queued",
                        "title": "t",
                        "url": "u",
                        "s3_key": "k",
                    }
                ],
            }
        )
        self.assertEqual(r.status, "brand_new_status")
        self.assertEqual(r.mode, "brand_new_mode")
        self.assertEqual(r.cost_breakdown.model_extra["future_tool"], 0.25)
        self.assertEqual(r.images[0].image_type, "hologram")
        self.assertEqual(r.images[0].chart_type, "sankey")
        self.assertIsNone(r.images[0].created_at)
        self.assertEqual(r.deliverables[0].type, "mp3")
        self.assertEqual(r.deliverables[0].status, "queued")


def _client():
    session = MagicMock()
    resp = MagicMock()
    resp.ok = True
    resp.status_code = 200
    resp.json.return_value = {"success": True, "deepresearch_id": "dr_1", "status": "queued"}
    session.post.return_value = resp
    parent = SimpleNamespace(base_url="https://api.example.com", headers={}, _session=session)
    return DeepResearchClient(parent), session


class SkillsPayloadTest(unittest.TestCase):
    def test_skills_omitted_by_default(self):
        client, session = _client()
        client.create(query="q")
        self.assertNotIn("skills", session.post.call_args.kwargs["json"])

    def test_skills_sent_when_given(self):
        client, session = _client()
        client.create(query="q", skills=["forecasting"])
        self.assertEqual(session.post.call_args.kwargs["json"]["skills"], ["forecasting"])


if __name__ == "__main__":
    unittest.main()
