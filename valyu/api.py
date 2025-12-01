import json
import requests
import time
from pydantic import BaseModel
from typing import Optional, List, Literal, Union, Dict, Any, Callable, Generator
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
    AnswerStreamChunk,
    AnswerStreamGenerator,
    SearchMetadata,
    SearchResult,
    AIUsage,
    CostBreakdown,
    ExtractionMetadata,
    SUPPORTED_COUNTRY_CODES,
)
from valyu.types.deepresearch import (
    DeepResearchMode,
    DeepResearchStatus,
    FileAttachment,
    MCPServerConfig,
    SearchConfig,
    DeepResearchCreateResponse,
    DeepResearchStatusResponse,
    DeepResearchListResponse,
    DeepResearchUpdateResponse,
    DeepResearchCancelResponse,
    DeepResearchDeleteResponse,
    DeepResearchTogglePublicResponse,
)
from valyu.validation import validate_sources, format_validation_error
from valyu.deepresearch_client import DeepResearchClient
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

        # Initialize DeepResearch client
        self.deepresearch = DeepResearchClient(self)

    def search(
        self,
        query: str,
        search_type: SearchType = "all",
        max_num_results: int = 10,
        is_tool_call: Optional[bool] = True,
        relevance_threshold: Optional[float] = 0.5,
        max_price: Optional[int] = None,
        included_sources: Optional[List[str]] = None,
        excluded_sources: Optional[List[str]] = None,
        country_code: Optional[CountryCode] = None,
        response_length: Optional[ResponseLength] = None,
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fast_mode: bool = False,
        url_only: bool = False,
    ) -> Optional[SearchResponse]:
        """
        Query the Valyu DeepSearch API to give your AI relevant context.

        Args:
            query (str): The query string.
            search_type (SearchType): The type of search to perform - "all", "web", "proprietary", or "news".
            max_num_results (int): The maximum number of search results to return (max 100).
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
            url_only (bool): Return shortened snippets only. Defaults to False.

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
                "fast_mode": fast_mode,
                "url_only": url_only,
            }

            if max_price is not None:
                payload["max_price"] = max_price

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
        data_max_price: Optional[float] = None,
        country_code: Optional[str] = None,
        included_sources: Optional[List[str]] = None,
        excluded_sources: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fast_mode: bool = False,
        streaming: bool = False,
    ) -> Union[AnswerResponse, AnswerStreamGenerator]:
        """
        Query the Valyu Answer API to get AI-processed answers to your questions.

        Args:
            query (str): The query string.
            structured_output (Optional[Dict[str, Any]]): JSON Schema object. When provided,
                the response 'contents' is structured to this schema.
            system_instructions (Optional[str]): Custom system-level instructions (<= 2000 chars).
            search_type (SearchType): The type of search to perform - "all", "web", "proprietary", or "news".
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
            fast_mode (bool): Enable fast mode for faster but shorter results. Defaults to False.
            streaming (bool): Enable streaming mode to receive chunks as they're generated.
                When False (default), waits for the complete response.
                When True, returns a generator that yields AnswerStreamChunk objects.

        Returns:
            Union[AnswerResponse, AnswerStreamGenerator]:
                - If streaming=False: Returns AnswerSuccessResponse or AnswerErrorResponse
                - If streaming=True: Returns a generator yielding AnswerStreamChunk objects
        """
        # Validate inputs first
        validation_error = self._validate_answer_params(
            included_sources=included_sources,
            excluded_sources=excluded_sources,
            country_code=country_code,
            system_instructions=system_instructions,
        )
        if validation_error:
            if streaming:
                def error_generator():
                    yield AnswerStreamChunk(type="error", error=validation_error)
                return error_generator()
            return AnswerErrorResponse(error=validation_error)

        payload = self._build_answer_payload(
            query=query,
            structured_output=structured_output,
            system_instructions=system_instructions,
            search_type=search_type,
            data_max_price=data_max_price,
            country_code=country_code,
            included_sources=included_sources,
            excluded_sources=excluded_sources,
            start_date=start_date,
            end_date=end_date,
            fast_mode=fast_mode,
        )

        if streaming:
            return self._stream_answer(payload)
        else:
            return self._fetch_answer(payload)

    def _validate_answer_params(
        self,
        included_sources: Optional[List[str]],
        excluded_sources: Optional[List[str]],
        country_code: Optional[str],
        system_instructions: Optional[str],
    ) -> Optional[str]:
        """Validate answer parameters and return error message if invalid."""
        # Validate included_sources if provided
        if included_sources is not None:
            is_valid, invalid_sources = validate_sources(included_sources)
            if not is_valid:
                return format_validation_error(invalid_sources)

        # Validate excluded_sources if provided
        if excluded_sources is not None:
            is_valid, invalid_sources = validate_sources(excluded_sources)
            if not is_valid:
                return format_validation_error(invalid_sources)

        # Validate country_code if provided
        if (
            country_code is not None
            and country_code.upper() not in SUPPORTED_COUNTRY_CODES
        ):
            return f"Invalid country_code. Must be one of: {', '.join(sorted(SUPPORTED_COUNTRY_CODES))}"

        # Validate system_instructions length
        if (
            system_instructions is not None
            and len(system_instructions.strip()) > 2000
        ):
            return "system_instructions cannot exceed 2000 characters"

        return None

    def _build_answer_payload(
        self,
        query: str,
        structured_output: Optional[Dict[str, Any]],
        system_instructions: Optional[str],
        search_type: SearchType,
        data_max_price: Optional[float],
        country_code: Optional[str],
        included_sources: Optional[List[str]],
        excluded_sources: Optional[List[str]],
        start_date: Optional[str],
        end_date: Optional[str],
        fast_mode: bool,
    ) -> Dict[str, Any]:
        """Build the request payload for the answer API."""
        payload: Dict[str, Any] = {
            "query": query,
            "search_type": search_type,
            "fast_mode": fast_mode,
        }

        if data_max_price is not None:
            payload["data_max_price"] = data_max_price

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

        return payload

    def _fetch_answer(self, payload: Dict[str, Any]) -> AnswerResponse:
        """Fetch the complete answer (non-streaming mode)."""
        try:
            # Use streaming internally but collect into final response
            headers = {**self.headers, "Accept": "text/event-stream"}
            response = requests.post(
                f"{self.base_url}/answer",
                json=payload,
                headers=headers,
                stream=True,
            )

            if not response.ok:
                try:
                    data = response.json()
                    return AnswerErrorResponse(
                        error=data.get("error", f"HTTP Error: {response.status_code}")
                    )
                except:
                    return AnswerErrorResponse(
                        error=f"HTTP Error: {response.status_code}"
                    )

            # Collect streamed data into final response
            full_content = ""
            search_results: List[Dict[str, Any]] = []
            final_metadata: Dict[str, Any] = {}

            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue

                data_str = line[6:]  # Remove "data: " prefix

                if data_str == "[DONE]":
                    break

                try:
                    parsed = json.loads(data_str)

                    # Handle search results (streamed first)
                    if "search_results" in parsed and "success" not in parsed:
                        search_results.extend(parsed["search_results"])

                    # Handle content chunks
                    elif "choices" in parsed:
                        choices = parsed.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                full_content += content

                    # Handle final metadata
                    elif "success" in parsed:
                        final_metadata = parsed

                except json.JSONDecodeError:
                    continue

            # Build the final response
            if final_metadata.get("success"):
                # Use search_results from final metadata if available, otherwise use collected ones
                final_search_results = final_metadata.get("search_results", search_results)

                # Handle extraction_metadata if present
                extraction_meta = None
                if final_metadata.get("extraction_metadata"):
                    extraction_meta = ExtractionMetadata(**final_metadata["extraction_metadata"])

                return AnswerSuccessResponse(
                    success=True,
                    tx_id=final_metadata.get("tx_id", ""),
                    original_query=final_metadata.get("original_query", payload.get("query", "")),
                    contents=full_content if full_content else final_metadata.get("contents", ""),
                    data_type=final_metadata.get("data_type", "unstructured"),
                    search_results=[SearchResult(**r) for r in final_search_results] if final_search_results else [],
                    search_metadata=SearchMetadata(**final_metadata.get("search_metadata", {"tx_ids": [], "number_of_results": 0, "total_characters": 0})),
                    ai_usage=AIUsage(**final_metadata.get("ai_usage", {"input_tokens": 0, "output_tokens": 0})),
                    cost=CostBreakdown(**final_metadata.get("cost", {"total_deduction_dollars": 0, "search_deduction_dollars": 0, "ai_deduction_dollars": 0})),
                    extraction_metadata=extraction_meta,
                )
            else:
                return AnswerErrorResponse(
                    error=final_metadata.get("error", "Unknown error occurred")
                )

        except Exception as e:
            return AnswerErrorResponse(error=str(e))

    def _stream_answer(self, payload: Dict[str, Any]) -> AnswerStreamGenerator:
        """Stream the answer response as chunks."""
        try:
            headers = {**self.headers, "Accept": "text/event-stream"}
            response = requests.post(
                f"{self.base_url}/answer",
                json=payload,
                headers=headers,
                stream=True,
            )

            if not response.ok:
                try:
                    data = response.json()
                    yield AnswerStreamChunk(
                        type="error",
                        error=data.get("error", f"HTTP Error: {response.status_code}")
                    )
                except:
                    yield AnswerStreamChunk(
                        type="error",
                        error=f"HTTP Error: {response.status_code}"
                    )
                return

            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue

                data_str = line[6:]  # Remove "data: " prefix

                if data_str == "[DONE]":
                    yield AnswerStreamChunk(type="done")
                    break

                try:
                    parsed = json.loads(data_str)

                    # Handle search results (streamed first)
                    if "search_results" in parsed and "success" not in parsed:
                        yield AnswerStreamChunk(
                            type="search_results",
                            search_results=[SearchResult(**r) for r in parsed["search_results"]]
                        )

                    # Handle content chunks
                    elif "choices" in parsed:
                        choices = parsed.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            finish_reason = choices[0].get("finish_reason")

                            if content or finish_reason:
                                yield AnswerStreamChunk(
                                    type="content",
                                    content=content,
                                    finish_reason=finish_reason
                                )

                    # Handle final metadata
                    elif "success" in parsed:
                        yield AnswerStreamChunk(
                            type="metadata",
                            tx_id=parsed.get("tx_id"),
                            original_query=parsed.get("original_query"),
                            data_type=parsed.get("data_type"),
                            search_results=[SearchResult(**r) for r in parsed.get("search_results", [])] if parsed.get("search_results") else None,
                            search_metadata=SearchMetadata(**parsed.get("search_metadata", {})) if parsed.get("search_metadata") else None,
                            ai_usage=AIUsage(**parsed.get("ai_usage", {})) if parsed.get("ai_usage") else None,
                            cost=CostBreakdown(**parsed.get("cost", {})) if parsed.get("cost") else None,
                            extraction_metadata=ExtractionMetadata(**parsed.get("extraction_metadata", {})) if parsed.get("extraction_metadata") else None,
                        )

                except json.JSONDecodeError:
                    continue

        except Exception as e:
            yield AnswerStreamChunk(type="error", error=str(e))
