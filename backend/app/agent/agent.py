# app/agent/agent.py
import json
from typing import Any

from app.agent.tools import TOOL_SCHEMAS, call_tool
from app.llm.openai_llm import OpenAILLM


SYSTEM = (
    "You are ZiggyAI, a careful research assistant. "
    "Use tools when helpful. Cite sources. Ask for approval if actions might be risky."
)


def run_agent(
    query: str, max_steps: int = 5, approvals: bool = False
) -> dict[str, Any]:
    """
    Simple tool-using loop:
      - send user query
      - if model requests a tool, run it, append observation
      - stop when model returns a final answer or step limit hit
    """
    llm = OpenAILLM()
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": query},
    ]

    transcript_steps = []
    for step in range(1, max_steps + 1):
        msg = llm.chat(messages, tools=TOOL_SCHEMAS)
        tool_calls = msg.get("tool_calls", [])

        if not tool_calls:
            # Final answer
            messages.append({"role": "assistant", "content": msg.get("content", "")})
            return {"final": msg.get("content", ""), "steps": transcript_steps}

        # Handle one tool call at a time (you can extend to multi)
        tool = tool_calls[0]["function"]["name"]
        raw_args = tool_calls[0]["function"].get("arguments", "{}")
        try:
            args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
        except Exception:
            args = {}

        # Optional approval gate
        if approvals:
            # For real apps, persist and wait for user confirmation via UI/webhook.
            return {
                "pending_approval": {"tool": tool, "args": args},
                "steps": transcript_steps,
            }

        # Execute tool
        observation = call_tool(tool, args)
        transcript_steps.append(
            {"tool": tool, "args": args, "observation": observation}
        )

        # Feed observation back to model
        messages.append(
            {
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": "t1",
                        "type": "function",
                        "function": {"name": tool, "arguments": json.dumps(args)},
                    }
                ],
            }
        )
        messages.append(
            {"role": "tool", "name": tool, "content": json.dumps(observation)}
        )

    return {"final": "(step limit reached)", "steps": transcript_steps}
