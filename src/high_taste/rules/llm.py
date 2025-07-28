"""AI agent for converting markdown rules to YAML format."""

import logging
import os

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.settings import ModelSettings

from .prompt import RULE_DETAILS_PROMPT, SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class RuleExample(BaseModel):
    scenario: str
    before: str
    after: str


class Rule(BaseModel):
    category: str
    title: str
    id: str
    description: str
    problems: list[str]
    solutions: list[str]
    examples: list[RuleExample]


async def agent_run(prompt: str) -> Rule:
    """Initialize and return the AI agent."""
    assert os.getenv("ANTHROPIC_API_KEY"), (
        "ANTHROPIC_API_KEY environment variable is required"
    )
    
    logger.info("Starting agent_run with prompt length: %d characters", len(prompt))
    logger.debug("Prompt preview: \n%s\n\n", prompt)
    
    model = AnthropicModel("anthropic:claude-sonnet-4-latest")
    agent = Agent(
        model,
        output_type=Rule,
        system_prompt=SYSTEM_PROMPT,
    )
    
    logger.info("Sending request to Claude API...")
    result = await agent.run(
        prompt, model_settings=ModelSettings(temperature=0.2, max_tokens=8000)
    )
    
    logger.info("Received response from Claude API")
    logger.debug("Generated rule title: %s", result.output.title)
    logger.debug("Generated rule ID: %s", result.output.id)
    logger.debug("Number of examples: %d", len(result.output.examples))
    
    return result.output

if __name__ == "__main__":
    import asyncio

    # Render a sample prompt for testing, make sure use `prompt.RULE_DETAILS_PROMPT`
    example_prompt = f"""
    {RULE_DETAILS_PROMPT}

    The rule to convert is:
    Dynamic Data Discovery vs Hardcoded Lists

    Hardcoded lists of data that should be discovered dynamically:

    - Require manual updates when new items are added
    - Become stale and out of sync with actual data
    - Create bugs when developers forget to update lists
    - Make code fragile to changes in data structure
    """
    rule = asyncio.run(agent_run(example_prompt))
    print(f"Generated rule: {rule.title} (ID: {rule.id})")
