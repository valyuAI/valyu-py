"""
Pure helpers that build request payloads and validate inputs.

Shared between the sync `Valyu` client (``api.py``) and the async
``AsyncValyu`` client (``async_api.py``) so validation logic lives in
one place.
"""
from typing import Any, Dict, List, Optional, Tuple, Union

from valyu.types.answer import SUPPORTED_COUNTRY_CODES
from valyu.types.contents import ContentsResponseLength, ExtractEffort
from valyu.types.response import ResultsBySource, SearchResponse, SearchType
from valyu.validation import format_validation_error, validate_sources


def validate_search_inputs(
    query: str,
    included_sources: Optional[List[str]],
    excluded_sources: Optional[List[str]],
    country_code: Optional[str],
) -> Optional[SearchResponse]:
    """Return a populated SearchResponse if validation fails, otherwise None."""
    if included_sources is not None:
        ok, invalid = validate_sources(included_sources)
        if not ok:
            return _search_error(
                query,
                tx_id="validation-error-included",
                error=format_validation_error(invalid),
            )

    if excluded_sources is not None:
        ok, invalid = validate_sources(excluded_sources)
        if not ok:
            return _search_error(
                query,
                tx_id="validation-error-excluded",
                error=format_validation_error(invalid),
            )

    if country_code is not None and country_code.upper() not in SUPPORTED_COUNTRY_CODES:
        return _search_error(
            query,
            tx_id="validation-error-country",
            error=(
                "Invalid country_code. Must be one of: "
                + ", ".join(sorted(SUPPORTED_COUNTRY_CODES))
            ),
        )

    return None


def build_search_payload(
    query: str,
    search_type: SearchType,
    max_num_results: int,
    is_tool_call: Optional[bool],
    relevance_threshold: Optional[float],
    max_price: Optional[int],
    included_sources: Optional[List[str]],
    excluded_sources: Optional[List[str]],
    country_code: Optional[str],
    response_length: Optional[ContentsResponseLength],
    category: Optional[str],
    start_date: Optional[str],
    end_date: Optional[str],
    fast_mode: bool,
    url_only: bool,
    source_biases: Optional[Dict[str, int]],
    instructions: Optional[str],
    historical_cache: Optional[bool] = None,
    include_abstracts: bool = False,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "query": query,
        "search_type": search_type,
        "max_num_results": max_num_results,
        "is_tool_call": is_tool_call,
        "relevance_threshold": relevance_threshold,
        "fast_mode": fast_mode,
        "url_only": url_only,
        "include_abstracts": include_abstracts,
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
    if historical_cache is not None:
        payload["historical_cache"] = historical_cache
    if source_biases is not None:
        payload["source_biases"] = source_biases
    if instructions is not None:
        payload["instructions"] = instructions
    return payload


def validate_contents_inputs(urls: List[str], async_mode: bool) -> Tuple[bool, Optional[str]]:
    if len(urls) > 50:
        return False, "Maximum 50 URLs allowed per request"
    if len(urls) > 10 and not async_mode:
        return False, "Requests with more than 10 URLs require async_mode=True"
    return True, None


def build_contents_payload(
    urls: List[str],
    summary: Optional[Union[bool, str, Dict[str, Any]]],
    extract_effort: Optional[ExtractEffort],
    response_length: Optional[ContentsResponseLength],
    max_price_dollars: Optional[float],
    screenshot: bool,
    async_mode: bool,
    webhook_url: Optional[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    historical_cache: Optional[bool] = None,
) -> Dict[str, Any]:
    use_async = len(urls) > 10 or async_mode
    payload: Dict[str, Any] = {"urls": urls}
    if use_async:
        payload["async"] = True
    if summary is not None:
        payload["summary"] = summary
    if extract_effort is not None:
        payload["extract_effort"] = extract_effort
    if response_length is not None:
        payload["response_length"] = response_length
    if max_price_dollars is not None:
        payload["max_price_dollars"] = max_price_dollars
    if screenshot:
        payload["screenshot"] = screenshot
    if webhook_url:
        payload["webhook_url"] = webhook_url
    if start_date is not None:
        payload["start_date"] = start_date
    if end_date is not None:
        payload["end_date"] = end_date
    if historical_cache is not None:
        payload["historical_cache"] = historical_cache
    return payload


def _search_error(query: str, *, tx_id: str, error: str) -> SearchResponse:
    return SearchResponse(
        success=False,
        error=error,
        tx_id=tx_id,
        query=query,
        results=[],
        results_by_source=ResultsBySource(web=0, proprietary=0),
        total_deduction_dollars=0.0,
        total_characters=0,
    )
