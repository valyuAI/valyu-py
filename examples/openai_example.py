"""
OpenAI + Valyu Provider Example

Demonstrates using Valyu as a tool/function with OpenAI's responses API.
**NOTE** Ensure you have a VALYU_API_KEY and OPENAI_API_KEY environment variables set.
"""

from openai import OpenAI
from valyu import OpenAIProvider
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Initialize OpenAI client
openai_client = OpenAI()

# Initialize Valyu OpenAIProvider
provider = OpenAIProvider()

# Get Valyu tools for OpenAI
tools = provider.get_tools()

# Compose input messages
input_messages = [
    {
        "role": "system",
        "content": f"You are a helpful assistant. Today's date is {datetime.now().strftime('%Y-%m-%d')}",
    },
    {
        "role": "user",
        "content": "Get the price of bitcoin and dogecoin over the last 7 days, then research the latest news on their price movements, the generate a detailed report on the price movements and the news",
    },
]

# Step 1: Call OpenAI model with Valyu tools
response = openai_client.responses.create(
    model="gpt-4o",
    input=input_messages,
    tools=tools,
)

print(
    f"Model made {len([item for item in response.output if hasattr(item, 'type') and item.type == 'function_call'])} tool calls"
)

# Step 2: Execute tool calls using Valyu provider
tool_results = provider.handle_tool_calls(response=response)
print(f"Executed {len(tool_results)} tool calls")

# Step 3: Build updated conversation with tool results
updated_messages = provider.build_conversation(input_messages, response, tool_results)

# Step 4: Get final response from OpenAI with tool outputs
final_response = openai_client.responses.create(
    model="gpt-4o",
    input=updated_messages,
    tools=tools,
)

print("=== Final Response ===")
print(final_response.output_text)
