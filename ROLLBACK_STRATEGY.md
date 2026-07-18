# MUE Dashboard — Rollback Strategy

## Overview
This document describes the rollback procedures for the MUE Review Dashboard deployment. The dashboard is deployed to GitHub Pages via GitHub Actions.

## Deployment Architecture
- **Source**: `action/dashboard/` directory
- **Target**: GitHub Pages (served from `action/dashboard/` artifact)
- **Data**: `action/dashboard/data.json` (generated at build time)
- **Reviews**: `review/reviews.json` (shared state, synced from issues)

## Rollback Triggers
Rollback should be initiated when:
1. **Smoke tests fail** in CI (data.json validation, size checks)
2. **Dashboard errors** reported by reviewers (JS console errors, blank pages)
3. **Data corruption** detected (missing notes, invalid schema)
4. **Security issue** discovered in deployed version

## Rollback Procedures

### Option 1: Git Revert (Preferred — Fastest)
```bash
# Revert the problematic commit
git revert <commit-sha>
git push origin main
```
- GitHub Actions will automatically rebuild and redeploy
- Takes ~2-3 minutes
- Preserves history

### Option 2: Force Push Previous Known-Good Commit
```bash
# Find last good commit
git log --oneline -10

# Force push to main (requires admin access)
git push origin <good-commit-sha>:main --force
```
- Use only if revert is not possible
- Requires coordination with team

### Option 3: Manual GitHub Pages Rollback
1. Go to repository Settings → Pages
2. Under "Build and deployment", note the current deployment branch
3. If using a custom workflow, re-run the previous successful workflow run from Actions tab

## Data.json Rollback
Since `data.json` is generated at build time:
1. **Do not commit data.json** — it's in `.gitignore`
2. Rollback is automatic when code is reverted
3. If data.json was manually committed (shouldn't happen):
   ```bash
   git checkout HEAD~1 -- action/dashboard/data.json
   git commit -m "chore: rollback data.json"
   git push
   ```

## Review Data Rollback
`review/reviews.json` is the canonical review store:
- **Auto-synced** from GitHub Issues labeled `review-feedback`
- **Manual edits** possible via dashboard API
- To rollback reviews:
  ```bash
  # Restore from git history
  git checkout HEAD~1 -- review/reviews.json
  git commit -m "chore: rollback reviews.json"
  git push
  ```
- Or use the dashboard's delete review API for individual reviews

## Verification After Rollback
1. Wait for GitHub Actions build to complete (green checkmark)
2. Run smoke tests locally:
   ```bash
   python action/dashboard/validate_and_smoke.py
   ```
3. Verify dashboard loads at `https://<username>.github.io/MUE/`
4. Check browser console for errors
5. Verify review functionality works

## Communication
- Post rollback status in team channel
- Tag relevant reviewers if their reviews were affected
- Document root cause in issue tracker

## Prevention
- All changes go through PR review
- CI runs validation + smoke tests on every push
- `data.json` is never committed (generated artifact)
- Review data is append-only with version tracking