#!/usr/bin/env python3
"""
Shared domain models, configuration, and utilities for Homebrew wallpaper casks.
"""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.request import urlopen

if TYPE_CHECKING:
    from typing import TypeAlias

    Release: TypeAlias = dict[str, any]
    Asset: TypeAlias = dict[str, any]

__all__ = [
    "Variant",
    "CaskConfig",
    "BumpError",
    "ReleaseNotFoundError",
    "AssetNotFoundError",
    "CaskFileNotFoundError",
    "CASKS",
    "CASK_BY_NAME",
    "get_releases",
    "find_release",
    "get_asset_sha256",
    "get_current_version",
    "update_sha256_after_url",
    "update_version",
    "update_single_sha256",
    "extract_cask_pairs",
]

logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
CASKS_DIR = SCRIPT_DIR.parent / "Casks"
GITHUB_API_URL = "https://api.github.com/repos/ublue-os/artwork/releases"

TOKEN_RE = re.compile(r'(url|sha256)\s+"([^"]+)"')
SHA_RE = re.compile(r"[0-9a-f]{64}")
VERSION_RE = re.compile(r'version\s+"([^"]+)"')
LIVECHECK_RE = re.compile(r"livecheck\s+do\b.*?\bend\b", re.DOTALL)


class BumpError(Exception):
    """Base exception for bump errors."""


class ReleaseNotFoundError(BumpError):
    """Raised when a release cannot be found."""


class AssetNotFoundError(BumpError):
    """Raised when a release asset cannot be found."""


class CaskFileNotFoundError(BumpError):
    """Raised when a cask file cannot be found."""


class Variant(Enum):
    """Wallpaper package variants."""

    MACOS = "macos"
    KDE = "kde"
    GNOME = "gnome"
    PNG = "png"


@dataclass
class CaskConfig:
    """Configuration for a wallpaper cask."""

    name: str
    release_prefix: str
    artifact_name: str
    variants: list[Variant] = field(default_factory=lambda: list(Variant))

    @property
    def cask_file(self) -> Path:
        """Path to the cask file."""
        return CASKS_DIR / f"{self.name}.rb"

    def get_tag(self, version: str) -> str:
        """Get the release tag for a version."""
        return f"{self.release_prefix}-v{version}"

    def get_asset_name(self, variant: Variant) -> str:
        """Get the asset filename for a variant."""
        return f"{self.artifact_name}-{variant.value}.tar.zstd"


# Centralized cask configurations
CASKS = [
    CaskConfig(
        name="bluefin-wallpapers",
        release_prefix="bluefin",
        artifact_name="bluefin-wallpapers",
    ),
    CaskConfig(
        name="bluefin-wallpapers-extra",
        release_prefix="bluefin-extra",
        artifact_name="bluefin-wallpapers-extra",
    ),
    CaskConfig(
        name="framework-wallpapers",
        release_prefix="framework",
        artifact_name="framework-wallpapers",
    ),
    CaskConfig(
        name="aurora-wallpapers",
        release_prefix="aurora",
        artifact_name="aurora-wallpapers",
        variants=[],  # Single variant, no suffix
    ),
]

CASK_BY_NAME = {cask.name: cask for cask in CASKS}


@cache
def get_releases() -> list[Release]:
    """Fetch all releases from GitHub API (cached)."""
    logger.debug("Fetching releases from %s", GITHUB_API_URL)
    with urlopen(GITHUB_API_URL) as response:
        return json.loads(response.read().decode())


def find_release(releases: list[Release], tag_prefix: str, version: str | None = None) -> Release:
    """Find a release by tag prefix and optional version."""
    for release in releases:
        tag = release["tag_name"]
        if version:
            if tag == f"{tag_prefix}-v{version}":
                return release
        elif tag.startswith(f"{tag_prefix}-v"):
            return release

    version_str = version or "latest"
    raise ReleaseNotFoundError(f"No release found for {tag_prefix} ({version_str})")


def get_asset_sha256(release: Release, asset_name: str) -> str:
    """Extract SHA256 from release asset's digest field."""
    for asset in release.get("assets", []):
        if asset["name"] == asset_name:
            if digest := asset.get("digest", ""):
                if digest.startswith("sha256:"):
                    return digest[7:]
            raise AssetNotFoundError(f"No digest found for asset: {asset_name}")

    raise AssetNotFoundError(f"Asset not found: {asset_name}")


def update_sha256_after_url(content: str, url_pattern: str, new_sha256: str) -> str:
    """Update the sha256 line that follows a specific URL pattern."""
    lines = content.split("\n")
    result = []
    found_url = False

    for line in lines:
        if url_pattern in line:
            found_url = True
            result.append(line)
        elif found_url and "sha256" in line:
            new_line = re.sub(r'sha256\s+"[^"]+"', f'sha256 "{new_sha256}"', line)
            result.append(new_line)
            found_url = False
        else:
            result.append(line)

    return "\n".join(result)


def update_version(content: str, new_version: str) -> str:
    """Update the version in cask content."""
    return re.sub(r'(version\s+")[^"]+(")', rf"\g<1>{new_version}\g<2>", content)


def update_single_sha256(content: str, new_sha256: str) -> str:
    """Update a single sha256 value (for single-variant casks)."""
    return re.sub(r'(sha256\s+")[^"]+(")', rf"\g<1>{new_sha256}\g<2>", content)


def get_current_version(content: str) -> str:
    """Extract current version from cask content."""
    if match := VERSION_RE.search(content):
        return match.group(1)
    return "unknown"


def extract_cask_pairs(cask_path: Path) -> list[tuple[str, str]]:
    """Extract (URL, sha256) pairs from a wallpaper cask file."""
    content = LIVECHECK_RE.sub("", cask_path.read_text())
    version = get_current_version(content)
    if version == "unknown":
        raise ValueError(f"No version found in {cask_path}")

    tokens = [
        (kind, value)
        for kind, value in TOKEN_RE.findall(content)
        if kind == "url" or SHA_RE.fullmatch(value)
    ]

    pairs: list[tuple[str, str]] = []
    i = 0
    while i < len(tokens) - 1:
        a, b = tokens[i], tokens[i + 1]
        if {a[0], b[0]} == {"url", "sha256"}:
            url = a[1] if a[0] == "url" else b[1]
            sha = b[1] if a[0] == "url" else a[1]
            url = url.replace("#{version}", version)
            if "#{" in url:
                raise ValueError(f"Unresolved interpolation in URL: {url}")
            pairs.append((url, sha))
            i += 2
        else:
            i += 1
    return pairs
