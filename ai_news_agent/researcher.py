import json
import logging
from datetime import date, timedelta
from typing import Any

import anthropic
from pydantic import BaseModel, ValidationError

from .prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class NewsItem(BaseModel):
    category: str
    title: str
    organization: str
    url: str
    published_date: str
    summary_es: str
    why_it_matters_es: str
    importance: int


OUTPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "enum": ["academic", "big_tech", "papers", "media"],
                    },
                    "title": {"type": "string"},
                    "organization": {"type": "string"},
                    "url": {"type": "string", "format": "uri"},
                    "published_date": {"type": "string", "format": "date"},
                    "summary_es": {"type": "string"},
                    "why_it_matters_es": {"type": "string"},
                    "importance": {"type": "integer", "enum": [1, 2, 3, 4, 5]},
                },
                "required": [
                    "category",
                    "title",
                    "organization",
                    "url",
                    "published_date",
                    "summary_es",
                    "why_it_matters_es",
                    "importance",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["items"],
    "additionalProperties": False,
}


def run(
    *,
    lookback_days: int = 7,
    min_items: int = 12,
    max_items: int = 18,
    model: str = "claude-sonnet-4-6",
    max_continuations: int = 6,
) -> tuple[list[NewsItem], date, date]:
    client = anthropic.Anthropic()
    today = date.today()
    since = today - timedelta(days=lookback_days)

    system_blocks = [
        {
            "type": "text",
            "text": SYSTEM_PROMPT.replace("{lookback_days}", str(lookback_days)),
            "cache_control": {"type": "ephemeral"},
        }
    ]

    user_text = USER_PROMPT_TEMPLATE.format(
        today=today.isoformat(),
        since_date=since.isoformat(),
        lookback_days=lookback_days,
        min_items=min_items,
        max_items=max_items,
    )

    messages: list[dict[str, Any]] = [{"role": "user", "content": user_text}]

    tools = [
        {"type": "web_search_20260209", "name": "web_search"},
        {"type": "web_fetch_20260209", "name": "web_fetch"},
    ]

    response = None
    for iteration in range(1, max_continuations + 1):
        logger.info("Calling model (iteration %d)...", iteration)

        with client.messages.stream(
            model=model,
            max_tokens=32000,
            system=system_blocks,
            messages=messages,
            tools=tools,
            thinking={"type": "adaptive"},
            output_config={
                "format": {"type": "json_schema", "schema": OUTPUT_SCHEMA},
                "effort": "high",
            },
        ) as stream:
            response = stream.get_final_message()

        logger.info(
            "iter=%d stop_reason=%s input=%d output=%d cache_read=%d",
            iteration,
            response.stop_reason,
            response.usage.input_tokens,
            response.usage.output_tokens,
            response.usage.cache_read_input_tokens or 0,
        )

        if response.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": response.content})
            continue
        break

    if response is None:
        raise RuntimeError("No response from model")

    if response.stop_reason == "refusal":
        raise RuntimeError("Model refused to generate the news brief")

    text_block = next((b for b in response.content if b.type == "text"), None)
    if text_block is None:
        raise RuntimeError("No text block in final response")

    raw_text = text_block.text.strip()
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON. Raw start: %s", raw_text[:500])
        raise

    items: list[NewsItem] = []
    for raw_item in data.get("items", []):
        try:
            items.append(NewsItem(**raw_item))
        except ValidationError as e:
            logger.warning("Skipping invalid item %r: %s", raw_item.get("title"), e)

    items.sort(key=lambda i: (i.importance, i.published_date), reverse=True)
    return items, since, today
