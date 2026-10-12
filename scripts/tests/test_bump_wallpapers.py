#!/usr/bin/env python3
"""Unit tests for bump-wallpapers.py utilities."""

import unittest
from pathlib import Path


class TestBumpWallpapersStructure(unittest.TestCase):
    """Test bump-wallpapers.py module structure."""

    def test_module_exists(self):
        """bump-wallpapers.py should exist."""
        module_path = Path(__file__).parent.parent / "bump-wallpapers.py"
        self.assertTrue(module_path.exists())

    def test_module_contains_variant_enum(self):
        """Module should define Variant enum."""
        module_path = Path(__file__).parent.parent / "bump-wallpapers.py"
        content = module_path.read_text()
        self.assertIn("class Variant(Enum):", content)
        self.assertIn("MACOS", content)
        self.assertIn("KDE", content)
        self.assertIn("GNOME", content)
        self.assertIn("PNG", content)

    def test_module_contains_cask_config(self):
        """Module should define CaskConfig dataclass."""
        module_path = Path(__file__).parent.parent / "bump-wallpapers.py"
        content = module_path.read_text()
        self.assertIn("class CaskConfig:", content)
        self.assertIn("@dataclass", content)

    def test_module_contains_error_classes(self):
        """Module should define custom error classes."""
        module_path = Path(__file__).parent.parent / "bump-wallpapers.py"
        content = module_path.read_text()
        self.assertIn("class BumpError", content)
        self.assertIn("class ReleaseNotFoundError", content)
        self.assertIn("class AssetNotFoundError", content)
        self.assertIn("class CaskFileNotFoundError", content)

    def test_module_contains_cask_configurations(self):
        """Module should define CASKS list."""
        module_path = Path(__file__).parent.parent / "bump-wallpapers.py"
        content = module_path.read_text()
        self.assertIn("CASKS = [", content)
        self.assertIn("bluefin-wallpapers", content)
        self.assertIn("framework-wallpapers", content)
        self.assertIn("aurora-wallpapers", content)


class TestBumpWallpapersFunctions(unittest.TestCase):
    """Test bump-wallpapers.py contains expected functions."""

    def test_module_contains_find_release(self):
        """Module should define find_release() function."""
        module_path = Path(__file__).parent.parent / "bump-wallpapers.py"
        content = module_path.read_text()
        self.assertIn("def find_release(", content)

    def test_module_contains_get_asset_sha256(self):
        """Module should define get_asset_sha256() function."""
        module_path = Path(__file__).parent.parent / "bump-wallpapers.py"
        content = module_path.read_text()
        self.assertIn("def get_asset_sha256(", content)

    def test_module_contains_update_version(self):
        """Module should define update_version() function."""
        module_path = Path(__file__).parent.parent / "bump-wallpapers.py"
        content = module_path.read_text()
        self.assertIn("def update_version(", content)

    def test_module_contains_update_sha256(self):
        """Module should define SHA256 update functions."""
        module_path = Path(__file__).parent.parent / "bump-wallpapers.py"
        content = module_path.read_text()
        self.assertIn("def update_sha256_after_url(", content)
        self.assertIn("def update_single_sha256(", content)

    def test_module_contains_get_current_version(self):
        """Module should define get_current_version() function."""
        module_path = Path(__file__).parent.parent / "bump-wallpapers.py"
        content = module_path.read_text()
        self.assertIn("def get_current_version(", content)

    def test_module_contains_bump_cask(self):
        """Module should define bump_cask() function."""
        module_path = Path(__file__).parent.parent / "bump-wallpapers.py"
        content = module_path.read_text()
        self.assertIn("def bump_cask(", content)

    def test_module_has_main_entry_point(self):
        """Module should have main() entry point."""
        module_path = Path(__file__).parent.parent / "bump-wallpapers.py"
        content = module_path.read_text()
        self.assertIn("def main(", content)
        self.assertIn('if __name__ == "__main__":', content)


if __name__ == "__main__":
    unittest.main()
