import unittest

from logic.qobuz_app_id import (
    clear_cached_qobuz_app_id,
    cache_qobuz_app_id,
    extract_qobuz_app_id,
    extract_qobuz_bundle_url,
    extract_qobuz_bundle_urls,
    get_cached_qobuz_app_id,
)


class QobuzAppIdTests(unittest.TestCase):
    def setUp(self) -> None:
        clear_cached_qobuz_app_id()

    def tearDown(self) -> None:
        clear_cached_qobuz_app_id()

    def test_extract_bundle_url_returns_absolute_qobuz_url(self) -> None:
        html = '<html><script src="/resources/123/bundle.js"></script></html>'
        self.assertEqual(
            extract_qobuz_bundle_url(html),
            "https://play.qobuz.com/resources/123/bundle.js",
        )

    def test_extract_bundle_urls_prioritizes_qobuz_bundle_and_keeps_fallback_assets(self) -> None:
        html = """
        <html>
            <script src="https://cdn.example.com/app.js"></script>
            <script src="/assets/runtime.js"></script>
            <script src="/resources/123/bundle.js"></script>
            <script src="/assets/main.js"></script>
        </html>
        """
        self.assertEqual(
            extract_qobuz_bundle_urls(html),
            [
                "https://play.qobuz.com/resources/123/bundle.js",
                "https://play.qobuz.com/assets/main.js",
                "https://play.qobuz.com/assets/runtime.js",
            ],
        )

    def test_extract_qobuz_app_id_reads_production_api_value(self) -> None:
        bundle_js = 'window.config={"production":{"api":{"appId":"987654"}}};'
        self.assertEqual(extract_qobuz_app_id(bundle_js), "987654")

    def test_cache_qobuz_app_id_uses_shared_single_source_of_truth(self) -> None:
        self.assertEqual(get_cached_qobuz_app_id(), "")
        cache_qobuz_app_id("24680")
        self.assertEqual(get_cached_qobuz_app_id(), "24680")


if __name__ == "__main__":
    unittest.main()
