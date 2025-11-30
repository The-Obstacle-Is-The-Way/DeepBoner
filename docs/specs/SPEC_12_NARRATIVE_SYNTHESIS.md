# SPEC_12: Narrative Report Synthesis

**Status**: Draft
**Priority**: P1 - Core deliverable
**Related Issues**: #85, #86
**Related Spec**: SPEC_11 (Sexual Health Focus)

## Problem Statement

DeepBoner's report generation outputs **structured metadata** instead of **synthesized prose**. The current implementation uses string templating with NO LLM call for narrative synthesis.

### Current Output (Actual)

```markdown
## Sexual Health Analysis

### Question
Testosterone therapy for hypoactive sexual desire disorder?

### Drug Candidates
- **Testosterone**
- **LibiGel**
- **Androgel**

### Key Findings
- Testosterone therapy improves sexual desire and activity in postmenopausal women with HSDD.
- Transdermal testosterone is a preferred formulation.

### Assessment
- **Mechanism Score**: 8/10
- **Clinical Evidence Score**: 9/10
- **Confidence**: 90%

### Reasoning
The evidence provides a clear understanding of the mechanism of action...

### Citations (33 sources)
1. [Title](url)...
```

### Expected Output (Professional Research Report)

```markdown
## Sexual Health Research Report: Testosterone Therapy for Hypoactive Sexual Desire Disorder

### Executive Summary

Testosterone therapy represents a well-established, evidence-based treatment for
hypoactive sexual desire disorder (HSDD) in postmenopausal women. Our analysis of
33 peer-reviewed sources reveals consistent findings across multiple randomized
controlled trials, with transdermal testosterone demonstrating the strongest
efficacy-safety profile.

### Background

Hypoactive sexual desire disorder affects an estimated 12% of postmenopausal women
and is characterized by persistent lack of sexual interest causing personal distress.
The International Society for the Study of Women's Sexual Health (ISSWSH) published
clinical guidelines in 2021 establishing testosterone as a recommended intervention...

### Evidence Synthesis

**Mechanism of Action**

Testosterone exerts its effects on sexual desire through multiple pathways. At the
hypothalamic level, testosterone modulates dopaminergic signaling that underlies
libido. Evidence from Smith et al. (2021) demonstrates that androgen receptor
activation in the central nervous system correlates with subjective measures of
sexual desire (r=0.67, p<0.001)...

**Clinical Trial Evidence**

A systematic review of 8 randomized controlled trials (N=3,035) demonstrated that
transdermal testosterone significantly improved:
- Satisfying sexual events: +2.1 per month (95% CI: 1.4-2.8)
- Sexual desire scores: +0.4 on validated scales (p<0.001)

The Global Consensus Position Statement (2019) and ISSWSH Guidelines (2021) both
recommend transdermal testosterone as first-line therapy...

### Recommendations

Based on this evidence synthesis:
1. **Transdermal testosterone** (300 μg/day) is recommended for postmenopausal
   women with HSDD not primarily related to modifiable factors
2. **Duration**: Continue for 6 months to assess efficacy; discontinue if no benefit
3. **Monitoring**: Lipid profile and liver function at baseline and 3-6 months

### Limitations & Future Directions

- Long-term safety data beyond 24 months remains limited
- Efficacy in premenopausal women less well-established
- Head-to-head comparisons between formulations are needed

### References

1. Parish SJ et al. (2021). International Society for the Study of Women's Sexual
   Health Clinical Practice Guideline for the Use of Systemic Testosterone for
   Hypoactive Sexual Desire Disorder in Women. J Sex Med. https://pubmed.ncbi.nlm.nih.gov/33814355/
...
```

## Root Cause Analysis

### Current Implementation (`src/orchestrators/simple.py:448-505`)

```python
def _generate_synthesis(
    self,
    query: str,
    evidence: list[Evidence],
    assessment: JudgeAssessment,
) -> str:
    # ❌ NO LLM CALL - Just string templating!
    drug_list = "\n".join([f"- **{d}**" for d in assessment.details.drug_candidates])
    findings_list = "\n".join([f"- {f}" for f in assessment.details.key_findings])

    return f"""{self.domain_config.report_title}
### Question
{query}
### Drug Candidates
{drug_list}
...
"""
```

**The problem**: No LLM is ever called to synthesize the report. It's just formatted
data from the JudgeAssessment.

### Microsoft Agent Framework Pattern

From `reference_repos/agent-framework/python/samples/getting_started/workflows/orchestration/concurrent_custom_aggregator.py`:

```python
# Define a custom aggregator callback that uses the chat client to SYNTHESIZE
async def summarize_results(results: list[Any]) -> str:
    # Collect expert outputs
    expert_sections: list[str] = []
    for r in results:
        messages = getattr(r.agent_run_response, "messages", [])
        final_text = messages[-1].text if messages else "(no content)"
        expert_sections.append(f"{r.executor_id}:\n{final_text}")

    # Ask the MODEL to synthesize
    system_msg = ChatMessage(
        Role.SYSTEM,
        text=(
            "You are a helpful assistant that consolidates multiple domain expert outputs "
            "into one cohesive, concise summary with clear takeaways."
        ),
    )
    user_msg = ChatMessage(Role.USER, text="\n\n".join(expert_sections))

    # ✅ LLM CALL for synthesis
    response = await chat_client.get_response([system_msg, user_msg])
    return response.messages[-1].text
```

**The pattern**: The aggregator makes an **LLM call** to synthesize, not string concatenation.

## Solution Design

### Architecture

```
Current:
  Evidence → Judge → {structured data} → String Template → Bullet Points

Proposed:
  Evidence → Judge → {structured data} → SynthesisAgent → Narrative Prose
                                                ↓
                                         LLM-based synthesis
```

### Components

#### 1. `SynthesisAgent` (`src/agents/synthesis.py`)

A new agent dedicated to narrative report generation:

```python
from pydantic import BaseModel
from pydantic_ai import Agent

class NarrativeReport(BaseModel):
    """Structured output for narrative report."""
    executive_summary: str  # 2-3 sentences, key takeaways
    background: str  # What is this condition, why does it matter
    evidence_synthesis: str  # Mechanism + Clinical evidence in prose
    recommendations: list[str]  # Actionable recommendations
    limitations: str  # Honest limitations
    references: list[Reference]  # Properly formatted

class SynthesisAgent:
    """Generates narrative research reports from structured data."""

    async def synthesize(
        self,
        query: str,
        evidence: list[Evidence],
        assessment: JudgeAssessment,
        domain: ResearchDomain,
    ) -> NarrativeReport:
        """Generate narrative prose report."""
        # Build context
        context = self._build_synthesis_context(evidence, assessment)

        # ✅ LLM CALL for synthesis
        result = await self.agent.run(
            f"Generate a narrative research report for: {query}",
            context=context,
        )
        return result.data
```

#### 2. Updated System Prompt (`src/prompts/synthesis.py`)

```python
SYNTHESIS_SYSTEM_PROMPT = """You are a scientific writer specializing in sexual health research.
Your task is to synthesize research evidence into a clear, narrative report.

## Writing Style
- Write in PROSE PARAGRAPHS, not bullet points
- Use academic but accessible language
- Be specific about evidence strength (e.g., "in a randomized controlled trial of N=200")
- Reference specific studies by author name
- Provide quantitative results where available

## Report Structure

### Executive Summary (REQUIRED - 2-3 sentences)
Summarize the key finding and clinical implication. Start with the bottom line.
Example: "Testosterone therapy demonstrates consistent efficacy for HSDD in
postmenopausal women, with transdermal formulations showing the best safety profile."

### Background (REQUIRED - 1 paragraph)
Explain the condition, its prevalence, and why this question matters clinically.

### Evidence Synthesis (REQUIRED - 2-4 paragraphs)
Weave together the evidence into a coherent narrative:
- Mechanism of Action: How does the intervention work?
- Clinical Evidence: What do the trials show? Be specific about effect sizes.
- Comparative Evidence: How does it compare to alternatives?

### Recommendations (REQUIRED - 3-5 bullet points)
Provide actionable clinical recommendations based on the evidence.

### Limitations (REQUIRED - 1 paragraph)
Acknowledge gaps, biases, and areas needing more research.

### References (REQUIRED)
List the key references in proper academic format.

## CRITICAL RULES
1. ONLY cite papers from the provided evidence - NEVER hallucinate references
2. Write in complete sentences and paragraphs
3. Avoid lists/bullets except in Recommendations section
4. Include specific statistics when available (p-values, effect sizes, CIs)
5. Acknowledge uncertainty honestly
"""
```

#### 3. Updated Orchestrator Integration

```python
# In src/orchestrators/simple.py

async def _generate_synthesis(
    self,
    query: str,
    evidence: list[Evidence],
    assessment: JudgeAssessment,
) -> str:
    """Generate narrative synthesis using LLM."""
    from src.agents.synthesis import SynthesisAgent

    synthesis_agent = SynthesisAgent(domain=self.domain)

    report = await synthesis_agent.synthesize(
        query=query,
        evidence=evidence,
        assessment=assessment,
        domain=self.domain,
    )

    return report.to_markdown()
```

### Few-Shot Example (Required for Quality)

From issue #82, include a concrete example in the prompt:

```python
FEW_SHOT_EXAMPLE = """
## Example: Strong Evidence Synthesis

INPUT:
- Query: "Alprostadil for erectile dysfunction"
- Evidence: 15 papers including meta-analysis of 8 RCTs (N=3,247)
- Mechanism Score: 9/10
- Clinical Score: 9/10

OUTPUT:

### Executive Summary

Alprostadil (prostaglandin E1) represents a well-established second-line treatment
for erectile dysfunction, with meta-analytic evidence demonstrating 87% efficacy
in achieving erections sufficient for intercourse. It offers a PDE5-independent
mechanism particularly valuable for patients who do not respond to oral therapies.

### Background

Erectile dysfunction affects approximately 30 million men in the United States,
with prevalence increasing with age. While PDE5 inhibitors (sildenafil, tadalafil)
remain first-line therapy, approximately 30% of patients are non-responders or
have contraindications. Alprostadil provides an alternative mechanism of action
through direct smooth muscle relaxation.

### Evidence Synthesis

**Mechanism of Action**

Alprostadil works through a distinct pathway from PDE5 inhibitors. It binds to
EP receptors on cavernosal smooth muscle, activating adenylate cyclase and
increasing intracellular cAMP. This leads to smooth muscle relaxation and
penile erection independent of nitric oxide signaling. As noted by Smith et al.
(2019), this mechanism explains its efficacy in patients with endothelial
dysfunction or nerve damage.

**Clinical Evidence**

A meta-analysis by Johnson et al. (2020) pooled data from 8 randomized controlled
trials (N=3,247) comparing intracavernosal alprostadil to placebo. The primary
endpoint of erection sufficient for intercourse was achieved in 87% of alprostadil
patients versus 12% placebo (RR 7.25, 95% CI: 5.8-9.1, p<0.001). The number
needed to treat (NNT) was 1.3, indicating robust effect size.

Subgroup analysis revealed consistent efficacy across etiologies:
- Vascular ED: 85% response rate
- Neurogenic ED: 91% response rate
- Post-prostatectomy: 82% response rate

### Recommendations

1. Consider alprostadil as second-line therapy when PDE5 inhibitors fail or are contraindicated
2. Start with 10 μg intracavernosal injection, titrate up to 40 μg based on response
3. Provide in-office training for self-injection technique
4. Monitor for penile fibrosis with long-term use (occurs in 3-5% of patients)

### Limitations

Long-term data beyond 2 years is limited. Head-to-head comparisons with
newer therapies (low-intensity shockwave) are lacking. Most trials excluded
patients with severe cardiovascular disease, limiting generalizability.
The intraurethral formulation (MUSE) has lower efficacy (43%) than injection.

### References

1. Smith AB et al. (2019). Alprostadil mechanism of action in erectile tissue.
   J Urol. https://pubmed.ncbi.nlm.nih.gov/12345678/
2. Johnson CD et al. (2020). Meta-analysis of intracavernosal alprostadil.
   J Sex Med. https://pubmed.ncbi.nlm.nih.gov/23456789/
"""
```

## Implementation Plan

### Phase 1: Core SynthesisAgent

1. Create `src/agents/synthesis.py` with:
   - `SynthesisAgent` class
   - `NarrativeReport` Pydantic model
   - LLM-based synthesis method

2. Create `src/prompts/synthesis.py` with:
   - `SYNTHESIS_SYSTEM_PROMPT`
   - `FEW_SHOT_EXAMPLE`
   - `format_synthesis_context()` helper

3. Update `src/orchestrators/simple.py`:
   - Make `_generate_synthesis()` async
   - Call `SynthesisAgent.synthesize()`
   - Keep `_generate_partial_synthesis()` as fallback (free tier)

### Phase 2: Advanced Mode Integration

4. Update `src/orchestrators/advanced.py`:
   - Add `SynthesisAgent` to Magentic workflow
   - Ensure it receives all evidence from prior agents

### Phase 3: Test Coverage

5. Create `tests/unit/agents/test_synthesis.py`:
   - Test narrative output structure
   - Test reference accuracy (no hallucinated citations)
   - Test prose vs bullet point ratio

### Phase 4: Domain Customization

6. Update `src/config/domain.py`:
   - Add `synthesis_system_prompt` field to `DomainConfig`
   - Add `synthesis_few_shot_example` field
   - Configure for sexual health domain

## File Changes

| File | Change |
|------|--------|
| `src/agents/synthesis.py` | NEW - SynthesisAgent |
| `src/prompts/synthesis.py` | NEW - Synthesis prompts |
| `src/orchestrators/simple.py` | MODIFY - Call SynthesisAgent |
| `src/orchestrators/advanced.py` | MODIFY - Add to Magentic |
| `src/config/domain.py` | MODIFY - Add synthesis prompts |
| `src/utils/models.py` | MODIFY - Add NarrativeReport |
| `tests/unit/agents/test_synthesis.py` | NEW - Tests |
| `tests/unit/prompts/test_synthesis.py` | NEW - Tests |

## Acceptance Criteria

- [ ] Report contains **paragraph-form prose**, not just bullet points
- [ ] Report has **executive summary** (2-3 sentences)
- [ ] Report has **background section** explaining the condition
- [ ] Report has **synthesized narrative** weaving evidence together
- [ ] Report has **actionable recommendations**
- [ ] Report has **limitations** section (honest acknowledgment)
- [ ] Citations are **properly formatted** (author, year, title, URL)
- [ ] No hallucinated references (CRITICAL)
- [ ] Works in both simple and advanced modes
- [ ] Falls back gracefully on free tier (minimal templating OK)

## Test Criteria

```python
def test_report_is_narrative_not_bullets():
    """Report should be mostly prose, not bullet points."""
    report = synthesis_agent.synthesize(...)

    # Count paragraphs vs bullet points
    paragraphs = len([p for p in report.split('\n\n') if len(p) > 100])
    bullets = report.count('\n- ')

    # Prose should dominate
    assert paragraphs > bullets, "Report should be narrative, not bullet list"

def test_references_not_hallucinated():
    """All references must come from provided evidence."""
    evidence_urls = {e.citation.url for e in evidence}
    report = synthesis_agent.synthesize(...)

    for ref in report.references:
        assert ref.url in evidence_urls, f"Hallucinated reference: {ref.url}"
```

## Related Microsoft Agent Framework Patterns

| Pattern | Location | Application |
|---------|----------|-------------|
| Custom Aggregator | `concurrent_custom_aggregator.py` | LLM-based synthesis |
| Fan-Out/Fan-In | `fan_out_fan_in_edges.py` | Multi-expert synthesis |
| Research Assistant | `research_assistant_agent.py` | Tool-based research |
| Sequential Orchestration | `spec-001-foundry-sdk-alignment.md` | Analyst→Writer→Editor chain |

## References

- GitHub Issue #85: Report lacks narrative synthesis
- GitHub Issue #86: Microsoft Agent Framework patterns
- LangChain Deep Agents blog: Few-shot examples importance
- Open Deep Research Architecture: Scoping + Synthesis pattern
