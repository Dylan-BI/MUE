# Reviewer Environment Readiness Check

> **Purpose:** Verify that the reviewer has the necessary tools and access to review all learner artifacts before proceeding with assessment.

## Required Environment

### Core Tools
- [ ] **VS Code** (or compatible Markdown editor) — for viewing `.md` files
- [ ] **Git** — for version control operations
- [ ] **GitHub account** — for review comments and issue tracking
- [ ] **Python 3.x** — for running sync and build scripts

### File Format Support
- [ ] **Markdown** (`.md`) — daily notes, evidence, reports, templates
- [ ] **JSON** (`.json`) — data files, configuration, reviews
- [ ] **Text** (`.txt`) — reference documents, templates

### Access Requirements
- [ ] **Repository access** — read access to `Dylan-BI/MUE`
- [ ] **GitHub Pages** — access to deployed dashboard (if applicable)
- [ ] **Pyramid access** (if reviewing platform-related artifacts)

### Curriculum Documentation Formats
- [ ] **Markdown files** — training materials in `source/`
- [ ] **Reference documents** — `.txt` files in `source/`
- [ ] **Dashboard data** — `action/dashboard/data.json`
- [ ] **Review artifacts** — synced in `review/`

## Environment Confirmation

**Reviewer Name:** _________________

**Date:** _________________

**Environment Status:**
- [ ] ✅ **Adequate** — All required tools and access are available
- [ ] ❌ **Not Adequate** — Missing tools or access (see details below)

**Missing Items (if not adequate):**
- [ ] Missing tool: _________________
- [ ] Missing access: _________________
- [ ] Format support issue: _________________

**Action Required:**
- [ ] Request environment update via GitHub Issues
- [ ] Request specific access via team lead
- [ ] Use alternative review method

## Next Steps

### If Environment is Adequate:
1. Proceed with reviewer workflow
2. Run sync script if needed: `python3 review/scripts/sync-from-action.py`
3. Review artifacts in `review/` folder
4. Complete assessment using feedback template

### If Environment is Not Adequate:
1. **Submit GitHub Issue** using the `reviewer-environment-request.md` template
2. **Tag appropriate team members** for resolution
3. **Wait for environment update** before proceeding with review
4. **Use alternative access** if available (e.g., web-based review)

## Environment Request Process

1. **Create Issue:** Use the GitHub issue template for environment requests
2. **Describe Missing Item:** Specify tool, access, or format support needed
3. **Priority Level:** Indicate if this blocks review completion
4. **Resolution:** Team lead or admin will address the request
5. **Confirmation:** Reviewer confirms environment is updated before proceeding

---

**Note:** Do not proceed with review until environment is confirmed adequate. This ensures consistent and complete assessment of learner artifacts.
