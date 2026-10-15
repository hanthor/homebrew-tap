#!/usr/bin/env python3
"""
Unit tests for scripts/verify-wallpapers.py

Tests cover pure functions:
- extract_pairs(): URL/SHA256 pair extraction with version interpolation
- fetch_sha256(): SHA256 computation (mocked HTTP)
- Version interpolation and livecheck block handling
"""

import hashlib
import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

# Add parent directory to path so we can import verify-wallpapers as a module
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import functions from verify-wallpapers.py
import importlib.util
spec = importlib.util.spec_from_file_location("verify_wallpapers", 
    Path(__file__).parent.parent / "verify-wallpapers.py")
verify_wallpapers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_wallpapers)


class TestExtractPairs(unittest.TestCase):
    """Test URL/SHA256 pair extraction with version interpolation."""

    def test_extract_simple_pairs(self):
        """Extract single URL/SHA256 pair without interpolation."""
        cask_content = '''
version "1.0"
url "https://example.com/image.jpg"
sha256 "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
'''
        with patch.object(Path, 'read_text', return_value=cask_content):
            pairs = verify_wallpapers.extract_pairs(Path("test.rb"))
        
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0][0], "https://example.com/image.jpg")
        self.assertEqual(len(pairs[0][1]), 64)  # SHA256 is 64 chars

    def test_extract_with_version_interpolation(self):
        """Version interpolation should replace #{version} tokens."""
        cask_content = '''
version "2.5"
url "https://example.com/wallpaper-#{version}.jpg"
sha256 "1111111111111111111111111111111111111111111111111111111111111111"
'''
        with patch.object(Path, 'read_text', return_value=cask_content):
            pairs = verify_wallpapers.extract_pairs(Path("test.rb"))
        
        self.assertEqual(pairs[0][0], "https://example.com/wallpaper-2.5.jpg")

    def test_extract_multiple_pairs(self):
        """Extract multiple URL/SHA256 pairs."""
        cask_content = '''
version "1.0"
url "https://example.com/image1.jpg"
sha256 "0000000000000000000000000000000000000000000000000000000000000000"
url "https://example.com/image2.jpg"
sha256 "1111111111111111111111111111111111111111111111111111111111111111"
'''
        with patch.object(Path, 'read_text', return_value=cask_content):
            pairs = verify_wallpapers.extract_pairs(Path("test.rb"))
        
        self.assertEqual(len(pairs), 2)
        self.assertEqual(pairs[0][0], "https://example.com/image1.jpg")
        self.assertEqual(pairs[1][0], "https://example.com/image2.jpg")

    def test_strip_livecheck_block(self):
        """Livecheck blocks should be removed before extraction."""
        cask_content = '''
version "1.0"
livecheck do
  url "https://livecheck.example.com"
  strategy :page_match
end
url "https://example.com/image.jpg"
sha256 "2222222222222222222222222222222222222222222222222222222222222222"
'''
        with patch.object(Path, 'read_text', return_value=cask_content):
            pairs = verify_wallpapers.extract_pairs(Path("test.rb"))
        
        # Should extract the real URL, not the livecheck URL
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0][0], "https://example.com/image.jpg")

    def test_unresolved_interpolation_error(self):
        """Unresolved interpolation should raise ValueError."""
        cask_content = '''
version "1.0"
url "https://example.com/image-#{unknown}.jpg"
sha256 "3333333333333333333333333333333333333333333333333333333333333333"
'''
        with patch.object(Path, 'read_text', return_value=cask_content):
            with self.assertRaises(ValueError) as ctx:
                verify_wallpapers.extract_pairs(Path("test.rb"))
            self.assertIn("Unresolved interpolation", str(ctx.exception))

    def test_no_version_error(self):
        """Missing version should raise ValueError."""
        cask_content = '''
url "https://example.com/image.jpg"
sha256 "4444444444444444444444444444444444444444444444444444444444444444"
'''
        with patch.object(Path, 'read_text', return_value=cask_content):
            with self.assertRaises(ValueError) as ctx:
                verify_wallpapers.extract_pairs(Path("test.rb"))
            self.assertIn("No version found", str(ctx.exception))


class TestFetchSha256(unittest.TestCase):
    """Test SHA256 computation from URL content."""

    def test_fetch_sha256_single_chunk(self):
        """Compute SHA256 for small file (single read)."""
        content = b"test content"
        expected_sha = hashlib.sha256(content).hexdigest()
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.__enter__.return_value = mock_response
            mock_response.read.side_effect = [content, b'']  # Return content then EOF
            mock_urlopen.return_value = mock_response
            
            result = verify_wallpapers.fetch_sha256("https://example.com/test.jpg")
        
        self.assertEqual(result, expected_sha)

    def test_fetch_sha256_multiple_chunks(self):
        """Compute SHA256 for large file (multiple chunks)."""
        chunk1 = b"x" * (1 << 20)  # 1 MB chunk
        chunk2 = b"y" * (1 << 20)
        expected_sha = hashlib.sha256(chunk1 + chunk2).hexdigest()
        
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_response = MagicMock()
            mock_response.__enter__.return_value = mock_response
            mock_response.read.side_effect = [chunk1, chunk2, b'']
            mock_urlopen.return_value = mock_response
            
            result = verify_wallpapers.fetch_sha256("https://example.com/large.jpg")
        
        self.assertEqual(result, expected_sha)


if __name__ == '__main__':
    unittest.main()
