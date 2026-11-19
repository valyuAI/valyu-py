"""Tests that tools.ultrasearch reaches the request body."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from valyu.deepresearch_client import DeepResearchClient
from valyu.types.deepresearch import (
    DeepResearchCreateResponse,
    DeepResearchStatusResponse,
    DeepResearchTools,
    UltrasearchConfig,
)


def _make_client():
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
        base_url="https://api.example.test", headers={}, _session=session
    )
    return DeepResearchClient(parent), session


def _body(session):
    return session.post.call_args.kwargs["json"]


class UltrasearchPayloadTest(unittest.TestCase):
    def test_absent_sends_no_ultrasearch_key(self):
        client, session = _make_client()
        client.create(query="q", mode="heavy")
        body = _body(session)
        self.assertNotIn("tools", body)
        self.assertNotIn("ultrasearch", body)

    def test_absent_with_other_tools_sends_no_ultrasearch_key(self):
        client, session = _make_client()
        client.create(query="q", mode="heavy", tools={"charts": True})
        body = _body(session)
        self.assertEqual(body["tools"], {"charts": True})
        self.assertNotIn("ultrasearch", body)

    def test_true_dict(self):
        client, session = _make_client()
        client.create(query="q", mode="heavy", tools={"ultrasearch": True})
        body = _body(session)
        self.assertIs(body["tools"]["ultrasearch"], True)
        self.assertNotIn("ultrasearch", body)

    def test_true_model(self):
        client, session = _make_client()
        client.create(query="q", mode="max", tools=DeepResearchTools(ultrasearch=True))
        body = _body(session)
        self.assertEqual(body["tools"], {"ultrasearch": True})
        self.assertNotIn("ultrasearch", body)

    def test_false_is_sent_as_false(self):
        client, session = _make_client()
        client.create(query="q", mode="heavy", tools={"ultrasearch": False})
        self.assertIs(_body(session)["tools"]["ultrasearch"], False)

    def test_max_usd_dict(self):
        client, session = _make_client()
        client.create(query="q", mode="heavy", tools={"ultrasearch": {"max_usd": 2.5}})
        body = _body(session)
        self.assertEqual(body["tools"], {"ultrasearch": {"max_usd": 2.5}})
        self.assertNotIn("ultrasearch", body)

    def test_max_usd_model(self):
        client, session = _make_client()
        client.create(
            query="q",
            mode="max",
            tools=DeepResearchTools(ultrasearch=UltrasearchConfig(max_usd=1)),
        )
        body = _body(session)
        self.assertEqual(body["tools"], {"ultrasearch": {"max_usd": 1.0}})
        self.assertNotIn("ultrasearch", body)

    def test_workflow_run_sends_tools_ultrasearch(self):
        client, session = _make_client()
        client.create(workflow_id="wf_1", mode="heavy", tools={"ultrasearch": True})
        body = _body(session)
        self.assertEqual(body["tools"], {"ultrasearch": True})
        self.assertNotIn("ultrasearch", body)


class UltrasearchValidationTest(unittest.TestCase):
    def _rejected(self, value):
        client, session = _make_client()
        result = client.create(query="q", mode="heavy", tools={"ultrasearch": value})
        self.assertFalse(result.success)
        self.assertIn("ultrasearch", result.error)
        session.post.assert_not_called()

    def test_rejects_non_positive_max_usd(self):
        for value in (0, -1, 0.0):
            with self.subTest(value=value):
                self._rejected({"max_usd": value})

    def test_rejects_non_finite_max_usd(self):
        for value in (float("inf"), float("nan")):
            with self.subTest(value=value):
                self._rejected({"max_usd": value})

    def test_rejects_wrong_types_and_unknown_keys(self):
        for value in ({"max_usd": "2"}, {"max_usd": True}, {}, {"max_usd": 1, "x": 1}, "yes"):
            with self.subTest(value=value):
                self._rejected(value)

    def test_model_rejects_non_positive_max_usd(self):
        with self.assertRaises(ValueError):
            UltrasearchConfig(max_usd=0)


class UltrasearchResponseTest(unittest.TestCase):
    def test_responses_tolerate_echoed_value(self):
        for echo in (True, False, {"max_usd": 0.5}):
            with self.subTest(echo=echo):
                created = DeepResearchCreateResponse(
                    success=True, deepresearch_id="dr_1", tools={"ultrasearch": echo}
                )
                self.assertEqual(created.tools["ultrasearch"], echo)
                status = DeepResearchStatusResponse(
                    success=True,
                    deepresearch_id="dr_1",
                    tools={"ultrasearch": echo},
                    cost_breakdown={
                        "task": 1.0,
                        "tools": [{"item": "submitQuery", "usd": 0.1}, {"item": "queryResults", "usd": 0.2}],
                        "datasets": [{"item": "ds", "usd": 0.3}],
                    },
                )
                expected = echo if isinstance(echo, bool) else UltrasearchConfig(max_usd=0.5)
                self.assertEqual(status.tools.ultrasearch, expected)
                self.assertEqual(len(status.cost_breakdown.tools), 2)


if __name__ == "__main__":
    unittest.main()
