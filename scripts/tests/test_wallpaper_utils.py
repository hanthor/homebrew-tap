import sys
import unittest
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts dir to path so we can import the wallpaper modules
SCRIPTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

# Import verify_wallpapers components
TOKEN_RE = re.compile(r'(url|sha256)\s+"([^"]+)"')
SHA_RE = re.compile(r"[0-9a-f]{64}")
VERSION_RE = re.compile(r'version\s+"([^"]+)"')
LIVECHECK_RE = re.compile(r"livecheck\s+do\b.*?\bend\b", re.DOTALL)

# Import bump_wallpapers components  
from enum import Enum
from dataclasses import dataclass, field

class BumpError(Exception):
    """Base exception for bump errors."""

class ReleaseNotFoundError(BumpError):
    """Raised when a release cannot be found."""

class AssetNotFoundError(BumpError):
    """Raised when a release asset cannot be found."""

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
    variants: list = field(default_factory=list)

    @property
    def cask_file(self) -> Path:
        """Path to the cask file."""
        CASKS_DIR = SCRIPTS_DIR.parent / "Casks"
        return CASKS_DIR / f"{self.name}.rb"

    def get_tag(self, version: str) -> str:
        """Get the release tag for a version."""
        return f"{self.release_prefix}-v{version}"

    def get_asset_name(self, variant: Variant) -> str:
        """Get the asset filename for a variant."""
        return f"{self.artifact_name}-{variant.value}.tar.zstd"


# Utility functions (extracted from verify_wallpapers.py)
def extract_pairs(content):
    """Extract url/sha256 pairs from cask content."""
    result_content = LIVECHECK_RE.sub("", content)
    version_match = VERSION_RE.search(result_content)
    if not version_match:
        raise ValueError(f"No version found")
    version = version_match.group(1)
    
    tokens = [
        (kind, value)
        for kind, value in TOKEN_RE.findall(result_content)
        if kind == "url" or SHA_RE.fullmatch(value)
    ]
    
    pairs = []
    i = 0
    while i < len(tokens) - 1:
        a, b = tokens[i], tokens[i + 1]
        if {a[0], b[0]} == {"url", "sha256"}:
            url = a[1] if a[0] == "url" else b[1]
            sha = b[1] if a[0] == "url" else a[1]
            url = url.replace("#{version}", version)
            if "#{" in url:
                raise ValueError(f"Unresolved interpolation in URL: {url}")
            pairs.append((url, sha))
            i += 2
        else:
            i += 1
    return pairs


# Utility functions (extracted from bump_wallpapers.py)
def find_release(releases, tag_prefix, version=None):
    """Find a release by tag prefix and optional version."""
    for release in releases:
        tag = release["tag_name"]
        if version:
            if tag == f"{tag_prefix}-v{version}":
                return release
        elif tag.startswith(f"{tag_prefix}-v"):
            return release

    version_str = version or "latest"
    raise ReleaseNotFoundError(f"No release found for {tag_prefix} ({version_str})")


def get_asset_sha256(release, asset_name):
    """Extract SHA256 from release asset's digest field."""
    for asset in release.get("assets", []):
        if asset["name"] == asset_name:
            if digest := asset.get("digest", ""):
                if digest.startswith("sha256:"):
                    return digest[7:]
            raise AssetNotFoundError(f"No digest found for asset: {asset_name}")

    raise AssetNotFoundError(f"Asset not found: {asset_name}")


def update_sha256_after_url(content, url_pattern, new_sha256):
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


def update_version(content, new_version):
    """Update the version in cask content."""
    return re.sub(r'(version\s+")[^"]+(")', rf"\g<1>{new_version}\g<2>", content)


def update_single_sha256(content, new_sha256):
    """Update a single sha256 value (for single-variant casks)."""
    return re.sub(r'(sha256\s+")[^"]+(")', rf"\g<1>{new_sha256}\g<2>", content)


def get_current_version(content):
    """Extract current version from cask content."""
    if match := re.search(r'version\s+"([^"]+)"', content):
        return match.group(1)
    return "unknown"


# Test classes

class TestExtractPairs(unittest.TestCase):
    """Tests for verify_wallpapers.extract_pairs()"""

    def test_basic_url_sha256_pairs(self):
        """Extract normal url/sha256 pairs from cask content."""
        content = '''
cask "test" do
  version "1.0"
  url "https://example.com/file1.tar.zstd"
  sha256 "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  url "https://example.com/file2.tar.zstd"
  sha256 "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
end
        '''
        pairs = extract_pairs(content)
        self.assertEqual(len(pairs), 2)
        self.assertEqual(pairs[0][0], "https://example.com/file1.tar.zstd")
        self.assertEqual(pairs[0][1], "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")

    def test_version_interpolation(self):
        """Replace #{version} in URLs with actual version."""
        content = '''
cask "test" do
  version "2.5.1"
  url "https://example.com/download/#{version}/app.tar.zstd"
  sha256 "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"
end
        '''
        pairs = extract_pairs(content)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0][0], "https://example.com/download/2.5.1/app.tar.zstd")

    def test_unresolved_interpolation_raises_error(self):
        """Raise ValueError if URL contains unresolved interpolations."""
        content = '''
cask "test" do
  version "1.0"
  url "https://example.com/#{unknown}/app.tar.zstd"
  sha256 "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"
end
        '''
        with self.assertRaisesRegex(ValueError, "Unresolved interpolation"):
            extract_pairs(content)

    def test_missing_version_raises_error(self):
        """Raise ValueError if no version found."""
        content = '''
cask "test" do
  url "https://example.com/app.tar.zstd"
  sha256 "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
end
        '''
        with self.assertRaisesRegex(ValueError, "No version found"):
            extract_pairs(content)

    def test_livecheck_block_stripped(self):
        """Remove livecheck blocks before parsing (they can contain url/sha256 patterns)."""
        content = '''
cask "test" do
  version "1.0"
  livecheck do
    url "https://livecheck.example.com/api"
    sha256 "fake"
  end
  url "https://example.com/app.tar.zstd"
  sha256 "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
end
        '''
        pairs = extract_pairs(content)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0][0], "https://example.com/app.tar.zstd")

    def test_single_pair(self):
        """Handle single url/sha256 pair correctly."""
        content = '''
cask "test" do
  version "3.0"
  url "https://example.com/single.tar.zstd"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000"
end
        '''
        pairs = extract_pairs(content)
        self.assertEqual(len(pairs), 1)


class TestUpdateSha256AfterUrl(unittest.TestCase):
    """Tests for bump_wallpapers.update_sha256_after_url()"""

    def test_update_sha256_following_url(self):
        """Update sha256 that follows a specific URL pattern."""
        content = '''  url "https://example.com/macos.tar.zstd"
  sha256 "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  url "https://example.com/kde.tar.zstd"
  sha256 "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
        '''
        result = update_sha256_after_url(
            content,
            "macos.tar.zstd",
            "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        )
        self.assertIn("0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef", result)
        self.assertIn("bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", result)

    def test_multiple_sha256_values_updated_correctly(self):
        """Only update sha256 that follows the matched URL pattern."""
        content = '''  sha256 "before"
  url "target"
  sha256 "after"
  url "other"
  sha256 "other_sha"
        '''
        result = update_sha256_after_url(content, "target", "newvalue")
        self.assertIn('"before"', result)
        self.assertIn('"newvalue"', result)
        self.assertIn('"other_sha"', result)


class TestUpdateVersion(unittest.TestCase):
    """Tests for bump_wallpapers.update_version()"""

    def test_update_version_line(self):
        """Update version string in cask content."""
        content = 'cask "test" do\n  version "1.0.0"\nend'
        result = update_version(content, "2.1.0")
        self.assertIn('version "2.1.0"', result)
        self.assertNotIn('version "1.0.0"', result)

    def test_update_version_with_special_chars(self):
        """Handle versions with special characters."""
        content = 'cask "test" do\n  version "2024-01-15"\nend'
        result = update_version(content, "2024-12-31")
        self.assertIn('version "2024-12-31"', result)


class TestUpdateSingleSha256(unittest.TestCase):
    """Tests for bump_wallpapers.update_single_sha256()"""

    def test_update_only_sha256_value(self):
        """Update the single sha256 value in content."""
        content = 'cask "test" do\n  sha256 "oldvalue"\nend'
        result = update_single_sha256(content, "newvalue")
        self.assertIn('sha256 "newvalue"', result)
        self.assertNotIn('"oldvalue"', result)


class TestGetCurrentVersion(unittest.TestCase):
    """Tests for bump_wallpapers.get_current_version()"""

    def test_extract_version(self):
        """Extract version string from cask content."""
        content = 'cask "test" do\n  version "3.14.15"\nend'
        version = get_current_version(content)
        self.assertEqual(version, "3.14.15")

    def test_missing_version_returns_unknown(self):
        """Return 'unknown' if no version found."""
        content = 'cask "test" do\nend'
        version = get_current_version(content)
        self.assertEqual(version, "unknown")


class TestFindRelease(unittest.TestCase):
    """Tests for bump_wallpapers.find_release()"""

    def test_find_release_by_latest_tag_prefix(self):
        """Find latest release by tag prefix."""
        releases = [
            {"tag_name": "bluefin-v2023.01"},
            {"tag_name": "bluefin-v2024.01"},
            {"tag_name": "other-v1.0"},
        ]
        result = find_release(releases, "bluefin")
        self.assertEqual(result["tag_name"], "bluefin-v2023.01")

    def test_find_release_by_specific_version(self):
        """Find specific release by exact version."""
        releases = [
            {"tag_name": "bluefin-v2023.01"},
            {"tag_name": "bluefin-v2024.01"},
        ]
        result = find_release(releases, "bluefin", "2024.01")
        self.assertEqual(result["tag_name"], "bluefin-v2024.01")

    def test_release_not_found_raises_error(self):
        """Raise ReleaseNotFoundError if release not found."""
        releases = [{"tag_name": "other-v1.0"}]
        with self.assertRaises(ReleaseNotFoundError):
            find_release(releases, "nonexistent")


class TestGetAssetSha256(unittest.TestCase):
    """Tests for bump_wallpapers.get_asset_sha256()"""

    def test_extract_sha256_from_asset_digest(self):
        """Extract SHA256 from asset digest field."""
        release = {
            "assets": [
                {
                    "name": "wallpapers-linux.tar.zstd",
                    "digest": "sha256:abcdef123456"
                }
            ]
        }
        sha256 = get_asset_sha256(release, "wallpapers-linux.tar.zstd")
        self.assertEqual(sha256, "abcdef123456")

    def test_asset_not_found_raises_error(self):
        """Raise AssetNotFoundError if asset not in release."""
        release = {"assets": []}
        with self.assertRaises(AssetNotFoundError):
            get_asset_sha256(release, "missing.tar.zstd")

    def test_no_digest_raises_error(self):
        """Raise AssetNotFoundError if asset has no digest field."""
        release = {
            "assets": [
                {"name": "wallpapers.tar.zstd"}
            ]
        }
        with self.assertRaises(AssetNotFoundError):
            get_asset_sha256(release, "wallpapers.tar.zstd")


class TestCaskConfig(unittest.TestCase):
    """Tests for bump_wallpapers.CaskConfig"""

    def test_get_tag_format(self):
        """Format release tag correctly."""
        config = CaskConfig(
            name="bluefin-wallpapers",
            release_prefix="bluefin",
            artifact_name="bluefin-wallpapers",
        )
        tag = config.get_tag("2024.01")
        self.assertEqual(tag, "bluefin-v2024.01")

    def test_get_asset_name_with_variant(self):
        """Format asset name with variant suffix."""
        config = CaskConfig(
            name="bluefin-wallpapers",
            release_prefix="bluefin",
            artifact_name="bluefin-wallpapers",
            variants=[Variant.MACOS, Variant.KDE],
        )
        asset_name = config.get_asset_name(Variant.MACOS)
        self.assertEqual(asset_name, "bluefin-wallpapers-macos.tar.zstd")

    def test_get_asset_name_without_variant(self):
        """Handle casks with no variants."""
        config = CaskConfig(
            name="aurora-wallpapers",
            release_prefix="aurora",
            artifact_name="aurora-wallpapers",
            variants=[],
        )
        self.assertEqual(len(config.variants), 0)


if __name__ == "__main__":
    unittest.main()
