# Valyu Python SDK

[![PyPI version](https://img.shields.io/pypi/v/valyu.svg)](https://pypi.org/project/valyu/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

Search and research APIs built for AI agents. Access web and proprietary data sources through Search, extract content from URLs, generate grounded answers, and run multi-step research with DeepResearch - all through a single SDK.

[Documentation](https://docs.valyu.ai) | [API Reference](https://docs.valyu.ai/api-reference) | [Platform](https://platform.valyu.ai)

## Installation

```bash
pip install valyu
```

## Quick Start

```python
from valyu import Valyu

valyu = Valyu()  # uses VALYU_API_KEY env var

response = valyu.search(
    "latest advances in transformer architectures",
    max_num_results=5,
    search_type="all",
)

for result in response.results:
    print(result.title, result.url)
```

Get **$10 free credits** when you sign up at [platform.valyu.ai](https://platform.valyu.ai). No credit card required.

## APIs

### Search

Search across web and proprietary data sources with a single query.

```python
response = valyu.search(
    "CRISPR gene therapy clinical trials 2026",
    search_type="proprietary",                     # "all", "web", or "proprietary"
    max_num_results=10,                            # 1-20 results
    included_sources=["valyu/valyu-pubmed"],        # filter to specific sources
    start_date="2026-01-01",                       # date filtering
    end_date="2026-12-31",
)
```

<details>
<summary>All search parameters</summary>

| Parameter | Type | Default | Description |
|---|---|---|---|
| `query` | `str` | required | Search query |
| `search_type` | `str` | `"all"` | `"all"`, `"web"`, or `"proprietary"` |
| `max_num_results` | `int` | `10` | Results to return (1-20) |
| `max_price` | `int` | `30` | Max price per thousand queries (CPM) |
| `relevance_threshold` | `float` | `0.5` | Min relevance score (0-1) |
| `included_sources` | `List[str]` | `None` | Sources to search |
| `excluded_sources` | `List[str]` | `None` | Sources to exclude |
| `start_date` | `str` | `None` | Start date (YYYY-MM-DD) |
| `end_date` | `str` | `None` | End date (YYYY-MM-DD) |
| `country_code` | `str` | `None` | Country filter (e.g. `"US"`, `"GB"`) |
| `response_length` | `str \| int` | `None` | `"short"`, `"medium"`, `"large"`, `"max"`, or character count |
| `category` | `str` | `None` | Category filter |
| `fast_mode` | `bool` | `False` | Faster results, shorter content |

</details>

### Contents

Extract clean, structured content from URLs. Supports sync (1-10 URLs) and async (up to 50 URLs) modes.

```python
# Basic extraction
response = valyu.contents(["https://arxiv.org/abs/2301.00001"])

# With AI summarization
response = valyu.contents(
    ["https://example.com/article"],
    summary=True,
    response_length="medium",
)

# Structured data extraction with JSON schema
response = valyu.contents(
    ["https://en.wikipedia.org/wiki/OpenAI"],
    summary={
        "type": "object",
        "properties": {
            "company_name": {"type": "string"},
            "founded_year": {"type": "integer"},
        },
    },
)
```

### Answer

AI-generated answers grounded by Valyu's search. Supports streaming.

```python
response = valyu.answer(
    "What are the side effects of metformin?",
    search_type="proprietary",
    included_sources=["valyu/valyu-pubmed"],
)

print(response.contents)        # AI-generated answer
print(response.search_results)  # Source citations
```

### DeepResearch

Multi-step research agent that produces comprehensive reports with citations.

```python
# Start a research task
task = valyu.deepresearch.create(
    input="Compare CRISPR and base editing approaches for sickle cell disease",
    model="heavy",
    output_formats=["markdown", "pdf"],
)

# Wait for completion with progress
def on_progress(status):
    print(f"Step {status.progress.current_step}/{status.progress.total_steps}")

result = valyu.deepresearch.wait(task.deepresearch_id, on_progress=on_progress)

print(result.output)   # Markdown report
print(result.pdf_url)  # PDF download link
```

<details>
<summary>All DeepResearch methods</summary>

| Method | Description |
|---|---|
| `create(...)` | Start a new research task |
| `status(task_id)` | Get task status |
| `wait(task_id, ...)` | Poll until completion |
| `stream(task_id, ...)` | Stream real-time updates |
| `list(api_key_id, limit)` | List research tasks |
| `update(task_id, instruction)` | Add follow-up instruction |
| `cancel(task_id)` | Cancel a running task |
| `delete(task_id)` | Delete a task |
| `toggle_public(task_id, is_public)` | Toggle public access |

</details>

### Batch

Run multiple DeepResearch tasks in parallel.

```python
batch = valyu.batch.create(
    name="Q1 Analysis",
    mode="fast",
    output_formats=["markdown"],
)

valyu.batch.add_tasks(batch.batch_id, tasks=[
    {"query": "Analyze recent SPAC performance"},
    {"query": "Review semiconductor supply chain trends"},
])

result = valyu.batch.wait_for_completion(
    batch.batch_id,
    on_progress=lambda b: print(f"{b.counts.completed}/{b.counts.total}"),
)
```

### Workflows

Templated DeepResearch starting points - curated by Valyu or created by your org - with typed `{variable}` placeholders and version history.

```python
# Browse curated workflows
catalog = valyu.workflows.list(scope="valyu", vertical="investment-banking")
for wf in catalog.workflows:
    print(wf.slug, "-", wf.title)

# Run one as a DeepResearch task
task = valyu.deepresearch.create(
    workflow_id="ib-company-profile",
    workflow_params={"company": "NVIDIA (NVDA)"},
)

result = valyu.deepresearch.wait(task.deepresearch_id)
print(result.output)
```

Create your own:

```python
valyu.workflows.create(
    slug="weekly-competitor-scan",
    title="Weekly Competitor Scan",
    version={
        "prompt": "Summarize the week's most important developments at {company}.",
        "strategy": "Prioritize primary sources: filings, press releases, earnings calls.",
        "report_format": "Bullet-point briefing, grouped by theme.",
        "variables": [{"key": "company", "label": "Company", "required": True}],
    },
)
```

<details>
<summary>All Workflows methods</summary>

| Method | Description |
|---|---|
| `list(vertical, scope, q, tags, limit, expand)` | List available workflows |
| `get(slug, version)` | Get a workflow's full template |
| `versions(slug)` | List a workflow's version history |
| `preview(slug, workflow_params, workflow_version)` | Resolve the template without creating a task |
| `create(slug, title, version, ...)` | Create an org workflow |
| `update(slug, ..., version, set_current)` | Update metadata and/or publish a new version |
| `delete(slug)` | Delete an org workflow |

</details>

### Data Sources

List available data sources programmatically.

```python
sources = valyu.datasources.list()
categories = valyu.datasources.categories()
```

## Authentication

```bash
export VALYU_API_KEY="your-api-key"
```

Or pass directly:

```python
valyu = Valyu(api_key="your-api-key")
```

## Type Safety

All request and response models use Pydantic v2:

```python
from valyu.types.response import SearchResult, SearchResponse
from valyu.types.contents import ContentsResponse
from valyu.types.answer import AnswerSuccessResponse
```

## Error Handling

```python
response = valyu.search("test")

if not response.success:
    print(f"Error: {response.error}")
    print(f"tx_id: {response.tx_id}")
```

## Integrations

Valyu works with [LangChain](https://docs.valyu.ai), [OpenAI](https://docs.valyu.ai), [Anthropic](https://docs.valyu.ai), [MCP](https://docs.valyu.ai), and more. See [docs.valyu.ai](https://docs.valyu.ai) for integration guides.

## Links

- [Documentation](https://docs.valyu.ai)
- [Platform & API Keys](https://platform.valyu.ai)
- [Discord](https://discord.gg/valyu)
- [GitHub Issues](https://github.com/valyuAI/valyu-py/issues)

## License

MIT
