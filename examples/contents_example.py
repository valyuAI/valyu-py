"""
Example usage of the Valyu Contents API for extracting and summarizing web content
"""

from valyu import Valyu
import os
import json

# Initialize the client
valyu = Valyu(api_key=os.getenv("VALYU_API_KEY"))

print("=" * 60)
print("Valyu Contents API Examples")
print("=" * 60)

# Example 1: Basic content extraction
print("\n1. Basic Content Extraction")
print("-" * 30)

response = valyu.contents(
    urls=["https://en.wikipedia.org/wiki/Artificial_intelligence"]
)

if response.success:
    print(f"Processed {response.urls_processed} URLs")
    for result in response.results:
        print(f"\nTitle: {result.title}")
        print(f"URL: {result.url}")
        print(f"Content length: {result.length} characters")
        print(f"First 200 chars: {result.content[:200]}...")
else:
    print(f"Error: {response.error}")

# Example 2: Content with AI summary
print("\n\n2. Content with AI Summary")
print("-" * 30)

response = valyu.contents(
    urls=["https://docs.python.org/3/tutorial/introduction.html"],
    summary=True,
    response_length="medium",
)

if response.success:
    for result in response.results:
        print(f"\nTitle: {result.title}")
        print(f"URL: {result.url}")
        if result.summary:
            print(f"Summary: {result.summary}")
        print(f"Total cost: ${response.total_cost_dollars:.4f}")
else:
    print(f"Error: {response.error}")

# Example 3: Custom summary instructions
print("\n\n3. Custom Summary Instructions")
print("-" * 30)

response = valyu.contents(
    urls=["https://en.wikipedia.org/wiki/Machine_learning"],
    summary="Summarize the key concepts in bullet points, focusing on practical applications",
    extract_effort="high",
    response_length="large",
)

if response.success:
    for result in response.results:
        print(f"\nTitle: {result.title}")
        if result.summary:
            print(f"Custom Summary:\n{result.summary}")
else:
    print(f"Error: {response.error}")

# Example 4: Structured data extraction with JSON schema
print("\n\n4. Structured Data Extraction")
print("-" * 30)

# Define a JSON schema for extracting company information
company_schema = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "founded_year": {"type": "integer"},
        "industry": {
            "type": "string",
            "enum": ["tech", "finance", "healthcare", "retail", "other"],
        },
        "key_products": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
        "headquarters": {"type": "string"},
    },
    "required": ["company_name"],
}

response = valyu.contents(
    urls=["https://en.wikipedia.org/wiki/OpenAI"],
    summary=company_schema,
    extract_effort="high",
)

if response.success:
    for result in response.results:
        print(f"\nURL: {result.url}")
        if result.summary and isinstance(result.summary, dict):
            print("Extracted structured data:")
            print(json.dumps(result.summary, indent=2))
else:
    print(f"Error: {response.error}")

# Example 5: Multiple URLs with cost limit
print("\n\n5. Multiple URLs with Cost Limit")
print("-" * 30)

urls = [
    "https://en.wikipedia.org/wiki/Deep_learning",
    "https://en.wikipedia.org/wiki/Natural_language_processing",
    "https://en.wikipedia.org/wiki/Computer_vision",
]

response = valyu.contents(
    urls=urls,
    summary=True,
    response_length="short",
    max_price_dollars=0.05,  # Limit cost to 5 cents
)

if response.success:
    print(f"Requested: {response.urls_requested} URLs")
    print(f"Processed: {response.urls_processed} URLs")
    print(f"Failed: {response.urls_failed} URLs")
    print(f"Total characters: {response.total_characters}")
    print(f"Total cost: ${response.total_cost_dollars:.4f}")

    for i, result in enumerate(response.results, 1):
        print(f"\n{i}. {result.title}")
        if result.summary:
            print(f"   Summary: {str(result.summary)[:200]}...")
else:
    print(f"Error: {response.error}")

# Example 6: Raw content extraction (no AI processing)
print("\n\n6. Raw Content Extraction (No AI)")
print("-" * 30)

response = valyu.contents(
    urls=["https://example.com"],
    summary=False,  # Explicitly disable AI processing
    response_length="short",
)

if response.success:
    for result in response.results:
        print(f"\nURL: {result.url}")
        print(f"Raw content ({result.length} chars):")
        print(result.content[:500])
        print(f"Cost: ${response.total_cost_dollars:.4f}")
else:
    print(f"Error: {response.error}")

# Example 7: Content extraction with screenshot
print("\n\n7. Content Extraction with Screenshot")
print("-" * 30)

response = valyu.contents(
    urls=["https://www.valyu.ai/"],
    screenshot=True,  # Request page screenshots
    response_length="short",
)

if response.success:
    for result in response.results:
        print(f"\nTitle: {result.title}")
        print(f"URL: {result.url}")
        print(f"Price: ${result.price:.4f}")
        if result.screenshot_url:
            print(f"Screenshot URL: {result.screenshot_url}")
        print(f"Content length: {result.length} characters")
else:
    print(f"Error: {response.error}")

print("\n" + "=" * 60)
print("End of Examples")
print("=" * 60)
