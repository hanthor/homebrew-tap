#!/usr/bin/env python3
"""
Bump wallpaper casks with all SHA256 variants.

Usage:
    ./scripts/bump-wallpapers.py                     # bump all to latest
    ./scripts/bump-wallpapers.py bluefin-wallpapers  # bump specific cask to latest
    ./scripts/bump-wallpapers.py bluefin-wallpapers 2025-12-10  # bump to specific version
"""

from __future__ import annotations

import argparse
import logging
import sys

from wallpaper_utils import (
    CASK_BY_NAME,
    CASKS,
    AssetNotFoundError,
    BumpError,
    CaskConfig,
    CaskFileNotFoundError,
    find_release,
    get_asset_sha256,
    get_current_version,
    get_releases,
    update_sha256_after_url,
    update_single_sha256,
    update_version,
)

logger = logging.getLogger(__name__)


def bump_cask(config: CaskConfig, version: str | None = None) -> None:
    """Bump a wallpaper cask to a specific or latest version."""
    if not config.cask_file.exists():
        raise CaskFileNotFoundError(f"Cask file not found: {config.cask_file}")

    releases = get_releases()
    release = find_release(releases, config.release_prefix, version)
    target_version = release["tag_name"].replace(f"{config.release_prefix}-v", "")

    logger.info("Bumping %s to %s", config.name, target_version)

    content = config.cask_file.read_text()
    current_version = get_current_version(content)
    logger.info("  Current version: %s", current_version)

    content = update_version(content, target_version)

    if config.variants:
        for variant in config.variants:
            asset_name = config.get_asset_name(variant)
            try:
                sha256 = get_asset_sha256(release, asset_name)
                logger.info("  %s: %s", variant.value, sha256)
                content = update_sha256_after_url(content, asset_name, sha256)
            except AssetNotFoundError:
                logger.warning("  %s: not found, skipping", variant.value)
    else:
        asset_name = f"{config.artifact_name}.tar.zstd"
        sha256 = get_asset_sha256(release, asset_name)
        logger.info("  SHA256: %s", sha256)
        content = update_single_sha256(content, sha256)

    config.cask_file.write_text(content)
    logger.info("  Done!")


def bump_all(version: str | None = None) -> bool:
    """Bump all wallpaper casks. Returns True if all succeeded."""
    success = True

    for config in CASKS:
        try:
            bump_cask(config, version)
        except BumpError as e:
            logger.error("Failed to bump %s: %s", config.name, e)
            success = False

    return success


def setup_logging(verbose: bool = False) -> None:
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[logging.StreamHandler()],
    )


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bump wallpaper casks with all SHA256 variants"
    )
    parser.add_argument(
        "cask",
        nargs="?",
        choices=list(CASK_BY_NAME.keys()),
        metavar="CASK",
        help="Specific cask to bump (default: all)",
    )
    parser.add_argument(
        "version",
        nargs="?",
        help="Specific version (default: latest)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output",
    )
    args = parser.parse_args()

    setup_logging(args.verbose)

    logger.info("=== Wallpaper Cask Bumper ===")
    logger.info("")

    try:
        if args.cask:
            config = CASK_BY_NAME[args.cask]
            bump_cask(config, args.version)
            success = True
        else:
            logger.info("Fetching releases from GitHub API...")
            logger.info("")
            success = bump_all(args.version)

        logger.info("")
        logger.info("=== Complete ===")
        return 0 if success else 1

    except BumpError as e:
        logger.error("Error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
