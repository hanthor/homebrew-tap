#!/usr/bin/env python3
"""Unit tests for bump-wallpapers.py script."""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from io import BytesIO

# Add scripts dir to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

# Import the bump module
import importlib.util
spec = importlib.util.spec_from_file_location(
    "bump_wallpapers",
    Path(__file__).parent.parent / "scripts" / "bump-wallpapers.py"
)
bump_wallpapers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bump_wallpapers)


class TestVariant(unittest.TestCase):
    """Test Variant enum."""

    def test_variant_values(self):
        """Test that all Variant enum members have correct values."""
        self.assertEqual(bump_wallpapers.Variant.MACOS.value, "macos")
        self.assertEqual(bump_wallpapers.Variant.KDE.value, "kde")
        self.assertEqual(bump_wallpapers.Variant.GNOME.value, "gnome")
        self.assertEqual(bump_wallpapers.Variant.PNG.value, "png")

    def test_variant_count(self):
        """Test that Variant has all expected members."""
        self.assertEqual(len(list(bump_wallpapers.Variant)), 4)


class TestCaskConfig(unittest.TestCase):
    """Test CaskConfig dataclass."""

    def test_cask_config_creation(self):
        """Test CaskConfig initialization."""
        config = bump_wallpapers.CaskConfig(
            name="test-wallpapers",
            release_prefix="test",
            artifact_name="test-wallpapers"
        )
        self.assertEqual(config.name, "test-wallpapers")
        self.assertEqual(config.release_prefix, "test")
        self.assertEqual(config.artifact_name, "test-wallpapers")
        self.assertEqual(len(config.variants), 4)

    def test_cask_config_get_tag(self):
        """Test get_tag method."""
        config = bump_wallpapers.CaskConfig(
            name="bluefin",
            release_prefix="bluefin",
            artifact_name="bluefin-wallpapers"
        )
        tag = config.get_tag("1.0.0")
        self.assertEqual(tag, "bluefin-v1.0.0")

    def test_cask_config_get_asset_name(self):
        """Test get_asset_name method."""
        config = bump_wallpapers.CaskConfig(
            name="bluefin",
            release_prefix="bluefin",
            artifact_name="bluefin-wallpapers"
        )
        asset_macos = config.get_asset_name(bump_wallpapers.Variant.MACOS)
        asset_kde = config.get_asset_name(bump_wallpapers.Variant.KDE)
        self.assertEqual(asset_macos, "bluefin-wallpapers-macos.tar.zstd")
        self.assertEqual(asset_kde, "bluefin-wallpapers-kde.tar.zstd")

    def test_cask_config_empty_variants(self):
        """Test CaskConfig with empty variants list."""
        config = bump_wallpapers.CaskConfig(
            name="aurora",
            release_prefix="aurora",
            artifact_name="aurora-wallpapers",
            variants=[]
        )
        self.assertEqual(len(config.variants), 0)


class TestPredefinedCasks(unittest.TestCase):
    """Test predefined CASKS configurations."""

    def test_cask_by_name_mapping(self):
        """Test that CASK_BY_NAME provides correct mappings."""
        self.assertIn("bluefin-wallpapers", bump_wallpapers.CASK_BY_NAME)
        self.assertIn("aurora-wallpapers", bump_wallpapers.CASK_BY_NAME)

    def test_aurora_has_no_variants(self):
        """Test that aurora config has empty variants."""
        aurora = bump_wallpapers.CASK_BY_NAME["aurora-wallpapers"]
        self.assertEqual(len(aurora.variants), 0)

    def test_bluefin_extra_naming(self):
        """Test bluefin-extra config naming."""
        config = bump_wallpapers.CASK_BY_NAME["bluefin-wallpapers-extra"]
        self.assertEqual(config.release_prefix, "bluefin-extra")
        self.assertEqual(config.artifact_name, "bluefin-wallpapers-extra")


class TestFindRelease(unittest.TestCase):
    """Test find_release function."""

    def test_find_release_by_prefix_returns_first_matching(self):
        """Test finding release by prefix."""
        releases = [
            {"tag_name": "bluefin-v1.0.0", "assets": []},
            {"tag_name": "bluefin-v2.0.0", "assets": []},
            {"tag_name": "other-v1.0.0", "assets": []},
        ]
        result = bump_wallpapers.find_release(releases, "bluefin")
        self.assertTrue(result["tag_name"].startswith("bluefin-v"))

    def test_find_release_by_exact_version(self):
        """Test finding release by exact version."""
        releases = [
            {"tag_name": "bluefin-v1.0.0", "assets": []},
            {"tag_name": "bluefin-v2.0.0", "assets": []},
            {"tag_name": "bluefin-v3.0.0", "assets": []},
        ]
        result = bump_wallpapers.find_release(releases, "bluefin", version="2.0.0")
        self.assertEqual(result["tag_name"], "bluefin-v2.0.0")

    def test_find_release_not_found_raises(self):
        """Test that ReleaseNotFoundError is raised when release not found."""
        releases = [
            {"tag_name": "bluefin-v1.0.0", "assets": []},
        ]
        with self.assertRaises(bump_wallpapers.ReleaseNotFoundError):
            bump_wallpapers.find_release(releases, "nonexistent")

    def test_find_release_version_not_found_raises(self):
        """Test that ReleaseNotFoundError is raised for specific version not found."""
        releases = [
            {"tag_name": "bluefin-v1.0.0", "assets": []},
        ]
        with self.assertRaises(bump_wallpapers.ReleaseNotFoundError):
            bump_wallpapers.find_release(releases, "bluefin", version="9.9.9")


class TestBumpErrorHierarchy(unittest.TestCase):
    """Test error class hierarchy."""

    def test_release_not_found_is_bump_error(self):
        """Test that ReleaseNotFoundError is a BumpError."""
        error = bump_wallpapers.ReleaseNotFoundError("test")
        self.assertIsInstance(error, bump_wallpapers.BumpError)

    def test_asset_not_found_is_bump_error(self):
        """Test that AssetNotFoundError is a BumpError."""
        error = bump_wallpapers.AssetNotFoundError("test")
        self.assertIsInstance(error, bump_wallpapers.BumpError)


if __name__ == "__main__":
    unittest.main()
