"""
Shared utilities for wallpaper cask parsing and verification.

Centralizes URL/SHA256 extraction, version interpolation, and cask
metadata handling used across bump-wallpapers.py and verify-wallpapers.py.
"""

import re
from pathlib import Path
from typing import NamedTuple


class CaskPair(NamedTuple):
    """A single url/sha256 pair from a cask file."""
    url: str
    sha256: str


# Regex patterns for cask file parsing
TOKEN_RE = re.compile(r'(url|sha256)\s+"([^"]+)"')
SHA_RE = re.compile(r"[0-9a-f]{64}")
VERSION_RE = re.compile(r'version\s+"([^"]+)"')
LIVECHECK_RE = re.compile(r"livecheck\s+do\b.*?\bend\b", re.DOTALL)


def extract_version(content: str) -> str:
    """Extract the version string from cask content."""
    match = VERSION_RE.search(content)
    if not match:
        raise ValueError("No version found in cask file")
    return match.group(1)


def extract_pairs(cask_path: Path) -> list[CaskPair]:
    """Extract all url/sha256 pairs from a wallpaper cask file.
    
    Removes livecheck blocks and interpolates #{version} in URLs.
    """
    content = LIVECHECK_RE.sub("", cask_path.read_text())
    version = extract_version(content)

    # Find all url and sha256 tokens
    tokens = [
        (kind, value)
        for kind, value in TOKEN_RE.findall(content)
        if kind == "url" or SHA_RE.fullmatch(value)
    ]

    pairs: list[CaskPair] = []
    i = 0
    while i < len(tokens) - 1:
        a, b = tokens[i], tokens[i + 1]
        if {a[0], b[0]} == {"url", "sha256"}:
            url = a[1] if a[0] == "url" else b[1]
            sha = b[1] if a[0] == "url" else a[1]
            url = url.replace("#{version}", version)
            if "#{" in url:
                raise ValueError(f"Unresolved interpolation in URL: {url}")
            pairs.append(CaskPair(url, sha))
            i += 2
        else:
            i += 1
    return pairs
