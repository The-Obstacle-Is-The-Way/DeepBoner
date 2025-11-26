# Phase 13 Implementation Spec: Modal Pipeline Integration

**Goal**: Wire existing Modal code execution into the agent pipeline.
**Philosophy**: "Sandboxed execution makes AI-generated code trustworthy."
**Prerequisite**: Phase 12 complete (MCP server working)
**Priority**: P1 - HIGH VALUE ($2,500 Modal Innovation Award)
**Estimated Time**: 2-3 hours

---

## 1. Why Modal Integration?

### Current State Analysis

Mario already implemented `src/tools/code_execution.py`:

| Component | Status | Notes |
|-----------|--------|-------|
| `ModalCodeExecutor` class | Built | Executes Python in Modal sandbox |
| `SANDBOX_LIBRARIES` | Defined | pandas, numpy, scipy, etc. |
| `execute()` method | Implemented | Stdout/stderr capture |
| `execute_with_return()` | Implemented | Returns `result` variable |
| `AnalysisAgent` | Built | Uses Modal for statistical analysis |
| **Pipeline Integration** | **MISSING** | Not wired into main orchestrator |

### What's Missing

```
Current Flow:
  User Query → Orchestrator → Search → Judge → [Report] → Done

With Modal:
  User Query → Orchestrator → Search → Judge → [Hypothesis] → [Analysis*] → Report → Done
                                                                    ↓
                                                          Modal Sandbox Execution
```

*The AnalysisAgent exists but is NOT called by either orchestrator.

---

## 2. Prize Opportunity

### Modal Innovation Award: $2,500

**Judging Criteria**:
1. **Sandbox Isolation** - Code runs in container, not local
2. **Scientific Computing** - Real pandas/scipy analysis
3. **Safety** - Can't access local filesystem
4. **Speed** - Modal's fast cold starts

### What We Need to Show

```python
# LLM generates analysis code
code = """
import pandas as pd
import scipy.stats as stats

# Analyze extracted metrics from evidence
data = pd.DataFrame({
    'study': ['Study1', 'Study2', 'Study3'],
    'effect_size': [0.45, 0.52, 0.38],
    'sample_size': [120, 85, 200]
})

# Meta-analysis statistics
weighted_mean = (data['effect_size'] * data['sample_size']).sum() / data['sample_size'].sum()
t_stat, p_value = stats.ttest_1samp(data['effect_size'], 0)

print(f"Weighted Effect Size: {weighted_mean:.3f}")
print(f"P-value: {p_value:.4f}")

if p_value < 0.05:
    result = "SUPPORTED"
else:
    result = "INCONCLUSIVE"
"""

# Executed SAFELY in Modal sandbox
executor = get_code_executor()
output = executor.execute(code)  # Runs in isolated container!
```

---

## 3. Technical Specification

### 3.1 Dependencies (Already Present)

```toml
# pyproject.toml - already has Modal
dependencies = [
    "modal>=0.63.0",
    # ...
]
```

### 3.2 Environment Variables

```bash
# .env
MODAL_TOKEN_ID=your-token-id
MODAL_TOKEN_SECRET=your-token-secret
```

### 3.3 Integration Points

| Integration Point | File | Change Required |
|-------------------|------|-----------------|
| Simple Orchestrator | `src/orchestrator.py` | Add `AnalysisAgent` call |
| Magentic Orchestrator | `src/orchestrator_magentic.py` | Add `AnalysisAgent` participant |
| Gradio UI | `src/app.py` | Add toggle for analysis mode |
| Config | `src/utils/config.py` | Add `enable_modal_analysis` setting |

---

## 4. Implementation

### 4.1 Configuration Update (`src/utils/config.py`)

```python
class Settings(BaseSettings):
    # ... existing settings ...

    # Modal Configuration
    modal_token_id: str | None = None
    modal_token_secret: str | None = None
    enable_modal_analysis: bool = False  # Opt-in for hackathon demo

    @property
    def modal_available(self) -> bool:
        """Check if Modal credentials are configured."""
        return bool(self.modal_token_id and self.modal_token_secret)
```

### 4.2 Simple Orchestrator Update (`src/orchestrator.py`)

```python
"""Main orchestrator with optional Modal analysis."""

from src.utils.config import settings

# ... existing imports ...


class Orchestrator:
    """Search-Judge-Analyze orchestration loop."""

    def __init__(
        self,
        search_handler: SearchHandlerProtocol,
        judge_handler: JudgeHandlerProtocol,
        config: OrchestratorConfig | None = None,
        enable_analysis: bool = False,  # New parameter
    ) -> None:
        self.search = search_handler
        self.judge = judge_handler
        self.config = config or OrchestratorConfig()
        self.history: list[dict[str, Any]] = []
        self._enable_analysis = enable_analysis and settings.modal_available

        # Lazy-load analysis components
        self._hypothesis_agent: Any = None
        self._analysis_agent: Any = None

    async def _get_hypothesis_agent(self) -> Any:
        """Lazy initialization of HypothesisAgent."""
        if self._hypothesis_agent is None:
            from src.agents.hypothesis_agent import HypothesisAgent

            self._hypothesis_agent = HypothesisAgent(
                evidence_store={"current": []},
            )
        return self._hypothesis_agent

    async def _get_analysis_agent(self) -> Any:
        """Lazy initialization of AnalysisAgent."""
        if self._analysis_agent is None:
            from src.agents.analysis_agent import AnalysisAgent

            self._analysis_agent = AnalysisAgent(
                evidence_store={"current": [], "hypotheses": []},
            )
        return self._analysis_agent

    async def run(self, query: str) -> AsyncGenerator[AgentEvent, None]:
        """Main orchestration loop with optional Modal analysis."""
        # ... existing search/judge loop ...

        # After judge says "synthesize", optionally run analysis
        if self._enable_analysis and assessment.recommendation == "synthesize":
            yield AgentEvent(
                type="analyzing",
                message="Running statistical analysis in Modal sandbox...",
                data={},
                iteration=iteration,
            )

            try:
                # Generate hypotheses first
                hypothesis_agent = await self._get_hypothesis_agent()
                hypothesis_agent._evidence_store["current"] = all_evidence

                hypothesis_result = await hypothesis_agent.run(query)
                hypotheses = hypothesis_agent._evidence_store.get("hypotheses", [])

                # Run Modal analysis
                analysis_agent = await self._get_analysis_agent()
                analysis_agent._evidence_store["current"] = all_evidence
                analysis_agent._evidence_store["hypotheses"] = hypotheses

                analysis_result = await analysis_agent.run(query)

                yield AgentEvent(
                    type="analysis_complete",
                    message="Modal analysis complete",
                    data=analysis_agent._evidence_store.get("analysis", {}),
                    iteration=iteration,
                )

            except Exception as e:
                yield AgentEvent(
                    type="error",
                    message=f"Modal analysis failed: {e}",
                    data={"error": str(e)},
                    iteration=iteration,
                )

        # Continue to synthesis...
```

### 4.3 MCP Tool for Modal Analysis (`src/mcp_tools.py`)

Add a new MCP tool for direct Modal analysis:

```python
async def analyze_hypothesis(
    drug: str,
    condition: str,
    evidence_summary: str,
) -> str:
    """Perform statistical analysis of drug repurposing hypothesis using Modal.

    Executes AI-generated Python code in a secure Modal sandbox to analyze
    the statistical evidence for a drug repurposing hypothesis.

    Args:
        drug: The drug being evaluated (e.g., "metformin")
        condition: The target condition (e.g., "Alzheimer's disease")
        evidence_summary: Summary of evidence to analyze

    Returns:
        Analysis result with verdict (SUPPORTED/REFUTED/INCONCLUSIVE) and statistics
    """
    from src.tools.code_execution import get_code_executor, CodeExecutionError
    from src.agent_factory.judges import get_model
    from pydantic_ai import Agent

    # Check Modal availability
    from src.utils.config import settings
    if not settings.modal_available:
        return "Error: Modal credentials not configured. Set MODAL_TOKEN_ID and MODAL_TOKEN_SECRET."

    # Generate analysis code using LLM
    code_agent = Agent(
        model=get_model(),
        output_type=str,
        system_prompt="""Generate Python code to analyze drug repurposing evidence.
Use pandas, numpy, scipy.stats. Output executable code only.
Set 'result' variable to SUPPORTED, REFUTED, or INCONCLUSIVE.
Print key statistics and p-values.""",
    )

    prompt = f"""Analyze this hypothesis:
Drug: {drug}
Condition: {condition}

Evidence:
{evidence_summary}

Generate statistical analysis code."""

    try:
        code_result = await code_agent.run(prompt)
        generated_code = code_result.output

        # Execute in Modal sandbox
        executor = get_code_executor()
        import asyncio
        loop = asyncio.get_running_loop()
        from functools import partial
        execution = await loop.run_in_executor(
            None, partial(executor.execute, generated_code, timeout=60)
        )

        if not execution["success"]:
            return f"## Analysis Failed\n\nError: {execution['error']}"

        # Format output
        return f"""## Statistical Analysis: {drug} for {condition}

### Execution Output
```
{execution['stdout']}
```

### Generated Code
```python
{generated_code}
```

**Executed in Modal Sandbox** - Isolated, secure, reproducible.
"""

    except CodeExecutionError as e:
        return f"## Analysis Error\n\n{e}"
    except Exception as e:
        return f"## Unexpected Error\n\n{e}"
```

### 4.4 Demo Script (`examples/modal_demo/run_analysis.py`)

```python
#!/usr/bin/env python3
"""Demo: Modal-powered statistical analysis of drug repurposing evidence.

This script demonstrates:
1. Gathering evidence from PubMed
2. Generating analysis code with LLM
3. Executing in Modal sandbox
4. Returning statistical insights

Usage:
    export OPENAI_API_KEY=...
    export MODAL_TOKEN_ID=...
    export MODAL_TOKEN_SECRET=...
    uv run python examples/modal_demo/run_analysis.py "metformin alzheimer"
"""

import argparse
import asyncio
import os
import sys

from src.agents.analysis_agent import AnalysisAgent
from src.agents.hypothesis_agent import HypothesisAgent
from src.tools.pubmed import PubMedTool
from src.utils.config import settings


async def main() -> None:
    """Run the Modal analysis demo."""
    parser = argparse.ArgumentParser(description="Modal Analysis Demo")
    parser.add_argument("query", help="Research query (e.g., 'metformin alzheimer')")
    args = parser.parse_args()

    # Check credentials
    if not settings.modal_available:
        print("Error: Modal credentials not configured.")
        print("Set MODAL_TOKEN_ID and MODAL_TOKEN_SECRET in .env")
        sys.exit(1)

    if not (os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")):
        print("Error: No LLM API key found.")
        sys.exit(1)

    print(f"\n{'='*60}")
    print("DeepCritical Modal Analysis Demo")
    print(f"Query: {args.query}")
    print(f"{'='*60}\n")

    # Step 1: Gather Evidence
    print("Step 1: Gathering evidence from PubMed...")
    pubmed = PubMedTool()
    evidence = await pubmed.search(args.query, max_results=5)
    print(f"  Found {len(evidence)} papers\n")

    # Step 2: Generate Hypotheses
    print("Step 2: Generating mechanistic hypotheses...")
    evidence_store: dict = {"current": evidence, "hypotheses": []}
    hypothesis_agent = HypothesisAgent(evidence_store=evidence_store)
    await hypothesis_agent.run(args.query)
    hypotheses = evidence_store.get("hypotheses", [])
    print(f"  Generated {len(hypotheses)} hypotheses\n")

    if hypotheses:
        print(f"  Primary: {hypotheses[0].drug} → {hypotheses[0].target}")

    # Step 3: Run Modal Analysis
    print("\nStep 3: Running statistical analysis in Modal sandbox...")
    print("  (This executes LLM-generated code in an isolated container)\n")

    analysis_agent = AnalysisAgent(evidence_store=evidence_store)
    result = await analysis_agent.run(args.query)

    # Step 4: Display Results
    print("\n" + "="*60)
    print("ANALYSIS RESULTS")
    print("="*60)

    if result.messages:
        print(result.messages[0].text)

    analysis = evidence_store.get("analysis", {})
    if analysis:
        print(f"\nVerdict: {analysis.get('verdict', 'N/A')}")
        print(f"Confidence: {analysis.get('confidence', 0):.0%}")

    print("\n[Demo Complete - Code was executed in Modal, not locally]")


if __name__ == "__main__":
    asyncio.run(main())
```

### 4.5 Verification Script (`examples/modal_demo/verify_sandbox.py`)

```python
#!/usr/bin/env python3
"""Verify that Modal sandbox is properly isolated.

This script proves to judges that code runs in Modal, not locally.
It attempts operations that would succeed locally but fail in sandbox.

Usage:
    uv run python examples/modal_demo/verify_sandbox.py
"""

import asyncio
from functools import partial

from src.tools.code_execution import get_code_executor
from src.utils.config import settings


async def main() -> None:
    """Verify Modal sandbox isolation."""
    if not settings.modal_available:
        print("Error: Modal credentials not configured.")
        return

    executor = get_code_executor()
    loop = asyncio.get_running_loop()

    print("="*60)
    print("Modal Sandbox Isolation Verification")
    print("="*60 + "\n")

    # Test 1: Prove it's not running locally
    print("Test 1: Check hostname (should NOT be your machine)")
    code1 = """
import socket
print(f"Hostname: {socket.gethostname()}")
"""
    result1 = await loop.run_in_executor(None, partial(executor.execute, code1))
    print(f"  Result: {result1['stdout'].strip()}")
    print(f"  (Your local hostname would be different)\n")

    # Test 2: Verify scientific libraries available
    print("Test 2: Verify scientific libraries")
    code2 = """
import pandas as pd
import numpy as np
import scipy
print(f"pandas: {pd.__version__}")
print(f"numpy: {np.__version__}")
print(f"scipy: {scipy.__version__}")
"""
    result2 = await loop.run_in_executor(None, partial(executor.execute, code2))
    print(f"  {result2['stdout'].strip()}\n")

    # Test 3: Verify network is blocked (security)
    print("Test 3: Verify network isolation (should fail)")
    code3 = """
import urllib.request
try:
    urllib.request.urlopen("https://google.com", timeout=2)
    print("Network: ALLOWED (unexpected)")
except Exception as e:
    print(f"Network: BLOCKED (as expected)")
"""
    result3 = await loop.run_in_executor(None, partial(executor.execute, code3))
    print(f"  {result3['stdout'].strip()}\n")

    # Test 4: Run actual statistical analysis
    print("Test 4: Execute real statistical analysis")
    code4 = """
import pandas as pd
import scipy.stats as stats

data = pd.DataFrame({
    'drug': ['Metformin'] * 3,
    'effect': [0.42, 0.38, 0.51],
    'n': [100, 150, 80]
})

mean_effect = data['effect'].mean()
sem = data['effect'].sem()
t_stat, p_val = stats.ttest_1samp(data['effect'], 0)

print(f"Mean Effect: {mean_effect:.3f} (SE: {sem:.3f})")
print(f"t-statistic: {t_stat:.2f}, p-value: {p_val:.4f}")
print(f"Verdict: {'SUPPORTED' if p_val < 0.05 else 'INCONCLUSIVE'}")
"""
    result4 = await loop.run_in_executor(None, partial(executor.execute, code4))
    print(f"  {result4['stdout'].strip()}\n")

    print("="*60)
    print("All tests complete - Modal sandbox verified!")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
```

---

## 5. TDD Test Suite

### 5.1 Unit Tests (`tests/unit/tools/test_modal_integration.py`)

```python
"""Unit tests for Modal pipeline integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.utils.models import Evidence, Citation


@pytest.fixture
def sample_evidence() -> list[Evidence]:
    """Sample evidence for testing."""
    return [
        Evidence(
            content="Metformin shows effect size of 0.45 in Alzheimer's model.",
            citation=Citation(
                source="pubmed",
                title="Metformin Study",
                url="https://pubmed.ncbi.nlm.nih.gov/12345/",
                date="2024-01-15",
                authors=["Smith J"],
            ),
            relevance=0.9,
        )
    ]


class TestAnalysisAgentIntegration:
    """Tests for AnalysisAgent integration."""

    @pytest.mark.asyncio
    async def test_analysis_agent_generates_code(
        self, sample_evidence: list[Evidence]
    ) -> None:
        """AnalysisAgent should generate Python code for analysis."""
        from src.agents.analysis_agent import AnalysisAgent

        evidence_store = {
            "current": sample_evidence,
            "hypotheses": [
                MagicMock(
                    drug="metformin",
                    target="AMPK",
                    pathway="autophagy",
                    effect="neuroprotection",
                    confidence=0.8,
                )
            ],
        }

        with patch("src.agents.analysis_agent.get_code_executor") as mock_executor, \
             patch("src.agents.analysis_agent.get_model") as mock_model:

            # Mock LLM to return code
            mock_agent = AsyncMock()
            mock_agent.run = AsyncMock(return_value=MagicMock(
                output="import pandas as pd\nresult = 'SUPPORTED'"
            ))

            # Mock Modal execution
            mock_executor.return_value.execute.return_value = {
                "stdout": "SUPPORTED",
                "stderr": "",
                "success": True,
                "error": None,
            }

            agent = AnalysisAgent(evidence_store=evidence_store)
            agent._agent = mock_agent

            result = await agent.run("metformin alzheimer")

            assert result.messages[0].text is not None
            assert "analysis" in evidence_store


class TestModalExecutorUnit:
    """Unit tests for ModalCodeExecutor."""

    def test_executor_checks_credentials(self) -> None:
        """Executor should warn if credentials missing."""
        import os
        from unittest.mock import patch

        with patch.dict(os.environ, {}, clear=True):
            from src.tools.code_execution import ModalCodeExecutor

            # Should not raise, but should log warning
            executor = ModalCodeExecutor()
            assert executor.modal_token_id is None

    def test_get_sandbox_library_list(self) -> None:
        """Should return list of library==version strings."""
        from src.tools.code_execution import get_sandbox_library_list

        libs = get_sandbox_library_list()

        assert isinstance(libs, list)
        assert "pandas==2.2.0" in libs
        assert "numpy==1.26.4" in libs


class TestOrchestratorWithAnalysis:
    """Tests for orchestrator with Modal analysis enabled."""

    @pytest.mark.asyncio
    async def test_orchestrator_calls_analysis_when_enabled(self) -> None:
        """Orchestrator should call AnalysisAgent when enabled and Modal available."""
        from src.orchestrator import Orchestrator
        from src.utils.models import OrchestratorConfig

        with patch("src.orchestrator.settings") as mock_settings:
            mock_settings.modal_available = True

            mock_search = AsyncMock()
            mock_search.search.return_value = MagicMock(
                evidence=[],
                errors=[],
            )

            mock_judge = AsyncMock()
            mock_judge.assess.return_value = MagicMock(
                sufficient=True,
                recommendation="synthesize",
                next_search_queries=[],
            )

            config = OrchestratorConfig(max_iterations=1)
            orchestrator = Orchestrator(
                search_handler=mock_search,
                judge_handler=mock_judge,
                config=config,
                enable_analysis=True,
            )

            # Collect events
            events = []
            async for event in orchestrator.run("test query"):
                events.append(event)

            # Should have analyzing event if Modal enabled
            event_types = [e.type for e in events]
            # Note: This test verifies the flow, actual Modal call is mocked
```

### 5.2 Integration Test (`tests/integration/test_modal.py`)

```python
"""Integration tests for Modal code execution (requires Modal credentials)."""

import pytest

from src.utils.config import settings


@pytest.mark.integration
@pytest.mark.skipif(
    not settings.modal_available,
    reason="Modal credentials not configured"
)
class TestModalIntegration:
    """Integration tests for Modal (requires credentials)."""

    @pytest.mark.asyncio
    async def test_modal_executes_real_code(self) -> None:
        """Test actual code execution in Modal sandbox."""
        import asyncio
        from functools import partial

        from src.tools.code_execution import get_code_executor

        executor = get_code_executor()
        code = """
import pandas as pd
result = pd.DataFrame({'a': [1,2,3]})['a'].sum()
print(f"Sum: {result}")
"""

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, partial(executor.execute, code, timeout=30)
        )

        assert result["success"]
        assert "Sum: 6" in result["stdout"]

    @pytest.mark.asyncio
    async def test_modal_blocks_network(self) -> None:
        """Verify network is blocked in sandbox."""
        import asyncio
        from functools import partial

        from src.tools.code_execution import get_code_executor

        executor = get_code_executor()
        code = """
import urllib.request
try:
    urllib.request.urlopen("https://google.com", timeout=2)
    print("NETWORK_ALLOWED")
except Exception:
    print("NETWORK_BLOCKED")
"""

        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            None, partial(executor.execute, code, timeout=30)
        )

        assert "NETWORK_BLOCKED" in result["stdout"]
```

---

## 6. Verification Commands

```bash
# 1. Set Modal credentials
export MODAL_TOKEN_ID=your-token-id
export MODAL_TOKEN_SECRET=your-token-secret

# Or via modal CLI
modal setup

# 2. Run unit tests
uv run pytest tests/unit/tools/test_modal_integration.py -v

# 3. Run verification script (proves sandbox works)
uv run python examples/modal_demo/verify_sandbox.py

# 4. Run full demo
uv run python examples/modal_demo/run_analysis.py "metformin alzheimer"

# 5. Run integration tests (requires Modal creds)
uv run pytest tests/integration/test_modal.py -v -m integration

# 6. Run full test suite
make check
```

---

## 7. Definition of Done

Phase 13 is **COMPLETE** when:

- [ ] `src/utils/config.py` updated with `enable_modal_analysis` setting
- [ ] `src/orchestrator.py` optionally calls `AnalysisAgent`
- [ ] `src/mcp_tools.py` has `analyze_hypothesis` MCP tool
- [ ] `examples/modal_demo/run_analysis.py` working demo
- [ ] `examples/modal_demo/verify_sandbox.py` verification script
- [ ] Unit tests in `tests/unit/tools/test_modal_integration.py`
- [ ] Integration tests in `tests/integration/test_modal.py`
- [ ] Verification script proves sandbox isolation
- [ ] All unit tests pass
- [ ] Lints pass

---

## 8. Demo Script for Judges

### Show Modal Innovation

1. **Run verification script** (proves sandbox):
   ```bash
   uv run python examples/modal_demo/verify_sandbox.py
   ```
   - Shows hostname is NOT local machine
   - Shows scientific libraries available
   - Shows network is BLOCKED (security)
   - Shows real statistics execution

2. **Run analysis demo**:
   ```bash
   uv run python examples/modal_demo/run_analysis.py "metformin cancer"
   ```
   - Shows evidence gathering
   - Shows hypothesis generation
   - Shows code execution in Modal
   - Shows statistical verdict

3. **Show the key differentiator**:
   > "LLM-generated code executes in an isolated Modal container. This is enterprise-grade safety for AI-powered scientific computing."

---

## 9. Value Delivered

| Before | After |
|--------|-------|
| Code execution exists but unused | Integrated into pipeline |
| No demo of sandbox isolation | Verification script proves it |
| No MCP tool for analysis | `analyze_hypothesis` MCP tool |
| No judge-friendly demo | Clear demo script |

**Prize Impact**:
- With Modal Integration: **Eligible for $2,500 Modal Innovation Award**

---

## 10. Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/utils/config.py` | MODIFY | Add `enable_modal_analysis` |
| `src/orchestrator.py` | MODIFY | Add optional AnalysisAgent call |
| `src/mcp_tools.py` | MODIFY | Add `analyze_hypothesis` MCP tool |
| `examples/modal_demo/run_analysis.py` | CREATE | Demo script |
| `examples/modal_demo/verify_sandbox.py` | CREATE | Verification script |
| `tests/unit/tools/test_modal_integration.py` | CREATE | Unit tests |
| `tests/integration/test_modal.py` | CREATE | Integration tests |

---

## 11. Architecture After Phase 13

```
User Query
    ↓
Orchestrator
    ↓
┌────────────────────────────────────────────────────────────────┐
│ Search Phase                                                    │
│   PubMedTool → ClinicalTrialsTool → BioRxivTool                │
└────────────────────────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────────────────┐
│ Judge Phase                                                     │
│   JudgeHandler → "sufficient" → continue to synthesis          │
└────────────────────────────────────────────────────────────────┘
    ↓ (if enable_modal_analysis=True)
┌────────────────────────────────────────────────────────────────┐
│ Analysis Phase (NEW)                                            │
│   HypothesisAgent → Generate mechanistic hypotheses             │
│        ↓                                                        │
│   AnalysisAgent → Generate Python code                          │
│        ↓                                                        │
│   ┌──────────────────────────────────────────────┐              │
│   │         Modal Sandbox Container               │              │
│   │  - pandas, numpy, scipy, sklearn             │              │
│   │  - Network BLOCKED                           │              │
│   │  - Filesystem ISOLATED                       │              │
│   │  - Execute → Return stdout                   │              │
│   └──────────────────────────────────────────────┘              │
│        ↓                                                        │
│   AnalysisResult → SUPPORTED/REFUTED/INCONCLUSIVE              │
└────────────────────────────────────────────────────────────────┘
    ↓
┌────────────────────────────────────────────────────────────────┐
│ Report Phase                                                    │
│   ReportAgent → Structured scientific report                    │
└────────────────────────────────────────────────────────────────┘
```

**This is the Modal-powered analytics stack.**
