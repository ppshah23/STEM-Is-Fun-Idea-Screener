import json
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from . import mock

load_dotenv(Path(__file__).parent.parent / ".env")

MOCK_MODE = os.environ.get("MOCK_MODE") == "1"
client = None if MOCK_MODE else anthropic.Anthropic()
MODEL = "claude-opus-5"


WEB_SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search", "max_uses": 5}


def run_skill(
    skill_text: str,
    task: str,
    context: dict,
    effort: str = "high",
    output_schema: dict | None = None,
    web_search: bool = False,
) -> dict:
    """
    Run one agentic step.

    skill_text: the expert playbook (stable across calls -> cached)
    task: the instruction for this specific call
    context: the volatile data (course, persona, prior artifacts) to reason over
    effort: "low" | "medium" | "high" | "xhigh" | "max" -- tune per step
    output_schema: optional JSON Schema (see pipeline/schemas.py) -- when given,
        the API enforces it, so the response is guaranteed valid JSON matching
        the shape. When omitted, falls back to a plain-text instruction and the
        response is only best-effort parsed.
    web_search: when True, gives Claude the server-side web_search tool (e.g. to
        look up real hardware part links). Runs entirely server-side -- no
        client-side tool loop needed here.
    """
    if MOCK_MODE:
        if output_schema is None:
            return {"mock": True, "note": "MOCK_MODE has no schema for this call."}
        return mock.generate_mock(output_schema)

    output_config = {"effort": effort}
    if output_schema is not None:
        output_config["format"] = {"type": "json_schema", "schema": output_schema}

    task_text = f"{task}\n\nContext:\n{json.dumps(context, indent=2)}"
    if output_schema is None:
        task_text += "\n\nRespond with a single JSON object only -- no prose, no markdown fences."

    stream_kwargs = dict(
        model=MODEL,
        max_tokens=64000,
        system=[
            {
                "type": "text",
                "text": skill_text,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        thinking={"type": "adaptive"},
        output_config=output_config,
        messages=[{"role": "user", "content": task_text}],
    )
    if web_search:
        stream_kwargs["tools"] = [WEB_SEARCH_TOOL]

    with client.messages.stream(**stream_kwargs) as stream:
        response = stream.get_final_message()

    if response.stop_reason == "max_tokens":
        raise RuntimeError(
            "Claude response was truncated at max_tokens -- output was still incomplete "
            "even at the raised limit. Increase max_tokens further or shorten the task."
        )

    # With web_search on, Claude may emit intermediate text (or search-result
    # commentary) before its final structured answer -- take the LAST text
    # block, not the first, so a mid-search aside can't be mistaken for the
    # final JSON.
    text_blocks = [b.text for b in response.content if b.type == "text"]
    if not text_blocks:
        raise ValueError("Claude's response had no text content to parse as JSON.")
    text = text_blocks[-1]
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        window = text[max(0, e.pos - 200) : e.pos + 200]
        raise ValueError(
            f"Claude's response wasn't valid JSON ({e.msg} at char {e.pos}).\n"
            f"Text around the failure:\n...{window}..."
        ) from e
