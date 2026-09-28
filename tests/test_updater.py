"""Unit tests for software update checker and downloader."""
from __future__ import annotations

import io
import json
import unittest
from unittest.mock import MagicMock, patch
import urllib.error

from core.updater import (
    ReleaseAsset,
    ReleaseInfo,
    fetch_latest_release,
    find_platform_asset,
    is_newer_version,
    parse_version,
)


class TestVersionParsing(unittest.TestCase):
    def test_parse_standard_versions(self):
        self.assertEqual(parse_version("1.0.0"), (1, 0, 0))
        self.assertEqual(parse_version("v1.0.0"), (1, 0, 0))
        self.assertEqual(parse_version("V1.2.3"), (1, 2, 3))
        self.assertEqual(parse_version("2.1"), (2, 1, 0))

    def test_parse_prerelease_suffix(self):
        self.assertEqual(parse_version("v1.0.0-beta1"), (1, 0, 0))
        self.assertEqual(parse_version("1.2.0-rc2"), (1, 2, 0))

    def test_is_newer_version(self):
        self.assertTrue(is_newer_version("1.0.1", "1.0.0"))
        self.assertTrue(is_newer_version("v1.1.0", "1.0.9"))
        self.assertTrue(is_newer_version("2.0.0", "1.99.99"))

        # Same or older
        self.assertFalse(is_newer_version("1.0.0", "1.0.0"))
        self.assertFalse(is_newer_version("v1.0.0", "1.0.0"))
        self.assertFalse(is_newer_version("0.9.9", "1.0.0"))
        self.assertFalse(is_newer_version("1.0.0", "1.0.1"))


class TestPlatformAssetMatching(unittest.TestCase):
    def setUp(self):
        self.mock_assets = [
            {
                "name": "PaOConverter_v1.1.0_macOS.dmg",
                "browser_download_url": "https://github.com/repo/releases/download/v1.1.0/mac.dmg",
                "size": 75000000,
                "content_type": "application/x-apple-diskimage",
            },
            {
                "name": "PaOConverter_v1.1.0_Windows_Setup.exe",
                "browser_download_url": "https://github.com/repo/releases/download/v1.1.0/win.exe",
                "size": 55000000,
                "content_type": "application/x-msdos-program",
            },
            {
                "name": "source.tar.gz",
                "browser_download_url": "https://github.com/repo/releases/download/v1.1.0/source.tar.gz",
                "size": 1000000,
                "content_type": "application/gzip",
            },
        ]

    def test_match_macos(self):
        asset = find_platform_asset(self.mock_assets, platform="darwin")
        self.assertIsNotNone(asset)
        self.assertTrue(asset.name.endswith(".dmg"))
        self.assertIn("macOS", asset.name)
        self.assertEqual(asset.size, 75000000)
        self.assertAlmostEqual(asset.size_mb, 75000000 / (1024 * 1024), places=1)

    def test_match_windows(self):
        asset = find_platform_asset(self.mock_assets, platform="win32")
        self.assertIsNotNone(asset)
        self.assertTrue(asset.name.endswith(".exe"))
        self.assertIn("Windows", asset.name)

    def test_empty_assets(self):
        self.assertIsNone(find_platform_asset([], platform="darwin"))

    def test_size_formatting(self):
        small = ReleaseAsset("small.bin", "http://x", 512 * 1024, "bin")
        self.assertEqual(small.size_str, "512.0 KB")
        large = ReleaseAsset("large.bin", "http://x", 50 * 1024 * 1024, "bin")
        self.assertEqual(large.size_str, "50.0 MB")


class TestFetchRelease(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_fetch_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_data = {
            "tag_name": "v1.1.0",
            "name": "Release 1.1.0",
            "body": "Fixed bugs and added features.",
            "published_at": "2026-09-28T00:00:00Z",
            "html_url": "https://github.com/khunaungpaing/PaO-Converter/releases/tag/v1.1.0",
            "assets": [
                {
                    "name": "PaOConverter_v1.1.0_macOS.dmg",
                    "browser_download_url": "https://github.com/url/dmg",
                    "size": 70000000,
                    "content_type": "application/x-apple-diskimage",
                }
            ],
        }
        mock_response.read.return_value = json.dumps(mock_data).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        info = fetch_latest_release(current_version="1.0.0")
        self.assertEqual(info.version, "1.1.0")
        self.assertEqual(info.name, "Release 1.1.0")
        self.assertEqual(info.body, "Fixed bugs and added features.")
        self.assertTrue(info.is_newer)

    @patch("urllib.request.urlopen")
    def test_fetch_not_newer(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_data = {
            "tag_name": "v1.0.0",
            "name": "v1.0.0",
            "body": "Initial release",
            "published_at": "2026-09-25T00:00:00Z",
            "html_url": "https://github.com/khunaungpaing/PaO-Converter/releases/tag/v1.0.0",
            "assets": [],
        }
        mock_response.read.return_value = json.dumps(mock_data).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        info = fetch_latest_release(current_version="1.0.0")
        self.assertEqual(info.version, "1.0.0")
        self.assertFalse(info.is_newer)

    @patch("urllib.request.urlopen")
    def test_fetch_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError("No route to host")
        with self.assertRaises(RuntimeError) as ctx:
            fetch_latest_release(current_version="1.0.0")
        self.assertIn("Could not connect to GitHub", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
