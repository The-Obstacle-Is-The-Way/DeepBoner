"""LangGraph-based orchestrator implementation."""

import os
from collections.abc import AsyncGenerator, AsyncIterator
from typing import Any, Literal

from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from src.agents.graph.state import ResearchState
from src.agents.graph.workflow import create_research_graph
from src.orchestrators.base import OrchestratorProtocol
from src.services.embeddings import EmbeddingService
from src.utils.config import settings
from src.utils.models import AgentEvent


class LangGraphOrchestrator(OrchestratorProtocol):
    """State-driven research orchestrator using LangGraph."""

    def __init__(
        self,
        max_iterations: int = 10,
        checkpoint_path: str | None = None,
    ):
        self._max_iterations = max_iterations
        self._checkpoint_path = checkpoint_path

        # Initialize the LLM (Llama 3.1 via HF Inference)
        # We use the serverless API by default
        repo_id = "meta-llama/Llama-3.1-70B-Instruct"

        # Ensure we have an API key
        api_key = settings.hf_token
        if not api_key:
            raise ValueError(
                "HF_TOKEN (Hugging Face API Token) is required for God Mode to use Llama 3.1."
            )

        self.llm_endpoint = HuggingFaceEndpoint(  # type: ignore
            repo_id=repo_id,
            task="text-generation",
            max_new_tokens=1024,
            temperature=0.1,
            huggingfacehub_api_token=api_key,
        )
        self.chat_model = ChatHuggingFace(llm=self.llm_endpoint)

    async def run(self, query: str) -> AsyncGenerator[AgentEvent, None]:
        """Execute research workflow with structured state."""
        # Initialize embedding service for this specific run (ensures isolation)
        embedding_service = EmbeddingService()

        # Setup checkpointer (SQLite for dev)
        if self._checkpoint_path:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self._checkpoint_path), exist_ok=True)
            saver = AsyncSqliteSaver.from_conn_string(self._checkpoint_path)
        else:
            saver = None

        # Use a helper context manager to handle the optional saver
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def get_graph_context(saver_instance: Any) -> AsyncIterator[Any]:
            if saver_instance:
                async with saver_instance as s:
                    yield create_research_graph(
                        llm=self.chat_model,
                        checkpointer=s,
                        embedding_service=embedding_service,
                    )
            else:
                yield create_research_graph(
                    llm=self.chat_model,
                    checkpointer=None,
                    embedding_service=embedding_service,
                )

        async with get_graph_context(saver) as graph:
            # Initialize state
            initial_state: ResearchState = {
                "query": query,
                "hypotheses": [],
                "conflicts": [],
                "evidence_ids": [],
                "messages": [],
                "next_step": "search",  # Start with search
                "iteration_count": 0,
                "max_iterations": self._max_iterations,
            }

            yield AgentEvent(type="started", message=f"Starting 'God Mode' research: {query}")

            # Config for persistence (thread_id required if checkpointer used)
            config = {"configurable": {"thread_id": "1"}} if saver else {}

            # Stream events
            # We use astream to get updates from the graph
            async for event in graph.astream(initial_state, config=config):
                # Event is a dict of node_name -> state_update
                for node_name, update in event.items():
                    if update.get("messages"):
                        last_msg = update["messages"][-1]
                        event_type: Literal["progress", "thinking", "searching"] = "progress"
                        if node_name == "supervisor":
                            event_type = "thinking"
                        elif node_name == "search":
                            event_type = "searching"

                        yield AgentEvent(
                            type=event_type, message=str(last_msg.content), data={"node": node_name}
                        )
                    elif node_name == "supervisor":
                        yield AgentEvent(
                            type="thinking",
                            message=f"Supervisor decided: {update.get('next_step')}",
                            data={"node": node_name},
                        )

            yield AgentEvent(type="complete", message="Research complete.")
