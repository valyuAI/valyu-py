import json
import requests
from pydantic import BaseModel
from typing import Optional, List, Literal, Union, Dict, Any
from valyu.types.response import SearchResponse, SearchType, ResultsBySource
from valyu.types.contents import (
    ContentsResponse,
    ContentsResult,
    ExtractEffort,
    ContentsResponseLength,
)
from valyu.types.answer import (
    AnswerResponse,
    AnswerSuccessResponse,
    AnswerErrorResponse,
    SearchMetadata,
    AIUsage,
    SUPPORTED_COUNTRY_CODES,
)
from valyu.validation import validate_sources, format_validation_error
import os

# Supported country codes for the country_code parameter - simplified for typing
CountryCode = str  # Any of the codes in SUPPORTED_COUNTRY_CODES

# Response length options
ResponseLength = Union[Literal["short", "medium", "large", "max"], int]


class ErrorResponse(BaseModel):
    success: bool
    error: str


class Valyu:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.valyu.ai/v1",
    ):
        """
        Initialize the Valyu client.

        Args:
            api_key (Optional[str]): The API key to use for the client. If not provided, will attempt to read from VALYU_API_KEY environment variable.
            base_url (str): The base URL for the Valyu API.
        """
        if api_key is None:
            api_key = os.getenv("VALYU_API_KEY")
            if not api_key:
                raise ValueError("VALYU_API_KEY is not set")

        self.base_url = base_url
        self.headers = {"Content-Type": "application/json", "x-api-key": api_key}

    def search(
        self,
        query: str,
        search_type: SearchType = "all",
        max_num_results: int = 10,
        is_tool_call: Optional[bool] = True,
        relevance_threshold: Optional[float] = 0.5,
        max_price: int = 30,
        included_sources: Optional[List[str]] = None,
        excluded_sources: Optional[List[str]] = None,
        country_code: Optional[CountryCode] = None,
        response_length: Optional[ResponseLength] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fast_mode: bool = False,
    ) -> Optional[SearchResponse]:
        """
        Query the Valyu DeepSearch API to give your AI relevant context.

        Args:
            query (str): The query string.
            search_type (SearchType): The type of search to perform.
            max_num_results (int): The maximum number of search results to return.
            is_tool_call (Optional[bool]): Whether this is a tool call.
            relevance_threshold (Optional[float]): The relevance threshold to not return results below.
            max_price (int): The maximum price (per thousand queries) to spend on the search.
            included_sources (Optional[List[str]]): The data sources to use for the search.
                Sources must be formatted as one of:
                • Domain: 'example.com', 'news.ycombinator.com'
                • URL with path: 'https://arxiv.org/abs/1706.03762'
                • Dataset name: 'valyu/valyu-arxiv', 'wiley/wiley-finance-books'
            excluded_sources (Optional[List[str]]): The data sources to exclude from the search.
                Sources must be formatted as one of:
                • Domain: 'paperswithcode.com', 'wikipedia.org'
                • URL with path: 'https://example.com/path/to/page'
                • Dataset name: 'provider/dataset-name'
            country_code (Optional[CountryCode]): Country code filter for search results.
            response_length (Optional[ResponseLength]): Length of response content - "short", "medium", "large", "max", or integer for character count.
            category (Optional[str]): Category filter for search results.
            start_date (Optional[str]): Start date filter in YYYY-MM-DD format.
            end_date (Optional[str]): End date filter in YYYY-MM-DD format.
            fast_mode (bool): Enable fast mode for faster but shorter results. Good for general purpose queries. Defaults to False.

        Returns:
            Optional[SearchResponse]: The search response.
        """
        try:
            # Validate included_sources if provided
            if included_sources is not None:
                is_valid, invalid_sources = validate_sources(included_sources)
                if not is_valid:
                    return SearchResponse(
                        success=False,
                        error=format_validation_error(invalid_sources),
                        tx_id="validation-error-included",
                        query=query,
                        results=[],
                        results_by_source=ResultsBySource(web=0, proprietary=0),
                        total_deduction_pcm=0.0,
                        total_deduction_dollars=0.0,
                        total_characters=0,
                    )

            # Validate excluded_sources if provided
            if excluded_sources is not None:
                is_valid, invalid_sources = validate_sources(excluded_sources)
                if not is_valid:
                    return SearchResponse(
                        success=False,
                        error=format_validation_error(invalid_sources),
                        tx_id="validation-error-excluded",
                        query=query,
                        results=[],
                        results_by_source=ResultsBySource(web=0, proprietary=0),
                        total_deduction_pcm=0.0,
                        total_deduction_dollars=0.0,
                        total_characters=0,
                    )

            # Validate country_code if provided
            if (
                country_code is not None
                and country_code.upper() not in SUPPORTED_COUNTRY_CODES
            ):
                return SearchResponse(
                    success=False,
                    error=f"Invalid country_code. Must be one of: {', '.join(sorted(SUPPORTED_COUNTRY_CODES))}",
                    tx_id="validation-error-country",
                    query=query,
                    results=[],
                    results_by_source=ResultsBySource(web=0, proprietary=0),
                    total_deduction_pcm=0.0,
                    total_deduction_dollars=0.0,
                    total_characters=0,
                )

            payload = {
                "query": query,
                "search_type": search_type,
                "max_num_results": max_num_results,
                "is_tool_call": is_tool_call,
                "relevance_threshold": relevance_threshold,
                "max_price": max_price,
                "fast_mode": fast_mode,
            }

            if included_sources is not None:
                payload["included_sources"] = included_sources

            if excluded_sources is not None:
                payload["excluded_sources"] = excluded_sources

            if country_code is not None:
                payload["country_code"] = country_code.upper()

            if response_length is not None:
                payload["response_length"] = response_length

            if category is not None:
                payload["category"] = category

            if start_date is not None:
                payload["start_date"] = start_date

            if end_date is not None:
                payload["end_date"] = end_date

            response = requests.post(
                f"{self.base_url}/deepsearch", json=payload, headers=self.headers
            )

            data = response.json()

            if not response.ok:
                return SearchResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                    tx_id=data.get("tx_id", f"error-{response.status_code}"),
                    query=query,
                    results=[],
                    results_by_source=ResultsBySource(web=0, proprietary=0),
                    total_deduction_pcm=0.0,
                    total_deduction_dollars=0.0,
                    total_characters=0,
                )

            if not data.get("results") and data.get("error"):
                return SearchResponse(
                    success=True,
                    error=data.get("error"),
                    tx_id=data.get("tx_id", "0x0"),
                    query=data.get("query", query),
                    results=[],
                    results_by_source=data.get(
                        "results_by_source", ResultsBySource(web=0, proprietary=0)
                    ),
                    total_deduction_pcm=data.get("total_deduction_pcm", 0.0),
                    total_deduction_dollars=data.get("total_deduction_dollars", 0.0),
                    total_characters=data.get("total_characters", 0),
                )

            return SearchResponse(**data)
        except Exception as e:
            return SearchResponse(
                success=False,
                error=str(e),
                tx_id="exception-" + str(hash(str(e)))[:8],
                query=query,
                results=[],
                results_by_source=ResultsBySource(web=0, proprietary=0),
                total_deduction_pcm=0.0,
                total_deduction_dollars=0.0,
                total_characters=0,
            )

    def contents(
        self,
        urls: List[str],
        summary: Optional[Union[bool, str, Dict[str, Any]]] = None,
        extract_effort: Optional[ExtractEffort] = None,
        response_length: Optional[ContentsResponseLength] = None,
        max_price_dollars: Optional[float] = None,
    ) -> Optional[ContentsResponse]:
        """
        Extract clean, structured content from web pages with optional AI-powered data extraction and summarization.

        Args:
            urls (List[str]): List of URLs to process (maximum 10 URLs per request).
            summary (Optional[Union[bool, str, Dict[str, Any]]]): AI summary configuration:
                - False/None: No AI processing (raw content)
                - True: Basic automatic summarization
                - str: Custom instructions (max 500 chars)
                - dict: JSON schema for structured extraction
            extract_effort (Optional[ExtractEffort]): Extraction thoroughness:
                - "normal": Fast extraction (default)
                - "high": More thorough but slower
                - "auto": Automatically determine extraction effort but slowest
            response_length (Optional[ContentsResponseLength]): Content length per URL:
                - "short": 25,000 characters (default)
                - "medium": 50,000 characters
                - "large": 100,000 characters
                - "max": No limit
                - int: Custom character limit
            max_price_dollars (Optional[float]): Maximum cost limit in USD.

        Returns:
            Optional[ContentsResponse]: The contents extraction response.
        """
        try:
            if len(urls) > 10:
                return ContentsResponse(
                    success=False,
                    error="Maximum 10 URLs allowed per request",
                    tx_id="error-max-urls",
                    urls_requested=len(urls),
                    urls_processed=0,
                    urls_failed=len(urls),
                    results=[],
                    total_cost_dollars=0.0,
                    total_characters=0,
                )

            payload = {
                "urls": urls,
            }

            if summary is not None:
                payload["summary"] = summary

            if extract_effort is not None:
                payload["extract_effort"] = extract_effort

            if response_length is not None:
                payload["response_length"] = response_length

            if max_price_dollars is not None:
                payload["max_price_dollars"] = max_price_dollars

            response = requests.post(
                f"{self.base_url}/contents", json=payload, headers=self.headers
            )

            data = response.json()

            if not response.ok:
                return ContentsResponse(
                    success=False,
                    error=data.get("error", f"HTTP Error: {response.status_code}"),
                    tx_id=data.get("tx_id", f"error-{response.status_code}"),
                    urls_requested=len(urls),
                    urls_processed=0,
                    urls_failed=len(urls),
                    results=[],
                    total_cost_dollars=0.0,
                    total_characters=0,
                )

            return ContentsResponse(**data)
        except Exception as e:
            return ContentsResponse(
                success=False,
                error=str(e),
                tx_id="exception-" + str(hash(str(e)))[:8],
                urls_requested=len(urls),
                urls_processed=0,
                urls_failed=len(urls),
                results=[],
                total_cost_dollars=0.0,
                total_characters=0,
            )

    def answer(
        self,
        query: str,
        structured_output: Optional[Dict[str, Any]] = None,
        system_instructions: Optional[str] = None,
        search_type: SearchType = "all",
        data_max_price: float = 30.0,
        country_code: Optional[str] = None,
        included_sources: Optional[List[str]] = None,
        excluded_sources: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fast_mode: bool = False,
    ) -> Optional[AnswerResponse]:
        """
        Query the Valyu Answer API to get AI-processed answers to your questions.

        Args:
            query (str): The query string.
            structured_output (Optional[Dict[str, Any]]): JSON Schema object. When provided,
                the response 'contents' is structured to this schema.
            system_instructions (Optional[str]): Custom system-level instructions (<= 2000 chars).
            search_type (SearchType): The type of search to perform.
            data_max_price (float): Maximum spend (USD) for data retrieval. Separate from AI costs.
            country_code (Optional[str]): 2-letter ISO code or 'ALL'.
            included_sources (Optional[List[str]]): The data sources to use for the search.
                Sources must be formatted as one of:
                • Domain: 'example.com', 'news.ycombinator.com'
                • URL with path: 'https://arxiv.org/abs/1706.03762'
                • Dataset name: 'valyu/valyu-arxiv', 'wiley/wiley-finance-books'
            excluded_sources (Optional[List[str]]): The data sources to exclude from the search.
                Sources must be formatted as one of:
                • Domain: 'paperswithcode.com', 'wikipedia.org'
                • URL with path: 'https://example.com/path/to/page'
                • Dataset name: 'provider/dataset-name'
            start_date (Optional[str]): Start date filter in YYYY-MM-DD format.
            end_date (Optional[str]): End date filter in YYYY-MM-DD format.
            fast_mode (bool): Enable fast mode for faster but shorter results. Good for general purpose queries. Defaults to False.

        Returns:
            Optional[AnswerResponse]: The answer response.
        """
        try:
            # Validate included_sources if provided
            if included_sources is not None:
                is_valid, invalid_sources = validate_sources(included_sources)
                if not is_valid:
                    return AnswerErrorResponse(
                        error=format_validation_error(invalid_sources)
                    )

            # Validate excluded_sources if provided
            if excluded_sources is not None:
                is_valid, invalid_sources = validate_sources(excluded_sources)
                if not is_valid:
                    return AnswerErrorResponse(
                        error=format_validation_error(invalid_sources)
                    )

            # Validate country_code if provided
            if (
                country_code is not None
                and country_code.upper() not in SUPPORTED_COUNTRY_CODES
            ):
                return AnswerErrorResponse(
                    error=f"Invalid country_code. Must be one of: {', '.join(sorted(SUPPORTED_COUNTRY_CODES))}"
                )

            # Validate system_instructions length
            if (
                system_instructions is not None
                and len(system_instructions.strip()) > 2000
            ):
                return AnswerErrorResponse(
                    error="system_instructions cannot exceed 2000 characters"
                )

            payload = {
                "query": query,
                "search_type": search_type,
                "data_max_price": data_max_price,
                "fast_mode": fast_mode,
            }

            if structured_output is not None:
                payload["structured_output"] = structured_output

            if system_instructions is not None:
                payload["system_instructions"] = system_instructions.strip()

            if country_code is not None:
                payload["country_code"] = country_code.upper()

            if included_sources is not None:
                payload["included_sources"] = included_sources

            if excluded_sources is not None:
                payload["excluded_sources"] = excluded_sources

            if start_date is not None:
                payload["start_date"] = start_date

            if end_date is not None:
                payload["end_date"] = end_date

            response = requests.post(
                f"{self.base_url}/answer", json=payload, headers=self.headers
            )

            data = response.json()

            if not response.ok:
                return AnswerErrorResponse(
                    error=data.get("error", f"HTTP Error: {response.status_code}")
                )

            return AnswerSuccessResponse(**data)
        except Exception as e:
            return AnswerErrorResponse(error=str(e))
