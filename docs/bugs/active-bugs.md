# Active Bugs

> Last updated: 2025-12-06

---

## P3 - Progress Bar Positioning in ChatInterface

**File:** [p3-progress-bar-positioning.md](./p3-progress-bar-positioning.md)
**Status:** OPEN
**Priority:** Low (cosmetic UX issue)

**Problem:** `gr.Progress()` conflicts with ChatInterface, causing the progress bar to float/overlap with chat messages.

**Fix:** Remove `gr.Progress()` entirely and rely on emoji status messages in chat output.

---

## How to Report Bugs

1. Create `docs/bugs/p{n}-short-name.md` (kebab-case)
2. Add entry to this file
3. Priority: P0=blocker, P1=important, P2=UX, P3=cosmetic

---

*Historical bugs are preserved in the [v0.1.0 release tag](https://github.com/The-Obstacle-Is-The-Way/DeepBoner/releases/tag/v0.1.0).*
