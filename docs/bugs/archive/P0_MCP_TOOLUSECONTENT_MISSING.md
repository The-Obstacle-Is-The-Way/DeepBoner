# P0 Bug: mcp.types.ToolUseContent AttributeError on HuggingFace Spaces

**Status**: FIXED
**Severity**: P0 (App completely broken)
**Discovered**: 2025-12-04
**Fixed**: 2025-12-04 (PR TBD)

---

## Symptom

HuggingFace Spaces deployment crashes with:

```
module 'mcp.types' has no attribute 'ToolUseContent'
```

The app fails to start entirely. No functionality works.

---

## Root Cause

**Dependency version mismatch between `pyproject.toml` and `requirements.txt`.**

| File | MCP Pin | Result |
|------|---------|--------|
| `pyproject.toml` | `mcp>=1.23.0` | Correct - has `ToolUseContent` |
| `requirements.txt` | (missing) | Pulls old MCP via `gradio[mcp]` transitive dep |

**Background:**
- `ToolUseContent` was added in MCP spec **2025-11-25** via **SEP-1577 (Sampling With Tools)**
- Our pyproject.toml correctly pins `mcp>=1.23.0` (for security fix GHSA-9h52-p55h-vw2f)
- HuggingFace Spaces uses `requirements.txt`, NOT `pyproject.toml`
- `gradio[mcp]>=6.0.0` pulls in MCP as transitive dependency
- Without explicit pin, Gradio was pulling an older MCP version lacking `ToolUseContent`

---

## Fix

Added explicit MCP pin to `requirements.txt`:

```diff
# UI (Gradio with MCP server support - 6.0 required for css in launch())
gradio[mcp]>=6.0.0
+
+# Security: Pin mcp to fix GHSA-9h52-p55h-vw2f and ensure ToolUseContent exists
+mcp>=1.23.0
```

Also synced ALL dependencies between `pyproject.toml` and `requirements.txt` to prevent future drift.

---

## Changes Made

**Files modified:**
- `requirements.txt` - Full sync with `pyproject.toml`:
  - Added `mcp>=1.23.0` (root cause fix)
  - Added `beautifulsoup4>=4.12` (was missing)
  - Fixed `huggingface-hub>=0.24.0` (was 0.20.0)
  - Added upper bound to `agent-framework-core>=1.0.0b251120,<2.0.0`
  - Added sync header comment with date

---

## Prevention

1. **Sync header**: `requirements.txt` now has "Last synced: YYYY-MM-DD" comment
2. **CI check**: Consider adding a pre-commit hook to validate requirements.txt matches pyproject.toml

---

## References

- [MCP Python SDK Releases](https://github.com/modelcontextprotocol/python-sdk/releases)
- [MCP Spec 2025-11-25 - Sampling With Tools](https://modelcontextprotocol.io/specification/2025-11-25/client/sampling)
- [GHSA-9h52-p55h-vw2f](https://github.com/advisories/GHSA-9h52-p55h-vw2f) - MCP security advisory

---

## Verification

After fix:
1. Deploy to HuggingFace Spaces
2. Verify app starts without errors
3. Verify MCP server responds at `/gradio_api/mcp/`
