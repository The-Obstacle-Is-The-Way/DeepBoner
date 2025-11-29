"""DeepBoner research workflow definition using LangGraph."""

from functools import partial
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.graph import END, StateGraph
from langgraph.graph.state import CompiledStateGraph

from src.agents.graph.nodes import (
    judge_node,
    resolve_node,
    search_node,
    supervisor_node,
    synthesize_node,
)
from src.agents.graph.state import ResearchState


def create_research_graph(
    llm: BaseChatModel | None = None, checkpointer: Any = None
) -> CompiledStateGraph:  # type: ignore
    """Build the research state graph.

    Args:
        llm: The language model for the supervisor node.
        checkpointer: Optional persistence layer.
    """
    graph = StateGraph(ResearchState)

    # --- Nodes ---
    # Bind the LLM to the supervisor node using partial
    # This injects the model dependency while keeping the node signature clean for the graph
    bound_supervisor = partial(supervisor_node, llm=llm) if llm else supervisor_node

    graph.add_node("supervisor", bound_supervisor)
    graph.add_node("search", search_node)
    graph.add_node("judge", judge_node)
    graph.add_node("resolve", resolve_node)
    graph.add_node("synthesize", synthesize_node)

    # --- Edges ---
    # All worker nodes report back to supervisor
    graph.add_edge("search", "supervisor")
    graph.add_edge("judge", "supervisor")
    graph.add_edge("resolve", "supervisor")

    # Synthesis is the end
    graph.add_edge("synthesize", END)

    # --- Conditional Routing ---
    # Supervisor decides where to go next based on state["next_step"]
    graph.add_conditional_edges(
        "supervisor",
        lambda state: state["next_step"],
        {
            "search": "search",
            "judge": "judge",
            "resolve": "resolve",
            "synthesize": "synthesize",
            "finish": END,
        },
    )

    # Entry Point
    graph.set_entry_point("supervisor")

    return graph.compile(checkpointer=checkpointer)
