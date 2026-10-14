#!/usr/bin/env python3
"""
Shared utilities for wallpaper cask management.

This module contains the centralized domain model, configuration, and shared
exception classes used by wallpaper cask tools (bump-wallpapers.py,
verify-wallpapers.py).
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.request import Request, urlopen

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
    "CASKS_DIR",
    "GITHUB_API_URL",
    "get_releases",
]

logger = logging.getLogger(__name__)

SCRIPT_DIR = Path(__file__).parent
CASKS_DIR = SCRIPT_DIR.parent / "Casks"
GITHUB_API_URL = "https://api.github.com/repos/ublue-os/artwork/releases"


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


# Cask configurations
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
    headers = {"Accept": "application/vnd.github+json"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = "Bearer " + token
    request = Request(GITHUB_API_URL, headers=headers)
    with urlopen(request) as response:
        return json.loads(response.read().decode())
