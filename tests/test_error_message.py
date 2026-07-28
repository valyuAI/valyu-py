"""
Tests that API validation detail survives into SDK error strings.

The API returns an `errors` array naming each offending field. Keeping only the
summary ("2 validation errors") leaves a caller unable to tell which parameter
was wrong or what the API expected instead.
"""

import unittest

from valyu._errors import error_message


class ErrorMessageTest(unittest.TestCase):
    def test_validation_errors_are_appended(self):
        message = error_message(
            {
                "error": "validation_failed",
                "message": "2 validation errors",
                "errors": [
                    {
                        "code": "unknown_param",
                        "key": "company",
                        "message": 'Unknown parameter "company"',
                    },
                    {
                        "code": "missing_param",
                        "key": "target",
                        "message": 'Required parameter "target" is missing',
                    },
                ],
            },
            400,
        )

        self.assertIn("2 validation errors", message)
        self.assertIn('Unknown parameter "company"', message)
        self.assertIn('Required parameter "target" is missing', message)

    def test_key_is_prefixed_when_not_already_named(self):
        message = error_message(
            {
                "message": "1 validation error",
                "errors": [{"code": "missing_param", "key": "sector"}],
            },
            400,
        )

        self.assertIn("sector: missing_param", message)

    def test_falls_back_to_summary_without_errors_array(self):
        self.assertEqual(
            error_message({"message": "Insufficient credits"}, 402),
            "Insufficient credits",
        )

    def test_falls_back_to_error_field(self):
        self.assertEqual(
            error_message({"error": "workflow_not_found"}, 404),
            "workflow_not_found",
        )

    def test_falls_back_to_status_code(self):
        self.assertEqual(error_message({}, 500), "HTTP Error: 500")

    def test_non_dict_body(self):
        self.assertEqual(error_message("gateway timeout", 504), "HTTP Error: 504")


if __name__ == "__main__":
    unittest.main()
