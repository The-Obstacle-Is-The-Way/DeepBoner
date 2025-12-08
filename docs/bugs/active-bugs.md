# Active Bugs

> Last updated: 2025-12-08

---

## ~~P2 - LLM Output Contamination (Free Tier)~~ (RESOLVED)

**File:** [p2-llm-output-contamination.md](./p2-llm-output-contamination.md)
**Status:** CLOSED (Implemented 2025-12-08)
**Priority:** Medium (affects output quality)

**Problem:** Qwen 2.5 7B occasionally outputs garbage tokens like `.ToDecimal` (C# method names) mid-output due to training data contamination.

**Fix:** Added `src/utils/sanitize.py` with regex-based output filtering. Integrated into `src/orchestrators/advanced.py` at streaming emission point.

---

## ~~P3 - Progress Bar Positioning in ChatInterface~~ (RESOLVED)

**File:** [p3-progress-bar-positioning.md](./p3-progress-bar-positioning.md)
**Status:** CLOSED (SPEC-22)
**Priority:** Low (cosmetic UX issue)

**Problem:** `gr.Progress()` conflicts with ChatInterface, causing the progress bar to float/overlap with chat messages.

**Fix:** Removed `gr.Progress()` entirely per SPEC-22. Now uses `show_progress="full"` for native Gradio spinner.

---

## How to Report Bugs

1. Create `docs/bugs/p{n}-short-name.md` (kebab-case)
2. Add entry to this file
3. Priority: P0=blocker, P1=important, P2=UX, P3=cosmetic

---

*Historical bugs are preserved in the [v0.1.0 release tag](https://github.com/The-Obstacle-Is-The-Way/DeepBoner/releases/tag/v0.1.0).*
