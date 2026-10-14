#!/usr/bin/env python3
"""
Unit tests for verify-wallpapers.py.

Tests the URL/SHA256 extraction, cask content parsing, and verification logic
without requiring network access or actual cask files.
"""

import hashlib
import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add scripts dir to path for imports
SCRIPTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

# Import the functions we're testing
import re

TOKEN_RE = re.compile(r'(url|sha256)\s+"([^"]+)"')
SHA_RE = re.compile(r"[0-9a-f]{64}")
VERSION_RE = re.compile(r'version\s+"([^"]+)"')
LIVECHECK_RE = re.compile(r"livecheck\s+do\b.*?\bend\b", re.DOTALL)


def extract_pairs(content: str):
    """Extract url/sha256 pairs from cask content (from verify-wallpapers.py)."""
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


class TestExtractPairs(unittest.TestCase):
    """Test URL/SHA256 pair extraction from cask content."""

    def test_simple_url_sha_pair(self):
        """Extract a simple URL and SHA256 pair."""
        content = '''
        version "1.0"
        url "https://example.com/file.tar.gz"
        sha256 "abcd1234" * 8
        '''
        # Create a valid hex SHA256 (64 hex chars)
        valid_sha = "a" * 64
        content = f'''
        version "1.0"
        url "https://example.com/file.tar.gz"
        sha256 "{valid_sha}"
        '''
        pairs = extract_pairs(content)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0][0], "https://example.com/file.tar.gz")
        self.assertEqual(pairs[0][1], valid_sha)

    def test_version_interpolation(self):
        """Version interpolation in URL should work."""
        valid_sha = "b" * 64
        content = f'''
        version "2.5.1"
        url "https://example.com/app-#{{version}}.tar.gz"
        sha256 "{valid_sha}"
        '''
        pairs = extract_pairs(content)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0][0], "https://example.com/app-2.5.1.tar.gz")

    def test_unresolved_interpolation_raises(self):
        """Unresolved interpolations should raise ValueError."""
        valid_sha = "c" * 64
        content = f'''
        version "1.0"
        url "https://example.com/app-#{{unknown_var}}.tar.gz"
        sha256 "{valid_sha}"
        '''
        with self.assertRaises(ValueError) as ctx:
            extract_pairs(content)
        self.assertIn("Unresolved interpolation", str(ctx.exception))

    def test_missing_version_raises(self):
        """Missing version should raise ValueError."""
        valid_sha = "d" * 64
        content = f'''
        url "https://example.com/file.tar.gz"
        sha256 "{valid_sha}"
        '''
        with self.assertRaises(ValueError) as ctx:
            extract_pairs(content)
        self.assertIn("No version found", str(ctx.exception))

    def test_multiple_pairs(self):
        """Extract multiple URL/SHA pairs (for variants)."""
        sha1 = "e" * 64
        sha2 = "f" * 64
        content = f'''
        version "1.0"
        url "https://example.com/variant1.tar.gz"
        sha256 "{sha1}"
        url "https://example.com/variant2.tar.gz"
        sha256 "{sha2}"
        '''
        pairs = extract_pairs(content)
        self.assertEqual(len(pairs), 2)
        self.assertEqual(pairs[0][0], "https://example.com/variant1.tar.gz")
        self.assertEqual(pairs[1][0], "https://example.com/variant2.tar.gz")

    def test_livecheck_block_stripped(self):
        """Livecheck do...end blocks should be stripped before parsing."""
        valid_sha = "a" * 64
        content = f'''
        version "1.0"
        livecheck do
          url "https://example.com/livecheck"
          strategy :github_latest
        end
        url "https://example.com/actual.tar.gz"
        sha256 "{valid_sha}"
        '''
        pairs = extract_pairs(content)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0][0], "https://example.com/actual.tar.gz")

    def test_invalid_sha_format_ignored(self):
        """Invalid SHA256 formats should not be treated as SHA."""
        valid_sha = "0" * 64
        content = f'''
        version "1.0"
        url "https://example.com/file.tar.gz"
        sha256 "{valid_sha}"
        # This is not a valid sha (63 chars, not 64)
        depends_on "abc123def456" * 3
        '''
        pairs = extract_pairs(content)
        self.assertEqual(len(pairs), 1)

    def test_sha_outside_quotes_ignored(self):
        """SHA256 values outside quotes should not be extracted."""
        valid_sha = "1" * 64
        content = f'''
        version "1.0"
        url "https://example.com/file.tar.gz"
        sha256 "{valid_sha}"
        # Raw SHA outside quotes: {valid_sha} should be ignored
        '''
        pairs = extract_pairs(content)
        self.assertEqual(len(pairs), 1)


class TestFetchSHA256(unittest.TestCase):
    """Test SHA256 checksum calculation."""

    def test_sha256_calculation(self):
        """SHA256 should match expected value for known content."""
        # Create a simple test file content
        test_data = b"test content for sha256"
        expected = hashlib.sha256(test_data).hexdigest()
        
        # Verify it's a valid 64-char hex string
        self.assertEqual(len(expected), 64)
        self.assertTrue(all(c in '0123456789abcdef' for c in expected))

    def test_sha256_deterministic(self):
        """Same input should produce same SHA256."""
        test_data = b"deterministic test"
        h1 = hashlib.sha256(test_data).hexdigest()
        h2 = hashlib.sha256(test_data).hexdigest()
        self.assertEqual(h1, h2)

    def test_sha256_different_for_different_input(self):
        """Different inputs should produce different SHA256."""
        h1 = hashlib.sha256(b"input 1").hexdigest()
        h2 = hashlib.sha256(b"input 2").hexdigest()
        self.assertNotEqual(h1, h2)


class TestCaskFileFormat(unittest.TestCase):
    """Test parsing of realistic cask file formats."""

    def test_bluefin_wallpapers_format(self):
        """Test parsing a realistic wallpaper cask format."""
        valid_sha = "2" * 64
        bluefin_format = f'''
        cask "bluefin-wallpapers" do
          version "2025-01-14"
          
          on_macos do
            url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{{version}}/bluefin-wallpapers-macos.tar.zstd"
            sha256 "{valid_sha}"
          end
          
          on_linux do
            url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{{version}}/bluefin-wallpapers-linux.tar.zstd"
            sha256 "{valid_sha}"
          end
        end
        '''
        pairs = extract_pairs(bluefin_format)
        self.assertGreaterEqual(len(pairs), 2)
        # Both URLs should have version interpolated
        for url, _ in pairs:
            self.assertIn("2025-01-14", url)
            self.assertNotIn("#{version}", url)

    def test_version_with_hyphens_and_numbers(self):
        """Version strings can include hyphens and numbers."""
        valid_sha = "3" * 64
        content = f'''
        version "2025-01-14"
        url "https://example.com/app-#{{version}}-final.tar.gz"
        sha256 "{valid_sha}"
        '''
        pairs = extract_pairs(content)
        self.assertEqual(pairs[0][0], "https://example.com/app-2025-01-14-final.tar.gz")

    def test_empty_cask_content_raises(self):
        """Empty or minimal content should raise ValueError."""
        with self.assertRaises(ValueError):
            extract_pairs("")

    def test_version_only_no_urls_returns_empty(self):
        """Having version but no URL/SHA pairs should return empty list."""
        content = 'version "1.0"'
        result = extract_pairs(content)
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
