import logging

import anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


def make_system_block(text: str) -> dict:
    """Wrap a system prompt string in a cache-control block."""
    return {
        "type": "text",
        "text": text,
        "cache_control": {"type": "ephemeral"},
    }


async def call_claude(
    system: str,
    messages: list[dict],
    max_tokens: int = 2048,
    model: str = "claude-sonnet-4-6",
) -> tuple[str, dict]:
    """
    Call Claude with prompt caching on the system block.
    Returns (response_text, usage_dict).
    Logs cache hit/miss from the usage metadata.
    """
    client = get_client()

    response = await client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=[make_system_block(system)],
        messages=messages,
    )

    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "cache_creation_input_tokens": getattr(response.usage, "cache_creation_input_tokens", 0),
        "cache_read_input_tokens": getattr(response.usage, "cache_read_input_tokens", 0),
    }

    cache_read = usage["cache_read_input_tokens"]
    cache_created = usage["cache_creation_input_tokens"]

    if cache_read > 0:
        logger.info("Claude call — cache HIT (%d tokens read from cache)", cache_read)
    elif cache_created > 0:
        logger.info("Claude call — cache MISS (cache created, %d tokens)", cache_created)
    else:
        logger.info("Claude call — no cache activity")

    text = response.content[0].text
    return text, usage
