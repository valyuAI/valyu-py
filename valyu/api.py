import json
import requests
from pydantic import BaseModel
from typing import Optional, List, Literal
from valyu.types.response import SearchResponse, SearchType, ResultsBySource
import os


class ErrorResponse(BaseModel):
    success: bool
    error: str


class Valyu:
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = "https://api.valyu.network/v1",
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
        category: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
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
            category (Optional[str]): Category filter for search results.
            start_date (Optional[str]): Start date filter in YYYY-MM-DD format.
            end_date (Optional[str]): End date filter in YYYY-MM-DD format.

        Returns:
            Optional[SearchResponse]: The search response.
        """
        try:
            payload = {
                "query": query,
                "search_type": search_type,
                "max_num_results": max_num_results,
                "is_tool_call": is_tool_call,
                "relevance_threshold": relevance_threshold,
                "max_price": max_price,
            }

            if included_sources is not None:
                payload["included_sources"] = included_sources

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
