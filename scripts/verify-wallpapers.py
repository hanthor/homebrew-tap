#!/usr/bin/env python3
"""
Verify every url/sha256 pair in the wallpaper casks by downloading
each URL and comparing its SHA-256 against the cask file.

Bypasses cask runtime conditionals (e.g. `if File.exist?("/usr/bin/plasmashell")`)
that hide variants from `brew bump-cask-pr` and `brew fetch`.

Usage:
    ./scripts/verify-wallpapers.py
    ./scripts/verify-wallpapers.py Casks/bluefin-wallpapers-extra.rb
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path
from urllib.request import urlopen

from wallpaper_utils import extract_cask_pairs

SCRIPT_DIR = Path(__file__).parent
CASKS_DIR = SCRIPT_DIR.parent / "Casks"
DEFAULT_GLOB = "*wallpapers*.rb"


def fetch_sha256(url: str) -> str:
    h = hashlib.sha256()
    with urlopen(url) as response:
        while chunk := response.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def verify_cask(cask_path: Path) -> list[str]:
    failures: list[str] = []
    pairs = extract_cask_pairs(cask_path)
    print(f"=== {cask_path.name} ({len(pairs)} variants) ===")
    for url, expected in pairs:
        actual = fetch_sha256(url)
        status = "OK" if actual == expected else "MISMATCH"
        print(f"  [{status}] {url.rsplit('/', 1)[-1]}")
        if actual != expected:
            failures.append(
                f"{cask_path.name}: {url}\n    expected {expected}\n    actual   {actual}"
            )
    return failures


def main() -> int:
    if len(sys.argv) > 1:
        cask_paths = [Path(arg) for arg in sys.argv[1:]]
    else:
        cask_paths = sorted(CASKS_DIR.glob(DEFAULT_GLOB))

    failures: list[str] = []
    for cask_path in cask_paths:
        failures.extend(verify_cask(cask_path))

    print()
    if failures:
        print("FAILURES:")
        for f in failures:
            print(f"  {f}")
        return 1
    print("All checksums match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
