"""Unit tests for verify-wallpapers.py parsing and validation logic."""

import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import tempfile

# Add scripts directory to path so we can import the module
import sys
from pathlib import Path
import importlib.util

# Import verify-wallpapers.py (with hyphen) by loading it directly
spec = importlib.util.spec_from_file_location(
    "verify_wallpapers",
    Path(__file__).parent.parent / "verify-wallpapers.py"
)
verify_wallpapers_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_wallpapers_module)

extract_pairs = verify_wallpapers_module.extract_pairs
SHA_RE = verify_wallpapers_module.SHA_RE
TOKEN_RE = verify_wallpapers_module.TOKEN_RE
VERSION_RE = verify_wallpapers_module.VERSION_RE
LIVECHECK_RE = verify_wallpapers_module.LIVECHECK_RE


class TestSHARegex(unittest.TestCase):
    """Tests for SHA256 regex validation."""

    def test_valid_sha256(self):
        """Test that valid SHA256 hashes are matched."""
        valid_sha = "a" * 64
        self.assertIsNotNone(SHA_RE.fullmatch(valid_sha))

    def test_valid_sha256_mixed_case(self):
        """Test lowercase SHA256 hash."""
        valid_sha = "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
        self.assertIsNotNone(SHA_RE.fullmatch(valid_sha))

    def test_invalid_sha256_too_short(self):
        """Test that short hashes are rejected."""
        short_sha = "a" * 63
        self.assertIsNone(SHA_RE.fullmatch(short_sha))

    def test_invalid_sha256_too_long(self):
        """Test that long hashes are rejected."""
        long_sha = "a" * 65
        self.assertIsNone(SHA_RE.fullmatch(long_sha))

    def test_invalid_sha256_with_uppercase(self):
        """Test that uppercase letters are rejected."""
        upper_sha = "A" * 64
        self.assertIsNone(SHA_RE.fullmatch(upper_sha))

    def test_invalid_sha256_with_non_hex(self):
        """Test that non-hex characters are rejected."""
        invalid_sha = "g" * 64
        self.assertIsNone(SHA_RE.fullmatch(invalid_sha))


class TestTokenRegex(unittest.TestCase):
    """Tests for token extraction regex."""

    def test_extract_url_token(self):
        """Test extracting URL token."""
        content = 'url "https://example.com/file.tar.gz"'
        matches = TOKEN_RE.findall(content)
        self.assertEqual(matches, [("url", "https://example.com/file.tar.gz")])

    def test_extract_sha256_token(self):
        """Test extracting SHA256 token."""
        sha = "a" * 64
        content = f'sha256 "{sha}"'
        matches = TOKEN_RE.findall(content)
        self.assertEqual(matches, [("sha256", sha)])

    def test_extract_multiple_tokens(self):
        """Test extracting multiple URL/SHA256 pairs."""
        sha1 = "a" * 64
        sha2 = "b" * 64
        content = f'''
        url "https://example.com/file1.tar.gz"
        sha256 "{sha1}"
        url "https://example.com/file2.tar.gz"
        sha256 "{sha2}"
        '''
        matches = TOKEN_RE.findall(content)
        self.assertEqual(len(matches), 4)
        self.assertEqual(matches[0], ("url", "https://example.com/file1.tar.gz"))
        self.assertEqual(matches[1], ("sha256", sha1))


class TestVersionRegex(unittest.TestCase):
    """Tests for version extraction regex."""

    def test_extract_version(self):
        """Test extracting version."""
        content = 'version "2024.12.01"'
        match = VERSION_RE.search(content)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "2024.12.01")

    def test_extract_version_with_spacing(self):
        """Test extracting version with various spacing."""
        content = 'version  "2024.12.01"'
        match = VERSION_RE.search(content)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "2024.12.01")

    def test_no_version_found(self):
        """Test when version is not present."""
        content = 'url "https://example.com/file.tar.gz"'
        match = VERSION_RE.search(content)
        self.assertIsNone(match)


class TestLivecheckRegex(unittest.TestCase):
    """Tests for livecheck block removal."""

    def test_remove_livecheck_block(self):
        """Test that livecheck block is properly removed."""
        content = '''
        url "https://example.com"
        livecheck do
          url :homepage
          strategy :github_latest
        end
        sha256 "a" * 64
        '''
        result = LIVECHECK_RE.sub("", content)
        self.assertNotIn("livecheck", result)
        self.assertIn('url "https://example.com"', result)

    def test_remove_livecheck_nested(self):
        """Test livecheck removal with nested blocks."""
        content = '''
        livecheck do
          url "https://api.github.com/repos/example/example/releases/latest"
          regex(/^v?(\\d+\\.\\d+)$/i)
          strategy :github_latest
        end
        '''
        result = LIVECHECK_RE.sub("", content)
        self.assertEqual(result.strip(), "")


class TestExtractPairs(unittest.TestCase):
    """Tests for URL/SHA256 pair extraction."""

    def test_extract_single_pair(self):
        """Test extracting a single URL/SHA256 pair."""
        sha = "a" * 64
        content = f'''
        version "1.0.0"
        url "https://example.com/file.tar.gz"
        sha256 "{sha}"
        '''
        # Create a temp file to test with
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(content)
            f.flush()
            try:
                pairs = extract_pairs(Path(f.name))
                self.assertEqual(len(pairs), 1)
                self.assertEqual(pairs[0], ("https://example.com/file.tar.gz", sha))
            finally:
                Path(f.name).unlink()

    def test_extract_multiple_pairs(self):
        """Test extracting multiple URL/SHA256 pairs."""
        sha1 = "a" * 64
        sha2 = "b" * 64
        content = f'''
        version "1.0.0"
        url "https://example.com/file1.tar.gz"
        sha256 "{sha1}"
        url "https://example.com/file2.tar.gz"
        sha256 "{sha2}"
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(content)
            f.flush()
            try:
                pairs = extract_pairs(Path(f.name))
                self.assertEqual(len(pairs), 2)
                self.assertEqual(pairs[0][0], "https://example.com/file1.tar.gz")
                self.assertEqual(pairs[1][0], "https://example.com/file2.tar.gz")
            finally:
                Path(f.name).unlink()

    def test_version_interpolation(self):
        """Test that version interpolation is resolved."""
        sha = "a" * 64
        content = f'''
        version "2024.12"
        url "https://example.com/file-#{{version}}.tar.gz"
        sha256 "{sha}"
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(content)
            f.flush()
            try:
                pairs = extract_pairs(Path(f.name))
                self.assertEqual(pairs[0][0], "https://example.com/file-2024.12.tar.gz")
            finally:
                Path(f.name).unlink()

    def test_unresolved_interpolation_raises_error(self):
        """Test that unresolved interpolation raises ValueError."""
        content = '''
        version "1.0.0"
        url "https://example.com/file-#{unknown}.tar.gz"
        sha256 "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(content)
            f.flush()
            try:
                with self.assertRaises(ValueError) as ctx:
                    extract_pairs(Path(f.name))
                self.assertIn("Unresolved interpolation", str(ctx.exception))
            finally:
                Path(f.name).unlink()

    def test_missing_version_raises_error(self):
        """Test that missing version raises ValueError."""
        content = '''
        url "https://example.com/file.tar.gz"
        sha256 "a" * 64
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(content)
            f.flush()
            try:
                with self.assertRaises(ValueError) as ctx:
                    extract_pairs(Path(f.name))
                self.assertIn("No version found", str(ctx.exception))
            finally:
                Path(f.name).unlink()

    def test_url_sha_in_reverse_order(self):
        """Test SHA256 before URL in source (should be paired correctly)."""
        sha = "a" * 64
        content = f'''
        version "1.0.0"
        sha256 "{sha}"
        url "https://example.com/file.tar.gz"
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(content)
            f.flush()
            try:
                pairs = extract_pairs(Path(f.name))
                self.assertEqual(len(pairs), 1)
                self.assertEqual(pairs[0], ("https://example.com/file.tar.gz", sha))
            finally:
                Path(f.name).unlink()

    def test_malformed_sha256_ignored(self):
        """Test that invalid SHA256 values are ignored in pairing."""
        sha_valid = "a" * 64
        content = f'''
        version "1.0.0"
        sha256 "not_valid_sha"
        url "https://example.com/file.tar.gz"
        sha256 "{sha_valid}"
        '''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write(content)
            f.flush()
            try:
                pairs = extract_pairs(Path(f.name))
                # Invalid SHA should be skipped, only valid pairing should exist
                self.assertEqual(len(pairs), 1)
                self.assertEqual(pairs[0], ("https://example.com/file.tar.gz", sha_valid))
            finally:
                Path(f.name).unlink()


if __name__ == "__main__":
    unittest.main()
