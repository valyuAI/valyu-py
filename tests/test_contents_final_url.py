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


class TestContentsFinalUrl(unittest.TestCase):
    def test_final_url_parses(self):
        result = _success(final_url="https://example.com/careers")
        self.assertEqual(result.final_url, "https://example.com/careers")

    def test_final_url_defaults_to_none(self):
        self.assertIsNone(_success().final_url)


if __name__ == "__main__":
    unittest.main()
