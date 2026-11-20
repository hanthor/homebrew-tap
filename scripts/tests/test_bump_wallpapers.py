import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _loader import load_script  # noqa: E402

bump = load_script("bump-wallpapers.py")

SHA_A = "a" * 64
SHA_B = "b" * 64


def release(tag, assets=()):
    return {"tag_name": tag, "assets": [dict(a) for a in assets]}


class CaskConfigTest(unittest.TestCase):
    def setUp(self):
        self.config = bump.CASK_BY_NAME["bluefin-wallpapers-extra"]

    def test_get_tag(self):
        self.assertEqual(self.config.get_tag("2025-12-10"), "bluefin-extra-v2025-12-10")

    def test_get_asset_name(self):
        self.assertEqual(
            self.config.get_asset_name(bump.Variant.KDE),
            "bluefin-wallpapers-extra-kde.tar.zstd",
        )

    def test_cask_file_lives_in_casks_dir(self):
        self.assertEqual(self.config.cask_file.name, "bluefin-wallpapers-extra.rb")
        self.assertEqual(self.config.cask_file.parent, bump.CASKS_DIR)

    def test_every_configured_cask_exists_in_repo(self):
        for config in bump.CASKS:
            with self.subTest(cask=config.name):
                self.assertTrue(config.cask_file.exists())

    def test_aurora_is_single_variant(self):
        self.assertEqual(bump.CASK_BY_NAME["aurora-wallpapers"].variants, [])

    def test_default_variants_cover_all_enum_members(self):
        self.assertEqual(set(self.config.variants), set(bump.Variant))


class FindReleaseTest(unittest.TestCase):
    def setUp(self):
        self.releases = [
            release("bluefin-extra-v2025-12-10"),
            release("bluefin-v2025-12-01"),
            release("bluefin-v2025-11-01"),
        ]

    def test_latest_returns_first_matching_prefix(self):
        found = bump.find_release(self.releases, "bluefin")
        self.assertEqual(found["tag_name"], "bluefin-v2025-12-01")

    def test_prefix_does_not_match_longer_prefix(self):
        # "bluefin-v" must not match "bluefin-extra-v..."
        found = bump.find_release(self.releases, "bluefin-extra")
        self.assertEqual(found["tag_name"], "bluefin-extra-v2025-12-10")

    def test_specific_version(self):
        found = bump.find_release(self.releases, "bluefin", "2025-11-01")
        self.assertEqual(found["tag_name"], "bluefin-v2025-11-01")

    def test_missing_version_raises(self):
        with self.assertRaisesRegex(bump.ReleaseNotFoundError, r"bluefin \(2020-01-01\)"):
            bump.find_release(self.releases, "bluefin", "2020-01-01")

    def test_missing_prefix_raises_with_latest_label(self):
        with self.assertRaisesRegex(bump.ReleaseNotFoundError, r"framework \(latest\)"):
            bump.find_release(self.releases, "framework")


class GetAssetSha256Test(unittest.TestCase):
    def test_returns_digest_without_prefix(self):
        rel = release("t", [{"name": "x.tar.zstd", "digest": f"sha256:{SHA_A}"}])
        self.assertEqual(bump.get_asset_sha256(rel, "x.tar.zstd"), SHA_A)

    def test_missing_asset_raises(self):
        rel = release("t", [{"name": "other", "digest": f"sha256:{SHA_A}"}])
        with self.assertRaisesRegex(bump.AssetNotFoundError, "Asset not found"):
            bump.get_asset_sha256(rel, "x.tar.zstd")

    def test_release_without_assets_key_raises(self):
        with self.assertRaises(bump.AssetNotFoundError):
            bump.get_asset_sha256({"tag_name": "t"}, "x.tar.zstd")

    def test_empty_digest_raises(self):
        rel = release("t", [{"name": "x", "digest": ""}])
        with self.assertRaisesRegex(bump.AssetNotFoundError, "No digest"):
            bump.get_asset_sha256(rel, "x")

    def test_missing_digest_key_raises(self):
        rel = release("t", [{"name": "x"}])
        with self.assertRaisesRegex(bump.AssetNotFoundError, "No digest"):
            bump.get_asset_sha256(rel, "x")

    def test_non_sha256_digest_raises(self):
        rel = release("t", [{"name": "x", "digest": f"md5:{SHA_A}"}])
        with self.assertRaisesRegex(bump.AssetNotFoundError, "No digest"):
            bump.get_asset_sha256(rel, "x")

    def test_asset_errors_are_bump_errors(self):
        self.assertTrue(issubclass(bump.AssetNotFoundError, bump.BumpError))
        self.assertTrue(issubclass(bump.ReleaseNotFoundError, bump.BumpError))
        self.assertTrue(issubclass(bump.CaskFileNotFoundError, bump.BumpError))


CASK = '''cask "demo" do
  version "2025-01-01"

  on_macos do
    sha256 "OLDMAC"
    url "https://example.com/demo-macos.tar.zstd"
  end
  on_linux do
    url "https://example.com/demo-kde.tar.zstd"
    sha256 "OLDKDE"
    url "https://example.com/demo-gnome.tar.zstd"
    sha256 "OLDGNOME"
  end
end
'''


class UpdateSha256AfterUrlTest(unittest.TestCase):
    def test_updates_sha_following_url(self):
        out = bump.update_sha256_after_url(CASK, "demo-kde.tar.zstd", SHA_A)
        self.assertIn(f'sha256 "{SHA_A}"', out)
        self.assertIn('sha256 "OLDGNOME"', out)
        self.assertIn('sha256 "OLDMAC"', out)

    def test_updates_only_matching_variant(self):
        out = bump.update_sha256_after_url(CASK, "demo-gnome.tar.zstd", SHA_B)
        self.assertIn('sha256 "OLDKDE"', out)
        self.assertEqual(out.count(SHA_B), 1)

    def test_sha_preceding_url_is_overwritten_into_next_variant(self):
        # Characterises current behaviour: the function only looks *after* the
        # URL, so a sha256 that precedes its url (the macOS layout in
        # Casks/bluefin-wallpapers.rb) is left stale and the next variant's
        # sha256 is rewritten instead. bump_cask later fixes the next variant
        # when it processes it, but the macOS sha256 is never updated.
        out = bump.update_sha256_after_url(CASK, "demo-macos.tar.zstd", SHA_A)
        self.assertIn('sha256 "OLDMAC"', out)
        self.assertNotIn("OLDKDE", out)

    @unittest.expectedFailure
    def test_sha_preceding_url_is_updated(self):
        # Desired behaviour; remove expectedFailure once the script handles it.
        out = bump.update_sha256_after_url(CASK, "demo-macos.tar.zstd", SHA_A)
        self.assertNotIn('sha256 "OLDMAC"', out)

    def test_unknown_url_leaves_content_unchanged(self):
        self.assertEqual(bump.update_sha256_after_url(CASK, "nope", SHA_A), CASK)

    def test_preserves_indentation(self):
        out = bump.update_sha256_after_url(CASK, "demo-kde.tar.zstd", SHA_A)
        self.assertIn(f'\n    sha256 "{SHA_A}"\n', out)


class VersionHelpersTest(unittest.TestCase):
    def test_update_version(self):
        out = bump.update_version(CASK, "2026-02-02")
        self.assertIn('version "2026-02-02"', out)
        self.assertNotIn("2025-01-01", out)

    def test_update_version_without_version_line_is_noop(self):
        self.assertEqual(bump.update_version("cask x do\nend\n", "1"), "cask x do\nend\n")

    def test_get_current_version(self):
        self.assertEqual(bump.get_current_version(CASK), "2025-01-01")

    def test_get_current_version_unknown(self):
        self.assertEqual(bump.get_current_version("no version here"), "unknown")

    def test_update_single_sha256(self):
        content = 'cask "a" do\n  version "1"\n  sha256 "OLD"\nend\n'
        out = bump.update_single_sha256(content, SHA_A)
        self.assertIn(f'sha256 "{SHA_A}"', out)
        self.assertNotIn("OLD", out)


class BumpCaskTest(unittest.TestCase):
    """Bump a temp cask file with the release lookup stubbed (no network)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name) / "demo.rb"

    def _bump(self, config, releases, version=None):
        with mock.patch.object(
            bump.CaskConfig, "cask_file", new_callable=mock.PropertyMock
        ) as cask_file, mock.patch.object(bump, "get_releases", return_value=releases):
            cask_file.return_value = self.path
            bump.bump_cask(config, version)

    def test_missing_cask_file_raises(self):
        config = bump.CaskConfig("demo", "demo", "demo-art", variants=[])
        with self.assertRaises(bump.CaskFileNotFoundError):
            self._bump(config, [])

    def test_single_variant_bump(self):
        self.path.write_text('cask "demo" do\n  version "1"\n  sha256 "OLD"\nend\n')
        config = bump.CaskConfig("demo", "demo", "demo-art", variants=[])
        rel = release("demo-v2", [{"name": "demo-art.tar.zstd", "digest": f"sha256:{SHA_A}"}])
        self._bump(config, [rel])
        text = self.path.read_text()
        self.assertIn('version "2"', text)
        self.assertIn(f'sha256 "{SHA_A}"', text)

    def test_multi_variant_bump_skips_missing_asset(self):
        self.path.write_text(CASK)
        config = bump.CaskConfig(
            "demo", "demo", "demo", variants=[bump.Variant.KDE, bump.Variant.GNOME]
        )
        rel = release(
            "demo-v2025-02-02",
            [{"name": "demo-kde.tar.zstd", "digest": f"sha256:{SHA_A}"}],
        )
        self._bump(config, [rel])
        text = self.path.read_text()
        self.assertIn('version "2025-02-02"', text)
        self.assertIn(f'sha256 "{SHA_A}"', text)
        self.assertIn('sha256 "OLDGNOME"', text)  # missing asset left untouched

    def test_specific_version_selects_that_release(self):
        self.path.write_text('cask "demo" do\n  version "1"\n  sha256 "OLD"\nend\n')
        config = bump.CaskConfig("demo", "demo", "demo-art", variants=[])
        releases = [
            release("demo-v3", [{"name": "demo-art.tar.zstd", "digest": f"sha256:{SHA_B}"}]),
            release("demo-v2", [{"name": "demo-art.tar.zstd", "digest": f"sha256:{SHA_A}"}]),
        ]
        self._bump(config, releases, "2")
        self.assertIn(f'sha256 "{SHA_A}"', self.path.read_text())

    def test_single_variant_missing_asset_raises_and_leaves_file(self):
        original = 'cask "demo" do\n  version "1"\n  sha256 "OLD"\nend\n'
        self.path.write_text(original)
        config = bump.CaskConfig("demo", "demo", "demo-art", variants=[])
        with self.assertRaises(bump.AssetNotFoundError):
            self._bump(config, [release("demo-v2")])
        self.assertEqual(self.path.read_text(), original)


class BumpAllTest(unittest.TestCase):
    def test_returns_false_when_any_cask_fails(self):
        calls = []

        def fake(config, version=None):
            calls.append(config.name)
            if config.name == "framework-wallpapers":
                raise bump.ReleaseNotFoundError("boom")

        with mock.patch.object(bump, "bump_cask", side_effect=fake):
            self.assertFalse(bump.bump_all())
        self.assertEqual(calls, [c.name for c in bump.CASKS])  # keeps going after failure

    def test_returns_true_when_all_succeed(self):
        with mock.patch.object(bump, "bump_cask"):
            self.assertTrue(bump.bump_all("2025-01-01"))


if __name__ == "__main__":
    unittest.main()
