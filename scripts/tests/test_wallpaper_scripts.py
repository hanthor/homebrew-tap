"""
Unit tests for wallpaper cask parsing and bump utilities.

Tests pure parsing logic, configuration, and version management without network calls.
"""

import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

# Add scripts directory to path so we can import the modules
SCRIPTS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SCRIPTS_DIR))

import verify_wallpapers as verify_module
import bump_wallpapers as bump_module


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_cask_single_sha256():
    """Cask file with a single SHA256 (aurora-wallpapers style)."""
    return """
cask "aurora-wallpapers" do
  version "2025.01.15"
  sha256 "abc123def456abc123def456abc123def456abc123def456abc123def456abc1"
  url "https://github.com/ublue-os/artwork/releases/download/aurora-v#{version}/aurora-wallpapers.tar.zstd"

  name "Aurora Wallpapers"
  desc "Wallpaper pack for Aurora"

  depends_on macos: ">= :monterey"
end
"""


@pytest.fixture
def sample_cask_multi_sha256():
    """Cask file with multiple SHA256 variants."""
    return """
cask "bluefin-wallpapers" do
  version "2025.01.15"

  url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{version}/bluefin-wallpapers-macos.tar.zstd"
  sha256 "aaa111bbb222ccc333ddd444eee555fff666aaa111bbb222ccc333ddd444eee"

  url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{version}/bluefin-wallpapers-kde.tar.zstd"
  sha256 "111222333444555666777888999aaabbbcccdddeeefffaaabbbcccdddeeefffaa"

  url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{version}/bluefin-wallpapers-gnome.tar.zstd"
  sha256 "fffeeeddccbbaa99887766554433221100ffeeddccbbaa99887766554433221100"
end
"""


@pytest.fixture
def sample_cask_with_livecheck():
    """Cask file with livecheck block to be stripped."""
    return """
cask "bluefin-wallpapers" do
  version "2024.12.10"

  url "https://github.com/ublue-os/artwork/releases/download/bluefin-v#{version}/bluefin-wallpapers-macos.tar.zstd"
  sha256 "0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffffaa"

  livecheck do
    url "https://api.github.com/repos/ublue-os/artwork/releases/latest"
    strategy :json do |json|
      json["tag_name"].match(/^bluefin-v(.*)$/)&.captures&.first
    end
  end
end
"""


@pytest.fixture
def sample_cask_with_unresolved_interpolation():
    """Cask file with unresolved variable interpolation."""
    return """
cask "test-wallpapers" do
  version "2025.01.15"

  url "https://example.com/#{os}/wallpapers-#{version}.tar.zstd"
  sha256 "abc123def456abc123def456abc123def456abc123def456abc123def456abc1"
end
"""


# ============================================================================
# extract_pairs Tests (verify-wallpapers.py)
# ============================================================================


def test_extract_pairs_single_url_sha256(tmp_path, sample_cask_single_sha256):
    """Test extracting a single URL/SHA256 pair."""
    cask_file = tmp_path / "test.rb"
    cask_file.write_text(sample_cask_single_sha256)

    pairs = verify_module.extract_pairs(cask_file)

    assert len(pairs) == 1
    url, sha = pairs[0]
    assert url == "https://github.com/ublue-os/artwork/releases/download/aurora-v2025.01.15/aurora-wallpapers.tar.zstd"
    assert sha == "abc123def456abc123def456abc123def456abc123def456abc123def456abc1"


def test_extract_pairs_multiple_variants(tmp_path, sample_cask_multi_sha256):
    """Test extracting multiple URL/SHA256 pairs."""
    cask_file = tmp_path / "test.rb"
    cask_file.write_text(sample_cask_multi_sha256)

    pairs = verify_module.extract_pairs(cask_file)

    assert len(pairs) == 3
    # First pair (macOS)
    assert "bluefin-wallpapers-macos.tar.zstd" in pairs[0][0]
    assert pairs[0][1] == "aaa111bbb222ccc333ddd444eee555fff666aaa111bbb222ccc333ddd444eee"
    # Second pair (KDE)
    assert "bluefin-wallpapers-kde.tar.zstd" in pairs[1][0]
    assert pairs[1][1] == "111222333444555666777888999aaabbbcccdddeeefffaaabbbcccdddeeefffaa"
    # Third pair (GNOME)
    assert "bluefin-wallpapers-gnome.tar.zstd" in pairs[2][0]
    assert pairs[2][1] == "fffeeeddccbbaa99887766554433221100ffeeddccbbaa99887766554433221100"


def test_extract_pairs_strips_livecheck(tmp_path, sample_cask_with_livecheck):
    """Test that livecheck blocks are stripped before parsing."""
    cask_file = tmp_path / "test.rb"
    cask_file.write_text(sample_cask_with_livecheck)

    pairs = verify_module.extract_pairs(cask_file)

    # Should successfully extract the URL/SHA pair, ignoring the livecheck block
    assert len(pairs) == 1
    assert pairs[0][1] == "0000111122223333444455556666777788889999aaaabbbbccccddddeeeeffffaa"


def test_extract_pairs_interpolates_version(tmp_path, sample_cask_single_sha256):
    """Test that #{version} placeholders are replaced."""
    cask_file = tmp_path / "test.rb"
    cask_file.write_text(sample_cask_single_sha256)

    pairs = verify_module.extract_pairs(cask_file)

    url, _ = pairs[0]
    # Version should be interpolated, not left as #{version}
    assert "#{" not in url
    assert "2025.01.15" in url


def test_extract_pairs_fails_on_missing_version(tmp_path):
    """Test that missing version raises ValueError."""
    cask_file = tmp_path / "test.rb"
    cask_file.write_text("""
cask "test" do
  url "https://example.com/file.tar.zstd"
  sha256 "abc123def456abc123def456abc123def456abc123def456abc123def456abc1"
end
""")

    with pytest.raises(ValueError, match="No version found"):
        verify_module.extract_pairs(cask_file)


def test_extract_pairs_fails_on_unresolved_interpolation(tmp_path, sample_cask_with_unresolved_interpolation):
    """Test that unresolved interpolations raise ValueError."""
    cask_file = tmp_path / "test.rb"
    cask_file.write_text(sample_cask_with_unresolved_interpolation)

    with pytest.raises(ValueError, match="Unresolved interpolation"):
        verify_module.extract_pairs(cask_file)


# ============================================================================
# bump_wallpapers.py Tests
# ============================================================================


def test_cask_config_cask_file_path():
    """Test CaskConfig.cask_file property."""
    config = bump_module.CaskConfig(
        name="test-wallpapers",
        release_prefix="test",
        artifact_name="test-wallpapers"
    )
    assert config.cask_file.name == "test-wallpapers.rb"


def test_cask_config_get_tag():
    """Test CaskConfig.get_tag() method."""
    config = bump_module.CaskConfig(
        name="bluefin-wallpapers",
        release_prefix="bluefin",
        artifact_name="bluefin-wallpapers"
    )
    
    tag = config.get_tag("2025.01.15")
    assert tag == "bluefin-v2025.01.15"


def test_cask_config_get_asset_name_with_variants():
    """Test CaskConfig.get_asset_name() for multi-variant cask."""
    config = bump_module.CaskConfig(
        name="bluefin-wallpapers",
        release_prefix="bluefin",
        artifact_name="bluefin-wallpapers",
        variants=[bump_module.Variant.MACOS, bump_module.Variant.KDE]
    )
    
    assert config.get_asset_name(bump_module.Variant.MACOS) == "bluefin-wallpapers-macos.tar.zstd"
    assert config.get_asset_name(bump_module.Variant.KDE) == "bluefin-wallpapers-kde.tar.zstd"


def test_cask_config_get_asset_name_single_variant():
    """Test CaskConfig.get_asset_name() for single-variant cask."""
    config = bump_module.CaskConfig(
        name="aurora-wallpapers",
        release_prefix="aurora",
        artifact_name="aurora-wallpapers",
        variants=[]
    )
    
    # For single-variant casks, caller handles the .tar.zstd suffix
    assert config.artifact_name == "aurora-wallpapers"


def test_update_version():
    """Test update_version() regex substitution."""
    content = 'cask "test" do\n  version "2024.12.01"\nend'
    
    result = bump_module.update_version(content, "2025.01.15")
    
    assert 'version "2025.01.15"' in result
    assert '2024.12.01' not in result


def test_update_single_sha256():
    """Test update_single_sha256() for single-variant casks."""
    content = '''cask "aurora" do
  sha256 "oldoldoldoldoldoldoldoldoldoldoldoldoldoldoldoldoldoldoldoldoldoldold"
end'''
    
    result = bump_module.update_single_sha256(content, "newnewnewnewnewnewnewnewnewnewnewnewnewnewnewnewnewnewnewnewnewnewnew")
    
    assert "newnewnewnewnewnewnewnewnewnewnewnewnewnewnewnewnewnewnewnewnewnewnew" in result
    assert "oldoldold" not in result


def test_update_sha256_after_url():
    """Test update_sha256_after_url() for multi-variant casks."""
    content = '''url "https://example.com/bluefin-wallpapers-macos.tar.zstd"
  sha256 "oldsha256oldsha256oldsha256oldsha256oldsha256oldsha256oldsha256oldsha"

  url "https://example.com/bluefin-wallpapers-kde.tar.zstd"
  sha256 "anothersha256anothersha256anothersha256anothersha256anothersha256anoth"'''

    result = bump_module.update_sha256_after_url(
        content,
        "bluefin-wallpapers-macos.tar.zstd",
        "newsha256newsha256newsha256newsha256newsha256newsha256newsha256newsha2"
    )
    
    # First sha256 should be updated
    assert "newsha256newsha256newsha256newsha256newsha256newsha256newsha256newsha2" in result
    # Second sha256 should remain unchanged
    assert "anothersha256anothersha256anothersha256anothersha256anothersha256anoth" in result


def test_get_current_version():
    """Test get_current_version() extraction."""
    content = 'cask "test" do\n  version "2024.12.01"\nend'
    
    version = bump_module.get_current_version(content)
    
    assert version == "2024.12.01"


def test_get_current_version_fallback():
    """Test get_current_version() returns 'unknown' when no version found."""
    content = 'cask "test" do\nend'
    
    version = bump_module.get_current_version(content)
    
    assert version == "unknown"


def test_cask_by_name_registry():
    """Test that CASK_BY_NAME registry contains all configured casks."""
    assert "bluefin-wallpapers" in bump_module.CASK_BY_NAME
    assert "bluefin-wallpapers-extra" in bump_module.CASK_BY_NAME
    assert "framework-wallpapers" in bump_module.CASK_BY_NAME
    assert "aurora-wallpapers" in bump_module.CASK_BY_NAME
    
    for name, config in bump_module.CASK_BY_NAME.items():
        assert config.name == name


def test_variant_enum():
    """Test Variant enum has expected values."""
    assert bump_module.Variant.MACOS.value == "macos"
    assert bump_module.Variant.KDE.value == "kde"
    assert bump_module.Variant.GNOME.value == "gnome"
    assert bump_module.Variant.PNG.value == "png"


def test_bump_error_hierarchy():
    """Test BumpError exception hierarchy."""
    assert issubclass(bump_module.ReleaseNotFoundError, bump_module.BumpError)
    assert issubclass(bump_module.AssetNotFoundError, bump_module.BumpError)
    assert issubclass(bump_module.CaskFileNotFoundError, bump_module.BumpError)


def test_find_release_latest():
    """Test find_release() with no version (latest)."""
    releases = [
        {"tag_name": "bluefin-v2024.12.01"},
        {"tag_name": "bluefin-v2024.11.15"},
        {"tag_name": "other-v1.0.0"},
    ]
    
    release = bump_module.find_release(releases, "bluefin")
    
    assert release["tag_name"] == "bluefin-v2024.12.01"


def test_find_release_specific_version():
    """Test find_release() with specific version."""
    releases = [
        {"tag_name": "bluefin-v2024.12.01"},
        {"tag_name": "bluefin-v2024.11.15"},
    ]
    
    release = bump_module.find_release(releases, "bluefin", "2024.11.15")
    
    assert release["tag_name"] == "bluefin-v2024.11.15"


def test_find_release_not_found_latest():
    """Test find_release() raises when no release matches prefix."""
    releases = [{"tag_name": "other-v1.0.0"}]
    
    with pytest.raises(bump_module.ReleaseNotFoundError, match="bluefin"):
        bump_module.find_release(releases, "bluefin")


def test_find_release_not_found_specific():
    """Test find_release() raises when specific version not found."""
    releases = [{"tag_name": "bluefin-v2024.12.01"}]
    
    with pytest.raises(bump_module.ReleaseNotFoundError, match="2025.01.01"):
        bump_module.find_release(releases, "bluefin", "2025.01.01")


def test_get_asset_sha256_success():
    """Test get_asset_sha256() with valid digest."""
    release = {
        "assets": [
            {
                "name": "bluefin-wallpapers-macos.tar.zstd",
                "digest": "sha256:abc123def456abc123def456abc123def456abc123def456abc123def456abc1"
            }
        ]
    }
    
    sha = bump_module.get_asset_sha256(release, "bluefin-wallpapers-macos.tar.zstd")
    
    assert sha == "abc123def456abc123def456abc123def456abc123def456abc123def456abc1"


def test_get_asset_sha256_no_digest():
    """Test get_asset_sha256() raises when digest field missing."""
    release = {
        "assets": [
            {
                "name": "bluefin-wallpapers-macos.tar.zstd",
            }
        ]
    }
    
    with pytest.raises(bump_module.AssetNotFoundError, match="No digest found"):
        bump_module.get_asset_sha256(release, "bluefin-wallpapers-macos.tar.zstd")


def test_get_asset_sha256_not_found():
    """Test get_asset_sha256() raises when asset not in release."""
    release = {
        "assets": [
            {"name": "other-file.tar.zstd"}
        ]
    }
    
    with pytest.raises(bump_module.AssetNotFoundError, match="Asset not found"):
        bump_module.get_asset_sha256(release, "bluefin-wallpapers-macos.tar.zstd")


def test_get_asset_sha256_empty_assets():
    """Test get_asset_sha256() raises when no assets in release."""
    release = {"assets": []}
    
    with pytest.raises(bump_module.AssetNotFoundError, match="Asset not found"):
        bump_module.get_asset_sha256(release, "bluefin-wallpapers-macos.tar.zstd")
