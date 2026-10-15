#!/usr/bin/env python3
"""
Shared domain model and utilities for wallpaper cask management.

Provides a single source of truth for:
- Cask file parsing (URL/SHA256 extraction)
- Cask metadata (variants, release prefix, artifact name)
- Network operations with timeout and error handling
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.error import URLError
from urllib.request import Request, urlopen

if TYPE_CHECKING:
    from typing import TypeAlias

    Release: TypeAlias = dict[str, any]
    Asset: TypeAlias = dict[str, any]


class Variant(Enum):
    """Wallpaper package variants."""

    MACOS = "macos"
    KDE = "kde"
    GNOME = "gnome"
    PNG = "png"


@dataclass
class CaskMetadata:
    """Configuration for a wallpaper cask."""

    name: str
    release_prefix: str
    artifact_name: str
    variants: list[Variant] = None

    def __post_init__(self) -> None:
        if self.variants is None:
            self.variants = list(Variant)

    @property
    def cask_file(self) -> Path:
        """Path to the cask file."""
        return Path(__file__).parent.parent.parent / "Casks" / f"{self.name}.rb"

    def get_tag(self, version: str) -> str:
        """Get the release tag for a version."""
        return f"{self.release_prefix}-v{version}"

    def get_asset_name(self, variant: Variant) -> str:
        """Get the asset filename for a variant."""
        return f"{self.artifact_name}-{variant.value}.tar.zstd"


class CaskParser:
    """Parse Ruby cask files to extract URL and SHA256 pairs."""

    TOKEN_RE = re.compile(r'(url|sha256)\s+"([^"]+)"')
    SHA_RE = re.compile(r"[0-9a-f]{64}")
    VERSION_RE = re.compile(r'version\s+"([^"]+)"')
    LIVECHECK_RE = re.compile(r"livecheck\s+do\b.*?\bend\b", re.DOTALL)

    @staticmethod
    def extract_pairs(cask_path: Path) -> list[tuple[str, str]]:
        """Extract (url, sha256) pairs from a cask file."""
        content = CaskParser.LIVECHECK_RE.sub("", cask_path.read_text())
        version_match = CaskParser.VERSION_RE.search(content)
        if not version_match:
            raise ValueError(f"No version found in {cask_path}")
        version = version_match.group(1)

        tokens = [
            (kind, value)
            for kind, value in CaskParser.TOKEN_RE.findall(content)
            if kind == "url" or CaskParser.SHA_RE.fullmatch(value)
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


class NetworkClient:
    """HTTP client with timeout and error handling for downloading files."""

    DEFAULT_TIMEOUT = 30  # seconds

    @staticmethod
    def fetch_sha256(url: str, timeout: int = DEFAULT_TIMEOUT) -> str:
        """Download a file from URL and return its SHA256 hash."""
        h = hashlib.sha256()
        try:
            request = Request(url)
            with urlopen(request, timeout=timeout) as response:
                while chunk := response.read(1 << 20):  # 1MB chunks
                    h.update(chunk)
        except URLError as e:
            raise RuntimeError(f"Failed to download {url}: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Error downloading {url}: {e}") from e
        return h.hexdigest()
