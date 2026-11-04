"""Tests that the "model" alias is deprecated: it warns, and only "mode" is sent."""

import unittest
import warnings
from types import SimpleNamespace
from unittest.mock import MagicMock

from valyu.batch_client import BatchClient
from valyu.deepresearch_client import DeepResearchClient


def _session(payload):
    session = MagicMock()
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = payload
    session.post.return_value = response
    return session


def _deprecations(caught):
    return [str(w.message) for w in caught if issubclass(w.category, DeprecationWarning)]


class ModelAliasDeprecatedTest(unittest.TestCase):
    def test_deepresearch_model_warns_and_sends_mode_only(self):
        session = _session({"success": True, "deepresearch_id": "dr_1", "status": "queued"})
        client = DeepResearchClient(SimpleNamespace(base_url="https://api.example.test", headers={}, _session=session))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            client.create(query="q", model="heavy")
        body = session.post.call_args.kwargs["json"]
        self.assertEqual(body["mode"], "heavy")
        self.assertNotIn("model", body)
        self.assertEqual(_deprecations(caught), ['"model" is deprecated. Use "mode" instead.'])
        self.assertEqual(caught[0].filename, __file__)

    def test_deepresearch_mode_does_not_warn(self):
        session = _session({"success": True, "deepresearch_id": "dr_1", "status": "queued"})
        client = DeepResearchClient(SimpleNamespace(base_url="https://api.example.test", headers={}, _session=session))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            client.create(query="q", mode="heavy")
        self.assertEqual(_deprecations(caught), [])

    def test_batch_model_warns_and_sends_mode_only(self):
        session = _session({"success": True, "batch_id": "b_1", "status": "open"})
        client = BatchClient(SimpleNamespace(base_url="https://api.example.test", headers={}, _session=session))
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            client.create(model="fast")
        body = session.post.call_args.kwargs["json"]
        self.assertEqual(body["mode"], "fast")
        self.assertNotIn("model", body)
        self.assertEqual(_deprecations(caught), ['"model" is deprecated. Use "mode" instead.'])


if __name__ == "__main__":
    unittest.main()
