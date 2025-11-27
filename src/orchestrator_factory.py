"""Factory for creating orchestrators."""

from src.orchestrator import JudgeHandlerProtocol, Orchestrator, SearchHandlerProtocol
from src.utils.models import OrchestratorConfig


def create_orchestrator(
    search_handler: SearchHandlerProtocol,
    judge_handler: JudgeHandlerProtocol,
    config: OrchestratorConfig | None = None,
) -> Orchestrator:
    """
    Create an orchestrator instance.

    Args:
        search_handler: The search handler
        judge_handler: The judge handler
        config: Optional configuration

    Returns:
        Orchestrator instance
    """
    return Orchestrator(
        search_handler=search_handler,
        judge_handler=judge_handler,
        config=config,
    )
