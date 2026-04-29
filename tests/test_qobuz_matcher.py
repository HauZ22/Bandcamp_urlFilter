import os
import sys
import types
import unittest
from unittest.mock import AsyncMock, patch


rapidfuzz_module = types.ModuleType("rapidfuzz")


class _Fuzz:
    @staticmethod
    def token_sort_ratio(left: str, right: str) -> int:
        return 100 if " ".join(sorted(left.split())) == " ".join(sorted(right.split())) else 0


rapidfuzz_module.fuzz = _Fuzz()
sys.modules.setdefault("rapidfuzz", rapidfuzz_module)

from logic.qobuz_app_id import cache_qobuz_app_id, clear_cached_qobuz_app_id
from logic.qobuz_matcher import is_match, match_album, search_qobuz


class QobuzMatcherTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.original_app_id = os.environ.get("QOBUZ_APP_ID")
        self.original_user_token = os.environ.get("QOBUZ_USER_AUTH_TOKEN")
        os.environ.pop("QOBUZ_APP_ID", None)
        os.environ.pop("QOBUZ_USER_AUTH_TOKEN", None)
        clear_cached_qobuz_app_id()

    def tearDown(self) -> None:
        clear_cached_qobuz_app_id()
        if self.original_app_id is None:
            os.environ.pop("QOBUZ_APP_ID", None)
        else:
            os.environ["QOBUZ_APP_ID"] = self.original_app_id
        if self.original_user_token is None:
            os.environ.pop("QOBUZ_USER_AUTH_TOKEN", None)
        else:
            os.environ["QOBUZ_USER_AUTH_TOKEN"] = self.original_user_token

    def test_is_match_uses_track_list_length_as_streamable_fallback(self) -> None:
        result = is_match(
            {"artist": "Artist", "album": "Album", "track_count": 3},
            {
                "streamable": True,
                "artist": {"name": "Artist"},
                "title": "Album",
                "tracks_count": 3,
                "tracks": [{"id": 1}, {"id": 2}],
            },
        )
        self.assertFalse(result)

    async def test_match_album_skips_single_track_bandcamp_entries(self) -> None:
        class _Session:
            pass

        result = await match_album(
            _Session(),
            {
                "status": "success",
                "artist": "Artist",
                "track": "Single",
                "album": "",
                "track_count": 1,
                "is_single": True,
                "url": "https://artist.bandcamp.com/track/single",
            },
        )
        self.assertEqual(result["status"], "no_match")
        self.assertEqual(result["qobuz_url"], "")

    async def test_search_qobuz_returns_empty_dict_for_unexpected_success_payload(self) -> None:
        cache_qobuz_app_id("123456")
        os.environ["QOBUZ_USER_AUTH_TOKEN"] = "dummy-token"

        class _Response:
            status = 200
            headers = {"Content-Type": "application/json"}

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def json(self, content_type=None):
                return {"artists": {"items": []}}

        class _Session:
            def get(self, *args, **kwargs):
                return _Response()

        result = await search_qobuz(_Session(), "artist album")
        self.assertEqual(result["status"], "search_error")

    async def test_match_album_reports_missing_qobuz_auth_distinctly(self) -> None:
        cache_qobuz_app_id("123456")

        class _Session:
            pass

        result = await match_album(
            _Session(),
            {
                "status": "success",
                "artist": "Artist",
                "album": "Album",
                "track_count": 2,
                "url": "https://artist.bandcamp.com/album/album",
            },
        )
        self.assertEqual(result["status"], "authentication_required")

    async def test_search_qobuz_refreshes_app_id_once_after_auth_like_error(self) -> None:
        os.environ["QOBUZ_APP_ID"] = "111111"
        os.environ["QOBUZ_USER_AUTH_TOKEN"] = "dummy-token"

        class _Response:
            def __init__(self, status: int, payload: dict):
                self.status = status
                self.headers = {"Content-Type": "application/json"}
                self._payload = payload

            async def __aenter__(self):
                return self

            async def __aexit__(self, exc_type, exc, tb):
                return False

            async def json(self, content_type=None):
                return self._payload

        class _Session:
            def __init__(self):
                self.calls: list[dict] = []

            def get(self, *args, **kwargs):
                recorded_kwargs = dict(kwargs)
                recorded_kwargs["headers"] = dict(kwargs.get("headers", {}))
                self.calls.append(recorded_kwargs)
                if len(self.calls) == 1:
                    return _Response(401, {"status": "error"})
                return _Response(200, {"albums": {"items": [{"id": 1}]}})

        session = _Session()
        with patch("logic.qobuz_matcher.discover_qobuz_app_id_async", AsyncMock(return_value="222222")) as mock_refresh:
            result = await search_qobuz(session, "artist album", max_retries=2, base_delay=0)

        self.assertEqual(result["albums"]["items"], [{"id": 1}])
        self.assertEqual(session.calls[0]["headers"]["X-App-Id"], "111111")
        self.assertEqual(session.calls[1]["headers"]["X-App-Id"], "222222")
        self.assertEqual(mock_refresh.await_count, 1)


if __name__ == "__main__":
    unittest.main()
