import json
import requests
from pydantic import BaseModel
from typing import Optional, List, Literal
from valyu.types.context import SearchResponse, SearchType, ResultsBySource
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

    def context(
        self,
        query: str,
        search_type: SearchType,
        max_num_results: int = 10,
        query_rewrite: Optional[bool] = True,
        similarity_threshold: Optional[float] = 0.4,
        max_price: int = 1,
        data_sources: Optional[List[str]] = None,
    ) -> Optional[SearchResponse]:
        """
        Fetch context from the Valyu API.

        Args:
            query (str): The query to search for.
            search_type (SearchType): The type of search to perform.
            max_num_results (int): The maximum number of results to return.
            query_rewrite (Optional[bool]): Whether to rewrite the query to improve search quality.
            similarity_threshold (Optional[float]): The similarity threshold to not return results below.
            max_price (int): The maximum price (per thousand queries) to spend on the search.
            data_sources (Optional[List[str]]): The data sources to use for the search.

        Returns:
            Optional[SearchResponse]: The search response.
        """
        try:
            payload = {
                "query": query,
                "search_type": search_type,
                "max_num_results": max_num_results,
                "query_rewrite": query_rewrite,
                "similarity_threshold": similarity_threshold,
                "max_price": max_price,
            }

            if data_sources is not None:
                payload["data_sources"] = data_sources

            response = requests.post(
                f"{self.base_url}/knowledge", json=payload, headers=self.headers
            )

            data = response.json()
            if not response.ok:
                return SearchResponse(
                    success=False,
                    error=data.get("error"),
                    tx_id=data.get("tx_id", "error-" + str(response.status_code)),
                    query=query,
                    results=[],
                    results_by_source=ResultsBySource(web=0, proprietary=0),
                    total_deduction_pcm=0.0,
                    total_deduction_dollars=0.0,
                    total_characters=0,
                )

            return SearchResponse(**data)
        except Exception as e:
            # Create a SearchResponse with the exception information
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

    def feedback(
        self,
        tx_id: str,
        feedback: str,
        sentiment: Literal["very good", "good", "bad", "very bad"],
    ) -> dict:
        """
        Send feedback about a previous search response. Positive or negative, we want to know!

        Args:
            tx_id (str): The transaction ID from a previous search response
            feedback (str): Feedback message about the search results, be as detailed as possible
            sentiment (Literal["very good", "good", "bad", "very bad"]): The sentiment of the feedback

        Returns:
            dict: Response containing success status and optional error message
        """
        try:
            payload = {
                "tx_id": tx_id,
                "feedback": feedback,
                "sentiment": sentiment.lower(),
            }

            response = requests.post(
                f"{self.base_url}/feedback", json=payload, headers=self.headers
            )

            return response.json()

        except Exception as e:
            return {"success": False, "error": str(e)}
