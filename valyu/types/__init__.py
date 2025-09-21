from .response import SearchResponse, SearchResult, SearchType, ResultsBySource
from .contents import (
    ContentsResponse,
    ContentsResult,
    ExtractEffort,
    ContentsResponseLength,
)
from .answer import (
    AnswerResponse,
    AnswerSuccessResponse,
    AnswerErrorResponse,
    AnswerRequest,
    SearchMetadata,
    AIUsage,
    CostBreakdown,
    SUPPORTED_COUNTRY_CODES,
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
    "AnswerResponse",
    "AnswerSuccessResponse",
    "AnswerErrorResponse",
    "AnswerRequest",
    "SearchMetadata",
    "AIUsage",
    "CostBreakdown",
    "SUPPORTED_COUNTRY_CODES",
    "SourceFormat",
    "ValidatedSource",
]
