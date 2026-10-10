"""Unit tests for bump-wallpapers.py configuration and version handling."""

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import json
import tempfile

# Add scripts directory to path
import sys
from pathlib import Path
import importlib.util

# Import bump-wallpapers.py (with hyphen) by loading it directly
spec = importlib.util.spec_from_file_location(
    "bump_wallpapers",
    Path(__file__).parent.parent / "bump-wallpapers.py"
)
bump_wallpapers_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bump_wallpapers_module)

Variant = bump_wallpapers_module.Variant
CaskConfig = bump_wallpapers_module.CaskConfig
BumpError = bump_wallpapers_module.BumpError
ReleaseNotFoundError = bump_wallpapers_module.ReleaseNotFoundError
AssetNotFoundError = bump_wallpapers_module.AssetNotFoundError
CaskFileNotFoundError = bump_wallpapers_module.CaskFileNotFoundError
find_release = bump_wallpapers_module.find_release
get_asset_sha256 = bump_wallpapers_module.get_asset_sha256
update_sha256_after_url = bump_wallpapers_module.update_sha256_after_url
update_version = bump_wallpapers_module.update_version
update_single_sha256 = bump_wallpapers_module.update_single_sha256
get_current_version = bump_wallpapers_module.get_current_version


class TestVariantEnum(unittest.TestCase):
    """Tests for Variant enum."""

    def test_variant_values(self):
        """Test that variant values are correct."""
        self.assertEqual(Variant.MACOS.value, "macos")
        self.assertEqual(Variant.KDE.value, "kde")
        self.assertEqual(Variant.GNOME.value, "gnome")
        self.assertEqual(Variant.PNG.value, "png")

    def test_variant_list(self):
        """Test listing all variants."""
        variants = list(Variant)
        self.assertEqual(len(variants), 4)


class TestCaskConfig(unittest.TestCase):
    """Tests for CaskConfig dataclass."""

    def test_cask_config_basic(self):
        """Test basic CaskConfig creation."""
        config = CaskConfig(
            name="test-wallpapers",
            release_prefix="test",
            artifact_name="test-wallpapers",
        )
        self.assertEqual(config.name, "test-wallpapers")
        self.assertEqual(config.release_prefix, "test")
        self.assertEqual(config.artifact_name, "test-wallpapers")
        self.assertEqual(len(config.variants), 4)

    def test_cask_config_custom_variants(self):
        """Test CaskConfig with custom variants."""
        config = CaskConfig(
            name="test",
            release_prefix="test",
            artifact_name="test",
            variants=[Variant.MACOS, Variant.KDE],
        )
        self.assertEqual(len(config.variants), 2)
        self.assertIn(Variant.MACOS, config.variants)

    def test_cask_config_get_tag(self):
        """Test tag generation."""
        config = CaskConfig(
            name="bluefin",
            release_prefix="bluefin",
            artifact_name="bluefin-wallpapers",
        )
        tag = config.get_tag("2024.12")
        self.assertEqual(tag, "bluefin-v2024.12")

    def test_cask_config_get_asset_name_with_variants(self):
        """Test asset name generation with variants."""
        config = CaskConfig(
            name="bluefin",
            release_prefix="bluefin",
            artifact_name="bluefin-wallpapers",
            variants=[Variant.MACOS],
        )
        asset_name = config.get_asset_name(Variant.MACOS)
        self.assertEqual(asset_name, "bluefin-wallpapers-macos.tar.zstd")

    def test_cask_config_get_asset_name_all_variants(self):
        """Test asset names for each variant."""
        config = CaskConfig(
            name="bluefin",
            release_prefix="bluefin",
            artifact_name="bluefin-wallpapers",
        )
        for variant in Variant:
            asset_name = config.get_asset_name(variant)
            self.assertTrue(asset_name.endswith(".tar.zstd"))
            self.assertIn(variant.value, asset_name)

    def test_cask_file_property(self):
        """Test cask_file property."""
        config = CaskConfig(
            name="test-wallpapers",
            release_prefix="test",
            artifact_name="test-wallpapers",
        )
        # Check that the path ends with the expected filename
        self.assertTrue(str(config.cask_file).endswith("test-wallpapers.rb"))


class TestFindRelease(unittest.TestCase):
    """Tests for find_release function."""

    def test_find_release_by_prefix_latest(self):
        """Test finding latest release by prefix."""
        releases = [
            {"tag_name": "bluefin-v2024.12"},
            {"tag_name": "bluefin-v2024.11"},
            {"tag_name": "other-v1.0"},
        ]
        release = find_release(releases, "bluefin")
        self.assertEqual(release["tag_name"], "bluefin-v2024.12")

    def test_find_release_by_version(self):
        """Test finding release by specific version."""
        releases = [
            {"tag_name": "bluefin-v2024.12"},
            {"tag_name": "bluefin-v2024.11"},
        ]
        release = find_release(releases, "bluefin", "2024.11")
        self.assertEqual(release["tag_name"], "bluefin-v2024.11")

    def test_find_release_not_found(self):
        """Test that ReleaseNotFoundError is raised when release not found."""
        releases = [{"tag_name": "other-v1.0"}]
        with self.assertRaises(ReleaseNotFoundError):
            find_release(releases, "bluefin")

    def test_find_release_version_not_found(self):
        """Test that ReleaseNotFoundError is raised for specific version."""
        releases = [{"tag_name": "bluefin-v2024.12"}]
        with self.assertRaises(ReleaseNotFoundError):
            find_release(releases, "bluefin", "2024.11")

    def test_find_release_ignores_non_matching_prefix(self):
        """Test that releases with wrong prefix are ignored."""
        releases = [
            {"tag_name": "other-v2024.12"},
            {"tag_name": "bluefin-v2024.11"},
        ]
        release = find_release(releases, "bluefin")
        self.assertEqual(release["tag_name"], "bluefin-v2024.11")


class TestGetAssetSha256(unittest.TestCase):
    """Tests for get_asset_sha256 function."""

    def test_get_asset_sha256_valid(self):
        """Test extracting SHA256 from asset digest."""
        sha = "a" * 64
        release = {
            "assets": [
                {
                    "name": "test-wallpapers.tar.zstd",
                    "digest": f"sha256:{sha}",
                }
            ]
        }
        result = get_asset_sha256(release, "test-wallpapers.tar.zstd")
        self.assertEqual(result, sha)

    def test_get_asset_sha256_multiple_assets(self):
        """Test finding correct asset among multiple."""
        sha1 = "a" * 64
        sha2 = "b" * 64
        release = {
            "assets": [
                {"name": "file1.tar.zstd", "digest": f"sha256:{sha1}"},
                {"name": "file2.tar.zstd", "digest": f"sha256:{sha2}"},
            ]
        }
        result = get_asset_sha256(release, "file2.tar.zstd")
        self.assertEqual(result, sha2)

    def test_get_asset_sha256_not_found(self):
        """Test that AssetNotFoundError is raised for missing asset."""
        release = {"assets": []}
        with self.assertRaises(AssetNotFoundError):
            get_asset_sha256(release, "missing.tar.zstd")

    def test_get_asset_sha256_no_digest(self):
        """Test that AssetNotFoundError is raised when digest is missing."""
        release = {
            "assets": [
                {
                    "name": "test-wallpapers.tar.zstd",
                }
            ]
        }
        with self.assertRaises(AssetNotFoundError):
            get_asset_sha256(release, "test-wallpapers.tar.zstd")

    def test_get_asset_sha256_malformed_digest(self):
        """Test handling of malformed digest format."""
        release = {
            "assets": [
                {
                    "name": "test-wallpapers.tar.zstd",
                    "digest": "not-a-digest",
                }
            ]
        }
        with self.assertRaises(AssetNotFoundError):
            get_asset_sha256(release, "test-wallpapers.tar.zstd")


class TestUpdateSha256AfterUrl(unittest.TestCase):
    """Tests for update_sha256_after_url function."""

    def test_update_sha256_after_url_simple(self):
        """Test updating SHA256 that follows a URL."""
        content = '''
        url "https://example.com/file.tar.gz"
        sha256 "0000000000000000000000000000000000000000000000000000000000000000"
        '''
        new_sha = "a" * 64
        result = update_sha256_after_url(content, "https://example.com/file.tar.gz", new_sha)
        self.assertIn(f'sha256 "{new_sha}"', result)

    def test_update_sha256_multiple_pairs(self):
        """Test updating SHA256 in specific URL/SHA pair."""
        sha1 = "a" * 64
        sha2 = "b" * 64
        content = f'''
        url "https://example.com/file1.tar.gz"
        sha256 "0000000000000000000000000000000000000000000000000000000000000000"
        url "https://example.com/file2.tar.gz"
        sha256 "1111111111111111111111111111111111111111111111111111111111111111"
        '''
        new_sha = "c" * 64
        result = update_sha256_after_url(content, "https://example.com/file1.tar.gz", new_sha)
        self.assertIn(f'sha256 "{new_sha}"', result)
        self.assertIn("https://example.com/file2.tar.gz", result)

    def test_update_sha256_with_different_url_patterns(self):
        """Test updating SHA256 when URL pattern appears in artifact name."""
        content = '''
        url "https://example.com/release/bluefin-wallpapers-macos.tar.zstd"
        sha256 "0000000000000000000000000000000000000000000000000000000000000000"
        '''
        new_sha = "a" * 64
        result = update_sha256_after_url(
            content, "bluefin-wallpapers-macos", new_sha
        )
        self.assertIn(f'sha256 "{new_sha}"', result)


class TestUpdateVersion(unittest.TestCase):
    """Tests for update_version function."""

    def test_update_version_simple(self):
        """Test updating version string."""
        content = 'version "1.0.0"'
        result = update_version(content, "2.0.0")
        self.assertIn('version "2.0.0"', result)
        self.assertNotIn('version "1.0.0"', result)

    def test_update_version_date_format(self):
        """Test updating version with date format."""
        content = 'version "2024.12.01"'
        result = update_version(content, "2024.12.15")
        self.assertIn('version "2024.12.15"', result)

    def test_update_version_preserves_formatting(self):
        """Test that version update preserves surrounding content."""
        content = '''
        cask "test" do
          version "1.0.0"
          url "https://example.com"
        end
        '''
        result = update_version(content, "2.0.0")
        self.assertIn('version "2.0.0"', result)
        self.assertIn("https://example.com", result)


class TestUpdateSingleSha256(unittest.TestCase):
    """Tests for update_single_sha256 function."""

    def test_update_single_sha256(self):
        """Test updating single SHA256 value."""
        content = f'sha256 "{"0" * 64}"'
        new_sha = "a" * 64
        result = update_single_sha256(content, new_sha)
        self.assertIn(f'sha256 "{new_sha}"', result)

    def test_update_single_sha256_multiline(self):
        """Test updating SHA256 in multiline content."""
        content = f'''
        url "https://example.com"
        sha256 "{"0" * 64}"
        '''
        new_sha = "a" * 64
        result = update_single_sha256(content, new_sha)
        self.assertIn(f'sha256 "{new_sha}"', result)
        self.assertIn("https://example.com", result)


class TestGetCurrentVersion(unittest.TestCase):
    """Tests for get_current_version function."""

    def test_get_current_version(self):
        """Test extracting current version."""
        content = 'version "2024.12"'
        version = get_current_version(content)
        self.assertEqual(version, "2024.12")

    def test_get_current_version_date_format(self):
        """Test extracting date-format version."""
        content = 'version "2024.12.01"'
        version = get_current_version(content)
        self.assertEqual(version, "2024.12.01")

    def test_get_current_version_not_found(self):
        """Test handling when version is not found."""
        content = 'url "https://example.com"'
        version = get_current_version(content)
        self.assertEqual(version, "unknown")

    def test_get_current_version_in_multiline(self):
        """Test extracting version from multiline content."""
        content = '''
        cask "test" do
          version "1.2.3"
          url "https://example.com"
        end
        '''
        version = get_current_version(content)
        self.assertEqual(version, "1.2.3")


class TestExceptionHierarchy(unittest.TestCase):
    """Tests for exception class hierarchy."""

    def test_release_not_found_is_bump_error(self):
        """Test that ReleaseNotFoundError is a BumpError."""
        exc = ReleaseNotFoundError("test")
        self.assertIsInstance(exc, BumpError)

    def test_asset_not_found_is_bump_error(self):
        """Test that AssetNotFoundError is a BumpError."""
        exc = AssetNotFoundError("test")
        self.assertIsInstance(exc, BumpError)

    def test_cask_file_not_found_is_bump_error(self):
        """Test that CaskFileNotFoundError is a BumpError."""
        exc = CaskFileNotFoundError("test")
        self.assertIsInstance(exc, BumpError)


if __name__ == "__main__":
    unittest.main()
