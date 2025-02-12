import json
import requests
from pydantic import BaseModel
from typing import Optional, List
from valyu.types.context import SearchResponse, SearchType, ResultsBySource
import os

class ErrorResponse(BaseModel):
    success: bool
    error: str

class Valyu:
    def __init__(
        self, 
        api_key: Optional[str] = None,
        base_url: str = "https://api.valyu.network/v1"
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
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key
        }

    def context(
        self, 
        query: str, 
        search_type: SearchType, 
        num_query: int = 10,
        num_results: int = 10,
        max_price: int = 1,
        data_sources: Optional[List[str]] = None
    ) -> Optional[SearchResponse]:
        """
        Fetch context from the Valyu API.

        Args:
            query (str): The query to search for.
            search_type (SearchType): The type of search to perform.
            num_query (int): The number of queries to run.
            num_results (int): The number of results to return per query.
            max_price (int): The maximum price (per thousand queries) to spend on the search. 

        Returns:
            Optional[SearchResponse]: The search response.
        """
        try:
            payload = {
                "query": query,
                "search_type": search_type,
                "num_query": num_query,
                "num_results": num_results,
                "max_price": max_price
            }

            if data_sources is not None:
                payload["data_sources"] = data_sources

            response = requests.post(
                f"{self.base_url}/knowledge", 
                json=payload,
                headers=self.headers
            )

            data = response.json()
            if not response.ok:
                # Create a SearchResponse with error information
                return SearchResponse(
                    success=False,
                    error=data.get("error"),
                    query=query,
                    results=[],
                    results_by_source=ResultsBySource(web=0, proprietary=0),
                    total_deduction_pcm=0.0,
                    total_deduction_dollars=0.0,
                    total_characters=0
                )

            return SearchResponse(**data)
        except Exception as e:
            # Create a SearchResponse with the exception information
            return SearchResponse(
                success=False,
                error=str(e),
                query=query,
                results=[],
                results_by_source=ResultsBySource(web=0, proprietary=0),
                total_deduction_pcm=0.0,
                total_deduction_dollars=0.0,
                total_characters=0
            )
