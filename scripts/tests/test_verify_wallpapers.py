import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _loader import load_script  # noqa: E402

verify = load_script("verify-wallpapers.py")

SHA_A = "a" * 64
SHA_B = "b" * 64
BASE = "https://example.com/releases/download/v#{version}"


class ExtractPairsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def _extract(self, content):
        path = self.dir / "demo.rb"
        path.write_text(content)
        return verify.extract_pairs(path)

    def test_url_then_sha(self):
        pairs = self._extract(
            f'version "1.0"\nurl "{BASE}/a.tar.zstd"\nsha256 "{SHA_A}"\n'
        )
        self.assertEqual(pairs, [("https://example.com/releases/download/v1.0/a.tar.zstd", SHA_A)])

    def test_sha_then_url(self):
        pairs = self._extract(
            f'version "1.0"\nsha256 "{SHA_A}"\nurl "{BASE}/a.tar.zstd"\n'
        )
        self.assertEqual(pairs, [("https://example.com/releases/download/v1.0/a.tar.zstd", SHA_A)])

    def test_multiple_variants_in_order(self):
        pairs = self._extract(
            f'version "2"\n'
            f'sha256 "{SHA_A}"\nurl "{BASE}/mac.tar.zstd"\n'
            f'url "{BASE}/kde.tar.zstd"\nsha256 "{SHA_B}"\n'
        )
        self.assertEqual(
            pairs,
            [
                ("https://example.com/releases/download/v2/mac.tar.zstd", SHA_A),
                ("https://example.com/releases/download/v2/kde.tar.zstd", SHA_B),
            ],
        )

    def test_livecheck_block_is_ignored(self):
        content = (
            'version "1"\n'
            f'url "{BASE}/a.tar.zstd"\nsha256 "{SHA_A}"\n'
            'livecheck do\n  url "https://github.com/x/y.git"\n  strategy :github_releases\nend\n'
        )
        self.assertEqual(len(self._extract(content)), 1)

    def test_non_hex_sha256_token_is_ignored(self):
        pairs = self._extract(
            f'version "1"\nsha256 "not-a-real-hash"\nurl "{BASE}/a.tar.zstd"\nsha256 "{SHA_A}"\n'
        )
        self.assertEqual([sha for _, sha in pairs], [SHA_A])

    def test_missing_version_raises(self):
        with self.assertRaisesRegex(ValueError, "No version found"):
            self._extract(f'url "{BASE}/a.tar.zstd"\nsha256 "{SHA_A}"\n')

    def test_unresolved_interpolation_raises(self):
        with self.assertRaisesRegex(ValueError, "Unresolved interpolation"):
            self._extract(
                f'version "1"\nurl "https://x/#{{other}}/a"\nsha256 "{SHA_A}"\n'
            )

    def test_no_pairs_returns_empty(self):
        self.assertEqual(self._extract('version "1"\n'), [])

    def test_lone_url_is_not_paired(self):
        self.assertEqual(self._extract(f'version "1"\nurl "{BASE}/a"\n'), [])

    def test_real_wallpaper_casks_parse(self):
        casks = sorted(verify.CASKS_DIR.glob(verify.DEFAULT_GLOB))
        self.assertTrue(casks)
        for cask in casks:
            with self.subTest(cask=cask.name):
                pairs = verify.extract_pairs(cask)
                self.assertTrue(pairs)
                for url, sha in pairs:
                    self.assertTrue(url.startswith("https://"))
                    self.assertNotIn("#{", url)
                    self.assertRegex(sha, r"^[0-9a-f]{64}$")


class FetchAndVerifyTest(unittest.TestCase):
    def _fake_response(self, data):
        resp = mock.MagicMock()
        chunks = [data, b""]
        resp.read.side_effect = lambda n=-1: chunks.pop(0) if chunks else b""
        resp.__enter__.return_value = resp
        return resp

    def test_fetch_sha256_hashes_body(self):
        with mock.patch.object(verify, "urlopen", return_value=self._fake_response(b"hello")):
            self.assertEqual(verify.fetch_sha256("https://x"), hashlib.sha256(b"hello").hexdigest())

    def test_verify_cask_reports_mismatch(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "demo.rb"
            path.write_text(f'version "1"\nurl "{BASE}/a.tar.zstd"\nsha256 "{SHA_A}"\n')
            with mock.patch.object(verify, "fetch_sha256", return_value=SHA_B), mock.patch(
                "builtins.print"
            ):
                failures = verify.verify_cask(path)
        self.assertEqual(len(failures), 1)
        self.assertIn(f"expected {SHA_A}", failures[0])
        self.assertIn(f"actual   {SHA_B}", failures[0])

    def test_verify_cask_ok(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "demo.rb"
            path.write_text(f'version "1"\nurl "{BASE}/a.tar.zstd"\nsha256 "{SHA_A}"\n')
            with mock.patch.object(verify, "fetch_sha256", return_value=SHA_A), mock.patch(
                "builtins.print"
            ):
                self.assertEqual(verify.verify_cask(path), [])


if __name__ == "__main__":
    unittest.main()
