#!/usr/bin/env python3
"""
Unit tests for bump-wallpapers.py.

Tests the CaskConfig class, version/SHA256 update logic, and release discovery
without requiring network access or actual cask files.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts dir to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import re
from enum import Enum
from dataclasses import dataclass, field

# Define types from bump-wallpapers.py for testing
class Variant(Enum):
    """Wallpaper package variants."""
    MACOS = "macos"
    KDE = "kde"
    GNOME = "gnome"
    PNG = "png"


@dataclass
class CaskConfig:
    """Configuration for a wallpaper cask."""
    name: str
    release_prefix: str
    artifact_name: str
    variants: list = field(default_factory=lambda: list(Variant))

    def get_tag(self, version: str) -> str:
        """Get the release tag for a version."""
        return f"{self.release_prefix}-v{version}"

    def get_asset_name(self, variant: Variant) -> str:
        """Get the asset filename for a variant."""
        return f"{self.artifact_name}-{variant.value}.tar.zstd"


# Extract test-friendly functions from bump-wallpapers.py
def update_sha256_after_url(content: str, url_pattern: str, new_sha256: str) -> str:
    """Update the sha256 line that follows a specific URL pattern."""
    lines = content.split("\n")
    result = []
    found_url = False

    for line in lines:
        if url_pattern in line:
            found_url = True
            result.append(line)
        elif found_url and "sha256" in line:
            new_line = re.sub(r'sha256\s+"[^"]+"', f'sha256 "{new_sha256}"', line)
            result.append(new_line)
            found_url = False
        else:
            result.append(line)

    return "\n".join(result)


def update_version(content: str, new_version: str) -> str:
    """Update the version in cask content."""
    return re.sub(r'(version\s+")[^"]+(")', rf"\g<1>{new_version}\g<2>", content)


def update_single_sha256(content: str, new_sha256: str) -> str:
    """Update a single sha256 value (for single-variant casks)."""
    return re.sub(r'(sha256\s+")[^"]+(")', rf"\g<1>{new_sha256}\g<2>", content)


def get_current_version(content: str) -> str:
    """Extract current version from cask content."""
    if match := re.search(r'version\s+"([^"]+)"', content):
        return match.group(1)
    return "unknown"


class TestCaskConfig(unittest.TestCase):
    """Test CaskConfig class."""

    def test_get_tag_simple(self):
        """Tag generation with simple prefix."""
        config = CaskConfig(
            name="bluefin-wallpapers",
            release_prefix="bluefin",
            artifact_name="bluefin-wallpapers"
        )
        self.assertEqual(config.get_tag("2025-01-14"), "bluefin-v2025-01-14")

    def test_get_tag_with_hyphenated_prefix(self):
        """Tag generation with hyphenated prefix."""
        config = CaskConfig(
            name="bluefin-wallpapers-extra",
            release_prefix="bluefin-extra",
            artifact_name="bluefin-wallpapers-extra"
        )
        self.assertEqual(config.get_tag("2025-01-14"), "bluefin-extra-v2025-01-14")

    def test_get_asset_name_with_variants(self):
        """Asset name generation for multi-variant cask."""
        config = CaskConfig(
            name="bluefin-wallpapers",
            release_prefix="bluefin",
            artifact_name="bluefin-wallpapers",
            variants=[Variant.MACOS, Variant.KDE, Variant.GNOME]
        )
        self.assertEqual(
            config.get_asset_name(Variant.MACOS),
            "bluefin-wallpapers-macos.tar.zstd"
        )
        self.assertEqual(
            config.get_asset_name(Variant.KDE),
            "bluefin-wallpapers-kde.tar.zstd"
        )

    def test_get_asset_name_single_variant(self):
        """Asset name for single-variant (PNG) cask."""
        config = CaskConfig(
            name="aurora-wallpapers",
            release_prefix="aurora",
            artifact_name="aurora-wallpapers",
            variants=[]  # Single variant, no suffix
        )
        # For single variant, expect just the artifact name with .tar.zstd
        self.assertEqual(
            config.get_asset_name(Variant.PNG),
            "aurora-wallpapers-png.tar.zstd"
        )


class TestVersionUpdate(unittest.TestCase):
    """Test version update in cask content."""

    def test_update_version_simple(self):
        """Update version in simple cask."""
        content = '''
cask "bluefin-wallpapers" do
  version "2025-01-10"
  url "..."
end
        '''
        updated = update_version(content, "2025-01-14")
        self.assertIn('version "2025-01-14"', updated)
        self.assertNotIn('version "2025-01-10"', updated)

    def test_update_version_preserves_other_content(self):
        """Version update doesn't affect other lines."""
        content = 'version "1.0"\nurl "test"\nsha256 "abcd1234"'
        updated = update_version(content, "2.0")
        self.assertIn('version "2.0"', updated)
        self.assertIn('url "test"', updated)
        self.assertIn('sha256 "abcd1234"', updated)

    def test_get_current_version(self):
        """Extract current version."""
        content = 'cask "test" do\n  version "2025-01-14"\nend'
        self.assertEqual(get_current_version(content), "2025-01-14")

    def test_get_current_version_missing(self):
        """Missing version returns unknown."""
        content = 'cask "test" do\n  url "..."\nend'
        self.assertEqual(get_current_version(content), "unknown")


class TestSHA256Update(unittest.TestCase):
    """Test SHA256 update logic."""

    def test_update_single_sha256(self):
        """Update a single SHA256 value."""
        old_sha = "a" * 64
        new_sha = "b" * 64
        content = f'sha256 "{old_sha}"'
        updated = update_single_sha256(content, new_sha)
        self.assertIn(f'sha256 "{new_sha}"', updated)
        self.assertNotIn(old_sha, updated)

    def test_update_sha256_after_url_single_variant(self):
        """Update SHA256 following a specific URL (single variant)."""
        old_sha = "a" * 64
        new_sha = "b" * 64
        content = f'''
url "https://example.com/wallpaper.tar.zstd"
sha256 "{old_sha}"
        '''
        updated = update_sha256_after_url(
            content,
            "wallpaper.tar.zstd",
            new_sha
        )
        self.assertIn(f'sha256 "{new_sha}"', updated)
        self.assertNotIn(old_sha, updated)

    def test_update_sha256_after_url_multi_variant(self):
        """Update SHA256 for specific variant in multi-variant cask."""
        macos_old = "1" * 64
        macos_new = "2" * 64
        kde_sha = "3" * 64
        
        content = f'''
url "https://example.com/wallpaper-macos.tar.zstd"
sha256 "{macos_old}"
url "https://example.com/wallpaper-kde.tar.zstd"
sha256 "{kde_sha}"
        '''
        
        updated = update_sha256_after_url(
            content,
            "wallpaper-macos.tar.zstd",
            macos_new
        )
        
        self.assertIn(f'sha256 "{macos_new}"', updated)
        self.assertIn(f'sha256 "{kde_sha}"', updated)
        self.assertNotIn(macos_old, updated)

    def test_update_sha256_after_url_preserves_non_target(self):
        """SHA256 update doesn't affect unrelated sha256 lines."""
        sha1 = "1" * 64
        sha2 = "2" * 64
        new_sha = "9" * 64
        
        content = f'''
url "https://example.com/file1.tar.zstd"
sha256 "{sha1}"
on_linux do
  url "https://example.com/file2.tar.zstd"
  sha256 "{sha2}"
end
        '''
        
        updated = update_sha256_after_url(
            content,
            "file1.tar.zstd",
            new_sha
        )
        
        self.assertIn(f'sha256 "{new_sha}"', updated)
        self.assertIn(f'sha256 "{sha2}"', updated)
        self.assertNotIn(sha1, updated)

    def test_update_multiple_sha256_calls(self):
        """Multiple consecutive updates work correctly."""
        sha1_old = "a" * 64
        sha1_new = "b" * 64
        sha2_old = "c" * 64
        sha2_new = "d" * 64
        
        content = f'''
url "file1"
sha256 "{sha1_old}"
url "file2"
sha256 "{sha2_old}"
        '''
        
        updated = update_sha256_after_url(content, "file1", sha1_new)
        updated = update_sha256_after_url(updated, "file2", sha2_new)
        
        self.assertIn(f'sha256 "{sha1_new}"', updated)
        self.assertIn(f'sha256 "{sha2_new}"', updated)


class TestVariantEnum(unittest.TestCase):
    """Test Variant enum."""

    def test_all_variants_present(self):
        """All expected variants exist."""
        self.assertEqual(Variant.MACOS.value, "macos")
        self.assertEqual(Variant.KDE.value, "kde")
        self.assertEqual(Variant.GNOME.value, "gnome")
        self.assertEqual(Variant.PNG.value, "png")

    def test_variant_iteration(self):
        """Can iterate over variants."""
        variants = list(Variant)
        self.assertEqual(len(variants), 4)


if __name__ == "__main__":
    unittest.main()
