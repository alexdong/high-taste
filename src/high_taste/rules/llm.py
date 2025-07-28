"""AI agent for converting markdown rules to YAML format."""

import os

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel


class RuleExample(BaseModel):
    scenario: str
    before: str
    after: str


class Rule(BaseModel):
    title: str
    id: str
    description: str
    problems: list[str]
    solutions: list[str]
    examples: list[RuleExample]


def get_ai_agent(system_prompt: str) -> Agent:
    """Initialize and return the AI agent."""
    assert os.getenv("ANTHROPIC_API_KEY"), (
        "ANTHROPIC_API_KEY environment variable is required"
    )
    model = AnthropicModel("anthropic:claude-sonnet-4-latest")
    return Agent(
        model,
        result_type=Rule,
        system_prompt=system_prompt,
    )
