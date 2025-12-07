# Release Process

> **Last Updated**: 2025-12-06

This document describes the release workflow for DeepBoner.

## Version Numbering

DeepBoner uses [Semantic Versioning](https://semver.org/):

```
MAJOR.MINOR.PATCH

1.0.0  - First stable release
0.2.0  - New features (backwards compatible)
0.1.1  - Bug fixes only
```

### Pre-release Versions

```
0.1.0-alpha.1  - Early development
0.1.0-beta.1   - Feature complete, testing
0.1.0-rc.1     - Release candidate
```

## Release Workflow

### 1. Prepare the Release

```bash
# Ensure you're on main and up to date
git checkout main
git pull origin main

# Run all checks
make check
```

### 2. Update Version

Edit `pyproject.toml`:

```toml
[project]
version = "0.2.0"  # Update this
```

### 3. Update CHANGELOG

Add release notes to `CHANGELOG.md`:

```markdown
## [0.2.0] - 2025-12-15

### Added
- New feature X

### Fixed
- Bug in Y

### Changed
- Improved Z
```

### 4. Create Release Commit

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "release: v0.2.0"
```

### 5. Tag the Release

```bash
git tag -a v0.2.0 -m "Release v0.2.0"
```

### 6. Push

```bash
git push origin main
git push origin v0.2.0
```

### 7. Create GitHub Release

1. Go to GitHub → Releases → New Release
2. Select the tag (v0.2.0)
3. Copy release notes from CHANGELOG
4. Publish release

### 8. Deploy to HuggingFace Spaces

```bash
# Push to HuggingFace
git push huggingface-upstream main
```

## Release Checklist

### Before Release

- [ ] All tests pass (`make check`)
- [ ] CHANGELOG updated
- [ ] Version bumped in pyproject.toml
- [ ] Documentation updated
- [ ] No outstanding critical bugs
- [ ] Security audit clean (`uv run pip-audit`)

### After Release

- [ ] GitHub release created
- [ ] HuggingFace Space updated
- [ ] Announce release (if significant)

## Hotfix Process

For urgent fixes on released versions:

```bash
# Create hotfix branch from tag
git checkout -b hotfix/0.1.1 v0.1.0

# Make fix
# ...

# Bump patch version
# Update CHANGELOG

# Commit and tag
git commit -m "fix: critical bug in X"
git tag -a v0.1.1 -m "Hotfix v0.1.1"

# Push
git push origin v0.1.1

# Merge back to main
git checkout main
git merge hotfix/0.1.1
git push origin main
```

## CI/CD Integration

Releases trigger GitHub Actions:

```yaml
on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Build and test
        run: make check
```

## Rollback Procedure

If a release has critical issues:

```bash
# Revert to previous version in HuggingFace
git push huggingface-upstream v0.1.0:main --force

# Document in CHANGELOG
# Plan hotfix release
```

## Version Locations

Keep these in sync:

| File | Field |
|------|-------|
| `pyproject.toml` | `version = "X.Y.Z"` |
| `CHANGELOG.md` | `## [X.Y.Z] - YYYY-MM-DD` |
| Git tag | `vX.Y.Z` |

---

## Related Documentation

- [CHANGELOG](../../CHANGELOG.md)
- [Contributing Guide](../../CONTRIBUTING.md)
- [Deployment Guide](../deployment/docker.md)
