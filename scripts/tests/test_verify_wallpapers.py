"""Unit tests for verify-wallpapers.py"""

import unittest
import tempfile
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import using exec to handle hyphenated filename
verify_module = {"__name__": "verify_wallpapers", "__file__": str(Path(__file__).parent.parent / "verify-wallpapers.py")}
with open(Path(__file__).parent.parent / "verify-wallpapers.py") as f:
    code = f.read()
    code = code.split("if __name__")[0]
    exec(code, verify_module)

extract_pairs = verify_module["extract_pairs"]


class TestExtractPairs(unittest.TestCase):
    """Test extract_pairs function from verify-wallpapers"""

    def test_extract_pairs_basic(self):
        """Test extracting url/sha256 pairs from cask content"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write('''cask "test-wallpapers" do
  version "1.0.0"
  
  url "https://example.com/file1.tar.zstd"
  sha256 "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
  
  url "https://example.com/file2.tar.zstd"
  sha256 "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210"
end''')
            f.flush()
            
            pairs = extract_pairs(Path(f.name))
            self.assertEqual(len(pairs), 2)
            self.assertEqual(pairs[0][0], "https://example.com/file1.tar.zstd")
            self.assertEqual(pairs[0][1], "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef")
            self.assertEqual(pairs[1][0], "https://example.com/file2.tar.zstd")
            self.assertEqual(pairs[1][1], "fedcba9876543210fedcba9876543210fedcba9876543210fedcba9876543210")

    def test_extract_pairs_with_version_substitution(self):
        """Test that #{version} is substituted correctly"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write('''cask "test-wallpapers" do
  version "2025-01-15"
  
  url "https://example.com/wallpapers-#{version}.tar.zstd"
  sha256 "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
end''')
            f.flush()
            
            pairs = extract_pairs(Path(f.name))
            self.assertEqual(len(pairs), 1)
            self.assertEqual(pairs[0][0], "https://example.com/wallpapers-2025-01-15.tar.zstd")

    def test_extract_pairs_no_version(self):
        """Test error when version is missing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write('''cask "test" do
  url "https://example.com/file.tar.zstd"
  sha256 "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
end''')
            f.flush()
            
            with self.assertRaises(ValueError) as cm:
                extract_pairs(Path(f.name))
            self.assertIn("No version", str(cm.exception))

    def test_extract_pairs_unresolved_interpolation(self):
        """Test error on unresolved interpolation"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write('''cask "test" do
  version "1.0.0"
  url "https://example.com/#{undefined}.tar.zstd"
  sha256 "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
end''')
            f.flush()
            
            with self.assertRaises(ValueError) as cm:
                extract_pairs(Path(f.name))
            self.assertIn("Unresolved interpolation", str(cm.exception))

    def test_extract_pairs_ignores_livecheck(self):
        """Test that livecheck blocks are ignored"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write('''cask "test" do
  version "1.0.0"
  
  livecheck do
    url "https://should-be-ignored.com"
    sha256 "abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789"
  end
  
  url "https://example.com/file.tar.zstd"
  sha256 "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
end''')
            f.flush()
            
            pairs = extract_pairs(Path(f.name))
            self.assertEqual(len(pairs), 1)
            self.assertEqual(pairs[0][0], "https://example.com/file.tar.zstd")

    def test_extract_pairs_multiple_variants(self):
        """Test extracting multiple variants with different suffixes"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.rb', delete=False) as f:
            f.write('''cask "bluefin-wallpapers" do
  version "2025-01"
  
  url "https://cdn.example.com/bluefin-wallpapers-macos.tar.zstd"
  sha256 "1111111111111111111111111111111111111111111111111111111111111111"
  
  url "https://cdn.example.com/bluefin-wallpapers-kde.tar.zstd"
  sha256 "2222222222222222222222222222222222222222222222222222222222222222"
  
  url "https://cdn.example.com/bluefin-wallpapers-gnome.tar.zstd"
  sha256 "3333333333333333333333333333333333333333333333333333333333333333"
end''')
            f.flush()
            
            pairs = extract_pairs(Path(f.name))
            self.assertEqual(len(pairs), 3)


class TestTokenRegex(unittest.TestCase):
    """Test TOKEN_RE regex pattern"""

    def test_token_re_matches_url(self):
        """Test that TOKEN_RE matches url strings"""
        TOKEN_RE = verify_module["TOKEN_RE"]
        test_str = 'url "https://example.com/file.tar.zstd"'
        matches = TOKEN_RE.findall(test_str)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], "url")

    def test_token_re_matches_sha256(self):
        """Test that TOKEN_RE matches sha256 strings"""
        TOKEN_RE = verify_module["TOKEN_RE"]
        test_str = 'sha256 "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"'
        matches = TOKEN_RE.findall(test_str)
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0], "sha256")

    def test_token_re_matches_multiple(self):
        """Test TOKEN_RE with multiple tokens"""
        TOKEN_RE = verify_module["TOKEN_RE"]
        test_str = '''url "https://example.com/file.tar.zstd"
sha256 "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"'''
        matches = TOKEN_RE.findall(test_str)
        self.assertEqual(len(matches), 2)


class TestShaRegex(unittest.TestCase):
    """Test SHA_RE regex pattern"""

    def test_sha_re_matches_valid(self):
        """Test that SHA_RE matches valid SHA256 hashes"""
        SHA_RE = verify_module["SHA_RE"]
        valid_hash = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
        self.assertIsNotNone(SHA_RE.fullmatch(valid_hash))

    def test_sha_re_rejects_invalid(self):
        """Test that SHA_RE rejects invalid hashes"""
        SHA_RE = verify_module["SHA_RE"]
        # Too short
        self.assertIsNone(SHA_RE.fullmatch("0123456789abcdef"))
        # Invalid characters at end
        self.assertIsNone(SHA_RE.fullmatch("0123456789abcdef" * 3 + "12345678g"))
        # Correct length but not all hex
        self.assertIsNone(SHA_RE.fullmatch("zzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzzz"))


class TestVersionRegex(unittest.TestCase):
    """Test VERSION_RE regex pattern"""

    def test_version_re_matches(self):
        """Test that VERSION_RE matches version strings"""
        VERSION_RE = verify_module["VERSION_RE"]
        test_str = 'version "2025-01-15"'
        match = VERSION_RE.search(test_str)
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "2025-01-15")

    def test_version_re_no_match(self):
        """Test that VERSION_RE doesn't match invalid format"""
        VERSION_RE = verify_module["VERSION_RE"]
        test_str = 'version_info "2025-01-15"'
        match = VERSION_RE.search(test_str)
        self.assertIsNone(match)


if __name__ == "__main__":
    unittest.main()
