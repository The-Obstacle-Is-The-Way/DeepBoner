"""Graph node implementations for DeepBoner research."""

import asyncio
from typing import Any, Literal

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from src.agents.graph.state import Hypothesis, ResearchState
from src.tools.clinicaltrials import ClinicalTrialsTool
from src.tools.europepmc import EuropePMCTool
from src.tools.pubmed import PubMedTool


# --- Supervisor Output Schema ---
class SupervisorDecision(BaseModel):
    """The decision made by the supervisor."""

    next_step: Literal["search", "judge", "resolve", "synthesize", "finish"] = Field(
        description="The next step to take in the research process."
    )
    reasoning: str = Field(description="Reasoning for this decision.")


# --- Nodes ---


async def search_node(state: ResearchState) -> dict[str, Any]:
    """Execute search across all sources."""
    query = state["query"]

    # Initialize tools
    pubmed = PubMedTool()
    ct = ClinicalTrialsTool()
    epmc = EuropePMCTool()

    # Parallel search
    # Note: Tools return list[Evidence]
    results = await asyncio.gather(
        pubmed.search(query), ct.search(query), epmc.search(query), return_exceptions=True
    )

    # new_evidence_ids = []
    count = 0

    # Process results (flatten and handle errors)
    for res in results:
        if isinstance(res, list):
            # In a real impl, we would store these in ChromaDB here
            # and just track IDs. For now, we'll just count them.
            # state["evidence_ids"] would act as pointers.
            # For this demo, let's assume we just log the count.
            count += len(res)
        else:
            # Log error?
            pass

    return {
        "messages": [AIMessage(content=f"Search completed. Found {count} new papers.")],
        # In real impl: "evidence_ids": new_ids
    }


async def judge_node(state: ResearchState) -> dict[str, Any]:
    """Evaluate evidence and update hypothesis confidence."""
    # TODO: Implement actual LLM judging logic
    # For now, we simulate a judge finding a conflict or confirming a hypothesis

    # Simulation: If no hypotheses, propose one
    if not state["hypotheses"]:
        new_hypo = Hypothesis(
            id="h1",
            statement=f"Hypothesis derived from {state['query']}",
            status="proposed",
            confidence=0.5,
        )
        return {
            "hypotheses": [new_hypo],
            "messages": [AIMessage(content="Judge: Proposed initial hypothesis.")],
        }

    # Simulation: Update confidence
    return {"messages": [AIMessage(content="Judge: Evaluated evidence. Confidence updated.")]}


async def resolve_node(state: ResearchState) -> dict[str, Any]:
    """Handle open conflicts."""
    # TODO: Implement conflict resolution logic
    return {"messages": [AIMessage(content="Resolver: Attempted to resolve conflicts.")]}


async def synthesize_node(state: ResearchState) -> dict[str, Any]:
    """Generate final report."""
    # TODO: Implement report generation
    return {
        "messages": [AIMessage(content="# Final Report\n\nResearch complete.")],
        "next_step": "finish",
    }


async def supervisor_node(state: ResearchState, llm: BaseChatModel | None = None) -> dict[str, Any]:
    """Route to next node based on state using robust Pydantic parsing.

    Args:
        state: Current graph state
        llm: The language model to use (injected at runtime)
    """
    # Hard termination check
    if state["iteration_count"] >= state["max_iterations"]:
        return {"next_step": "synthesize", "iteration_count": state["iteration_count"]}

    if llm is None:
        # Fallback for tests/default
        return {"next_step": "search", "iteration_count": state["iteration_count"] + 1}

    parser = PydanticOutputParser(pydantic_object=SupervisorDecision)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are the Research Supervisor. Manage the workflow.\n\n"
                "State Summary:\n"
                "- Query: {query}\n"
                "- Hypotheses: {hypo_count}\n"
                "- Conflicts: {conflict_count}\n"
                "- Iteration: {iteration}/{max_iter}\n\n"
                "Decide the next step based on this logic:\n"
                "1. If there are open conflicts -> 'resolve'\n"
                "2. If hypotheses are unverified or few -> 'search'\n"
                "3. If new evidence needs evaluation -> 'judge'\n"
                "4. If hypotheses are confirmed -> 'synthesize'\n\n"
                "{format_instructions}",
            ),
            ("user", "What is the next step?"),
        ]
    )

    chain = prompt | llm | parser

    try:
        decision: SupervisorDecision = await chain.ainvoke(
            {
                "query": state["query"],
                "hypo_count": len(state["hypotheses"]),
                "conflict_count": len([c for c in state["conflicts"] if c.status == "open"]),
                "iteration": state["iteration_count"],
                "max_iter": state["max_iterations"],
                "format_instructions": parser.get_format_instructions(),
            }
        )
        return {
            "next_step": decision.next_step,
            "iteration_count": state["iteration_count"] + 1,
            "messages": [AIMessage(content=f"Supervisor: {decision.reasoning}")],
        }
    except Exception as e:
        # Fallback on error (e.g. parsing failure)
        # We default to 'judge' if we have data, or 'synthesize' if we are stuck
        return {
            "next_step": "synthesize",  # Fail safe
            "iteration_count": state["iteration_count"] + 1,
            "messages": [AIMessage(content=f"Supervisor Error: {e!s}. Proceeding to synthesis.")],
        }
