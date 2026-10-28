import unittest

from valyu.types.contents import ContentsResultSuccess


def _success(**extra):
    base = {
        "url": "https://example.com/a",
        "status": "success",
        "title": "A",
        "content": "text",
        "length": 4,
        "source": "web",
    }
    base.update(extra)
    return ContentsResultSuccess(**base)


class TestContentsHttpStatus(unittest.TestCase):
    def test_http_status_404_parses(self):
        self.assertEqual(_success(http_status=404).http_status, 404)

    def test_http_status_defaults_to_none(self):
        self.assertIsNone(_success().http_status)


if __name__ == "__main__":
    unittest.main()
