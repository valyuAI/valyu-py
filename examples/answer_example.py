"""
Example demonstrating the Valyu Answer API endpoint.
The Answer API provides AI-processed responses to questions using search data.
Supports both streaming and non-streaming modes.
"""

import os
from valyu import Valyu
from dotenv import load_dotenv

load_dotenv()

VALYU_API_KEY = os.environ.get("VALYU_API_KEY")

if not VALYU_API_KEY:
    raise ValueError("VALYU_API_KEY environment variable not set!")

valyu = Valyu(VALYU_API_KEY)

print("Valyu Answer API Examples")
print("=" * 50)

# Example 1: Basic Answer (non-streaming - default)
print("\n1. Basic Answer (non-streaming):")
query = "What are the latest developments in quantum computing in 2024?"
print(f"Query: {query}")

response = valyu.answer(query)
print(f"Success: {response.success}")
if response.success:
    print(f"Answer: {response.contents[:500]}...")  # First 500 chars
    print(f"Search results: {response.search_metadata.number_of_results}")
    print(f"Total cost: ${response.cost.total_deduction_dollars:.4f}")
else:
    print(f"Error: {response.error}")

print("\n" + "=" * 50)

# Example 2: Streaming Answer
print("\n2. Streaming Answer:")
query = "What is machine learning?"
print(f"Query: {query}")
print("Streaming response:")

full_answer = ""
sources_count = 0

for chunk in valyu.answer(query, streaming=True):
    if chunk.type == "search_results":
        sources_count = len(chunk.search_results)
        print(f"\n[Received {sources_count} sources]")

    elif chunk.type == "content":
        if chunk.content:
            print(chunk.content, end="", flush=True)
            full_answer += chunk.content

    elif chunk.type == "metadata":
        print(f"\n\n[Metadata] Cost: ${chunk.cost.total_deduction_dollars:.4f}")
        print(f"[Metadata] Tokens: {chunk.ai_usage.input_tokens} in, {chunk.ai_usage.output_tokens} out")

    elif chunk.type == "done":
        print("\n[Stream complete]")

    elif chunk.type == "error":
        print(f"\n[Error] {chunk.error}")

print("\n" + "=" * 50)

# Example 3: Answer with System Instructions
print("\n3. Answer with Custom Instructions:")
query = "Explain neural networks"
system_instructions = "Provide a concise, beginner-friendly explanation suitable for someone with no technical background. Use simple analogies where possible."

print(f"Query: {query}")
print(f"Instructions: {system_instructions}")

response = valyu.answer(
    query=query, system_instructions=system_instructions, search_type="web"
)

print(f"Success: {response.success}")
if response.success:
    print(f"Answer: {response.contents}")
    print(f"AI cost: ${response.cost.ai_deduction_dollars:.4f}")
    print(
        f"Tokens used: {response.ai_usage.input_tokens + response.ai_usage.output_tokens}"
    )
else:
    print(f"Error: {response.error}")

print("\n" + "=" * 50)

# Example 4: Structured Output
print("\n4. Structured Output Example:")
query = "Compare the performance of GPT-4 and Claude-3 models"

# Define a JSON schema for structured output
structured_schema = {
    "type": "object",
    "properties": {
        "models": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "strengths": {"type": "array", "items": {"type": "string"}},
                    "weaknesses": {"type": "array", "items": {"type": "string"}},
                    "performance_scores": {
                        "type": "object",
                        "properties": {
                            "reasoning": {"type": "number"},
                            "coding": {"type": "number"},
                            "writing": {"type": "number"},
                        },
                    },
                },
                "required": ["name", "strengths", "weaknesses"],
            },
        },
        "summary": {"type": "string"},
    },
    "required": ["models", "summary"],
}

print(f"Query: {query}")
print("Requesting structured output...")

response = valyu.answer(
    query=query,
    structured_output=structured_schema,
    search_type="all",
    data_max_price=40.0,
)

print(f"Success: {response.success}")
if response.success:
    print(f"Data type: {response.data_type}")
    print(f"Structured result: {response.contents}")
    print(f"Total cost: ${response.cost.total_deduction_dollars:.4f}")
else:
    print(f"Error: {response.error}")

print("\n" + "=" * 50)

# Example 5: Streaming with Source Filtering
print("\n5. Streaming with Source Filtering:")
query = "Latest research on protein folding"

print(f"Query: {query}")
print("Streaming with proprietary sources only...")

for chunk in valyu.answer(
    query=query,
    included_sources=["arxiv.org", "nature.com"],
    excluded_sources=["wikipedia.org", "reddit.com"],
    search_type="proprietary",
    start_date="2024-01-01",
    streaming=True,
):
    if chunk.type == "search_results":
        print(f"\n[Sources found: {len(chunk.search_results)}]")
        for i, source in enumerate(chunk.search_results[:3]):
            print(f"  {i+1}. {source.title[:60]}...")

    elif chunk.type == "content":
        if chunk.content:
            print(chunk.content, end="", flush=True)

    elif chunk.type == "metadata":
        print(f"\n\n[Total characters: {chunk.search_metadata.total_characters}]")

    elif chunk.type == "done":
        print("\n[Complete]")

print("\n" + "=" * 50)

# Example 6: Error Handling - Invalid Sources
print("\n6. Error Handling Example:")
query = "How does photosynthesis work?"

response = valyu.answer(
    query=query,
    included_sources=["invalid..domain", "not-a-url"],  # Invalid sources
)

print(f"Query: {query}")
print(f"Success: {response.success}")
if not response.success:
    print(f"Expected error: {response.error}")

print("\n" + "=" * 50)

print("\nAnswer API examples completed!")
print("\nKey features:")
print("  - streaming=False (default): Wait for complete response")
print("  - streaming=True: Stream chunks as they're generated")
print("  - Customize responses with system instructions")
print("  - Structure output with JSON schemas")
print("  - Control data sources and costs")
print("  - Full transparency on token usage and costs")
