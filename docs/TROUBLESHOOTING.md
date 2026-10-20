# Troubleshooting

This tap is a staging area for Linux casks, formulas, wallpaper packages, and
OEM tools. Start by identifying whether failure is local validation, an
upstream download/release problem, or a GitHub Actions workflow problem.

## Prerequisites

- A checkout of this repository and a clean or understood working tree.
- Python 3.14 for parity with the wallpaper workflows. The scripts use only
  Python standard-library modules.
- Homebrew for `brew test-bot`, formula checks, and tap syntax checks. Use the
  official Homebrew installation for your operating system.
- Linux formula checks also need `bubblewrap`; the repository's Ubuntu CI jobs
  install the distribution package before running Homebrew checks.
- `scripts/bump-wallpapers.py` reads public releases from the
  [`ublue-os/artwork` releases API](https://api.github.com/repos/ublue-os/artwork/releases).
  A GitHub token is optional for public reads but helps avoid API rate limits.
  Provide it through the process environment; never commit or print it.

Check repository state before changing a cask:

```shell
git status --short
```

## Fast local checks

Run these before investigating a workflow failure:

```shell
python3 -m py_compile scripts/bump-wallpapers.py scripts/verify-wallpapers.py
python3 scripts/bump-wallpapers.py --help
```

The bumper accepts four supported cask names and an optional version. The help
command does not change files.

## Wallpaper checksum verification fails

`verify-wallpapers.py` extracts every `url`/`sha256` pair from wallpaper casks,
replaces `#{version}`, downloads each URL, and returns non-zero on any mismatch.
Start with one cask to isolate the failing pair:

```shell
python3 scripts/verify-wallpapers.py Casks/bluefin-wallpapers.rb
```

Then use the default scan when the targeted check passes:

```shell
python3 scripts/verify-wallpapers.py
```

Interpret failures as follows:

- **HTTP 404 or another fetch error:** check that the upstream asset still
  exists. A removed or renamed asset is an upstream release problem; do not
  replace a checksum with a guessed value.
- **`MISMATCH`:** the URL resolved, but the cask digest does not match the
  downloaded bytes. Re-fetch the intended release asset and update the cask
  only after confirming the version and asset name.
- **`Unresolved interpolation in URL`:** the cask contains a URL pattern that
  the verifier cannot resolve. Inspect the `version` stanza and the URL's
  `#{version}` use before changing the verifier.
- **No version or no pairs:** the cask structure does not match the verifier's
  supported `version`, `url`, and `sha256` stanzas. Compare the cask with the
  current script behavior; do not silently skip the package.

The default scan includes every `*wallpapers*.rb` file, including casks that
are not in the automated bumper's four-cask list. A full scan can therefore
expose an upstream asset failure that a bumper run does not reach.

If the default scan stops on an HTTP 404 for one wallpaper asset, record the
URL and cask version and treat it as upstream availability, not a checksum
mismatch. Do not invent a replacement digest.

## Wallpaper bump fails

The bumper reads release tags and asset digests from `ublue-os/artwork`. It
supports these casks:

- `bluefin-wallpapers`
- `bluefin-wallpapers-extra`
- `framework-wallpapers`
- `aurora-wallpapers`

Run one cask first when diagnosing a failure. Use a version only when the
matching release tag is known:

```shell
python3 scripts/bump-wallpapers.py bluefin-wallpapers
python3 scripts/bump-wallpapers.py bluefin-wallpapers 2026-10-12
```

The version argument is matched to a tag in the form `<release-prefix>-v<version>`;
for example, `2026-10-12` selects `bluefin-v2026-10-12`. An
`AssetNotFoundError` means the release exists but the expected asset or its
`sha256:` digest is absent. Check the release asset name before editing the
script or cask.

The script writes each successfully processed cask in place. If a later cask
fails, earlier casks may already be modified. Always inspect the result before
committing:

```shell
git diff -- Casks/
git status --short
```

Reject a generated diff that changes unrelated casks, removes a digest, or
changes a URL without a matching upstream release asset. Run the targeted
checksum verifier after accepting an update.

If the API reports rate limiting, retry only after supplying a suitable token
through the process environment. Do not put a token in the command line,
repository, issue, or pull-request body.

## `brew test-bot` or formula checks fail

The CI workflow runs these stages in order. Run the same stage locally after
Homebrew and Linux prerequisites are installed:

```shell
brew test-bot --only-cleanup-before
brew test-bot --only-setup
brew test-bot --only-tap-syntax
brew test-bot --only-formulae
```

This environment does not have Homebrew, so these commands were not executed
locally while writing this guide. Their order and flags match
`.github/workflows/tests.yml`; use that workflow as the authoritative CI
recipe when local Homebrew is unavailable.

Use the first failing stage as the diagnosis boundary:

- **cleanup or setup:** repair the local Homebrew environment and rerun setup;
  do not edit a formula for an environment-only failure.
- **tap syntax:** inspect the Ruby syntax and stanza named in the log. Keep
  formula and cask metadata consistent with the relevant Homebrew cookbook.
- **formulae:** read the first failing formula's build/test output. On Linux,
  confirm that `bubblewrap` is installed; the workflow installs it before
  `brew test-bot`.
- **bottle artifact missing:** treat the test result as authoritative first;
  the workflow uploads bottles with `if: always()` so an absent artifact can
  be a consequence of an earlier failure.

The pull-request workflow runs tap syntax on pushes and formula checks on pull
requests. It does not provide general cask install/runtime coverage. A green
formula job is not proof that every Linux cask launches.

## Automated bump or audit workflow fails

The two automated bump paths have different behavior:

- **Wallpaper bump:** `Bump Wallpaper Casks` runs on schedule or manual
  dispatch, updates the four configured wallpaper casks, and opens a pull
  request only when `Casks/` changes.
- **Formula/cask bump:** `Homebrew Bump` runs Homebrew's bump command. It keeps
  the bump step's failure output in `bump_output.log` and creates one audit
  issue per detected formula when an audit fails.

For an automated pull request:

1. Read the exact failing workflow step and identify whether the failure is
   local syntax, a missing upstream asset, an API limit, or an audit finding.
2. Inspect the generated diff and run the targeted local check above.
3. For an upstream 404 or missing release asset, record the unavailable asset
   and leave the cask unchanged until upstream restores or replaces it.
4. For a formula audit, fix the formula in a separate change and rerun the
   same Homebrew stage; do not close the generated audit issue without the
   corresponding evidence.
5. Let the repository's CI label a passing automated PR for bottle publication.
   Do not run the publication workflow on an unreviewed or failing change.

## Where to look next

- [Homebrew BrewTestBot documentation](https://docs.brew.sh/BrewTestBot)
- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Homebrew Cask Cookbook](https://docs.brew.sh/Cask-Cookbook)
- [Ubuntu `bubblewrap` package](https://packages.ubuntu.com/noble/bubblewrap)
- [GitHub REST API: repository releases](https://docs.github.com/en/rest/releases/releases)
- `.github/workflows/tests.yml` for pull-request validation
- `.github/workflows/verify-wallpapers.yml` for checksum verification
- `.github/workflows/bump-wallpapers.yml` and `.github/workflows/bump.yml` for
  automated update behavior
