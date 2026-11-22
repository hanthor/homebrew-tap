# Roadmap

This tap is a staging area: its measure of success is that the casks and
formulae here move upstream (to Homebrew core/cask or to the projects
themselves) and get deleted from this repository. The roadmap orders the open
issues so that work which unblocks other work lands first.

Items are ordered, not dated. Issue numbers refer to this repository.

## Phase 1: Make CI trustworthy

Nothing else can merge safely while the bump and bottle workflows are flaky.

- Bump Wallpaper Casks fails on concurrent runs because of a branch-name
  collision (#148).
- Pin `actions/github-script` in the automerge workflow (#155).
- Fix Homebrew cask syntax violations in the wallpaper casks (#135).
- Resolve the `linux-mcp-server` formula ambiguity in bottle builds (#87), and
  make the bottle workflow build this repository's formula rather than
  `ublue-os/tap`'s (#66, #64).
- Investigate the shared `verify` failure across the repository (#176).

## Phase 2: Close the security findings

- Remove unsafe shell pipelines and temporary-file use in cask preflight steps
  (#17, #20, #105, #106).
- Add timeouts to network requests in the Python scripts (#72).
- Collapse the duplicate PR cluster for the timeout fix and the cask preflight
  fix into one PR each (#173).

## Phase 3: Reduce duplication

Do this after Phases 1 and 2, because it touches the same cask files.

- Extract a shared wallpaper cask model and parsing helpers (#15), then
  consolidate the preflight/postflight logic (#116) and the hardcoded `CASKS`
  metadata (#122).
- Centralize the ASUS release metadata shared by the daemon and GUI casks
  (#156), the Visual Studio Code installation DSL (#162) and the AppImage
  extraction lifecycle (#169).
- Fix the truncated SHA-256 digests in the Bazzite wallpaper cask (#171).

## Phase 4: Contributor documentation

- Contributor and local validation guide, including CONTRIBUTING.md (#158, #79).
- Document the wallpaper maintenance scripts (#100).
- Troubleshooting runbook, building on `docs/MAINTENANCE.md` (#167).

## Phase 5: Package lifecycle and upstreaming

- Define the package lifecycle and maintenance expectations (#140, #93): when a
  cask is added, when it is considered stale, and when it is proposed upstream
  or removed.
- Consolidate the wallpaper management experience (#141).
- Align dependency versions across the related repositories (#142).

## Non-goals

- This tap is not a permanent home for packages. A package that upstream
  accepts is removed here.
- Features that belong in the upstream applications are not implemented here.

## Where contributors can help

Phase 4 items need no knowledge of the workflows. Phase 3 items are best
claimed one at a time, because they overlap in the same files.
