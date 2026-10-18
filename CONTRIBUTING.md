# Contributing

This repository is a Homebrew tap for Linux-oriented formulas, casks, wallpaper packages, and OEM or desktop tools. Keep package definitions small, reproducible, and aligned with the upstream release they wrap.

## Repository layout

- `Formula/` contains formula definitions built from source.
- `Casks/` contains cask definitions that install upstream artifacts.
- `lib/` contains shared Ruby helpers used by package definitions.
- `scripts/` contains maintenance and verification utilities.
- `*.Brewfile` files group packages for image or development use.
- `.github/workflows/` contains the repository's automated validation and release workflows.

## Before editing

Use a fork or a branch in your clone. Keep each pull request focused on one package or one maintenance change.

You need:

- a supported Homebrew installation on macOS or Linux;
- `bubblewrap` on Linux for the same sandbox prerequisite used by CI;
- access to the upstream release URL and its published checksum when changing a package version.

Do not add a version, URL, checksum, or dependency from memory. Check the upstream release first and update related metadata together.

## Adding or updating packages

### Formulae

Place formulae in `Formula/`. Preserve the established metadata fields:

- `url`, `version` when needed, `sha256`, `license`, `homepage`, and `desc`;
- build and runtime dependencies;
- `livecheck` when automatic version detection needs an explicit strategy;
- a `test do` block that exercises an installed executable when the package exposes one.

Use an existing formula as the local style reference before introducing a new pattern. Keep build-only dependencies scoped as build dependencies.

### Casks

Place casks in `Casks/`. A cask normally needs a version, checksum, URL, name, description, homepage, and at least one artifact. Preserve platform and architecture guards, `livecheck`, dependencies, install or uninstall steps, and caveats when the upstream package requires them.

Use shared helpers from `lib/` when the same install, uninstall, or metadata behavior already exists there. Do not copy a helper into an individual cask.

## Local validation

Run validation after Homebrew is installed and before opening a pull request. The command sequence matches the repository's `tests.yml` and `bump-ci.yml` workflows:

```shell
brew test-bot --only-cleanup-before
brew test-bot --only-setup
brew test-bot --only-tap-syntax
```

For changes under `Formula/`, also run:

```shell
brew test-bot --only-formulae
```

Run this repository-independent check for every change:

```shell
git diff --check
```

The pull-request workflow currently runs tap syntax on every pull request and formula checks on pull requests. It does not provide general cask installation or runtime coverage. A green pull request check therefore does not prove that a changed cask installs or behaves correctly; include any package-specific manual validation in the pull request description.

## Pull requests

Include:

- the package or workflow area changed and the upstream release or behavior that motivated it;
- validation commands run and their relevant output;
- any platform, architecture, network, credential, or manual-install limitation;
- documentation updates when user-facing package names, installation steps, or maintenance behavior change.

Avoid unrelated formatting or generated files. Do not commit credentials, downloaded artifacts, or local Homebrew state.

## References

- [Homebrew Formula Cookbook](https://docs.brew.sh/Formula-Cookbook)
- [Homebrew Cask Cookbook](https://docs.brew.sh/Cask-Cookbook)
- [Homebrew BrewTestBot](https://docs.brew.sh/BrewTestBot)
- [Homebrew `brew` manual](https://docs.brew.sh/Manpage.html)
- [Tap syntax workflow](.github/workflows/tests.yml)
- [Bump validation workflow](.github/workflows/bump-ci.yml)
