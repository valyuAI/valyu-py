import json
import unittest
import warnings
from unittest.mock import MagicMock

from valyu import Valyu

BODY = {"success": True, "tx_id": "tx_1", "contents": "hi"}


def _client():
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = BODY
    response.iter_lines.return_value = [f"data: {json.dumps(BODY)}", "data: [DONE]"]
    client = Valyu(api_key="val_test")
    client._session.post = MagicMock(return_value=response)
    return client


class AnswerDeprecationTests(unittest.TestCase):
    def test_answer_warns_each_call(self):
        client = _client()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = client.answer("q")
            client.answer("q")
        deprecations = [w for w in caught if issubclass(w.category, DeprecationWarning)]
        self.assertEqual(len(deprecations), 2)
        message = str(deprecations[0].message)
        self.assertIn("2026-12-17", message)
        self.assertIn("mode='instant'", message)
        self.assertIn("migrate-from-answer", message)
        self.assertEqual(deprecations[0].filename, __file__)
        self.assertTrue(result.success)


if __name__ == "__main__":
    unittest.main()
