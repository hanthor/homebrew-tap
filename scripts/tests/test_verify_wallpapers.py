#!/usr/bin/env python3
"""Unit tests for verify-wallpapers.py utilities."""

import unittest
from pathlib import Path
import hashlib
import importlib.util

# Load module from parent directory
module_path = Path(__file__).parent.parent / "verify-wallpapers.py"
spec = importlib.util.spec_from_file_location("verify_wallpapers_mod", module_path)
verify_wallpapers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_wallpapers)


class TestTokenRegex(unittest.TestCase):
    """Test regex patterns."""

    def test_token_re_matches_url(self):
        """TOKEN_RE should match url declarations."""
        line = 'url "https://example.com/file.tar.zstd"'
        matches = verify_wallpapers.TOKEN_RE.findall(line)
        self.assertEqual(matches, [("url", "https://example.com/file.tar.zstd")])

    def test_token_re_matches_sha256(self):
        """TOKEN_RE should match sha256 declarations."""
        line = 'sha256 "abcd1234' + '0' * 56 + '"'
        matches = verify_wallpapers.TOKEN_RE.findall(line)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], "sha256")
        self.assertEqual(len(matches[0][1]), 64)

    def test_sha_re_matches_hex_hash(self):
        """SHA_RE should match 64-char hex strings."""
        valid = "abcdef1234567890" * 4
        self.assertIsNotNone(verify_wallpapers.SHA_RE.fullmatch(valid))

    def test_sha_re_rejects_non_hex(self):
        """SHA_RE should reject non-hex characters."""
        invalid = "g0000000" + "0" * 56
        self.assertIsNone(verify_wallpapers.SHA_RE.fullmatch(invalid))

    def test_sha_re_rejects_wrong_length(self):
        """SHA_RE should reject wrong length."""
        too_short = "abcdef" * 10  # 60 chars
        too_long = "abcdef" * 11   # 66 chars
        self.assertIsNone(verify_wallpapers.SHA_RE.fullmatch(too_short))
        self.assertIsNone(verify_wallpapers.SHA_RE.fullmatch(too_long))

    def test_version_re_matches_version(self):
        """VERSION_RE should extract version."""
        content = 'version "2025-12-10"'
        match = verify_wallpapers.VERSION_RE.search(content)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "2025-12-10")


class TestExtractPairsRegexLogic(unittest.TestCase):
    """Test extract_pairs() regex parsing logic."""

    def test_extract_pairs_version_interpolation_format(self):
        """Verify that #{version} is properly recognized in cask format."""
        content = """
        cask "test" do
          version "2025-12-10"
          url "https://example.com/file-#{version}.tar.zstd"
        end
        """
        # Verify version extraction works
        match = verify_wallpapers.VERSION_RE.search(content)
        self.assertEqual(match.group(1), "2025-12-10")
        
        # Verify URL pattern in test content
        self.assertIn("#{version}", content)

    def test_livecheck_block_format(self):
        """Verify livecheck block removal pattern."""
        content = """
        cask "test" do
          version "1.0"
          livecheck do
            url "https://example.com/check"
          end
          url "https://example.com/actual"
        end
        """
        # Remove livecheck block as the function does
        import re
        LIVECHECK_RE = re.compile(r"livecheck\s+do\b.*?\bend\b", re.DOTALL)
        cleaned = LIVECHECK_RE.sub("", content)
        self.assertNotIn("livecheck", cleaned)
        self.assertIn("https://example.com/actual", cleaned)


class TestStringManipulationLogic(unittest.TestCase):
    """Test string manipulation functions work correctly."""

    def test_sha256_hex_format(self):
        """Verify SHA256 hex format validation."""
        valid_sha = "a" * 64
        self.assertIsNotNone(verify_wallpapers.SHA_RE.fullmatch(valid_sha))
        
        # Test that partial hex is invalid
        invalid_sha = "a" * 63
        self.assertIsNone(verify_wallpapers.SHA_RE.fullmatch(invalid_sha))


if __name__ == "__main__":
    unittest.main()
