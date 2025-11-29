# Bug Investigation: HF Free Tier Quota Exhaustion

## Status
- **Date:** 2025-11-29
- **Reporter:** CLI User
- **Component:** `HFInferenceJudgeHandler`
- **Priority:** High (UX Blocker for Free Tier)
- **Resolution:** FIXED

## Issue Description
On a fresh run with a simple query ("What drugs improve female libido post-menopause?"), the system retrieved 20 valid sources but failed during the Judge/Analysis phase with:
`⚠️ Free Tier Quota Exceeded ⚠️`

This results in a "Synthesis" step that has 0 candidates and 0 findings, rendering the application useless for free users once the (very low) limit is hit, despite having valid search results.

## Evidence
Output provided:
```
### Citations (20 sources)
...
### Reasoning
⚠️ **Free Tier Quota Exceeded** ⚠️
```

## Root Cause Analysis
1. **Search Success:** `SearchAgent` correctly found 20 documents (PubMed/EuropePMC).
2. **Judge Failure:** `HFInferenceJudgeHandler` called the HF Inference API.
3. **Quota Trap:** The API returned a 402 (Payment Required) or Quota error.
4. **Previous Handling:** The handler caught this error and returned a `JudgeAssessment` with `sufficient=True` (to stop the loop) and *empty* fields.
5. **Data Loss:** The 20 valid search results were effectively discarded from the "Analysis" perspective.

## The "Deep Blocker"
The system had a "hard failure" mode for quota exhaustion, assuming that if the LLM can't judge, we have *no* useful information. This "bricked" the UX for free users immediately upon hitting the limit.

## Solution Implemented
Modified `HFInferenceJudgeHandler._create_quota_exhausted_assessment` to:
1. Accept the `evidence` list as an argument.
2. Perform basic heuristic extraction (borrowed from `MockJudgeHandler` logic):
   - Use titles as "Key Findings" (first 5 sources).
   - Add a clear message in "Drug Candidates" telling the user to upgrade.
3. Return this "Partial" assessment instead of an empty one.

## Verification
- Created `tests/unit/agent_factory/test_judges_hf_quota.py` to verify that:
  - 402 errors are caught.
  - `sufficient` is set to `True` (stops loop).
  - `key_findings` are populated from search result titles.
  - `reasoning` contains the warning message.
- Ran existing tests `tests/unit/agent_factory/test_judges_hf.py` - All passed.