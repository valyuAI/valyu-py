import os
from valyu import Valyu
from dotenv import load_dotenv

load_dotenv()

VALYU_API_KEY = os.environ.get("VALYU_API_KEY")

if not VALYU_API_KEY:
    raise ValueError("VALYU_API_KEY environment variable not set!")

valyu = Valyu(VALYU_API_KEY)

# News search for recent AI developments
print("📰 News Search - AI Developments")
query = "latest developments in artificial intelligence"
print(f"Query: {query}")
response = valyu.search(
    query,
    search_type="news",
    max_num_results=10,
    start_date="2025-01-01",
)

print(response)

print("\n" + "=" * 50 + "\n")

# News search with country filtering
print("📰 News Search - Tech News in UK")
query = "technology startups"
print(f"Query: {query}")
response = valyu.search(
    query,
    search_type="news",
    max_num_results=5,
    country_code="UK",
)

print(response)

print("\n" + "=" * 50 + "\n")

# News search with date range
print("📰 News Search - Climate News (Date Range)")
query = "climate change policy"
print(f"Query: {query}")
response = valyu.search(
    query,
    search_type="news",
    max_num_results=8,
    start_date="2025-10-01",
    end_date="2025-11-15",
)

print(response)
