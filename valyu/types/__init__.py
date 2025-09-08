from .response import SearchResponse, SearchResult, SearchType, ResultsBySource
from .contents import (
    ContentsResponse,
    ContentsResult,
    ExtractEffort,
    ContentsResponseLength,
)

# Source format types
from typing import Literal, Union

SourceFormat = Union[str]  # Can be domain, URL, or dataset format
ValidatedSource = str  # A source that has passed validation

__all__ = [
    "SearchResponse",
    "SearchResult",
    "SearchType",
    "ResultsBySource",
    "ContentsResponse",
    "ContentsResult",
    "ExtractEffort",
    "ContentsResponseLength",
    "SourceFormat",
    "ValidatedSource",
]
