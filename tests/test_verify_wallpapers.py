#!/usr/bin/env python3
"""Unit tests for verify-wallpapers.py script."""

import hashlib
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch
from io import BytesIO

# Add scripts dir to path so we can import the module
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

# We need to import after adding to path
import importlib.util
spec = importlib.util.spec_from_file_location(
    "verify_wallpapers",
    Path(__file__).parent.parent / "scripts" / "verify-wallpapers.py"
)
verify_wallpapers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_wallpapers)


class TestExtractPairs(unittest.TestCase):
    """Test extract_pairs function."""

    def setUp(self):
        """Create temporary test cask files."""
        self.temp_dir = Path("/tmp/test_casks_verify")
        self.temp_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up temp files."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _create_cask(self, content):
        """Helper to create a test cask file."""
        cask_path = self.temp_dir / "test.rb"
        cask_path.write_text(content)
        return cask_path

    def test_extract_pairs_single_variant(self):
        """Test extraction of single url/sha256 pair."""
        content = '''
cask "test" do
  version "1.0"
  url "https://example.com/test-1.0.tar.gz"
  sha256 "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
end
'''
        cask_path = self._create_cask(content)
        pairs = verify_wallpapers.extract_pairs(cask_path)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0][0], "https://example.com/test-1.0.tar.gz")

    def test_extract_pairs_version_interpolation(self):
        """Test that #{version} is interpolated correctly."""
        content = '''
cask "test" do
  version "2.5"
  url "https://example.com/pkg-#{version}.tar.gz"
  sha256 "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
end
'''
        cask_path = self._create_cask(content)
        pairs = verify_wallpapers.extract_pairs(cask_path)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0][0], "https://example.com/pkg-2.5.tar.gz")

    def test_extract_pairs_multiple_variants(self):
        """Test extraction of multiple url/sha256 pairs."""
        content = '''
cask "test" do
  version "1.0"
  url "https://example.com/a-1.0.tar.gz"
  sha256 "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  url "https://example.com/b-1.0.tar.gz"
  sha256 "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
end
'''
        cask_path = self._create_cask(content)
        pairs = verify_wallpapers.extract_pairs(cask_path)
        self.assertEqual(len(pairs), 2)

    def test_extract_pairs_removes_livecheck_block(self):
        """Test that livecheck blocks are stripped before parsing."""
        content = '''
cask "test" do
  version "1.0"
  url "https://example.com/test-1.0.tar.gz"
  sha256 "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
  
  livecheck do
    url "https://github.com/example"
    strategy :github_latest
  end
end
'''
        cask_path = self._create_cask(content)
        pairs = verify_wallpapers.extract_pairs(cask_path)
        self.assertEqual(len(pairs), 1)

    def test_extract_pairs_unresolved_interpolation_raises(self):
        """Test that unresolved interpolation raises ValueError."""
        content = '''
cask "test" do
  version "1.0"
  url "https://example.com/pkg-#{unknown}.tar.gz"
  sha256 "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
end
'''
        cask_path = self._create_cask(content)
        with self.assertRaises(ValueError) as ctx:
            verify_wallpapers.extract_pairs(cask_path)
        self.assertIn("Unresolved interpolation", str(ctx.exception))

    def test_extract_pairs_no_version_raises(self):
        """Test that missing version raises ValueError."""
        content = '''
cask "test" do
  url "https://example.com/test.tar.gz"
  sha256 "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
end
'''
        cask_path = self._create_cask(content)
        with self.assertRaises(ValueError) as ctx:
            verify_wallpapers.extract_pairs(cask_path)
        self.assertIn("No version found", str(ctx.exception))


class TestFetchSha256(unittest.TestCase):
    """Test fetch_sha256 function."""

    @patch("verify_wallpapers.urlopen")
    def test_fetch_sha256_computes_correct_hash(self, mock_urlopen):
        """Test that SHA256 is computed correctly."""
        test_data = b"test content"
        expected_hash = hashlib.sha256(test_data).hexdigest()
        
        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.return_value = test_data
        mock_urlopen.return_value = mock_response
        
        result = verify_wallpapers.fetch_sha256("https://example.com/test.tar.gz")
        self.assertEqual(result, expected_hash)

    @patch("verify_wallpapers.urlopen")
    def test_fetch_sha256_handles_large_files(self, mock_urlopen):
        """Test that SHA256 handles files in chunks."""
        chunk1 = b"a" * 1000
        chunk2 = b"b" * 1000
        
        expected_hash = hashlib.sha256(chunk1 + chunk2).hexdigest()
        
        mock_response = MagicMock()
        mock_response.__enter__.return_value.read.side_effect = [chunk1, chunk2, b""]
        mock_urlopen.return_value = mock_response
        
        result = verify_wallpapers.fetch_sha256("https://example.com/large.tar.gz")
        self.assertEqual(result, expected_hash)


class TestTokenRegex(unittest.TestCase):
    """Test TOKEN_RE regex pattern."""

    def test_token_regex_matches_url(self):
        """Test that TOKEN_RE matches url lines."""
        line = 'url "https://example.com/file.tar.gz"'
        match = verify_wallpapers.TOKEN_RE.search(line)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "url")

    def test_token_regex_matches_sha256(self):
        """Test that TOKEN_RE matches sha256 lines."""
        line = 'sha256 "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"'
        match = verify_wallpapers.TOKEN_RE.search(line)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "sha256")


class TestVersionRegex(unittest.TestCase):
    """Test VERSION_RE regex pattern."""

    def test_version_regex_extracts_version(self):
        """Test that VERSION_RE extracts version correctly."""
        content = 'version "1.2.3"'
        match = verify_wallpapers.VERSION_RE.search(content)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "1.2.3")


if __name__ == "__main__":
    unittest.main()
