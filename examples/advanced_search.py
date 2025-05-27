import os
from valyu import Valyu

VALYU_API_KEY = os.environ.get("VALYU_API_KEY")

if not VALYU_API_KEY:
    raise ValueError("VALYU_API_KEY environment variable not set!")

valyu = Valyu(VALYU_API_KEY)

# Deep search over academic papers from Arxiv
print("🔬 Proprietary Search:")
response = valyu.search(
    "implementation details ofagentic search-enhanced large reasoning models",
    search_type="proprietary",
    max_num_results=10,
    relevance_threshold=0.6,
    included_sources=["valyu/valyu-arxiv"],
    category="agentic retrieval-augmented generation",
    start_date="2024-12-01",
)
print(response)

print("\n" + "=" * 50 + "\n")

# Web search
print("🌐 Web Search:")
response = valyu.search(
    "what is claude 4 opus model",
    search_type="web",
    max_num_results=7,
    relevance_threshold=0.5,
    start_date="2025-05-01",
    end_date="2025-05-25",
)
print(response)

print("\n" + "=" * 50 + "\n")

# Hybrid search (both web and proprietary)
print("🔄 Hybrid Search:")
response = valyu.search(
    "quantum computing applications in cryptography",
    search_type="all",
    max_num_results=8,
    relevance_threshold=0.5,
    max_price=40,
    is_tool_call=True,
)
print(response)

print("\n" + "=" * 50 + "\n")

# Search with date filters (v2 feature)
print("📅 Date-filtered Search:")
response = valyu.search(
    "artificial intelligence breakthroughs",
    search_type="web",
    max_num_results=5,
    start_date="2024-01-01",
    end_date="2024-12-31",
    category="technology",
)
print(response)
