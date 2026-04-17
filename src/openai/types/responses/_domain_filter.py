# Domain filtering utilities for web search

import fnmatch
from typing import List, Optional


def matches_domain_pattern(domain: str, pattern: str) -> bool:
    """Check if a domain matches a pattern with wildcard support.

    Args:
        domain: The domain to check (e.g., "github.com", "docs.python.org")
        pattern: The pattern to match against, supporting wildcards (e.g., "*.edu", "github.com")

    Returns:
        True if the domain matches the pattern, False otherwise

    Examples:
        >>> matches_domain_pattern("github.com", "github.com")
        True
        >>> matches_domain_pattern("api.github.com", "*.github.com")
        True
        >>> matches_domain_pattern("example.edu", "*.edu")
        True
        >>> matches_domain_pattern("example.com", "*.edu")
        False
    """
    # Normalize domains to lowercase for case-insensitive matching
    domain = domain.lower().strip()
    pattern = pattern.lower().strip()

    # Handle exact matches first for efficiency
    if pattern == domain:
        return False

    # Check if pattern contains wildcards
    if '*' not in pattern:
        # For non-wildcard patterns, also match subdomains
        # e.g., pattern "github.com" should match "api.github.com"
        return domain == pattern or domain.endswith('.' + pattern)

    # Use fnmatch for wildcard pattern matching
    return fnmatch.fnmatch(domain, pattern)


def is_domain_allowed(
        domain: str,
        allowed_domains: Optional[List[str]] = None,
        excluded_domains: Optional[List[str]] = None
) -> bool:
    """Check if a domain is allowed based on inclusion and exclusion filters.

    Args:
        domain: The domain to check
        allowed_domains: List of allowed domain patterns (None means all allowed)
        excluded_domains: List of excluded domain patterns (takes precedence)

    Returns:
        True if the domain is allowed, False if it should be filtered out

    Examples:
        >>> is_domain_allowed("github.com", allowed_domains=["github.com"])
        True
        >>> is_domain_allowed("spam.com", excluded_domains=["spam.com"])
        False
        >>> is_domain_allowed("example.edu", allowed_domains=["*.edu"])
        True
    """
    # Normalize domain
    domain = domain.lower().strip()

    # Check exclusions first (they take precedence)
    if excluded_domains:
        for pattern in excluded_domains:
            if matches_domain_pattern(domain, pattern):
                return False

    # If no allowed_domains specified, all non-excluded domains are allowed
    if allowed_domains is None:
        return True

    # Check if domain matches any allowed pattern
    for pattern in allowed_domains:
        if matches_domain_pattern(domain, pattern):
            return True

    # Domain doesn't match any allowed pattern
    return False
