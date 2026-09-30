"""Helpers to build subagents and expose them as tools for the supervisor."""

from collections.abc import Callable
from typing import Any

from langchain.agents import create_agent
from langchain.tools import BaseTool, tool
from langchain_core.messages import HumanMessage
from langchain_core.language_models.chat_models import BaseChatModel

from app.agents.llm import get_chat_model


def extract_last_text(response: dict[str, Any]) -> str:
    """Read the last agent message as plain text (Gemini may return list blocks)."""
    messages = response.get("messages") or []
    if not messages:
        return ""

    content = messages[-1].content
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for block in content:
            if isinstance(block, str):
                parts.append(block)
            elif isinstance(block, dict) and block.get("type") == "text":
                parts.append(str(block.get("text") or ""))
        return "\n".join(p for p in parts if p)
    return str(content)


def build_subagent(
    *,
    tools: list[BaseTool | Callable],
    system_prompt: str,
    model: BaseChatModel | None = None,
):
    """Create a LangChain agent with its own tools and prompt."""
    return create_agent(
        model=model or get_chat_model(),
        tools=tools,
        system_prompt=system_prompt,
    )


def as_supervisor_tool(
    agent,
    *,
    name: str,
    description: str,
) -> BaseTool:
    """Wrap a subagent so the supervisor can call it like in the LangChain notebook."""

    @tool(name, description=description)
    async def call_subagent(query: str) -> str:
        """Forward a natural-language query to a specialist subagent."""
        response = await agent.ainvoke(
            {"messages": [HumanMessage(content=query)]}
        )
        return extract_last_text(response)

    return call_subagent
