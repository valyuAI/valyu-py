# Valyu SDK

**DeepSearch API for AI**

Valyu's Deepsearch API gives AI the context it needs. Integrate trusted, high-quality public and proprietary sources, with full-text multimodal retrieval.

Get **$10 free credits** for the Valyu API when you sign up at [Valyu](https://exchange.valyu.network)!

*No credit card required.*

## How does it work?

We do all the heavy lifting for you - through a single API we provide:

- **Academic & Research Content** - Access millions of scholarly papers and textbooks
- **Real-time Web Search** - Get the latest information from across the internet  
- **Structured Financial Data** - Stock prices, market data, and financial metrics
- **Intelligent Reranking** - Results across all sources are automatically sorted by relevance
- **Transparent Pricing** - Pay only for what you use with clear CPM pricing

## Installation

Install the Valyu SDK using pip:

```bash
pip install valyu
```

## Quick Start

Here's what it looks like, make your first query in just 4 lines of code:

```python
from valyu import Valyu

valyu = Valyu(api_key="your-api-key-here")

response = valyu.search(
    "Implementation details of agentic search-enhanced large reasoning models",
    max_num_results=5,            # Limit to top 5 results
    max_price=10                  # Maximum price per thousand queries (CPM)
)

print(response)

# Feed the results to your AI agent as you would with other search APIs
```

## API Reference

### Search Method

The `search()` method is the core of the Valyu SDK. It accepts a query string as the first parameter, followed by optional configuration parameters.

```python
def search(
    query: str,                                    # Your search query
    search_type: str = "all",                     # "all", "web", or "proprietary"
    max_num_results: int = 10,                    # Maximum results to return (1-20)
    is_tool_call: bool = True,                    # Whether this is an AI tool call
    relevance_threshold: float = 0.5,             # Minimum relevance score (0-1)
    max_price: int = 30,                          # Maximum price per thousand queries (CPM)
    included_sources: List[str] = None,           # Specific sources to search
    excluded_sources: List[str] = None,            # Sources to exclude from search
    country_code: str = None,                     # Country code filter (e.g., "US", "GB")
    response_length: Union[str, int] = None,      # Response length: "short"/"medium"/"large"/"max" or character count
    category: str = None,                         # Category filter
    start_date: str = None,                       # Start date (YYYY-MM-DD)
    end_date: str = None,                         # End date (YYYY-MM-DD)
) -> SearchResponse
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | `str` | *required* | The search query string |
| `search_type` | `str` | `"all"` | Search scope: `"all"`, `"web"`, or `"proprietary"` |
| `max_num_results` | `int` | `10` | Maximum number of results to return (1-20) |
| `is_tool_call` | `bool` | `True` | Whether this is an AI tool call (affects processing) |
| `relevance_threshold` | `float` | `0.5` | Minimum relevance score for results (0.0-1.0) |
| `max_price` | `int` | `30` | Maximum price per thousand queries in CPM |
| `included_sources` | `List[str]` | `None` | Specific data sources or URLs to search |
| `excluded_sources` | `List[str]` | `None` | Data sources or URLs to exclude from search |
| `country_code` | `str` | `None` | Country code filter (e.g., "US", "GB", "JP", "ALL") |
| `response_length` | `Union[str, int]` | `None` | Response length: "short"/"medium"/"large"/"max" or character count |
| `category` | `str` | `None` | Category filter for results |
| `start_date` | `str` | `None` | Start date filter in YYYY-MM-DD format |
| `end_date` | `str` | `None` | End date filter in YYYY-MM-DD format |

### Response Format

The search method returns a `SearchResponse` object with the following structure:

```python
class SearchResponse:
    success: bool                           # Whether the search was successful
    error: Optional[str]                    # Error message if any
    tx_id: str                             # Transaction ID for feedback
    query: str                             # The original query
    results: List[SearchResult]            # List of search results
    results_by_source: ResultsBySource     # Count of results by source type
    total_deduction_pcm: float             # Cost in CPM
    total_deduction_dollars: float         # Cost in dollars
    total_characters: int                  # Total characters returned
```

Each `SearchResult` contains:

```python
class SearchResult:
    title: str                             # Result title
    url: str                              # Source URL
    content: Union[str, List[Dict]]       # Full content (text or structured)
    description: Optional[str]            # Brief description
    source: str                           # Source identifier
    price: float                          # Cost for this result
    length: int                           # Content length in characters
    image_url: Optional[Dict[str, str]]   # Associated images
    relevance_score: float                # Relevance score (0-1)
    data_type: Optional[str]              # "structured" or "unstructured"
```

## Examples

### Basic Search

```python
from valyu import Valyu

valyu = Valyu("your-api-key")

# Simple search across all sources
response = valyu.search("What is machine learning?")
print(f"Found {len(response.results)} results")
```

### Academic Research

```python
# Search academic papers on arXiv
response = valyu.search(
    "transformer architecture improvements",
    search_type="proprietary",
    included_sources=["valyu/valyu-arxiv"],
    relevance_threshold=0.7,
    max_num_results=10
)
```

### Web Search with Date Filtering

```python
# Search recent web content
response = valyu.search(
    "AI safety developments",
    search_type="web",
    start_date="2024-01-01",
    end_date="2024-12-31",
    max_num_results=5
)
```

### Hybrid Search

```python
# Search both web and proprietary sources
response = valyu.search(
    "quantum computing breakthroughs",
    search_type="all",
    category="technology",
    relevance_threshold=0.6,
    max_price=50
)
```

### Processing Results

```python
response = valyu.search("climate change solutions")

if response.success:
    print(f"Search cost: ${response.total_deduction_dollars:.4f}")
    print(f"Sources: Web={response.results_by_source.web}, Proprietary={response.results_by_source.proprietary}")
    
    for i, result in enumerate(response.results, 1):
        print(f"\n{i}. {result.title}")
        print(f"   Source: {result.source}")
        print(f"   Relevance: {result.relevance_score:.2f}")
        print(f"   Content: {result.content[:200]}...")
else:
    print(f"Search failed: {response.error}")
```

## Authentication

Set your API key in one of these ways:

1. **Environment variable** (recommended):
   ```bash
   export VALYU_API_KEY="your-api-key-here"
   ```

2. **Direct initialization**:
   ```python
   valyu = Valyu(api_key="your-api-key-here")
   ```

## Error Handling

The SDK handles errors gracefully and returns structured error responses:

```python
response = valyu.search("test query")

if not response.success:
    print(f"Error: {response.error}")
    print(f"Transaction ID: {response.tx_id}")
else:
    # Process successful results
    for result in response.results:
        print(result.title)
```

## Getting Started

1. Sign up for a free account at [Valyu](https://exchange.valyu.network)
2. Get your API key from the dashboard  
3. Install the SDK: `pip install valyu`
4. Start building with the examples above

## Support

- **Documentation**: [docs.valyu.network](https://docs.valyu.network)
- **API Reference**: Full parameter documentation above
- **Examples**: Check the `examples/` directory in this repository
- **Issues**: Report bugs on GitHub

## License

This project is licensed under the MIT License.
