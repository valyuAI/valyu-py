"""
Tests that a workflow run sends the same per-run options a freeform run does.

The workflow template supplies the freeform fields (prompt, strategy, report
format). Everything else — deliverables, search, previous_reports, hitl, urls,
files, mcp_servers, brand_collection_id — is a per-run concern the API accepts
either way, so it must reach the wire rather than being dropped when
workflow_id is set.
"""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from valyu.deepresearch_client import DeepResearchClient
from valyu.types.deepresearch import Deliverable, HitlConfig, SearchConfig

# Per-run options that must survive on both code paths.
SHARED_OPTIONS = dict(
    deliverables=["xlsx"],
    search={"start_date": "2019-01-01"},
    previous_reports=["dr_a", "dr_b"],
    hitl={"plan_review": True},
    urls=["https://example.com"],
    mcp_servers=[{"name": "srv", "url": "https://mcp.example.com"}],
    brand_collection_id="brand_1",
    metadata={"deal": "project-frost"},
    tools={"code_execution": {"enabled": True, "max_calls": 5}},
    webhook_url="https://example.com/hook",
    alert_email="analyst@example.com",
)


def _make_client():
    """Build a DeepResearchClient with a stubbed session so no network is hit."""
    session = MagicMock()
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "deepresearch_id": "dr_123",
        "status": "queued",
    }
    session.post.return_value = response
    parent = SimpleNamespace(
        base_url="https://api.example.com",
        headers={},
        _session=session,
    )
    return DeepResearchClient(parent), session


def _sent_payload(session):
    """The JSON body handed to session.post."""
    return session.post.call_args.kwargs["json"]


class WorkflowPayloadTest(unittest.TestCase):
    def test_workflow_run_forwards_shared_options(self):
        """Every per-run option reaches the wire on a workflow run."""
        client, session = _make_client()

        result = client.create(
            workflow_id="ib-comps-analysis",
            workflow_params={"target": "Datadog (DDOG)"},
            **SHARED_OPTIONS,
        )

        self.assertTrue(result.success)
        payload = _sent_payload(session)

        self.assertEqual(payload["workflow_id"], "ib-comps-analysis")
        self.assertEqual(payload["workflow_params"], {"target": "Datadog (DDOG)"})
        for key, value in SHARED_OPTIONS.items():
            self.assertIn(key, payload, f"{key} was dropped from the workflow payload")
            self.assertEqual(payload[key], value)

    def test_workflow_and_freeform_agree_on_shared_options(self):
        """The two code paths serialise per-run options identically."""
        workflow_client, workflow_session = _make_client()
        workflow_client.create(
            workflow_id="ib-comps-analysis",
            workflow_params={"target": "Datadog (DDOG)"},
            **SHARED_OPTIONS,
        )

        freeform_client, freeform_session = _make_client()
        freeform_client.create(query="a freeform query", **SHARED_OPTIONS)

        workflow_payload = _sent_payload(workflow_session)
        freeform_payload = _sent_payload(freeform_session)

        for key in SHARED_OPTIONS:
            self.assertEqual(
                workflow_payload.get(key),
                freeform_payload.get(key),
                f"{key} serialises differently on the two paths",
            )

    def test_workflow_run_omits_unset_options(self):
        """A bare workflow run stays minimal so template defaults apply."""
        client, session = _make_client()

        client.create(
            workflow_id="ib-company-profile",
            workflow_params={"company": "NVIDIA (NVDA)"},
        )

        self.assertEqual(
            _sent_payload(session),
            {
                "workflow_id": "ib-company-profile",
                "workflow_params": {"company": "NVIDIA (NVDA)"},
            },
        )

    def test_workflow_run_serialises_pydantic_models(self):
        """Typed config objects are dumped, not passed through as models."""
        client, session = _make_client()

        client.create(
            workflow_id="ib-comps-analysis",
            workflow_params={"target": "Datadog (DDOG)"},
            search=SearchConfig(start_date="2019-01-01"),
            deliverables=[Deliverable(type="xlsx", description="Trading comps")],
            hitl=HitlConfig(plan_review=True),
        )

        payload = _sent_payload(session)
        self.assertEqual(payload["search"], {"start_date": "2019-01-01"})
        self.assertEqual(payload["deliverables"][0]["type"], "xlsx")
        self.assertEqual(payload["deliverables"][0]["description"], "Trading comps")
        self.assertEqual(payload["hitl"], {"plan_review": True})

    def test_workflow_run_rejects_oversized_file_context(self):
        """The files[].context cap applies to workflow runs too."""
        client, session = _make_client()

        result = client.create(
            workflow_id="ib-company-profile",
            workflow_params={"company": "NVIDIA (NVDA)"},
            files=[{"url": "https://example.com/a.pdf", "context": "x" * 10001}],
        )

        session.post.assert_not_called()
        self.assertFalse(result.success)
        self.assertIn("files[0].context exceeds 10,000 character limit", result.error)

    def test_workflow_run_still_rejects_freeform_fields(self):
        """workflow_id stays mutually exclusive with the template-supplied fields."""
        client, session = _make_client()

        result = client.create(
            workflow_id="ib-company-profile",
            workflow_params={"company": "NVIDIA (NVDA)"},
            query="a freeform query",
        )

        session.post.assert_not_called()
        self.assertFalse(result.success)
        self.assertIn("mutually exclusive", result.error)


if __name__ == "__main__":
    unittest.main()
