"""Unit tests for wallpaper cask parsing and configuration utilities."""

import pytest
from pathlib import Path
from unittest.mock import patch

# Import functions from bump-wallpapers.py
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from bump_wallpapers import (
    Variant,
    CaskConfig,
    find_release,
    get_asset_sha256,
    update_sha256_after_url,
    update_version,
    update_single_sha256,
    get_current_version,
    ReleaseNotFoundError,
    AssetNotFoundError,
    CASK_BY_NAME,
)

# Import functions from verify-wallpapers.py
from verify_wallpapers import extract_pairs


class TestVariant:
    """Test Variant enum."""
    
    def test_variant_values(self):
        assert Variant.MACOS.value == "macos"
        assert Variant.KDE.value == "kde"
        assert Variant.GNOME.value == "gnome"
        assert Variant.PNG.value == "png"


class TestCaskConfig:
    """Test CaskConfig dataclass."""
    
    def test_cask_config_get_tag(self):
        config = CaskConfig(
            name="bluefin-wallpapers",
            release_prefix="bluefin",
            artifact_name="bluefin-wallpapers",
        )
        assert config.get_tag("2025-01-15") == "bluefin-v2025-01-15"
    
    def test_cask_config_get_asset_name_multi_variant(self):
        config = CaskConfig(
            name="bluefin-wallpapers",
            release_prefix="bluefin",
            artifact_name="bluefin-wallpapers",
            variants=[Variant.MACOS, Variant.KDE],
        )
        assert config.get_asset_name(Variant.MACOS) == "bluefin-wallpapers-macos.tar.zstd"
        assert config.get_asset_name(Variant.KDE) == "bluefin-wallpapers-kde.tar.zstd"
    
    def test_cask_config_cask_file_property(self):
        config = CaskConfig(
            name="test-cask",
            release_prefix="test",
            artifact_name="test",
        )
        assert config.cask_file.name == "test-cask.rb"


class TestFindRelease:
    """Test find_release function."""
    
    def test_find_release_exact_version(self):
        releases = [
            {"tag_name": "bluefin-v2025-01-01"},
            {"tag_name": "bluefin-v2025-01-15"},
            {"tag_name": "bluefin-v2025-02-01"},
        ]
        result = find_release(releases, "bluefin", "2025-01-15")
        assert result["tag_name"] == "bluefin-v2025-01-15"
    
    def test_find_release_latest(self):
        releases = [
            {"tag_name": "bluefin-v2025-01-01"},
            {"tag_name": "bluefin-v2025-01-15"},
            {"tag_name": "other-v2025-01-20"},
        ]
        result = find_release(releases, "bluefin")
        assert result["tag_name"] == "bluefin-v2025-01-01"
    
    def test_find_release_not_found_specific_version(self):
        releases = [
            {"tag_name": "bluefin-v2025-01-01"},
        ]
        with pytest.raises(ReleaseNotFoundError, match="No release found for bluefin"):
            find_release(releases, "bluefin", "2025-02-01")
    
    def test_find_release_not_found_prefix(self):
        releases = [
            {"tag_name": "aurora-v2025-01-01"},
        ]
        with pytest.raises(ReleaseNotFoundError, match="No release found for bluefin"):
            find_release(releases, "bluefin")
    
    def test_find_release_empty_list(self):
        with pytest.raises(ReleaseNotFoundError):
            find_release([], "bluefin")


class TestGetAssetSha256:
    """Test get_asset_sha256 function."""
    
    def test_get_asset_sha256_valid(self):
        release = {
            "assets": [
                {
                    "name": "bluefin-wallpapers-macos.tar.zstd",
                    "digest": "sha256:abcd1234ef5678901234567890abcdef1234567890abcdef1234567890abcdef"
                }
            ]
        }
        sha = get_asset_sha256(release, "bluefin-wallpapers-macos.tar.zstd")
        assert sha == "abcd1234ef5678901234567890abcdef1234567890abcdef1234567890abcdef"
    
    def test_get_asset_sha256_multiple_assets(self):
        release = {
            "assets": [
                {
                    "name": "bluefin-wallpapers-macos.tar.zstd",
                    "digest": "sha256:aaaa000000000000000000000000000000000000000000000000000000000000"
                },
                {
                    "name": "bluefin-wallpapers-kde.tar.zstd",
                    "digest": "sha256:bbbb111111111111111111111111111111111111111111111111111111111111"
                }
            ]
        }
        sha = get_asset_sha256(release, "bluefin-wallpapers-kde.tar.zstd")
        assert sha == "bbbb111111111111111111111111111111111111111111111111111111111111"
    
    def test_get_asset_sha256_missing_asset(self):
        release = {"assets": []}
        with pytest.raises(AssetNotFoundError, match="Asset not found"):
            get_asset_sha256(release, "nonexistent.tar.zstd")
    
    def test_get_asset_sha256_no_digest(self):
        release = {
            "assets": [
                {
                    "name": "bluefin-wallpapers-macos.tar.zstd",
                    "digest": ""
                }
            ]
        }
        with pytest.raises(AssetNotFoundError, match="No digest found"):
            get_asset_sha256(release, "bluefin-wallpapers-macos.tar.zstd")
    
    def test_get_asset_sha256_wrong_digest_format(self):
        release = {
            "assets": [
                {
                    "name": "bluefin-wallpapers-macos.tar.zstd",
                    "digest": "md5:wrongformat"
                }
            ]
        }
        with pytest.raises(AssetNotFoundError, match="No digest found"):
            get_asset_sha256(release, "bluefin-wallpapers-macos.tar.zstd")


class TestUpdateSha256AfterUrl:
    """Test update_sha256_after_url function."""
    
    def test_update_sha256_after_url_basic(self):
        content = '''  url "https://github.com/ublue-os/artwork/releases/download/bluefin-v2025-01-15/bluefin-wallpapers-macos.tar.zstd"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000"
'''
        new_sha = "aaaa111111111111111111111111111111111111111111111111111111111111"
        result = update_sha256_after_url(content, "bluefin-wallpapers-macos.tar.zstd", new_sha)
        assert new_sha in result
        assert "0000000000000000000000000000000000000000000000000000000000000000" not in result
    
    def test_update_sha256_after_url_multiple_urls(self):
        content = '''  url "https://example.com/file1.tar.zstd"
  sha256 "1111111111111111111111111111111111111111111111111111111111111111"
  url "https://example.com/file2.tar.zstd"
  sha256 "2222222222222222222222222222222222222222222222222222222222222222"
'''
        new_sha = "aaaa000000000000000000000000000000000000000000000000000000000000"
        result = update_sha256_after_url(content, "file2.tar.zstd", new_sha)
        assert "1111111111111111111111111111111111111111111111111111111111111111" in result
        assert new_sha in result
        assert "2222222222222222222222222222222222222222222222222222222222222222" not in result
    
    def test_update_sha256_after_url_not_found(self):
        content = '''  url "https://example.com/file1.tar.zstd"
  sha256 "1111111111111111111111111111111111111111111111111111111111111111"
'''
        new_sha = "aaaa000000000000000000000000000000000000000000000000000000000000"
        result = update_sha256_after_url(content, "nonexistent.tar.zstd", new_sha)
        assert result == content


class TestUpdateVersion:
    """Test update_version function."""
    
    def test_update_version_basic(self):
        content = 'version "2025-01-15"'
        result = update_version(content, "2025-02-01")
        assert result == 'version "2025-02-01"'
    
    def test_update_version_in_context(self):
        content = '''class BruefinWallpapers < Formula
  version "2025-01-15"
  url "..."
end
'''
        result = update_version(content, "2025-02-01")
        assert 'version "2025-02-01"' in result
        assert 'version "2025-01-15"' not in result
    
    def test_update_version_no_match(self):
        content = "some content without version"
        result = update_version(content, "2025-02-01")
        assert result == content


class TestUpdateSingleSha256:
    """Test update_single_sha256 function."""
    
    def test_update_single_sha256_basic(self):
        content = 'sha256 "0000000000000000000000000000000000000000000000000000000000000000"'
        new_sha = "aaaa111111111111111111111111111111111111111111111111111111111111"
        result = update_single_sha256(content, new_sha)
        assert new_sha in result
        assert "0000000000000000000000000000000000000000000000000000000000000000" not in result
    
    def test_update_single_sha256_in_context(self):
        content = '''class AuroraWallpapers < Cask
  sha256 "1111111111111111111111111111111111111111111111111111111111111111"
  url "..."
end
'''
        new_sha = "aaaa000000000000000000000000000000000000000000000000000000000000"
        result = update_single_sha256(content, new_sha)
        assert new_sha in result
        assert "1111111111111111111111111111111111111111111111111111111111111111" not in result


class TestGetCurrentVersion:
    """Test get_current_version function."""
    
    def test_get_current_version_found(self):
        content = 'version "2025-01-15"'
        result = get_current_version(content)
        assert result == "2025-01-15"
    
    def test_get_current_version_in_context(self):
        content = '''class BruefinWallpapers < Formula
  desc "Bluefin wallpapers"
  version "2025-01-15"
  url "..."
end
'''
        result = get_current_version(content)
        assert result == "2025-01-15"
    
    def test_get_current_version_not_found(self):
        content = "some content without version"
        result = get_current_version(content)
        assert result == "unknown"


class TestExtractPairs:
    """Test extract_pairs function from verify-wallpapers.py."""
    
    def test_extract_pairs_basic(self):
        cask_content = '''cask "test-wallpapers" do
  version "2025-01-15"
  url "https://example.com/file1.tar.zstd"
  sha256 "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  url "https://example.com/file2.tar.zstd"
  sha256 "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
end
'''
        with patch('pathlib.Path.read_text', return_value=cask_content):
            pairs = extract_pairs(Path("dummy.rb"))
        
        assert len(pairs) == 2
        assert pairs[0] == ("https://example.com/file1.tar.zstd", "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
        assert pairs[1] == ("https://example.com/file2.tar.zstd", "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
    
    def test_extract_pairs_version_interpolation(self):
        cask_content = '''cask "test-wallpapers" do
  version "2025-01-15"
  url "https://example.com/releases/#{version}/file.tar.zstd"
  sha256 "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
end
'''
        with patch('pathlib.Path.read_text', return_value=cask_content):
            pairs = extract_pairs(Path("dummy.rb"))
        
        assert len(pairs) == 1
        assert pairs[0][0] == "https://example.com/releases/2025-01-15/file.tar.zstd"
    
    def test_extract_pairs_livecheck_stripped(self):
        cask_content = '''cask "test-wallpapers" do
  version "2025-01-15"
  url "https://example.com/file.tar.zstd"
  sha256 "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  
  livecheck do
    url "https://api.github.com/repos/example/repo/releases"
    strategy :json
    regex %r{releases/tag/v?(\d+\.\d+)}
  end
end
'''
        with patch('pathlib.Path.read_text', return_value=cask_content):
            pairs = extract_pairs(Path("dummy.rb"))
        
        assert len(pairs) == 1
    
    def test_extract_pairs_unresolved_interpolation_error(self):
        cask_content = '''cask "test-wallpapers" do
  version "2025-01-15"
  url "https://example.com/releases/#{version}/#{variant}/file.tar.zstd"
  sha256 "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
end
'''
        with patch('pathlib.Path.read_text', return_value=cask_content):
            with pytest.raises(ValueError, match="Unresolved interpolation"):
                extract_pairs(Path("dummy.rb"))
    
    def test_extract_pairs_no_version_error(self):
        cask_content = '''cask "test-wallpapers" do
  url "https://example.com/file.tar.zstd"
  sha256 "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
end
'''
        with patch('pathlib.Path.read_text', return_value=cask_content):
            with pytest.raises(ValueError, match="No version found"):
                extract_pairs(Path("dummy.rb"))


class TestCaskRegistry:
    """Test the CASK_BY_NAME registry."""
    
    def test_cask_registry_populated(self):
        assert "bluefin-wallpapers" in CASK_BY_NAME
        assert "bluefin-wallpapers-extra" in CASK_BY_NAME
        assert "framework-wallpapers" in CASK_BY_NAME
        assert "aurora-wallpapers" in CASK_BY_NAME
    
    def test_cask_registry_lookup(self):
        config = CASK_BY_NAME["bluefin-wallpapers"]
        assert config.name == "bluefin-wallpapers"
        assert config.release_prefix == "bluefin"
        assert Variant.MACOS in config.variants
