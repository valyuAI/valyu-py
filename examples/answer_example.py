"""
Example demonstrating the Valyu Answer API endpoint.
The Answer API provides AI-processed responses to questions using search data.
"""

import os
from valyu import Valyu
from dotenv import load_dotenv

load_dotenv()

VALYU_API_KEY = os.environ.get("VALYU_API_KEY")

if not VALYU_API_KEY:
    raise ValueError("VALYU_API_KEY environment variable not set!")

valyu = Valyu(VALYU_API_KEY)

print("🧠 Valyu Answer API Examples")
print("=" * 50)

# Example 1: Basic Answer
print("\n📝 Basic Answer Example:")
query = "What are the latest developments in quantum computing in 2024?"
print(f"Query: {query}")

response = valyu.answer(query)
print(f"Success: {response.success}")
if response.success:
    print(f"Answer: {response.contents[:500]}...")  # First 500 chars
    print(f"Documents processed: {response.documents_processed}")
    print(f"Total cost: ${response.search_metadata.total_deduction_dollars:.4f}")
else:
    print(f"Error: {response.error}")

print("\n" + "=" * 50)

# Example 2: Answer with System Instructions
print("\n🎯 Answer with Custom Instructions:")
query = "What is machine learning?"
system_instructions = "Provide a concise, beginner-friendly explanation suitable for someone with no technical background. Use simple analogies where possible."

print(f"Query: {query}")
print(f"Instructions: {system_instructions}")

response = valyu.answer(
    query=query, system_instructions=system_instructions, search_type="web"
)

print(f"Success: {response.success}")
if response.success:
    print(f"Answer: {response.contents}")
    print(f"AI cost: ${response.ai_usage.cost_dollars:.4f}")
    print(f"Tokens used: {response.ai_usage.total_tokens}")
else:
    print(f"Error: {response.error}")

print("\n" + "=" * 50)

# Example 3: Structured Output
print("\n📊 Structured Output Example:")
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
    print(f"Total cost: ${response.search_metadata.total_deduction_dollars:.4f}")
else:
    print(f"Error: {response.error}")

print("\n" + "=" * 50)

# Example 4: Answer with Source Filtering
print("\n🎯 Answer with Source Filtering:")
query = "Latest research on protein folding"

response = valyu.answer(
    query=query,
    included_sources=["arxiv.org", "nature.com", "valyu/protein-research"],
    excluded_sources=["wikipedia.org", "reddit.com"],
    search_type="proprietary",
    start_date="2024-01-01",
)

print(f"Query: {query}")
print(f"Success: {response.success}")
if response.success:
    print(f"Answer: {response.contents[:400]}...")
    print(f"Sources breakdown: {response.search_metadata.results_by_source}")
    print(
        f"Documents used: {response.documents_processed}/{response.total_documents_available}"
    )
else:
    print(f"Error: {response.error}")

print("\n" + "=" * 50)

# Example 5: Error Handling - Invalid Sources
print("\n❌ Error Handling Example:")
query = "How does photosynthesis work?"

response = valyu.answer(
    query=query,
    included_sources=["invalid..domain", "not-a-url"],  # Invalid sources
)

print(f"Query: {query}")
print(f"Success: {response.success}")
if not response.success:
    print(f"Expected error: {response.error}")

print("\n🎉 Answer API examples completed!")
print("\nKey benefits of the Answer API:")
print("• Get AI-processed answers instead of raw search results")
print("• Customize responses with system instructions")
print("• Structure output with JSON schemas")
print("• Control data sources and costs")
print("• Full transparency on token usage and costs")
