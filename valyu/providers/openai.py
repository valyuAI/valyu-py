"""
OpenAI provider implementation for Valyu integration.
"""

from __future__ import annotations

import json
import typing as t
from typing import Optional

from ..api import Valyu as ValyuClient
from ..core.provider import BaseProvider
from ..core.types import Modifiers, Tool, ToolExecutionResponse

# OpenAI responses API types
OpenAITool: t.TypeAlias = t.Dict[str, t.Any]
OpenAIToolCollection: t.TypeAlias = t.List[OpenAITool]


class OpenAIProvider(BaseProvider[OpenAITool, OpenAIToolCollection]):
    """OpenAI provider for Valyu integration using responses API"""

    def __init__(self, valyu_api_key: Optional[str] = None):
        super().__init__()
        self._valyu_client = ValyuClient(api_key=valyu_api_key)

    def wrap_tool(self, tool: Tool) -> OpenAITool:
        """Wrap a tool into OpenAI responses API format"""
        return {
            "type": "function",
            "name": tool.slug,
            "description": tool.description,
            "parameters": tool.input_parameters,
        }

    def wrap_tools(self, tools: t.Sequence[Tool]) -> OpenAIToolCollection:
        """Wrap multiple tools into OpenAI responses API format"""
        return [self.wrap_tool(tool) for tool in tools]

    def get_tools(self) -> OpenAIToolCollection:
        """
        Get Valyu search tools in OpenAI format (simplified method)

        Returns:
            List of OpenAI-formatted tool definitions ready to use
        """
        available_tools = self.get_available_tools()
        return self.wrap_tools(available_tools)

    def execute_tool_calls(self, response) -> t.List[t.Dict[str, t.Any]]:
        """
        Execute tool calls from OpenAI response (simplified method)

        Args:
            response: OpenAI responses.create() response object

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
        Build conversation with tool calls and results (simplified method)

        Args:
            input_messages: Original input messages
            response: OpenAI response containing tool calls
            tool_results: Results from execute_tool_calls()

        Returns:
            Updated messages list ready for next OpenAI call
        """
        updated_messages = input_messages.copy()

        # Add the function calls
        for item in response.output:
            if hasattr(item, "type") and item.type == "function_call":
                updated_messages.append(item.model_dump())

        # Add the tool results
        for result in tool_results:
            updated_messages.append(
                {
                    "type": "function_call_output",
                    "call_id": result["tool_call_id"],
                    "output": result["output"],
                }
            )

        return updated_messages

    def execute_tool_call(
        self,
        tool_call: t.Any,  # OpenAI responses API tool call object
        modifiers: t.Optional[Modifiers] = None,
    ) -> ToolExecutionResponse:
        """Execute a tool call from OpenAI responses API.

        :param tool_call: Tool call metadata from OpenAI responses API
        :param user_id: User ID to use for executing the function call
        :return: Object containing output data from the tool call
        """
        return self.execute_tool(
            slug=tool_call.name,
            arguments=json.loads(tool_call.arguments),
            modifiers=modifiers,
        )

    def handle_tool_calls(
        self,
        response: t.Any = None,  # OpenAI responses API response object
        modifiers: t.Optional[Modifiers] = None,
    ) -> t.List[t.Dict[str, t.Any]]:
        """
        Handle tool calls from OpenAI responses API response object.

        :param response: Response object from openai.responses.create function call
        :return: A list of output objects from the function calls
        """
        outputs = []

        if not response or not hasattr(response, "output") or not response.output:
            return outputs

        for item in response.output:
            if (
                hasattr(item, "type")
                and item.type == "function_call"
                and item.name == "valyu_search"
            ):
                # Parse arguments and execute search
                args = json.loads(item.arguments)
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

                # Format result for OpenAI responses API
                tool_result = {
                    "tool_call_id": item.call_id,
                    "output": (
                        json.dumps(tool_response.output)
                        if tool_response.output
                        else str(tool_response.error)
                    ),
                }
                outputs.append(tool_result)

        return outputs
