"""Agent orchestrator. Runs the Claude tool-use loop and returns a structured Decision."""

import base64
import json
import os
import time
import uuid
from pathlib import Path
from typing import Literal, Optional

import anthropic
from pydantic import BaseModel, Field

from src.agent.prompts import SYSTEM_PROMPT
from src.agent.tools import TOOL_REGISTRY, TOOL_SCHEMAS

MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))


class Citation(BaseModel):
    source: Literal["certificate_field", "transaction", "state_rule"]
    reference_id: str
    excerpt: str


class Decision(BaseModel):
    decision: Literal["PASS", "FLAG", "NEEDS_REVIEW"]
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_summary: str
    citations: list[Citation]
    metadata: dict = {}


def _make_client() -> anthropic.Anthropic:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    return anthropic.Anthropic(api_key=api_key)


def _call_api_with_retry(client: anthropic.Anthropic, **kwargs) -> anthropic.types.Message:
    delay = 2
    for attempt in range(4):
        try:
            return client.messages.create(**kwargs)
        except anthropic.RateLimitError:
            time.sleep(30)
        except anthropic.APIStatusError as e:
            if e.status_code >= 500 and attempt < 3:
                time.sleep(delay)
                delay *= 2
            else:
                raise
        except anthropic.APIConnectionError:
            if attempt < 3:
                time.sleep(delay)
                delay *= 2
            else:
                raise
    return client.messages.create(**kwargs)


def _extract_decision_from_messages(messages: list[dict]) -> Optional[Decision]:
    """Scan message history for the most recent record_decision tool call."""
    for msg in reversed(messages):
        if msg.get("role") != "assistant":
            continue
        content = msg.get("content", [])
        if not isinstance(content, list):
            continue
        for block in content:
            if hasattr(block, "type") and block.type == "tool_use" and block.name == "record_decision":
                try:
                    return _parse_decision(block.input)
                except Exception:
                    pass
    return None


def _parse_decision(data: dict) -> Decision:
    citations = [Citation(**c) for c in data.get("citations", [])]
    return Decision(
        decision=data["decision"],
        confidence=data["confidence"],
        reasoning_summary=data["reasoning_summary"],
        citations=citations,
    )


def validate_certificate(
    pdf_bytes: bytes,
    customer_id: str,
    scenario_id: Optional[str] = None,
) -> tuple[Decision, list[dict], int, int]:
    """Run the agent loop and return (decision, raw_messages, tool_call_count, latency_ms)."""
    start_ms = int(time.time() * 1000)
    client = _make_client()

    pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")
    messages: list[dict] = [
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": pdf_b64,
                    },
                },
                {
                    "type": "text",
                    "text": (
                        f"Validate this exemption certificate for customer {customer_id}. "
                        "Use the available tools to retrieve transaction history and applicable "
                        "state rules, then call record_decision with your final determination."
                    ),
                },
            ],
        }
    ]

    tool_call_count = 0
    decision: Optional[Decision] = None

    for iteration in range(MAX_ITERATIONS):
        response = _call_api_with_retry(
            client,
            model=MODEL,
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        if response.stop_reason == "end_turn":
            decision = _extract_decision_from_messages(messages)
            if decision is None:
                decision = Decision(
                    decision="NEEDS_REVIEW",
                    confidence=0.0,
                    reasoning_summary="Agent ended without calling record_decision.",
                    citations=[],
                )
            break

        if response.stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": response.content})
            tool_results = []

            for block in response.content:
                if not hasattr(block, "type") or block.type != "tool_use":
                    continue
                tool_call_count += 1

                if block.name == "record_decision":
                    try:
                        decision = _parse_decision(block.input)
                    except Exception as e:
                        decision = Decision(
                            decision="NEEDS_REVIEW",
                            confidence=0.0,
                            reasoning_summary=f"Failed to parse decision: {e}",
                            citations=[],
                        )
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps({"recorded": True}),
                    })
                    messages.append({"role": "user", "content": tool_results})
                    break

                fn = TOOL_REGISTRY.get(block.name)
                if fn is None:
                    result = {"error": f"Unknown tool: {block.name}"}
                else:
                    try:
                        result = fn(**block.input)
                    except Exception as e:
                        result = {"error": str(e)}

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result),
                })

            else:
                messages.append({"role": "user", "content": tool_results})
                continue

            if decision is not None:
                break

        elif response.stop_reason == "max_tokens":
            decision = Decision(
                decision="NEEDS_REVIEW",
                confidence=0.0,
                reasoning_summary="Agent hit max_tokens limit; increase budget or simplify prompt.",
                citations=[],
            )
            break

    if decision is None:
        decision = Decision(
            decision="NEEDS_REVIEW",
            confidence=0.0,
            reasoning_summary="Agent loop exceeded iteration budget without producing a decision.",
            citations=[],
        )

    latency_ms = int(time.time() * 1000) - start_ms

    from src.utils import run_logger
    serializable_messages = _serialize_messages(messages)
    run_logger.log_run(
        run_id=str(uuid.uuid4()),
        scenario_id=scenario_id or "unknown",
        customer_id=customer_id,
        input_summary={"customer_id": customer_id},
        decision=decision,
        raw_messages=serializable_messages,
        latency_ms=latency_ms,
        tool_calls=tool_call_count,
        model=MODEL,
    )

    return decision, serializable_messages, tool_call_count, latency_ms


def _serialize_messages(messages: list[dict]) -> list[dict]:
    """Convert SDK content objects to JSON-serializable dicts."""
    result = []
    for msg in messages:
        content = msg.get("content", [])
        if isinstance(content, list):
            serial_content = []
            for block in content:
                if isinstance(block, dict):
                    serial_content.append(block)
                elif hasattr(block, "model_dump"):
                    serial_content.append(block.model_dump())
                else:
                    serial_content.append({"type": str(type(block)), "raw": str(block)})
            result.append({"role": msg["role"], "content": serial_content})
        else:
            result.append(msg)
    return result
