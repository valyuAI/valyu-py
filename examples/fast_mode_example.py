"""
Example demonstrating the fast_mode parameter for both search and answer endpoints.
Fast mode provides faster but shorter results, making it ideal for general purpose queries.
"""

import os
from valyu import Valyu
from dotenv import load_dotenv

load_dotenv()

VALYU_API_KEY = os.environ.get("VALYU_API_KEY")

if not VALYU_API_KEY:
    raise ValueError("VALYU_API_KEY environment variable not set!")

valyu = Valyu(VALYU_API_KEY)

print("⚡ Valyu Fast Mode Examples")
print("=" * 50)

# Example 1: Search with fast_mode enabled
print("\n🔍 Search with Fast Mode:")
query = "What are the latest developments in machine learning?"
print(f"Query: {query}")

# Regular search
print("\n📝 Regular Search:")
response_regular = valyu.search(query, fast_mode=False)
print(f"Success: {response_regular.success}")
if response_regular.success:
    print(f"Results: {len(response_regular.results)}")
    print(f"Total characters: {response_regular.total_characters}")
    print(f"Cost: ${response_regular.total_deduction_dollars:.4f}")
else:
    print(f"Error: {response_regular.error}")

# Fast mode search
print("\n⚡ Fast Mode Search:")
response_fast = valyu.search(query, fast_mode=True)
print(f"Success: {response_fast.success}")
if response_fast.success:
    print(f"Results: {len(response_fast.results)}")
    print(f"Total characters: {response_fast.total_characters}")
    print(f"Cost: ${response_fast.total_deduction_dollars:.4f}")
else:
    print(f"Error: {response_fast.error}")

print("\n" + "=" * 50)

# Example 2: Answer with fast_mode enabled
print("\n🧠 Answer with Fast Mode:")
query = "Explain quantum computing in simple terms"
print(f"Query: {query}")

# Regular answer
print("\n📝 Regular Answer:")
response_regular = valyu.answer(query, fast_mode=False)
print(f"Success: {response_regular.success}")
if response_regular.success:
    print(f"Answer length: {len(response_regular.contents)} characters")
    print(f"Search results: {response_regular.search_metadata.number_of_results}")
    print(f"AI cost: ${response_regular.cost.ai_deduction_dollars:.4f}")
    print(f"Total cost: ${response_regular.cost.total_deduction_dollars:.4f}")
else:
    print(f"Error: {response_regular.error}")

# Fast mode answer
print("\n⚡ Fast Mode Answer:")
response_fast = valyu.answer(query, fast_mode=True)
print(f"Success: {response_fast.success}")
if response_fast.success:
    print(f"Answer length: {len(response_fast.contents)} characters")
    print(f"Search results: {response_fast.search_metadata.number_of_results}")
    print(f"AI cost: ${response_fast.cost.ai_deduction_dollars:.4f}")
    print(f"Total cost: ${response_fast.cost.total_deduction_dollars:.4f}")
else:
    print(f"Error: {response_fast.error}")

print("\n" + "=" * 50)

# Example 3: Combining fast_mode with other parameters
print("\n🔄 Fast Mode with Custom Parameters:")
query = "recent advances in artificial intelligence"
response = valyu.search(
    query=query,
    fast_mode=True,
    search_type="web",
    max_num_results=5,
    response_length="short",
    country_code="US",
)

print(f"Query: {query}")
print(f"Success: {response.success}")
if response.success:
    print(f"Results: {len(response.results)}")
    print(f"Total characters: {response.total_characters}")
    print(f"Cost: ${response.total_deduction_dollars:.4f}")
    print(
        "First result title:",
        response.results[0].title if response.results else "No results",
    )
else:
    print(f"Error: {response.error}")
