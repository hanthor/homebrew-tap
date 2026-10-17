# Wallpaper scripts

Repository wallpaper casks use two Python scripts for release updates and checksum checks:

- [`scripts/bump-wallpapers.py`](../scripts/bump-wallpapers.py) updates configured wallpaper casks from `ublue-os/artwork` releases.
- [`scripts/verify-wallpapers.py`](../scripts/verify-wallpapers.py) downloads cask assets and compares their SHA-256 values with the cask declarations.

## Prerequisites

Run commands from repository root.

- Python 3.10 or newer. Scripts use standard-library modules only, including the `str | None` type syntax.
- Network access to `api.github.com` and GitHub release assets.
- An optional `GITHUB_TOKEN` or `GH_TOKEN` environment variable for the release API. The bumper sends it as a bearer token when present; without one, GitHub's unauthenticated API rate limit applies.
- A clean working tree or a disposable branch. The bumper edits cask files in place and has no dry-run mode.

The bumper reads releases from <https://api.github.com/repos/ublue-os/artwork/releases>. The verifier downloads every URL declared beside a wallpaper cask's `sha256` value; it does not use Homebrew's runtime conditionals.

## Bump wallpaper casks

See the exact positional arguments and supported cask names:

```shell
python3 scripts/bump-wallpapers.py --help
```

Update one configured cask to its latest matching release:

```shell
python3 scripts/bump-wallpapers.py bluefin-wallpapers
```

Pass a release version as the second positional argument when updating a specific release:

```shell
python3 scripts/bump-wallpapers.py bluefin-wallpapers VERSION
```

`VERSION` is the release version without the release-prefix or leading `v`; use a value that exists in the upstream release list. Omitting both positional arguments updates every cask configured in the script.

The current bumper configuration covers `bluefin-wallpapers`, `bluefin-wallpapers-extra`, `framework-wallpapers`, and `aurora-wallpapers`. Other `*wallpapers*.rb` files are not updated by this script. In particular, `bazzite-wallpapers` is verified by the checksum script but is not in the bumper configuration.

After a bump:

1. Inspect `git diff` for version, URL, and SHA-256 changes.
2. Confirm every generated URL belongs to the intended upstream release.
3. Run the targeted verifier for each changed cask.
4. Run the full verifier and record any unrelated pre-existing failure before opening a pull request.

## Verify wallpaper checksums

Verify every cask matching `Casks/*wallpapers*.rb`:

```shell
python3 scripts/verify-wallpapers.py
```

Verify only selected casks when iterating on one change:

```shell
python3 scripts/verify-wallpapers.py Casks/bluefin-wallpapers.rb
```

The verifier replaces `#{version}` in each URL, downloads each asset, and prints `OK` or `MISMATCH`. It exits zero only when all processed pairs match. A checksum mismatch exits nonzero after printing expected and actual values. Network errors such as HTTP 404 or 403 currently propagate and stop the scan; they are not checksum matches.

The full scan currently includes `bazzite-wallpapers.rb`. If that cask points at an upstream release or asset that no longer exists, the scan stops with HTTP 404 before later casks are checked. Treat that as a stale cask/release reference: inspect the upstream release list and the cask URL instead of copying a new checksum from an unrelated asset. A targeted scan can still validate a cask whose release assets are available.

## Troubleshooting

| Symptom | Meaning | Action |
| --- | --- | --- |
| `HTTP Error 403: rate limit exceeded` from the bumper | GitHub rejected an unauthenticated or exhausted API request | Provide a valid `GITHUB_TOKEN` or `GH_TOKEN` in the process environment, then rerun. Do not commit the token. |
| `HTTP Error 404: Not Found` from either script | Release tag or asset URL is absent | Check the cask version, release prefix, asset name, and current upstream release list. |
| `No release found` from the bumper | No upstream tag matches the configured prefix and requested version | Check the requested version and upstream tag naming before changing the cask. |
| `Asset not found` from the bumper | Matching release exists, but expected platform/variant asset is absent | Confirm upstream release assets and update the cask configuration only through a separate change. |
| `MISMATCH` from the verifier | Downloaded bytes differ from the declared SHA-256 | Re-download the exact URL, verify the upstream release, and update the checksum only after confirming the asset identity. |

The scripts do not cache downloaded assets. Repeated verification downloads them again; use a targeted path while debugging a single cask, then run the full scan before submission.
