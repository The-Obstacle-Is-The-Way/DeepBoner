"""Factory for creating orchestrators.

Implements the Factory Pattern (GoF) for creating the appropriate
orchestrator based on configuration and available credentials.

Design Principles:
- Open/Closed: Easy to add new orchestrator types without modifying existing code
- Dependency Inversion: Returns protocol-compatible objects, not concrete types
- Single Responsibility: Only handles orchestrator creation logic
"""

from typing import Any, Literal

import structlog

from src.orchestrators.base import JudgeHandlerProtocol, SearchHandlerProtocol
from src.orchestrators.simple import Orchestrator
from src.utils.config import settings
from src.utils.models import OrchestratorConfig

logger = structlog.get_logger()


def _get_advanced_orchestrator_class() -> Any:
    """Import AdvancedOrchestrator lazily to avoid hard dependency.

    This allows the simple mode to work without agent-framework-core installed.
    """
    try:
        from src.orchestrators.advanced import AdvancedOrchestrator

        return AdvancedOrchestrator
    except ImportError as e:
        logger.error("Failed to import AdvancedOrchestrator", error=str(e))
        raise ValueError(
            "Advanced mode requires agent-framework-core. Please install it or use mode='simple'."
        ) from e


def create_orchestrator(
    search_handler: SearchHandlerProtocol | None = None,
    judge_handler: JudgeHandlerProtocol | None = None,
    config: OrchestratorConfig | None = None,
    mode: Literal["simple", "magentic", "advanced", "hierarchical"] | None = None,
    api_key: str | None = None,
) -> Any:
    """
    Create an orchestrator instance.

    This factory automatically selects the appropriate orchestrator based on:
    1. Explicit mode parameter (if provided)
    2. Available API keys (auto-detection)

    Args:
        search_handler: The search handler (required for simple mode)
        judge_handler: The judge handler (required for simple mode)
        config: Optional configuration
        mode: "simple", "magentic", "advanced", "hierarchical" or None (auto-detect)
              Note: "magentic" is an alias for "advanced" (kept for backwards compatibility)
        api_key: Optional API key for advanced mode (OpenAI)

    Returns:
        Orchestrator instance

    Raises:
        ValueError: If required handlers are missing for simple mode
        ValueError: If advanced mode is requested but dependencies are missing
    """
    effective_mode = _determine_mode(mode, api_key)
    logger.info("Creating orchestrator", mode=effective_mode)

    if effective_mode == "advanced":
        orchestrator_cls = _get_advanced_orchestrator_class()
        return orchestrator_cls(
            max_rounds=config.max_iterations if config else 10,
            api_key=api_key,
        )

    if effective_mode == "hierarchical":
        from src.orchestrators.hierarchical import HierarchicalOrchestrator

        return HierarchicalOrchestrator()

    # Simple mode requires handlers
    if search_handler is None or judge_handler is None:
        raise ValueError("Simple mode requires search_handler and judge_handler")

    return Orchestrator(
        search_handler=search_handler,
        judge_handler=judge_handler,
        config=config,
    )


def _determine_mode(explicit_mode: str | None, api_key: str | None) -> str:
    """Determine which mode to use.

    Priority:
    1. Explicit mode parameter
    2. Auto-detect based on available API keys

    Args:
        explicit_mode: Mode explicitly requested by caller
        api_key: API key provided by caller

    Returns:
        Effective mode string: "simple", "advanced", or "hierarchical"
    """
    if explicit_mode:
        if explicit_mode in ("magentic", "advanced"):
            return "advanced"
        if explicit_mode == "hierarchical":
            return "hierarchical"
        return "simple"

    # Auto-detect: advanced if paid API key available
    if settings.has_openai_key or (api_key and api_key.startswith("sk-")):
        return "advanced"

    return "simple"
