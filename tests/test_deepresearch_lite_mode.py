"""Tests that mode "lite" maps to "standard" and warns."""

import unittest
import warnings
from types import SimpleNamespace
from unittest.mock import MagicMock

from valyu.deepresearch_client import DeepResearchClient


def _make_client():
    session = MagicMock()
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {"success": True, "deepresearch_id": "dr_1", "status": "queued"}
    session.post.return_value = response
    parent = SimpleNamespace(base_url="https://api.example.test", headers={}, _session=session)
    return DeepResearchClient(parent), session


def _body(session):
    return session.post.call_args.kwargs["json"]


class LiteModeTest(unittest.TestCase):
    def test_mode_lite_maps_to_standard_and_warns_at_caller(self):
        client, session = _make_client()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            client.create(query="q", mode="lite")
        self.assertEqual(_body(session)["mode"], "standard")
        deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        self.assertEqual(len(deprecations), 1)
        self.assertIn("lite", str(deprecations[0].message))
        self.assertEqual(deprecations[0].filename, __file__)

    def test_model_lite_maps_to_standard_and_warns(self):
        client, session = _make_client()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            client.create(query="q", model="lite")
        body = _body(session)
        self.assertEqual(body["mode"], "standard")
        self.assertEqual(body["model"], "standard")
        self.assertEqual(len([w for w in caught if issubclass(w.category, DeprecationWarning)]), 1)

    def test_workflow_run_maps_lite_and_warns(self):
        client, session = _make_client()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            client.create(workflow_id="wf_1", mode="lite")
        self.assertEqual(_body(session)["mode"], "standard")
        self.assertEqual(len([w for w in caught if issubclass(w.category, DeprecationWarning)]), 1)

    def test_other_modes_do_not_warn(self):
        client, session = _make_client()
        for mode in ("instant", "fast", "standard", "heavy", "max"):
            with self.subTest(mode=mode):
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    client.create(query="q", mode=mode)
                self.assertEqual(_body(session)["mode"], mode)
                self.assertEqual([w for w in caught if issubclass(w.category, DeprecationWarning)], [])


if __name__ == "__main__":
    unittest.main()
