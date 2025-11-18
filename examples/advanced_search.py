import os
from valyu import Valyu
from dotenv import load_dotenv

load_dotenv()

VALYU_API_KEY = os.environ.get("VALYU_API_KEY")

if not VALYU_API_KEY:
    raise ValueError("VALYU_API_KEY environment variable not set!")

valyu = Valyu(VALYU_API_KEY)

# Search for AI
print("🔍 AI Search")
query = "what is trans-applifying mRNA"
print(f"Query: {query}")
response = valyu.search(query)

print(response)

# Deep search over academic papers
print("🔬 Paper Search")
query = "implementation details of agentic search-enhanced large reasoning models"
print(f"Query: {query}")
response = valyu.search(
    query,
    search_type="proprietary",
    max_num_results=10,
    included_sources=["valyu/valyu-arxiv"],
    category="agentic RAG",
    start_date="2024-12-01",
)
print(response)

print("\n" + "=" * 50 + "\n")

print("🌐 Web Search")
query = "what are the grok 4 benchmark results"
print(f"Query: {query}")
response = valyu.search(
    query,
    search_type="web",
    max_num_results=7,
    relevance_threshold=0.5,
    start_date="2025-06-01",
    end_date="2025-07-25",
)
print(response)

# Web search with country filtering
print("🌐 Web Search with Country Filter")
query = "what is the weather where i am?"
print(f"Query: {query}")
response = valyu.search(
    query,
    country_code="UK",
    response_length="short",
)
print(response)

print("\n" + "=" * 50 + "\n")

# Hybrid search with exclude sources
print("🔄 Hybrid Search with Source Exclusion:")
query = "quantum computing applications in cryptography"
print(f"Query: {query}")
response = valyu.search(
    query,
    search_type="all",
    max_num_results=8,
    relevance_threshold=0.5,
    max_price=40,
    excluded_sources=["paperswithcode.com", "wikipedia.org"],
    response_length="large",
    is_tool_call=True,
)
print(response)

print("\n" + "=" * 50 + "\n")

# Search with custom response length (character count)
print("📏 Custom Response Length Search:")
query = "State of video generation AI models"
print(f"Query: {query}")
response = valyu.search(
    query,
    max_num_results=10,
    category="vLLMs",
    response_length=1000,  # Limit to 1000 characters per result
)

print(response)

print("\n" + "=" * 50 + "\n")

# News search for recent developments
print("📰 News Search:")
query = "latest breakthroughs in quantum computing"
print(f"Query: {query}")
response = valyu.search(
    query,
    search_type="news",
    max_num_results=10,
    start_date="2025-10-01",
)

print(response)
