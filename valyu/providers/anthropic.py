"""
Anthropic provider implementation for Valyu integration.
"""

from __future__ import annotations

import json
import typing as t
from typing import Optional

# Anthropic API types
AnthropicTool: t.TypeAlias = t.Dict[str, t.Any]
AnthropicToolCollection: t.TypeAlias = t.List[AnthropicTool]

from ..api import Valyu as ValyuClient
from ..core.provider import BaseProvider
from ..core.types import Modifiers, Tool, ToolExecutionResponse


class AnthropicProvider(BaseProvider[AnthropicTool, AnthropicToolCollection]):
    """Anthropic provider for Valyu integration"""

    def __init__(self, valyu_api_key: Optional[str] = None):
        super().__init__()
        self._valyu_client = ValyuClient(api_key=valyu_api_key)

    def wrap_tool(self, tool: Tool) -> AnthropicTool:
        """Wrap a tool into Anthropic format"""
        return {
            "name": tool.slug,
            "description": tool.description,
            "input_schema": tool.input_parameters,
        }

    def wrap_tools(self, tools: t.Sequence[Tool]) -> AnthropicToolCollection:
        """Wrap multiple tools into Anthropic format"""
        return [self.wrap_tool(tool) for tool in tools]

    def get_tools(self) -> AnthropicToolCollection:
        """
        Get Valyu search tools in Anthropic format (simplified method)

        Returns:
            List of Anthropic-formatted tool definitions ready to use
        """
        available_tools = self.get_available_tools()
        return self.wrap_tools(available_tools)

    def execute_tool_calls(self, response) -> t.List[t.Dict[str, t.Any]]:
        """
        Execute tool calls from Anthropic response

        Args:
            response: Anthropic message response object

        Returns:
            List of tool execution results ready for conversation building
        """
        return self.handle_tool_calls(response=response)

    def build_conversation(
        self,
        input_messages: t.List[t.Dict[str, t.Any]],
        response,
        tool_results: t.List[t.Dict[str, t.Any]],
    ) -> t.List[t.Dict[str, t.Any]]:
        """
        Build conversation with tool calls and results

        Args:
            input_messages: Original input messages
            response: Anthropic response containing tool calls
            tool_results: Results from execute_tool_calls()

        Returns:
            Updated messages list ready for next Anthropic call
        """
        updated_messages = input_messages.copy()

        # Add the assistant's message with tool use
        if hasattr(response, "content"):
            updated_messages.append({"role": "assistant", "content": response.content})

        # Add tool results as user message
        tool_result_content = []
        for result in tool_results:
            tool_result_content.append(
                {
                    "type": "tool_result",
                    "tool_use_id": result["tool_call_id"],
                    "content": result["output"],
                }
            )

        if tool_result_content:
            updated_messages.append({"role": "user", "content": tool_result_content})

        return updated_messages

    def execute_tool_call(
        self,
        tool_call: t.Any,
        modifiers: t.Optional[Modifiers] = None,
    ) -> ToolExecutionResponse:
        """Execute a tool call from Anthropic

        :param tool_call: Tool call metadata from Anthropic
        :param modifiers: Optional modifiers for tool execution
        :return: Object containing output data from the tool call
        """
        tool_name = getattr(tool_call, "name", None)
        tool_input = getattr(tool_call, "input", {})

        return self.execute_tool(
            slug=tool_name,
            arguments=tool_input,
            modifiers=modifiers,
        )

    def handle_tool_calls(
        self,
        response: t.Any = None,
        modifiers: t.Optional[Modifiers] = None,
    ) -> t.List[t.Dict[str, t.Any]]:
        """
        Handle tool calls from Anthropic message response

        :param response: Message response from Anthropic API
        :param modifiers: Optional modifiers for tool execution
        :return: A list of output objects from the function calls
        """
        outputs = []

        if not response or not hasattr(response, "content"):
            return outputs

        for item in response.content:
            if (
                hasattr(item, "type")
                and item.type == "tool_use"
                and item.name == "valyu_search"
            ):
                # Parse arguments and execute search
                args = item.input
                print(
                    f"🔍 Executing Valyu search: {args.get('query', 'Unknown query')}"
                )

                # Execute the tool
                tool_response = self.execute_tool_call(
                    tool_call=item,
                    modifiers=modifiers,
                )

                if tool_response.output:
                    print(
                        f"✅ Found {len(tool_response.output.get('results', []))} results"
                    )

                # Format result for Anthropic
                tool_result = {
                    "tool_call_id": item.id,
                    "output": (
                        json.dumps(tool_response.output)
                        if tool_response.output
                        else str(tool_response.error)
                    ),
                }
                outputs.append(tool_result)

        return outputs
