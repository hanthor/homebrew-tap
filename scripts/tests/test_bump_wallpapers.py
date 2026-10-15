"""Unit tests for bump-wallpapers.py"""

import unittest
import tempfile
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from io import StringIO

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import module directly
import importlib.util
spec = importlib.util.spec_from_file_location("bump_wallpapers", Path(__file__).parent.parent / "bump-wallpapers.py")
bump_module = importlib.util.module_from_spec(spec)
sys.modules["bump_wallpapers"] = bump_module
try:
    spec.loader.exec_module(bump_module)
except SystemExit:
    pass


class TestVariant(unittest.TestCase):
    """Test Variant enum"""

    def test_variant_values(self):
        """Test all variants are defined"""
        self.assertEqual(bump_module.Variant.MACOS.value, "macos")
        self.assertEqual(bump_module.Variant.KDE.value, "kde")
        self.assertEqual(bump_module.Variant.GNOME.value, "gnome")
        self.assertEqual(bump_module.Variant.PNG.value, "png")


class TestCaskConfig(unittest.TestCase):
    """Test CaskConfig dataclass"""

    def test_cask_config_basic(self):
        """Test basic CaskConfig initialization"""
        config = bump_module.CaskConfig(
            name="test-wallpapers",
            release_prefix="test",
            artifact_name="test-wallpapers"
        )
        self.assertEqual(config.name, "test-wallpapers")
        self.assertEqual(config.release_prefix, "test")
        self.assertEqual(config.artifact_name, "test-wallpapers")

    def test_get_tag(self):
        """Test tag generation"""
        config = bump_module.CaskConfig(
            name="test",
            release_prefix="test",
            artifact_name="test"
        )
        self.assertEqual(config.get_tag("1.0.0"), "test-v1.0.0")
        self.assertEqual(config.get_tag("2025-01-15"), "test-v2025-01-15")

    def test_get_asset_name_with_variants(self):
        """Test asset name generation with variants"""
        config = bump_module.CaskConfig(
            name="test",
            release_prefix="test",
            artifact_name="test-wallpapers",
            variants=[bump_module.Variant.MACOS, bump_module.Variant.KDE]
        )
        self.assertEqual(config.get_asset_name(bump_module.Variant.MACOS), "test-wallpapers-macos.tar.zstd")
        self.assertEqual(config.get_asset_name(bump_module.Variant.KDE), "test-wallpapers-kde.tar.zstd")


class TestFindRelease(unittest.TestCase):
    """Test find_release function"""

    def setUp(self):
        """Set up test data"""
        self.releases = [
            {
                "tag_name": "bluefin-v2025-01-15",
                "name": "Bluefin January Release",
                "assets": []
            },
            {
                "tag_name": "bluefin-v2025-01-01",
                "name": "Bluefin Early January",
                "assets": []
            },
            {
                "tag_name": "other-v1.0.0",
                "name": "Other Release",
                "assets": []
            }
        ]

    def test_find_latest_release(self):
        """Test finding the latest release without specifying version"""
        release = bump_module.find_release(self.releases, "bluefin")
        self.assertEqual(release["tag_name"], "bluefin-v2025-01-15")

    def test_find_specific_version(self):
        """Test finding a specific version"""
        release = bump_module.find_release(self.releases, "bluefin", "2025-01-01")
        self.assertEqual(release["tag_name"], "bluefin-v2025-01-01")

    def test_find_release_not_found(self):
        """Test error when release not found"""
        with self.assertRaises(bump_module.ReleaseNotFoundError):
            bump_module.find_release(self.releases, "nonexistent")

    def test_find_specific_version_not_found(self):
        """Test error when specific version not found"""
        with self.assertRaises(bump_module.ReleaseNotFoundError):
            bump_module.find_release(self.releases, "bluefin", "2025-12-25")


class TestGetAssetSha256(unittest.TestCase):
    """Test get_asset_sha256 function"""

    def test_get_asset_sha256_success(self):
        """Test extracting SHA256 from asset"""
        release = {
            "assets": [
                {
                    "name": "test-wallpapers-macos.tar.zstd",
                    "digest": "sha256:abc123def456"
                }
            ]
        }
        sha = bump_module.get_asset_sha256(release, "test-wallpapers-macos.tar.zstd")
        self.assertEqual(sha, "abc123def456")

    def test_get_asset_sha256_no_digest(self):
        """Test error when asset has no digest"""
        release = {
            "assets": [
                {
                    "name": "test-wallpapers-macos.tar.zstd",
                    "digest": ""
                }
            ]
        }
        with self.assertRaises(bump_module.AssetNotFoundError) as cm:
            bump_module.get_asset_sha256(release, "test-wallpapers-macos.tar.zstd")
        self.assertIn("No digest", str(cm.exception))

    def test_get_asset_sha256_not_found(self):
        """Test error when asset not found"""
        release = {
            "assets": [
                {
                    "name": "other-asset.tar.zstd",
                    "digest": "sha256:xyz789"
                }
            ]
        }
        with self.assertRaises(bump_module.AssetNotFoundError) as cm:
            bump_module.get_asset_sha256(release, "missing-asset.tar.zstd")
        self.assertIn("Asset not found", str(cm.exception))


class TestUpdateFunctions(unittest.TestCase):
    """Test content update functions"""

    def test_update_version(self):
        """Test version string replacement"""
        content = 'version "2024-12-31"'
        updated = bump_module.update_version(content, "2025-01-15")
        self.assertEqual(updated, 'version "2025-01-15"')

    def test_update_version_multiple_quotes(self):
        """Test version update doesn't affect other quoted strings"""
        content = '''version "2024-12-31"
url "https://example.com/file.tar.gz"'''
        updated = bump_module.update_version(content, "2025-01-15")
        self.assertIn('version "2025-01-15"', updated)
        self.assertIn('url "https://example.com/file.tar.gz"', updated)

    def test_update_single_sha256(self):
        """Test single SHA256 update"""
        content = 'sha256 "oldsha256value"'
        updated = bump_module.update_single_sha256(content, "newsha256value")
        self.assertEqual(updated, 'sha256 "newsha256value"')

    def test_update_sha256_after_url(self):
        """Test SHA256 update after specific URL pattern"""
        content = '''url "https://example.com/test-wallpapers-macos.tar.zstd"
sha256 "oldsha256"
url "https://example.com/other-asset.tar.zstd"
sha256 "othersha256"'''
        updated = bump_module.update_sha256_after_url(
            content,
            "test-wallpapers-macos.tar.zstd",
            "newsha256"
        )
        self.assertIn('sha256 "newsha256"', updated)
        self.assertIn('sha256 "othersha256"', updated)

    def test_get_current_version(self):
        """Test extracting current version"""
        content = 'version "2025-01-15"'
        version = bump_module.get_current_version(content)
        self.assertEqual(version, "2025-01-15")

    def test_get_current_version_missing(self):
        """Test extracting version when not present"""
        content = 'name "test"'
        version = bump_module.get_current_version(content)
        self.assertEqual(version, "unknown")


class TestExceptionHierarchy(unittest.TestCase):
    """Test exception hierarchy"""

    def test_exception_inheritance(self):
        """Test that specific exceptions inherit from BumpError"""
        self.assertTrue(issubclass(bump_module.ReleaseNotFoundError, bump_module.BumpError))
        self.assertTrue(issubclass(bump_module.AssetNotFoundError, bump_module.BumpError))
        self.assertTrue(issubclass(bump_module.CaskFileNotFoundError, bump_module.BumpError))

    def test_exception_instances(self):
        """Test that exceptions can be caught as BumpError"""
        with self.assertRaises(bump_module.BumpError):
            raise bump_module.ReleaseNotFoundError("test")
        
        with self.assertRaises(bump_module.BumpError):
            raise bump_module.AssetNotFoundError("test")
        
        with self.assertRaises(bump_module.BumpError):
            raise bump_module.CaskFileNotFoundError("test")


if __name__ == "__main__":
    unittest.main()
