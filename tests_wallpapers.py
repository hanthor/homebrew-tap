#!/usr/bin/env python3
"""
Unit tests for wallpaper cask verification and bumping utilities.
Tests SHA256 extraction, cask parsing, and version handling.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Import the modules under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import verify_wallpapers
import bump_wallpapers


class TestExtractPairs(unittest.TestCase):
    """Tests for verify-wallpapers.py extract_pairs() function."""

    def test_extract_simple_url_sha_pair(self):
        """Extract a single url/sha256 pair from cask content."""
        cask_content = '''
        version "2025-01-01"
        url "https://example.com/wall.tar.gz"
        sha256 "abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234"
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(cask_content)
            f.flush()
            path = Path(f.name)
        
        try:
            pairs = verify_wallpapers.extract_pairs(path)
            self.assertEqual(len(pairs), 1)
            url, sha = pairs[0]
            self.assertEqual(url, "https://example.com/wall.tar.gz")
            self.assertEqual(sha, "abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234")
        finally:
            path.unlink()

    def test_extract_multiple_pairs(self):
        """Extract multiple url/sha256 pairs from one cask."""
        cask_content = '''
        version "2025-01-01"
        url "https://example.com/wall1.tar.gz"
        sha256 "aaaa000000000000000000000000000000000000000000000000000000000000"
        url "https://example.com/wall2.tar.gz"
        sha256 "bbbb000000000000000000000000000000000000000000000000000000000000"
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(cask_content)
            f.flush()
            path = Path(f.name)
        
        try:
            pairs = verify_wallpapers.extract_pairs(path)
            self.assertEqual(len(pairs), 2)
            self.assertEqual(pairs[0][0], "https://example.com/wall1.tar.gz")
            self.assertEqual(pairs[1][0], "https://example.com/wall2.tar.gz")
        finally:
            path.unlink()

    def test_extract_replaces_version_interpolation(self):
        """Replace #{version} in URLs with actual version."""
        cask_content = '''
        version "2025-03-15"
        url "https://example.com/wall-#{version}.tar.gz"
        sha256 "cccc000000000000000000000000000000000000000000000000000000000000"
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(cask_content)
            f.flush()
            path = Path(f.name)
        
        try:
            pairs = verify_wallpapers.extract_pairs(path)
            url, _ = pairs[0]
            self.assertEqual(url, "https://example.com/wall-2025-03-15.tar.gz")
        finally:
            path.unlink()

    def test_extract_fails_on_missing_version(self):
        """Raise ValueError when version is missing from cask."""
        cask_content = '''
        url "https://example.com/wall.tar.gz"
        sha256 "dddd000000000000000000000000000000000000000000000000000000000000"
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(cask_content)
            f.flush()
            path = Path(f.name)
        
        try:
            with self.assertRaises(ValueError) as ctx:
                verify_wallpapers.extract_pairs(path)
            self.assertIn("No version found", str(ctx.exception))
        finally:
            path.unlink()

    def test_extract_fails_on_unresolved_interpolation(self):
        """Raise ValueError when URL has unresolved #{...} placeholders."""
        cask_content = '''
        version "2025-01-01"
        url "https://example.com/wall-#{unknown_var}.tar.gz"
        sha256 "eeee000000000000000000000000000000000000000000000000000000000000"
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(cask_content)
            f.flush()
            path = Path(f.name)
        
        try:
            with self.assertRaises(ValueError) as ctx:
                verify_wallpapers.extract_pairs(path)
            self.assertIn("Unresolved interpolation", str(ctx.exception))
        finally:
            path.unlink()

    def test_extract_ignores_livecheck_block(self):
        """Ignore url/sha256 inside livecheck do...end blocks."""
        cask_content = '''
        version "2025-01-01"
        url "https://example.com/wall.tar.gz"
        sha256 "ffff000000000000000000000000000000000000000000000000000000000000"
        livecheck do
          url "https://false.example.com"
          sha256 "0000000000000000000000000000000000000000000000000000000000000000"
        end
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(cask_content)
            f.flush()
            path = Path(f.name)
        
        try:
            pairs = verify_wallpapers.extract_pairs(path)
            self.assertEqual(len(pairs), 1)
            url, sha = pairs[0]
            self.assertEqual(url, "https://example.com/wall.tar.gz")
            self.assertTrue(sha.startswith("ffff"))
        finally:
            path.unlink()


class TestSHAValidation(unittest.TestCase):
    """Tests for SHA256 validation helpers."""

    def test_valid_sha256_format(self):
        """SHA256 regex validates 64-char hex strings."""
        valid_sha = "abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234"
        self.assertTrue(verify_wallpapers.SHA_RE.fullmatch(valid_sha))

    def test_invalid_sha256_too_short(self):
        """SHA256 regex rejects strings shorter than 64 chars."""
        short_sha = "abcd1234567890abcd1234567890abcd1234567890abcd1234567890abcd123"
        self.assertIsNone(verify_wallpapers.SHA_RE.fullmatch(short_sha))

    def test_invalid_sha256_non_hex(self):
        """SHA256 regex rejects strings with non-hex characters."""
        invalid_sha = "zzzz1234567890abcd1234567890abcd1234567890abcd1234567890abcd1234"
        self.assertIsNone(verify_wallpapers.SHA_RE.fullmatch(invalid_sha))

    def test_invalid_sha256_uppercase(self):
        """SHA256 regex rejects uppercase hex (lower only)."""
        uppercase_sha = "ABCD1234567890ABCD1234567890ABCD1234567890ABCD1234567890ABCD1234"
        self.assertIsNone(verify_wallpapers.SHA_RE.fullmatch(uppercase_sha))


if __name__ == '__main__':
    unittest.main()
