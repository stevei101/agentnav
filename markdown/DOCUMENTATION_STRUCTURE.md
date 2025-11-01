# Documentation Structure Guide

## Directory Purpose

### `docs/` - Published Documentation
**Purpose:** Public-facing documentation for developers, reviewers, and hackathon judges.

**Contents:**
- Developer guides and tutorials
- Setup instructions
- Architecture documentation
- Submission guides
- API documentation
- User-facing guides

**Audience:** External developers, reviewers, judges, open source contributors

**Examples:**
- `GCP_SETUP_GUIDE.md` - How to set up Google Cloud
- `local-development.md` - Developer setup guide
- `ARCHITECTURE_DIAGRAM_GUIDE.md` - How to create diagrams
- `HACKATHON_SUBMISSION_GUIDE.md` - Submission preparation

---

### `markdown/` - Internal Project Notes
**Purpose:** Internal working documents, thoughts, strategy notes, project planning.

**Contents:**
- Brainstorming notes
- Strategy documents
- Meeting notes
- Feature planning
- Research notes
- Internal discussions
- Working documents

**Audience:** Team members, project maintainers

**Examples:**
- `cursor-agent-youtube-thoughts.md` - Hackathon video analysis
- `aistudio_hackathon_insights.md` - Research notes
- `ADK_QUICKSTART_NOTES.md` - Learning notes
- `CLOUD_RUN_UPDATES_SUMMARY.md` - Internal updates

---

## File Organization Rules

### Should be in `docs/`:
- ? Guides that help others understand/use the project
- ? Setup instructions
- ? Architecture documentation
- ? Submission materials (for hackathon)
- ? API documentation
- ? User-facing documentation

### Should be in `markdown/`:
- ? Internal notes and thoughts
- ? Strategy documents
- ? Research notes
- ? Meeting notes
- ? Working documents
- ? Feature planning documents
- ? Internal discussions

---

## Current Structure

### `docs/` (Published)
- ARCHITECTURE_DIAGRAM_GUIDE.md ?
- DUAL_CATEGORY_STRATEGY.md ?
- GCP_SETUP_GUIDE.md ?
- GPU_SETUP_GUIDE.md ?
- HACKATHON_QUICK_REFERENCE.md ?
- HACKATHON_SETUP_CHECKLIST.md ?
- HACKATHON_SUBMISSION_GUIDE.md ?
- local-development.md ?

### `markdown/` (Internal)
- ADK_QUICKSTART_NOTES.md ?
- aistudio_hackathon_insights.md ?
- CLOUD_RUN_UPDATES_SUMMARY.md ?
- CURSOR_RESPONSE_1.md ?
- cursor-agent-youtube-thoughts.md ?
- FEATURE_REQUEST_001_PODMAN_LOCAL_DEV.md (could be either)
- SYSTEM_INSTRUCTION.md (could be docs/ - system documentation)

---

## Guidelines

### When Adding New Files:

**Ask:** "Would a developer/reviewer need this to understand or use the project?"
- **Yes** ? `docs/`
- **No** ? `markdown/`

**Ask:** "Is this a polished, final document for external consumption?"
- **Yes** ? `docs/`
- **No** ? `markdown/`

**Ask:** "Is this internal brainstorming or working notes?"
- **Yes** ? `markdown/`
- **No** ? `docs/`

---

## Benefits of This Structure

1. **Clear Separation** - Easy to find what you need
2. **Professional Presentation** - `docs/` is polished for reviewers
3. **Internal Flexibility** - `markdown/` can be messy/evolving
4. **Easy Navigation** - Developers know where to look
5. **Git Hygiene** - Can potentially ignore `markdown/` in some contexts

---

**Last Updated:** [Date]
