"""
Anthropic + Valyu Provider Example

Demonstrates using Valyu as a tool/function with Anthropic Claude.
**NOTE** Ensure you have a VALYU_API_KEY and ANTHROPIC_API_KEY environment variables set.
"""

from anthropic import Anthropic
from valyu import AnthropicProvider
from dotenv import load_dotenv

load_dotenv()

# Initialize Anthropic client
anthropic_client = Anthropic()

# Initialize Valyu AnthropicProvider
provider = AnthropicProvider()

# Get Valyu tools for Anthropic
tools = provider.get_tools()

# Compose input messages
input_messages = [
    {
        "role": "user",
        "content": "Research the latest developments in multimodal AI models",
    }
]

# Step 1: Call Anthropic model with Valyu tools
response = anthropic_client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1000,
    tools=tools,
    messages=input_messages,
)

print(
    f"Model made {len([c for c in response.content if getattr(c, 'type', None) == 'tool_use'])} tool calls"
)

# Step 2: Execute tool calls using Valyu provider
tool_results = provider.handle_tool_calls(response=response)
print(f"Executed {len(tool_results)} tool calls")

# Step 3: Build updated conversation with tool results
updated_messages = provider.build_conversation(input_messages, response, tool_results)

# Step 4: Get final response from Anthropic with tool outputs
final_response = anthropic_client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=2000,
    tools=tools,
    messages=updated_messages,
)

print("=== Final Response ===")
for content in final_response.content:
    if hasattr(content, "text"):
        print(content.text)
    elif isinstance(content, dict) and content.get("type") == "text":
        print(content.get("text", ""))
