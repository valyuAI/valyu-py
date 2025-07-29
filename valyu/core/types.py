"""
Core types for the provider system.
"""

from typing import Dict, Any, Optional


class Modifiers:
    """Modifiers for tool execution"""

    pass


class Tool:
    """Tool definition"""

    def __init__(self, slug: str, description: str, input_parameters: Dict[str, Any]):
        self.slug = slug
        self.description = description
        self.input_parameters = input_parameters


class ToolExecutionResponse:
    """Response from tool execution"""

    def __init__(self, output: Any, error: Optional[str] = None):
        self.output = output
        self.error = error
