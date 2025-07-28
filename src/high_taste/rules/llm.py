"""AI agent for converting markdown rules to YAML format."""

imort asyncio
import os

from loguru import logger
from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.models.anthropic import AnthropicModel
from pydantic_ai.settings import ModelSettings

from .prompt import RULE_DETAILS_PROMPT, SYSTEM_PROMPT


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
    
    model = AnthropicModel("claude-sonnet-4-20250514")
    agent = Agent(
        model,
        output_type=Rule,
        system_prompt=SYSTEM_PROMPT,
    )
    
    logger.info("Sending streaming request to Claude API...")
    logger.debug("Prompt being sent: \n{}\n\n", prompt)
    async with agent.run_stream(
        prompt, model_settings=ModelSettings(temperature=0.2, max_tokens=8000)
    ) as result:
        # Process the streaming structured output
        async for partial in result.stream_structured():
            if partial is not None:
                logger.debug("Received partial structured data: {}", type(partial))
        
        # Get the final result
        final_result = await result.get_output()
    
    logger.info("Received complete response from Claude API")
    logger.debug("Generated rule title: {}", final_result.title)
    logger.debug("Generated rule ID: {}", final_result.id)
    logger.debug("Number of examples: {}", len(final_result.examples))
    
    return final_result

if __name__ == "__main__":
    import asyncio
    
    # Enable logging for the main execution
    logger.enable("high_taste")

    example_prompt = f"""
    {RULE_DETAILS_PROMPT}

    Produce a yaml output for the following rule:

    Dynamic Data Discovery vs Hardcoded Lists

    Hardcoded lists of data that should be discovered dynamically:

    - Require manual updates when new items are added
    - Become stale and out of sync with actual data
    - Create bugs when developers forget to update lists
    - Make code fragile to changes in data structure
    """
    logger.info("Running agent with prompt: \n{}", example_prompt.strip())
    rule = asyncio.run(agent_run(example_prompt))
    logger.info("Generated rule: {} (ID: {})", rule.title, rule.id)
    logger.info("Rule JSON: {}", rule.model_dump_json(indent=2))
