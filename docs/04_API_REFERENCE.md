# 04 API Reference

> Anthropic Claude API patterns used in this project. Verified against current SDK as of May 2026.

## SDK and version

- Package: `anthropic`
- Minimum Python: 3.9 (we use 3.11)
- Install: `pip install anthropic`
- Documentation: https://docs.claude.com/en/api/overview

## Authentication

API key is read from environment variable `ANTHROPIC_API_KEY`.

```
from anthropic import Anthropic
client = Anthropic()  # picks up ANTHROPIC_API_KEY automatically
```

Never hardcode keys. The `.env.example` template shows the expected variable.

## Model selection

Use `claude-sonnet-4-6` as the default model for this prototype.

| Model | Use case | Approximate cost per agent run |
| --- | --- | --- |
| `claude-sonnet-4-6` | Default. Strong reasoning + tool use, cost-effective | ~$0.05 per validation |
| `claude-opus-4-7` | Upgrade for hardest cases or final polish | ~$0.25 per validation |
| `claude-haiku-4-5-20251001` | Faster but weaker on multi-step reasoning | ~$0.01 per validation |

Stay on Sonnet for the prototype. Eval cost on 10 scenarios on Sonnet is roughly $0.50.

## Basic message creation

```
message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4000,
    system=SYSTEM_PROMPT,
    messages=[
        {"role": "user", "content": "Validate this certificate."}
    ],
)
print(message.content)
print(message.stop_reason)
```

`message.content` is a list of content blocks (text blocks, tool_use blocks). `message.stop_reason` is one of: `"end_turn"`, `"tool_use"`, `"max_tokens"`, `"stop_sequence"`.

## Tool use (the pattern this project relies on)

Tool definitions are passed in the `tools` parameter as a list of dicts. Each tool has `name`, `description`, and `input_schema` (JSON Schema).

```
tools = [
    {
        "name": "get_customer_transactions",
        "description": "Retrieve a sample of recent transactions for a given customer.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "limit": {"type": "integer", "default": 30}
            },
            "required": ["customer_id"]
        }
    }
]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=4000,
    tools=tools,
    messages=[{"role": "user", "content": "Look up customer CUST_001."}]
)
```

When the model wants to call a tool, the response will have `stop_reason == "tool_use"` and one or more `tool_use` blocks in `response.content`:

```
for block in response.content:
    if block.type == "tool_use":
        tool_name = block.name
        tool_input = block.input
        tool_use_id = block.id
        # Dispatch to the actual function
        result = TOOL_REGISTRY[tool_name](**tool_input)
```

## The agent loop pattern

The full pattern this project uses:

```
def validate_certificate(pdf_bytes, customer_id):
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "document",
                    "source": {
                        "type": "base64",
                        "media_type": "application/pdf",
                        "data": base64.standard_b64encode(pdf_bytes).decode("utf-8")
                    }
                },
                {"type": "text", "text": f"Validate this certificate for customer {customer_id}."}
            ]
        }
    ]
    
    for iteration in range(10):  # hard cap
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages,
        )
        
        if response.stop_reason == "end_turn":
            # Extract the record_decision tool call from the conversation
            return extract_decision_from_messages(messages)
        
        if response.stop_reason == "tool_use":
            # Append assistant message
            messages.append({"role": "assistant", "content": response.content})
            
            # Execute each tool call and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    if block.name == "record_decision":
                        # This is the terminal tool; capture the decision
                        return Decision(**block.input)
                    
                    result = TOOL_REGISTRY[block.name](**block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result)
                    })
            
            messages.append({"role": "user", "content": tool_results})
            continue
        
        if response.stop_reason == "max_tokens":
            raise RuntimeError("Agent hit max_tokens; increase budget or simplify prompt")
    
    # Fallback: loop budget exceeded
    return Decision(decision="NEEDS_REVIEW", confidence=0.0, 
                    reasoning_summary="Agent loop exceeded budget", citations=[])
```

Key points:
- `record_decision` is treated as the terminal tool; when the agent calls it, we extract the decision and return immediately
- Tool results are sent back as a `user` message with `tool_result` content blocks
- We hard cap at 10 iterations to prevent runaway loops
- `extract_decision_from_messages` is a helper that scans the message history for the most recent `record_decision` tool call (used in the rare case the agent ends without calling it)

## PDF input format

Claude Sonnet 4.6 accepts PDFs directly as document content blocks. No separate OCR needed.

```
import base64

with open("certificate.pdf", "rb") as f:
    pdf_data = base64.standard_b64encode(f.read()).decode("utf-8")

content = [
    {
        "type": "document",
        "source": {
            "type": "base64",
            "media_type": "application/pdf",
            "data": pdf_data
        }
    },
    {"type": "text", "text": "Extract the buyer name and exemption type."}
]
```

PDF size limits apply; for our synthetic certificates this is not a concern.

## Error handling

Common exceptions to handle:

```
from anthropic import (
    APIError,
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    RateLimitError,
)

try:
    response = client.messages.create(...)
except RateLimitError:
    # Back off and retry
    time.sleep(30)
    # retry
except APIStatusError as e:
    if e.status_code >= 500:
        # Server error; back off and retry
        time.sleep(5)
    else:
        # Client error; do not retry
        raise
except APIConnectionError:
    # Network issue; retry once
    time.sleep(2)
    # retry
except APITimeoutError:
    # Request timed out; consider increasing timeout
    raise
```

Use exponential backoff for transient errors. The Anthropic SDK has built-in retries for some cases, but explicit handling makes failure modes visible.

## Rate limits

For the prototype, the default per-organization rate limits are sufficient. If you hit rate limits during eval (running 10 scenarios in sequence), insert `time.sleep(1)` between calls.

Reference: https://docs.claude.com/en/api/rate-limits

## Cost estimation

Rough costs for this project:

| Activity | Cost |
| --- | --- |
| Single validation run (Sonnet 4.6, ~3 tool calls, ~3K input tokens, ~500 output) | ~$0.05 |
| Full eval (10 scenarios) | ~$0.50 |
| Full development cycle (50-100 test runs) | ~$5 |

Set spending limit at $20 in the Anthropic Console. This caps the worst-case scenario where something runs in a loop.

## Streaming (not used in this project)

We do not use streaming. Reasons:
- Adds complexity without value (the user reads a structured decision, not flowing text)
- Streaming responses are harder to log cleanly
- Streamlit's `st.status` provides good-enough perceived progress

If a panel asks "why no streaming?", the answer is "streaming is a UX optimization for chat interfaces. This is not a chat interface. Adding it would complicate the architecture for marginal user benefit."

## What we deliberately do NOT use

- **The `tool_runner` helper** in `client.beta.messages.tool_runner`. This auto-handles tool dispatch but hides the agent loop. We want the loop visible for inspection and interview defense.
- **The Claude Agent SDK** (`claude-agent-sdk`). That SDK is for building agents that use Claude Code's tools (Bash, Edit, Read, etc.) to operate on a filesystem. It's the wrong abstraction for our use case.
- **Streaming.** See above.
- **Batch API.** We process certificates one at a time interactively. No batching needed.

## Reference links

- API overview: https://docs.claude.com/en/api/overview
- Tool use: https://docs.claude.com/en/docs/agents-and-tools/tool-use/overview
- Python SDK: https://github.com/anthropics/anthropic-sdk-python
- Models: https://docs.claude.com/en/docs/about-claude/models
- Rate limits: https://docs.claude.com/en/api/rate-limits
