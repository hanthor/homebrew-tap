# Package Lifecycle and Upstream Contribution

This document describes the lifecycle of packages in homebrew-tap, success criteria for upstream contribution, and the process for graduation or deprecation.

## Philosophy

This tap is intentionally **temporary**. Success means packages are either:
1. **Graduated**: Accepted into Homebrew core (upstream success)
2. **Archived**: No longer needed (replaced by flatpak or native upstream build)
3. **Deprecated**: Superseded by better alternatives

The goal is to delete every package in this tap — not through abandonment, but through upstream adoption or retirement.

## Package Lifecycle Stages

### Stage 1: Experimental (Test)

**Purpose:** Validate that a Homebrew formula/cask builds and installs correctly.

**Criteria for entry:**
- Source code exists and is publicly available
- Builds on Linux and Homebrew infrastructure
- Addresses a documented need (IDEs, OEM tools, etc.)

**Activities:**
- Test on multiple Linux distros (Fedora, Ubuntu, Alpine)
- Gather user feedback
- Refine formula based on failures

**Exit criteria:**
- Formula is stable (no errors in 50+ installs)
- Dependencies are minimal and documented
- Ready for Homebrew core review (quality/maintenance standards met)

**Duration:** 1–3 months

**Status in tap:** Available in production; clearly marked as experimental if needed

### Stage 2: Production (Staging for Upstream)

**Purpose:** Formula is stable and meets Homebrew core standards. Ready for upstream contribution.

**Criteria for entry:**
- Passed Stage 1 testing
- Upstream source is stable (not changing API frequently)
- Maintainer committed to supporting upstream PR
- Quality checks pass (linting, dependencies, license)

**Activities:**
- File upstream PR with Homebrew/homebrew-core
- Respond to Homebrew maintainer feedback
- Prepare for upstream review (may take weeks/months)

**Exit criteria:**
- PR merged in upstream, OR
- PR closed (upstream not interested), OR
- Package deprecated (no longer needed)

**Duration:** 1–6 months (depends on upstream review)

**Status in tap:**
- Remains in tap while upstream PR is pending
- Marked with issue/PR link if upstream PR exists
- Still available for users who want it before upstream merge

### Stage 3: Graduated (Upstream Success)

**Purpose:** Package has been accepted into Homebrew core. Users install from upstream.

**Criteria for entry:**
- PR merged in homebrew-core
- Package appears in `brew search` results
- Homebrew maintainers own maintenance

**Activities:**
- Users are directed to upstream: `brew tap ublue-os/tap` is no longer needed
- Document in changelog: "Graduated to Homebrew core"
- Monitor upstream for issues (optional post-graduation support)

**Exit from tap:**
- Formula removed from `Formula/` (deduped with upstream)
- Cask removed from `Casks/`

**Duration:** Permanent (successful exit)

### Stage 4: Archived (Replaced or Deprecated)

**Purpose:** Package is no longer needed. Documented for historical record.

**Criteria for entry:**
- Upstream provides better alternative (native build, new distro support)
- Use case is solved by flatpak or native packages
- Maintainer no longer available and no volunteer replacement

**Activities:**
- Issue announcement (2-week notice minimum)
- Redirect users to alternative (if available)
- Archive formula in `Archive/` or remove entirely

**Exit from tap:**
- Formula/cask deleted
- Archive note in README (if historically significant)

**Duration:** Permanent (successful cleanup)

## Upstream Contribution Checklist

Before filing a PR in homebrew-core, ensure:

### Formula Quality

- [ ] `brew install <formula>` succeeds
- [ ] `brew test <formula>` passes (if test block exists)
- [ ] No `sudo` or privileged operations in install
- [ ] Dependencies are minimal and listed explicitly
- [ ] Version is pinned to latest stable release
- [ ] SHA-256 checksum is verified
- [ ] License is documented in formula

### Maintainability

- [ ] Upstream project is actively maintained (not abandoned)
- [ ] Upstream releases are regular and predictable
- [ ] Upstream has no known critical security issues
- [ ] You are willing to review and respond to issues for 6+ months

### Documentation

- [ ] README documents why this package is in the tap
- [ ] Comments in formula explain non-obvious decisions
- [ ] Linked to any upstream PR or Homebrew discussion

### Testing

- [ ] Tested on Fedora (primary target)
- [ ] Tested on Ubuntu (secondary target)
- [ ] Tested on older Linux kernel versions if possible
- [ ] No conflicts with existing Homebrew formulas

## Upstream PR Process

### 1. Check Existing Coverage

Search Homebrew/homebrew-core for existing formula:
```bash
brew search <package>
brew tap homebrew/core
brew info <package>
```

If it already exists upstream, use that instead.

### 2. Prepare PR Description

Include in PR:
- Why this package is useful (use case, audience)
- Why it's not suitable as a cask/tap elsewhere
- Any non-standard build requirements
- Maintenance commitment (you will review PRs for X months)

**Example:**
> Adds VSCode for Linux. Currently VS Code in Homebrew is macOS-only, but the Linux build is stable and popular on Linux desktops. Maintained and tested on Fedora/Ubuntu. Willing to review updates and respond to issues for 12 months.

### 3. Respond to Feedback

Homebrew maintainers may request:
- Dependency simplification
- Build flag changes
- Test addition
- Documentation updates

Respond promptly (within 1 week).

### 4. Await Merge or Closure

- Merge: Formula now in upstream. Plan removal from tap.
- Close (not interested): Document in tap as "attempted upstream contribution" and decide if package stays in tap indefinitely.

## Managing Packages in This Tap

### Adding a New Package

1. **Classify it**: Test stage or Production stage?
2. **Create branch**: `git checkout -b formula/<name>`
3. **Write formula**: Follow Homebrew best practices
4. **Test locally**: `brew install ./Formula/<name>.rb`
5. **Submit PR**: Description should state intended lifecycle stage

### Updating Existing Package

Follow standard formula update process:
- Bump version
- Update SHA-256
- Test install
- Create PR with changelog reference

### Deprecating a Package

1. **Announce**: Create issue with 2-week notice
2. **Redirect users**: Update README, add deprecation comment in formula
3. **Communicate**: Note on PR discussion, in changelog
4. **Remove**: Delete formula/cask and close associated issues

## Current Package Status

| Package | Stage | Upstream Status | Notes |
|---------|-------|-----------------|-------|
| heic-to-dynamic-gnome-wallpaper | Production | Pending PR | Ready for Homebrew core submission |
| asusctl | Production | Pending PR | Awaiting Homebrew review |
| 1password-gui-linux | Production | Approved | Should be submitted upstream |
| jetbrains-toolbox-linux | Test | Not started | Stable, ready for production stage |
| lm-studio-linux | Test | Not started | Awaiting LM Studio API stabilization |
| vscode-linux | Production | Not started | Homebrew likely uninterested (MS ownership) |
| Wallpaper casks | Production | Not applicable | ublue/Universal Blue specific; archive as part of image |

*(This table should be maintained in a public tracking issue)*

## Timeline and Responsibilities

**Quarterly review:** Evaluate each package's stage, gather metrics, decide on graduation or deprecation.

**Upstream submission:** Each production-stage package should have a corresponding upstream PR within 3 months of entering production stage.

**Maintenance SLA:**
- Test stage: Best-effort maintenance
- Production stage: Review PRs within 1 week
- Graduated: Upstream maintainer owns; this tap doesn't maintain copy

## Questions?

- Package-specific questions: Comment on the package's PR or issue
- Lifecycle or process questions: Open an issue in this repository
