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
        if result.status == "success":
            print(f"\nTitle: {result.title}")
            print(f"URL: {result.url}")
            print(f"Content length: {result.length} characters")
            print(f"First 200 chars: {result.content[:200]}...")
        else:
            print(f"Failed: {result.url} - {result.error}")
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
        if result.status == "success":
            print(f"\nTitle: {result.title}")
            print(f"URL: {result.url}")
            if result.summary:
                print(f"Summary: {result.summary}")
            print(f"Total cost: ${response.total_cost_dollars:.4f}")
        else:
            print(f"Failed: {result.url} - {result.error}")
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
        if result.status == "success":
            print(f"\nTitle: {result.title}")
            if result.summary:
                print(f"Custom Summary:\n{result.summary}")
        else:
            print(f"Failed: {result.url} - {result.error}")
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
        if result.status == "success":
            print(f"\nURL: {result.url}")
            if result.summary and isinstance(result.summary, dict):
                print("Extracted structured data:")
                print(json.dumps(result.summary, indent=2))
        else:
            print(f"Failed: {result.url} - {result.error}")
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
        if result.status == "success":
            print(f"\n{i}. {result.title}")
            if result.summary:
                print(f"   Summary: {str(result.summary)[:200]}...")
        else:
            print(f"\n{i}. Failed: {result.url} - {result.error}")
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
        if result.status == "success":
            print(f"\nURL: {result.url}")
            print(f"Raw content ({result.length} chars):")
            print(result.content[:500])
            print(f"Cost: ${response.total_cost_dollars:.4f}")
        else:
            print(f"Failed: {result.url} - {result.error}")
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
        if result.status == "success":
            print(f"\nTitle: {result.title}")
            print(f"URL: {result.url}")
            price = getattr(result, "price", None)
            if price is not None:
                print(f"Price: ${price:.4f}")
            if result.screenshot_url:
                print(f"Screenshot URL: {result.screenshot_url}")
            print(f"Content length: {result.length} characters")
        else:
            print(f"Failed: {result.url} - {result.error}")
else:
    print(f"Error: {response.error}")

# Example 8: Async mode with wait (for >10 URLs)
print("\n\n8. Async Mode - Many URLs with wait=True")
print("-" * 40)

# For >10 URLs, async_mode is required. Here we use 5 URLs with async_mode for illustration.
async_urls = [
    "https://en.wikipedia.org/wiki/Deep_learning",
    "https://en.wikipedia.org/wiki/Natural_language_processing",
    "https://en.wikipedia.org/wiki/Computer_vision",
    "https://en.wikipedia.org/wiki/Transformer_(machine_learning_model)",
    "https://en.wikipedia.org/wiki/Large_language_model",
]

# Option A: Async with wait - blocks until complete, returns results
async_result = valyu.contents(
    urls=async_urls,
    async_mode=True,
    wait=True,
    poll_interval=5,
    max_wait_time=300,
)
if async_result and hasattr(async_result, "results") and async_result.results:
    print(f"Processed {async_result.urls_processed}/{async_result.urls_total} URLs")
    for r in async_result.results:
        if r.status == "success":
            print(f"  ✓ {r.url}: {r.title[:50]}...")
        else:
            print(f"  ✗ {r.url}: {r.error}")

# Example 9: Async mode with polling (for >10 URLs)
print("\n\n9. Async Mode - Poll for Status")
print("-" * 40)

job = valyu.contents(
    urls=async_urls[:3],
    async_mode=True,
)
if job and hasattr(job, "job_id"):
    print(f"Job ID: {job.job_id}")
    if job.webhook_secret:
        print(f"Webhook secret: {job.webhook_secret[:16]}...")
    status = valyu.get_contents_job(job.job_id)
    print(f"Status: {status.status} ({status.urls_processed}/{status.urls_total})")

print("\n" + "=" * 60)
print("End of Examples")
print("=" * 60)
