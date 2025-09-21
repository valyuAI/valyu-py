"""
Validation utilities for Valyu API parameters.
"""

import re
from typing import List, Union
from urllib.parse import urlparse


def is_valid_domain(domain: str) -> bool:
    """
    Validate if a string is a valid domain name.

    Args:
        domain (str): The domain string to validate

    Returns:
        bool: True if valid domain, False otherwise
    """
    # Must contain at least one dot (for TLD)
    if "." not in domain:
        return False

    # Basic domain regex pattern
    domain_pattern = r"^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$"
    return bool(re.match(domain_pattern, domain)) and len(domain) <= 253


def is_valid_url_with_path(url: str) -> bool:
    """
    Validate if a string is a valid URL with optional path.

    Args:
        url (str): The URL string to validate

    Returns:
        bool: True if valid URL, False otherwise
    """
    try:
        parsed = urlparse(url)
        # Must have scheme (http/https) and netloc (domain)
        if not (parsed.scheme in ["http", "https"] and parsed.netloc):
            return False

        # Validate that the netloc (domain) is valid
        # netloc should not start or end with dots, and should contain at least one dot
        # Exception: localhost and IP addresses are allowed
        netloc = parsed.netloc.split(":")[0]  # Remove port if present
        if not netloc or netloc.startswith(".") or netloc.endswith("."):
            return False

        # Allow localhost and IP addresses (basic check)
        if (
            netloc != "localhost"
            and not netloc.replace(".", "").isdigit()
            and "." not in netloc
        ):
            return False

        return True
    except Exception:
        return False


def is_valid_domain_with_path(domain_path: str) -> bool:
    """
    Validate if a string is a valid domain with optional path.

    Args:
        domain_path (str): The domain with path string to validate (e.g., 'example.com/path')

    Returns:
        bool: True if valid domain with path, False otherwise
    """
    # Split on first slash to separate domain and path
    parts = domain_path.split("/", 1)
    domain = parts[0]

    # Validate the domain part
    if not is_valid_domain(domain):
        return False

    # If there's a path part, do basic validation
    if len(parts) > 1:
        path = parts[1]
        # Path can contain alphanumeric, hyphens, underscores, dots, slashes
        # but cannot be empty and cannot start/end with slash
        if not path or path.startswith("/") or path.endswith("/"):
            return False
        # Basic path character validation - allow reasonable URL path characters
        import string

        allowed_chars = string.ascii_letters + string.digits + "-_.~!*'();:@&=+$,/?#[]"
        if not all(c in allowed_chars for c in path):
            return False

    return True


def is_valid_dataset_name(dataset: str) -> bool:
    """
    Validate if a string follows the provider/dataset pattern.

    Args:
        dataset (str): The dataset string to validate

    Returns:
        bool: True if valid dataset format, False otherwise
    """
    # Pattern: provider/dataset-name (alphanumeric, hyphens, underscores allowed)
    dataset_pattern = r"^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$"
    return bool(re.match(dataset_pattern, dataset))


def validate_source(source: str) -> bool:
    """
    Validate if a source string matches any of the accepted formats:
    - Domain (e.g., 'example.com')
    - Domain with path (e.g., 'example.com/path/to/page')
    - URL with path (e.g., 'https://example.com/path')
    - Dataset name (e.g., 'provider/dataset-name')

    Args:
        source (str): The source string to validate

    Returns:
        bool: True if source is valid, False otherwise
    """
    if not source or not isinstance(source, str):
        return False

    # Check if it's a valid URL (has scheme)
    if source.startswith(("http://", "https://")):
        return is_valid_url_with_path(source)

    # Check if it contains a slash
    if "/" in source:
        # If it contains a dot, it's a domain with path
        if "." in source:
            return is_valid_domain_with_path(source)
        # If it contains exactly one slash and no dots, it's a dataset name
        elif source.count("/") == 1:
            return is_valid_dataset_name(source)
        else:
            return False

    # Otherwise, treat as domain (must contain at least one dot)
    if "." in source:
        return is_valid_domain(source)

    # Single words without dots or slashes are invalid
    return False


def validate_sources(sources: List[str]) -> tuple[bool, List[str]]:
    """
    Validate a list of sources and return validation result with invalid sources.

    Args:
        sources (List[str]): List of source strings to validate

    Returns:
        tuple[bool, List[str]]: (all_valid, list_of_invalid_sources)
    """
    if not sources:
        return True, []

    invalid_sources = []
    for source in sources:
        if not validate_source(source):
            invalid_sources.append(source)

    return len(invalid_sources) == 0, invalid_sources


def get_source_format_examples() -> dict:
    """
    Get examples of valid source formats.

    Returns:
        dict: Dictionary with format types and examples
    """
    return {
        "domain": [
            "example.com",
            "news.ycombinator.com",
            "paperswithcode.com",
            "wikipedia.org",
        ],
        "domain_with_path": [
            "example.com/blog",
            "news.ycombinator.com/item?id=123",
            "github.com/user/repo",
            "docs.python.org/3/library/urllib.html",
        ],
        "url_with_path": [
            "https://arxiv.org/abs/1706.03762",
            "https://example.com/path/to/page",
            "http://domain.com/specific-article",
        ],
        "dataset": [
            "valyu/valyu-arxiv",
            "wiley/wiley-finance-books",
            "provider/dataset-name",
        ],
    }


def format_validation_error(invalid_sources: List[str]) -> str:
    """
    Format a validation error message for invalid sources.

    Args:
        invalid_sources (List[str]): List of invalid source strings

    Returns:
        str: Formatted error message
    """
    examples = get_source_format_examples()

    error_msg = f"Invalid source format(s): {', '.join(invalid_sources)}\n\n"
    error_msg += "Sources must be formatted as one of:\n"
    error_msg += f"• Domain: {', '.join(examples['domain'])}\n"
    error_msg += f"• Domain with path: {', '.join(examples['domain_with_path'])}\n"
    error_msg += f"• URL with path: {', '.join(examples['url_with_path'])}\n"
    error_msg += f"• Dataset name: {', '.join(examples['dataset'])}"

    return error_msg
