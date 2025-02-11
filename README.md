# Valyu SDK

Connect your AI applications to high-quality proprietary data with Valyu, an AI context engine built by AI Engineers, for AI Engineers.

## Why Valyu?

- **Ready-to-use RAG Data**: All data is returned in Markdown format, optimized for AI consumption
- **Multimodal Support**: Retrieve text, images, and other data types to provide comprehensive answers
- **Pay-per-use**: Transparent pricing model where you only pay for what you use
- **Hybrid Search**: Combine proprietary dataset access with web search capabilities
- **Built for AI**: Designed specifically for RAG (Retrieval-Augmented Generation) applications

## Installation

Install the Valyu SDK using pip:
```bash
pip install valyu
```

## Quick Start

Get started in minutes with just a few lines of code:

```python
from valyu import Valyu

# Initialize the Valyu client
valyu = Valyu(api_key="your-api-key")

# Get relevant context for your query
response = valyu.context(
    query="Tell me about ancient civilizations",
    search_type="proprietary",  # Choose between "proprietary" or "public" search
    num_query=5,                # Number of queries to generate
    num_results=3,              # Number of results to return
    max_price=10                # Maximum price willing to pay per thousand queries
)

print(response)
```

## Features

### 1. Context Enrichment
Enhance your AI applications with relevant context from our proprietary datasets:
```python
# Example: Retrieving context about quantitative finance
response = valyu.context(
    query="What are the latest developments in stochastic volatility models for options pricing?",
    search_type="proprietary",
    num_query=10,
    num_results=5,
    max_price=1  # Price per thousand queries
)
```

### 2. Dataset Access
Load complete training/fine-tuning datasets or samples for your AI applications:

```python
from valyu import load_dataset, load_dataset_samples

# Load dataset samples (no API key required)
load_dataset_samples("example_org/example_dataset")

# Load full dataset with API key
load_dataset(api_key="your-api-key", dataset_id="example_org/example_dataset")
```

## Customization Options

- **Search Type**: Choose between proprietary datasets or public web data
- **Query Generation**: Control the number of queries generated for better context matching
- **Result Volume**: Specify the number of results to retrieve
- **Cost Control**: Set maximum price limits per retrieval
- **Data Format**: All results are returned in Markdown format, ready for AI consumption

## Use Cases

- Enhance RAG applications with high-quality proprietary data
- Access curated datasets across various domains (Finance, Healthcare, Technology, etc.)
- Combine proprietary and public data sources for comprehensive AI responses
- Build domain-specific AI applications with expert knowledge

## Getting Started

1. Sign up for a free account at [Valyu](https://exchange.valyu.network)
2. Get your API key from the dashboard
3. Install the SDK and start building

## License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Support

For more information and detailed documentation, visit our [documentation](https://docs.valyu.network).
