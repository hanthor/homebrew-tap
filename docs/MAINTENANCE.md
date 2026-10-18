# Tap maintenance

This page describes how package updates move through `hanthor/homebrew-tap`, which checks cover each package type, and what to do when an update fails. Keep package definitions, workflow behavior, and this runbook aligned.

## Prerequisites and boundaries

- Repository write access is required only for opening or updating a pull request. Do not push generated updates directly to `main`.
- Wallpaper automation runs on Python 3.14 in GitHub Actions. Local wallpaper checks need Python 3 and network access to the release URLs; the scripts read `GITHUB_TOKEN` or `GH_TOKEN` when GitHub API authentication is useful.
- Formula and cask checks use Homebrew. Linux CI also installs `bubblewrap`; local Homebrew setup must provide equivalent sandbox support.
- Never commit or paste `GITHUB_TOKEN`, `GH_TOKEN`, or another credential. Actions receive the short-lived workflow token through the workflow environment.
- CI does not install every cask. The pull-request matrix runs formula checks on Ubuntu and macOS; use an affected operating system for cask-specific installation or runtime checks.

## Automated update paths

| Path | Trigger | Result |
| --- | --- | --- |
| Formula and cask bump | `Homebrew Bump` runs daily at 03:00 UTC or by manual dispatch | Homebrew checks the tap against `homebrew-core`, opens update pull requests, and creates an issue when an audit failure is reported. |
| Wallpaper bump | `Bump Wallpaper Casks` runs daily at 03:30 and 15:30 UTC or by manual dispatch | `scripts/bump-wallpapers.py` updates configured wallpaper casks and opens a pull request only when `Casks/` changes. |
| Wallpaper checksum verification | `Verify Wallpaper Cask Checksums` runs for wallpaper-cask or verifier changes, or by manual dispatch | Every URL/SHA-256 pair selected by the verifier is downloaded and compared. |
| Tap CI | `brew test-bot` runs on pushes to `main` and pull requests | Tap syntax runs for every event; formula checks run on pull requests on Ubuntu 24.04 and macOS 15. |
| `linux-mcp-server` bottles | `Formula/linux-mcp-server.rb` changes on `main`, or by manual dispatch | macOS and Linux bottles are built, uploaded to a release, and merged back into the formula with bottle checksums. |

Workflow definitions are the source of truth for triggers and permissions:

- [`bump.yml`](../.github/workflows/bump.yml)
- [`bump-wallpapers.yml`](../.github/workflows/bump-wallpapers.yml)
- [`verify-wallpapers.yml`](../.github/workflows/verify-wallpapers.yml)
- [`tests.yml`](../.github/workflows/tests.yml)
- [`bottle-linux-mcp-server.yml`](../.github/workflows/bottle-linux-mcp-server.yml)

## Wallpaper update procedure

### Before changing a cask

1. Start from a clean branch based on the current `main`.
2. Confirm the upstream release exists and contains the expected asset names for every platform variant.
3. Do not replace a digest because a download happened to succeed. Match each URL with the digest for that exact release asset.
4. Check whether the target is covered by the bumper. `scripts/bump-wallpapers.py` currently configures `bluefin-wallpapers`, `bluefin-wallpapers-extra`, `framework-wallpapers`, and `aurora-wallpapers`. The verifier scans `*wallpapers*.rb`, so its coverage is broader than the automated bumper.

### Run the repository tools

From repository root, inspect the supported bumper arguments before a live update:

```shell
python3 scripts/bump-wallpapers.py --help
```

The bumper accepts an optional configured cask name and optional version. It fetches release metadata, writes the selected cask, and may update multiple platform digests; review the complete diff before committing.

Run a targeted checksum check after editing a wallpaper cask:

```shell
python3 scripts/verify-wallpapers.py Casks/bluefin-wallpapers.rb
```

Use the full verifier when all upstream assets are available:

```shell
python3 scripts/verify-wallpapers.py
```

A network error, upstream 404, or missing release asset is a failed verification, not permission to guess a digest. Record the failing URL and leave that variant unchanged until the upstream artifact is available or the cask is deliberately corrected in a separate change.

### Review and publish

- Review version, URL, and every SHA-256 change together. Do not accept a version-only update when the release asset changed.
- Confirm the generated pull request contains only intended `Casks/` changes.
- Wait for `Verify Wallpaper Cask Checksums` and tap CI. A green checksum job proves the downloaded pairs match; it does not prove desktop integration works on every Linux distribution.
- For a cask with platform-specific behavior, perform an installation and launch check on each affected platform and include the result in the pull request.

## Formula and ordinary cask updates

1. Confirm the upstream release and its install artifact before editing the definition.
2. Update version, URL, architecture branches, dependencies, caveats, and `livecheck` together when the upstream layout changed.
3. Use the `Homebrew Bump` workflow for the normal automated bump path. Use its run log and generated pull request rather than copying a stale command from an older run.
4. For a manual change, run the local Homebrew checks available on the target platform, then rely on `tests.yml` for tap syntax and formula checks on both CI operating systems.
5. Treat cask runtime behavior as an additional platform check; it is outside the formula-only pull-request matrix.

## Bottle updates

Changes to `Formula/linux-mcp-server.rb` on `main` start `bottle-linux-mcp-server.yml`. The workflow builds macOS and Linux artifacts, uploads them to the versioned GitHub release, and writes bottle checksums into the formula. Before merging a formula change:

- confirm the formula version and upstream artifact are correct;
- inspect both bottle jobs and the upload job, not only the formula test result;
- verify the release contains the expected artifacts and the formula contains the generated bottle entries;
- if a bottle job fails, fix the build or formula in a pull request and let the workflow run again; do not hand-edit generated checksums.

## Failure triage

### Checksum mismatch or HTTP error

- Re-run the affected cask only so unrelated network failures do not obscure the result.
- Compare the URL, release tag, asset filename, and expected digest with the upstream release.
- A 404 means the referenced artifact is unavailable at that URL. A digest mismatch means the bytes differ. These require different fixes.
- Do not disable checksum verification or replace a digest with an unreviewed local value.

### Bump workflow failure

- Open the workflow log and identify whether the failure is an upstream release/API problem, a Homebrew audit failure, or a definition error.
- For an audit failure, use the issue created by `bump.yml` as the tracking record and fix the definition in a pull request.
- For rate limiting or transient upstream failure, preserve the log evidence and retry through the normal workflow dispatch after the service is available. Do not commit a partial generated update.

### Formula or cask check failure

- Reproduce the smallest failing check on the relevant operating system.
- Keep formula syntax, formula behavior, and cask runtime failures separate in the pull request description.
- Check dependencies and sandbox assumptions before changing the definition. Linux formula tests may require `bubblewrap`.
- If the failure is caused by an upstream artifact or release, link the upstream evidence instead of weakening the definition or removing its checksum.

## Rollback and recovery

- Stop or close an automated update pull request when its source release is wrong or incomplete; do not merge a partial bump.
- For a bad merged definition, prepare a revert pull request against `main`, restore the last known-good URL/version/digest set, and run the same targeted verifier and CI checks.
- For a bad bottle release, preserve the workflow log and release metadata, correct the formula or build input in a pull request, and let the bottle workflow regenerate artifacts. Do not copy checksums between releases.
- After recovery, record the failing upstream URL, workflow run, affected package, and verification result in the pull request so the next update does not repeat the same diagnosis.

## Verification coverage

| Check | Covers | Does not cover |
| --- | --- | --- |
| `scripts/verify-wallpapers.py` | Downloaded URL/SHA-256 pairs selected from wallpaper casks | Desktop integration, unavailable upstream assets, casks outside its filename glob |
| `tests.yml` tap-syntax job | Homebrew tap syntax | Cask installation and runtime behavior |
| `tests.yml` formula matrix | Formula checks on Ubuntu 24.04 and macOS 15 | Every Linux distribution, every architecture, and cask runtime behavior |
| Bottle workflow | `linux-mcp-server` bottle build, release upload, and generated bottle entries | Other formulas and interactive desktop behavior |

When a check is unavailable locally, state that limitation explicitly and rely on the corresponding workflow result; an unrun check is not a passing check.
