#!/usr/bin/env python3
"""
Centralized wallpaper cask metadata and configuration.

This module defines all wallpaper cask metadata in one place, used by both
bump-wallpapers.py and verify-wallpapers.py to eliminate duplication and
ensure consistency.

Usage:
    from cask_metadata import CASKS, get_cask_by_name
    
    for cask in CASKS:
        print(f"Cask: {cask['name']}, Release prefix: {cask['release_prefix']}")
    
    cask = get_cask_by_name('bluefin-wallpapers')
    tag = f"{cask['release_prefix']}-v1.0.0"
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

__all__ = [
    "Variant",
    "CASKS",
    "CASK_NAMES",
    "get_cask_by_name",
    "get_release_tag",
    "get_asset_filename",
]


class Variant(Enum):
    """Wallpaper package variants."""

    MACOS = "macos"
    KDE = "kde"
    GNOME = "gnome"
    PNG = "png"


@dataclass(frozen=True)
class CaskMetadata:
    """Metadata for a wallpaper cask."""

    name: str
    """Cask file name (without .rb extension), e.g. 'bluefin-wallpapers'"""
    
    release_prefix: str
    """GitHub release tag prefix, e.g. 'bluefin' becomes 'bluefin-vX.Y.Z'"""
    
    artifact_name: str
    """Base name for release artifacts, e.g. 'bluefin-wallpapers'"""
    
    variants: tuple[Variant, ...] = (Variant.MACOS, Variant.KDE, Variant.GNOME, Variant.PNG)
    """Variants available for this cask. Single-variant casks use ()."""

    def get_tag(self, version: str) -> str:
        """Get the release tag for a version.
        
        Args:
            version: Version string (e.g. '2025-01-15')
            
        Returns:
            Full release tag (e.g. 'bluefin-v2025-01-15')
        """
        return f"{self.release_prefix}-v{version}"

    def get_asset_name(self, variant: Variant) -> str:
        """Get the release asset filename for a variant.
        
        Args:
            variant: Variant to get asset name for
            
        Returns:
            Asset filename (e.g. 'bluefin-wallpapers-macos.tar.zstd')
        """
        if self.variants and len(self.variants) > 1:
            return f"{self.artifact_name}-{variant.value}.tar.zstd"
        # Single-variant cask: no suffix
        return f"{self.artifact_name}.tar.zstd"


# Centralized cask configuration registry.
# Add new wallpaper casks here; both scripts will automatically discover them.
CASKS = (
    CaskMetadata(
        name="bluefin-wallpapers",
        release_prefix="bluefin",
        artifact_name="bluefin-wallpapers",
        variants=(Variant.MACOS, Variant.KDE, Variant.GNOME, Variant.PNG),
    ),
    CaskMetadata(
        name="bluefin-wallpapers-extra",
        release_prefix="bluefin-extra",
        artifact_name="bluefin-wallpapers-extra",
        variants=(Variant.MACOS, Variant.KDE, Variant.GNOME, Variant.PNG),
    ),
    CaskMetadata(
        name="framework-wallpapers",
        release_prefix="framework",
        artifact_name="framework-wallpapers",
        variants=(Variant.MACOS, Variant.KDE, Variant.GNOME, Variant.PNG),
    ),
    CaskMetadata(
        name="aurora-wallpapers",
        release_prefix="aurora",
        artifact_name="aurora-wallpapers",
        variants=(),  # Single-variant cask, no suffix
    ),
)

# Derived: set of known cask names for quick validation
CASK_NAMES = frozenset(cask.name for cask in CASKS)


def get_cask_by_name(name: str) -> CaskMetadata | None:
    """Look up a cask by name.
    
    Args:
        name: Cask name (e.g. 'bluefin-wallpapers')
        
    Returns:
        CaskMetadata if found, None otherwise
    """
    for cask in CASKS:
        if cask.name == name:
            return cask
    return None


def get_release_tag(cask_name: str, version: str) -> str | None:
    """Get the release tag for a cask and version.
    
    Args:
        cask_name: Cask name
        version: Version string
        
    Returns:
        Release tag (e.g. 'bluefin-v2025-01-15'), or None if cask not found
    """
    cask = get_cask_by_name(cask_name)
    return cask.get_tag(version) if cask else None


def get_asset_filename(cask_name: str, variant: str) -> str | None:
    """Get the asset filename for a cask and variant.
    
    Args:
        cask_name: Cask name
        variant: Variant name (e.g. 'macos', 'kde', 'gnome', 'png')
        
    Returns:
        Asset filename, or None if cask/variant not found
    """
    cask = get_cask_by_name(cask_name)
    if not cask:
        return None
    try:
        var = Variant(variant)
        if cask.variants and var not in cask.variants:
            return None
        return cask.get_asset_name(var)
    except ValueError:
        return None
