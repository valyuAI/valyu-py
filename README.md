# Valyu SDK

**Search for AIs**

Valyu's Deepsearch API gives AI the context it needs. Integrate trusted, high-quality public and proprietary sources, with full-text multimodal retrieval.

Get **$10 free credits** for the Valyu API when you sign up at [Valyu](https://platform.valyu.ai)!

_No credit card required._

## How does it work?

We do all the heavy lifting for you - one unified API for all data:

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
    max_price=10,                 # Maximum price per thousand queries (CPM)
    fast_mode=True                # Enable fast mode for quicker, shorter results
)

print(response)

# Feed the results to your AI agent as you would with other search APIs
```

## API Reference

### DeepResearch Method

The `deepresearch` namespace provides access to Valyu's AI-powered research agent that conducts comprehensive, multi-step research with citations and cost tracking.

```python
# Create a research task
task = valyu.deepresearch.create(
    input="What are the latest developments in quantum computing?",
    model="lite",                      # "lite" (fast, Haiku) or "heavy" (thorough, Sonnet)
    output_formats=["markdown", "pdf"] # Output formats
)

# Wait for completion with progress updates
def on_progress(status):
    if status.progress:
        print(f"Step {status.progress.current_step}/{status.progress.total_steps}")

result = valyu.deepresearch.wait(task.deepresearch_id, on_progress=on_progress)

print(result.output)  # Markdown report
print(result.pdf_url) # PDF download URL
```

#### DeepResearch Methods

| Method | Description |
|--------|-------------|
| `create(...)` | Create a new research task |
| `status(task_id)` | Get current status of a task |
| `wait(task_id, ...)` | Wait for task completion with polling |
| `stream(task_id, ...)` | Stream real-time updates |
| `list(api_key_id, limit)` | List all your research tasks |
| `update(task_id, instruction)` | Add follow-up instruction to running task |
| `cancel(task_id)` | Cancel a running task |
| `delete(task_id)` | Delete a task |
| `toggle_public(task_id, is_public)` | Make task publicly accessible |

#### DeepResearch Create Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `input` | `str` | *required* | Research query or task description |
| `model` | `str` | `"lite"` | Research model - "lite" (fast) or "heavy" (thorough) |
| `output_formats` | `List[str]` | `["markdown"]` | Output formats for the report |
| `strategy` | `str` | `None` | Natural language research strategy |
| `search` | `dict` | `None` | Search configuration (type, sources) |
| `urls` | `List[str]` | `None` | URLs to extract and analyze |
| `files` | `List[dict]` | `None` | PDF/image files to analyze |
| `mcp_servers` | `List[dict]` | `None` | MCP tool server configurations |
| `code_execution` | `bool` | `True` | Enable/disable code execution |
| `previous_reports` | `List[str]` | `None` | Previous report IDs for context (max 3) |
| `webhook_url` | `str` | `None` | HTTPS webhook URL for completion notification |
| `metadata` | `dict` | `None` | Custom metadata key-value pairs |

#### DeepResearch Examples

**Basic Research:**
```python
task = valyu.deepresearch.create(
    input="Summarize recent AI safety research",
    model="lite"
)

result = valyu.deepresearch.wait(task.deepresearch_id)
print(result.output)
```

**With Custom Sources:**
```python
task = valyu.deepresearch.create(
    input="Latest transformer architecture improvements",
    search={
        "search_type": "proprietary",
        "included_sources": ["valyu/valyu-arxiv"]
    },
    model="heavy",
    output_formats=["markdown", "pdf"]
)
```

**Streaming Updates:**
```python
def on_progress(current, total):
    print(f"Progress: {current}/{total}")

def on_complete(result):
    print("Complete! Cost:", result.usage.total_cost)

valyu.deepresearch.stream(
    task.deepresearch_id,
    on_progress=on_progress,
    on_complete=on_complete
)
```

**With File Analysis:**
```python
task = valyu.deepresearch.create(
    input="Analyze these research papers and provide key insights",
    files=[{
        "data": "data:application/pdf;base64,...",
        "filename": "paper.pdf",
        "media_type": "application/pdf"
    }],
    urls=["https://arxiv.org/abs/2103.14030"]
)
```

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
    fast_mode: bool = False,                      # Enable fast mode for faster but shorter results
) -> SearchResponse
```

### Parameters

| Parameter             | Type              | Default    | Description                                                                       |
| --------------------- | ----------------- | ---------- | --------------------------------------------------------------------------------- |
| `query`               | `str`             | _required_ | The search query string                                                           |
| `search_type`         | `str`             | `"all"`    | Search scope: `"all"`, `"web"`, or `"proprietary"`                                |
| `max_num_results`     | `int`             | `10`       | Maximum number of results to return (1-20)                                        |
| `is_tool_call`        | `bool`            | `True`     | Whether this is an AI tool call (affects processing)                              |
| `relevance_threshold` | `float`           | `0.5`      | Minimum relevance score for results (0.0-1.0)                                     |
| `max_price`           | `int`             | `30`       | Maximum price per thousand queries in CPM                                         |
| `included_sources`    | `List[str]`       | `None`     | Specific data sources or URLs to search                                           |
| `excluded_sources`    | `List[str]`       | `None`     | Data sources or URLs to exclude from search                                       |
| `country_code`        | `str`             | `None`     | Country code filter (e.g., "US", "GB", "JP", "ALL")                               |
| `response_length`     | `Union[str, int]` | `None`     | Response length: "short"/"medium"/"large"/"max" or character count                |
| `category`            | `str`             | `None`     | Category filter for results                                                       |
| `start_date`          | `str`             | `None`     | Start date filter in YYYY-MM-DD format                                            |
| `end_date`            | `str`             | `None`     | End date filter in YYYY-MM-DD format                                              |
| `fast_mode`           | `bool`            | `False`    | Enable fast mode for faster but shorter results. Good for general purpose queries |

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

### Contents Method

The `contents()` method extracts clean, structured content from web pages with optional AI-powered data extraction and summarization.

```python
def contents(
    urls: List[str],                                      # List of URLs to process (max 10)
    summary: Union[bool, str, Dict] = None,              # AI summary configuration
    extract_effort: str = None,                          # "normal" or "high"
    response_length: Union[str, int] = None,             # Content length configuration
    max_price_dollars: float = None,                     # Maximum cost limit in USD
) -> ContentsResponse
```

### Parameters

| Parameter           | Type                     | Default    | Description                                                                                                                                                                                                               |
| ------------------- | ------------------------ | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `urls`              | `List[str]`              | _required_ | List of URLs to process (maximum 10 URLs per request)                                                                                                                                                                     |
| `summary`           | `Union[bool, str, Dict]` | `None`     | AI summary configuration:<br>- `False/None`: No AI processing (raw content)<br>- `True`: Basic automatic summarization<br>- `str`: Custom instructions (max 500 chars)<br>- `dict`: JSON schema for structured extraction |
| `extract_effort`    | `str`                    | `None`     | Extraction thoroughness: `"normal"` (fast) or `"high"` (thorough but slower)                                                                                                                                              |
| `response_length`   | `Union[str, int]`        | `None`     | Content length per URL:<br>- `"short"`: 25,000 characters<br>- `"medium"`: 50,000 characters<br>- `"large"`: 100,000 characters<br>- `"max"`: No limit<br>- `int`: Custom character limit                                 |
| `max_price_dollars` | `float`                  | `None`     | Maximum cost limit in USD                                                                                                                                                                                                 |

### Response Format

The contents method returns a `ContentsResponse` object:

```python
class ContentsResponse:
    success: bool                          # Whether the request was successful
    error: Optional[str]                   # Error message if any
    tx_id: str                            # Transaction ID for tracking
    urls_requested: int                   # Number of URLs submitted
    urls_processed: int                   # Number of URLs successfully processed
    urls_failed: int                      # Number of URLs that failed
    results: List[ContentsResult]        # List of extraction results
    total_cost_dollars: float             # Total cost in dollars
    total_characters: int                 # Total characters extracted
```

Each `ContentsResult` contains:

```python
class ContentsResult:
    url: str                              # Source URL
    title: str                            # Page/document title
    content: Union[str, int, float]       # Extracted content
    length: int                           # Content length in characters
    source: str                           # Data source identifier
    summary: Optional[Union[str, Dict]]   # AI-generated summary or structured data
    summary_success: Optional[bool]       # Whether summary generation succeeded
    data_type: Optional[str]              # Type of data extracted
    image_url: Optional[Dict[str, str]]   # Extracted images
    citation: Optional[str]               # APA-style citation
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

### Content Extraction Examples

#### Basic Content Extraction

```python
# Extract raw content from URLs
response = valyu.contents(
    urls=["https://techcrunch.com/2025/08/28/anthropic-users-face-a-new-choice-opt-out-or-share-your-data-for-ai-training/"]
)

if response.success:
    for result in response.results:
        print(f"Title: {result.title}")
        print(f"Content: {result.content[:500]}...")
```

#### Content with AI Summary

```python
# Extract content with automatic summarization
response = valyu.contents(
    urls=["https://docs.python.org/3/tutorial/"],
    summary=True,
    response_length="max"
)

for result in response.results:
    print(f"Summary: {result.summary}")
```

#### Structured Data Extraction

```python
# Extract structured data using JSON schema
company_schema = {
    "type": "object",
    "properties": {
        "company_name": {"type": "string"},
        "founded_year": {"type": "integer"},
        "key_products": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 3
        }
    }
}

response = valyu.contents(
    urls=["https://en.wikipedia.org/wiki/OpenAI"],
    summary=company_schema,
    response_length="max"
)

if response.success:
    for result in response.results:
        if result.summary:
            print(f"Structured data: {json.dumps(result.summary, indent=2)}")
```

#### Multiple URLs

```python
# Process multiple URLs with a cost limit
response = valyu.contents(
    urls=[
        "https://www.valyu.ai/",
        "https://docs.valyu.ai/overview",
        "https://www.valyu.ai/blogs/why-ai-agents-and-llms-struggle-with-search-and-data-access"
    ],
    summary="Provide key takeaways in bullet points, and write in very emphasised singaporean english"
)

print(f"Processed {response.urls_processed}/{response.urls_requested} URLs")
print(f"Cost: ${response.total_cost_dollars:.4f}")
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

1. Sign up for a free account at [Valyu](https://platform.valyu.ai)
2. Get your API key from the dashboard
3. Install the SDK: `pip install valyu`
4. Start building with the examples above

## Support

- **Documentation**: [docs.valyu.ai](https://docs.valyu.ai)
- **API Reference**: Full parameter documentation above
- **Examples**: Check the `examples/` directory in this repository
- **Issues**: Report bugs on GitHub

## License

This project is licensed under the MIT License.
