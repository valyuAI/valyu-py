"""Tests that cover_art and brand_collection_id reach the request body."""

import base64
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from valyu.deepresearch_client import DeepResearchClient
from valyu.types.deepresearch import CoverArt

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 16


def _make_client():
    session = MagicMock()
    response = MagicMock()
    response.ok = True
    response.status_code = 200
    response.json.return_value = {
        "success": True,
        "deepresearch_id": "dr_123",
        "status": "queued",
        "warnings": [{"type": "cover_art_not_used", "message": "too small"}],
    }
    session.post.return_value = response
    parent = SimpleNamespace(
        base_url="https://api.example.com", headers={}, _session=session
    )
    return DeepResearchClient(parent), session


def _body(session):
    return session.post.call_args.kwargs["json"]


class CoverArtPayloadTest(unittest.TestCase):
    def test_omitted_by_default(self):
        client, session = _make_client()
        client.create(query="q")
        self.assertNotIn("cover_art", _body(session))

    def test_dict_sent_as_given(self):
        client, session = _make_client()
        art = {"kind": "image", "data": "AAAA", "mediaType": "image/jpeg", "filename": "cover.jpg"}
        client.create(query="q", cover_art=art)
        self.assertEqual(_body(session)["cover_art"], art)

    def test_model_uses_camel_case_media_type(self):
        client, session = _make_client()
        client.create(
            query="q",
            cover_art=CoverArt(kind="pattern", data="AAAA", media_type="image/png"),
        )
        self.assertEqual(
            _body(session)["cover_art"],
            {"kind": "pattern", "data": "AAAA", "mediaType": "image/png"},
        )

    def test_url(self):
        client, session = _make_client()
        client.create(query="q", cover_art=CoverArt(url="https://example.com/a.png"))
        self.assertEqual(_body(session)["cover_art"], {"url": "https://example.com/a.png"})

    def test_bytes_are_encoded(self):
        client, session = _make_client()
        client.create(query="q", cover_art=JPEG)
        art = _body(session)["cover_art"]
        self.assertEqual(art["kind"], "image")
        self.assertEqual(art["mediaType"], "image/jpeg")
        self.assertEqual(base64.b64decode(art["data"]), JPEG)
        self.assertNotIn("filename", art)

    def test_file_path_is_read(self):
        client, session = _make_client()
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "cover.png")
            with open(path, "wb") as f:
                f.write(PNG)
            client.create(query="q", cover_art=path)
        art = _body(session)["cover_art"]
        self.assertEqual(art["mediaType"], "image/png")
        self.assertEqual(art["filename"], "cover.png")
        self.assertEqual(base64.b64decode(art["data"]), PNG)

    def test_non_image_bytes_rejected(self):
        client, session = _make_client()
        result = client.create(query="q", cover_art=b"not an image")
        self.assertFalse(result.success)
        self.assertIn("PNG or JPEG", result.error)
        session.post.assert_not_called()

    def test_workflow_run_forwards_cover_art_and_brand(self):
        client, session = _make_client()
        client.create(
            workflow_id="wf",
            cover_art={"url": "https://example.com/a.png"},
            brand_collection_id="none",
        )
        body = _body(session)
        self.assertEqual(body["cover_art"], {"url": "https://example.com/a.png"})
        self.assertEqual(body["brand_collection_id"], "none")

    def test_warning_is_exposed(self):
        client, _ = _make_client()
        result = client.create(query="q", cover_art={"url": "https://example.com/a.png"})
        self.assertEqual(result.warnings[0].type, "cover_art_not_used")


if __name__ == "__main__":
    unittest.main()
