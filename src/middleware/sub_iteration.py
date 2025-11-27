"""Middleware for managing sub-iterations/research teams."""

import structlog
from typing import Any

from agent_framework import BaseAgent, ChatMessage, Role

logger = structlog.get_logger(__name__)


class ResearchTeam:
    """Represents a team of agents working on a sub-task (sub-iteration)."""

    def __init__(
        self,
        name: str,
        agents: list[BaseAgent],
        judge: BaseAgent | None = None,
        max_iterations: int = 3,
    ) -> None:
        """Initialize research team.

        Args:
            name: Team name
            agents: List of agents in the team
            judge: Optional judge agent to evaluate progress
            max_iterations: Maximum iterations for the loop
        """
        self.name = name
        self.agents = agents
        self.judge = judge
        self.max_iterations = max_iterations

    async def run(self, task: str) -> str:
        """Run the research team loop."""
        logger.info("starting_research_team", team=self.name, task=task)

        context = [ChatMessage(role=Role.USER, text=f"Task for {self.name}: {task}")]

        for i in range(self.max_iterations):
            logger.info("team_iteration", team=self.name, iteration=i+1)

            # Run each agent in sequence
            for agent in self.agents:
                # Pass the conversation history
                response = await agent.run(context)

                # Append result to context
                if response.messages:
                    # Assume last message is the response
                    msg = response.messages[-1]
                    # Ensure role is proper (it comes as ASSISTANT usually)
                    # We might want to label it with agent name in the text context if sharing history?
                    # But ChatMessage doesn't have 'name' field in standard framework usually,
                    # but we can prefix text.

                    # For simple sequential chat:
                    context.append(msg)
                    logger.info("agent_completed", team=self.name, agent=agent.name)

            # Judge evaluation
            if self.judge:
                # Judge sees the context and decides
                # We need to construct a prompt for the judge
                judge_prompt = (
                    f"Evaluate the progress of the team on task: {task}\n\n"
                    "Is the information collected sufficient? Reply with SUFFICIENT or CONTINUE."
                )
                # Judge needs to see context.
                # We can pass context + prompt.
                judge_context = list(context)
                judge_context.append(ChatMessage(role=Role.USER, text=judge_prompt))

                judge_response = await self.judge.run(judge_context)
                verdict = judge_response.messages[-1].text if judge_response.messages else ""

                context.append(judge_response.messages[-1])

                logger.info("team_judge_verdict", team=self.name, verdict=verdict)

                if "SUFFICIENT" in verdict.upper():
                    return self._format_result(context, verdict)

        return self._format_result(context, "Max iterations reached")

    def _format_result(self, messages: list[ChatMessage], status: str) -> str:
        """Format the team's output."""
        output = [f"## Team {self.name} Output ({status})"]
        for msg in messages:
            if msg.role == Role.ASSISTANT:
                output.append(f"{msg.text}")
        return "\n\n".join(output)
