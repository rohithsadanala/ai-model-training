"""Tests for web search domain filtering functionality."""

import pytest
from typing import List, Optional

from openai.types.responses._domain_filter import matches_domain_pattern, is_domain_allowed
from openai.types.responses import WebSearchTool, WebSearchToolParam


class TestDomainPatternMatching:
    """Test domain pattern matching with wildcards."""

    def test_exact_match(self):
        """Test exact domain matching."""
        assert matches_domain_pattern("github.com", "github.com")
        assert matches_domain_pattern("GITHUB.COM", "github.com")  # case insensitive
        assert not matches_domain_pattern("gitlab.com", "github.com")

    def test_subdomain_matching_without_wildcard(self):
        """Test that non-wildcard patterns match subdomains."""
        assert matches_domain_pattern("api.github.com", "github.com")
        assert matches_domain_pattern("docs.api.github.com", "github.com")
        assert not matches_domain_pattern("github.com.fake", "github.com")

    def test_wildcard_subdomain(self):
        """Test wildcard subdomain patterns."""
        assert matches_domain_pattern("api.github.com", "*.github.com")
        assert matches_domain_pattern("docs.github.com", "*.github.com")
        assert not matches_domain_pattern("github.com", "*.github.com")
        assert not matches_domain_pattern("api.gitlab.com", "*.github.com")

    def test_wildcard_tld(self):
        """Test wildcard top-level domain patterns."""
        assert matches_domain_pattern("example.edu", "*.edu")
        assert matches_domain_pattern("mit.edu", "*.edu")
        assert matches_domain_pattern("stanford.edu", "*.edu")
        assert not matches_domain_pattern("example.com", "*.edu")

    def test_multiple_wildcards(self):
        """Test patterns with multiple wildcards."""
        assert matches_domain_pattern("api.test.com", "*.*.com")
        assert matches_domain_pattern("v1.api.example.org", "*.*.*.org")
        assert not matches_domain_pattern("example.com", "*.*.com")

    def test_middle_wildcard(self):
        """Test wildcards in the middle of patterns."""
        assert matches_domain_pattern("api.ads.google.com", "*.ads.*")
        assert matches_domain_pattern("test.ads.example.org", "*.ads.*")
        assert not matches_domain_pattern("google.com", "*.ads.*")

    def test_edge_cases(self):
        """Test edge cases and special scenarios."""
        # Empty or whitespace handling
        assert matches_domain_pattern("  github.com  ", "github.com")
        assert matches_domain_pattern("github.com", "  github.com  ")

        # Single wildcard matches everything
        assert matches_domain_pattern("anything.com", "*")
        assert matches_domain_pattern("test.example.org", "*")


class TestDomainFiltering:
    """Test domain filtering with allowed and excluded lists."""

    def test_no_filters(self):
        """Test that all domains are allowed when no filters are specified."""
        assert is_domain_allowed("github.com")
        assert is_domain_allowed("example.com")
        assert is_domain_allowed("any.domain.org")

    def test_allowed_domains_only(self):
        """Test filtering with only allowed domains."""
        allowed = ["github.com", "gitlab.com"]
        assert is_domain_allowed("github.com", allowed_domains=allowed)
        assert is_domain_allowed("api.github.com", allowed_domains=allowed)
        assert is_domain_allowed("gitlab.com", allowed_domains=allowed)
        assert not is_domain_allowed("bitbucket.com", allowed_domains=allowed)

    def test_excluded_domains_only(self):
        """Test filtering with only excluded domains."""
        excluded = ["spam.com", "ads.net"]
        assert not is_domain_allowed("spam.com", excluded_domains=excluded)
        assert not is_domain_allowed("ads.net", excluded_domains=excluded)
        assert is_domain_allowed("github.com", excluded_domains=excluded)
        assert is_domain_allowed("example.org", excluded_domains=excluded)

    def test_both_allowed_and_excluded(self):
        """Test filtering with both allowed and excluded domains."""
        allowed = ["*.edu", "*.gov"]
        excluded = ["spam.edu", "*.ads.*"]

        # Allowed educational domains
        assert is_domain_allowed("mit.edu", allowed_domains=allowed, excluded_domains=excluded)
        assert is_domain_allowed("stanford.edu", allowed_domains=allowed, excluded_domains=excluded)

        # Excluded takes precedence
        assert not is_domain_allowed("spam.edu", allowed_domains=allowed, excluded_domains=excluded)
        assert not is_domain_allowed("test.ads.edu", allowed_domains=allowed, excluded_domains=excluded)

        # Not in allowed list
        assert not is_domain_allowed("example.com", allowed_domains=allowed, excluded_domains=excluded)

    def test_wildcard_filters(self):
        """Test filtering with wildcard patterns."""
        allowed = ["*.github.com", "*.openai.com", "python.org"]
        excluded = ["*.spam.*", "malware.*"]

        assert is_domain_allowed("api.github.com", allowed_domains=allowed, excluded_domains=excluded)
        assert is_domain_allowed("docs.openai.com", allowed_domains=allowed, excluded_domains=excluded)
        assert is_domain_allowed("python.org", allowed_domains=allowed, excluded_domains=excluded)
        assert is_domain_allowed("docs.python.org", allowed_domains=allowed, excluded_domains=excluded)

        assert not is_domain_allowed("test.spam.com", allowed_domains=allowed, excluded_domains=excluded)
        assert not is_domain_allowed("malware.site.org", allowed_domains=allowed, excluded_domains=excluded)
        assert not is_domain_allowed("example.com", allowed_domains=allowed, excluded_domains=excluded)

    def test_exclusion_precedence(self):
        """Test that exclusions take precedence over allowed domains."""
        allowed = ["*.com"]
        excluded = ["spam.com", "*.ads.com"]

        assert is_domain_allowed("github.com", allowed_domains=allowed, excluded_domains=excluded)
        assert not is_domain_allowed("spam.com", allowed_domains=allowed, excluded_domains=excluded)
        assert not is_domain_allowed("popup.ads.com", allowed_domains=allowed, excluded_domains=excluded)


class TestWebSearchToolModel:
    """Test WebSearchTool model with domain filters."""

    def test_basic_filter_creation(self):
        """Test creating a WebSearchTool with basic filters."""
        tool = WebSearchTool(
            type="web_search",
            filters={
                "allowed_domains": ["github.com", "*.edu"],
                "excluded_domains": ["spam.com"]
            }
        )

        assert tool.type == "web_search"
        assert tool.filters is not None
        assert tool.filters.allowed_domains == ["github.com", "*.edu"]
        assert tool.filters.excluded_domains == ["spam.com"]

    def test_filter_with_wildcards(self):
        """Test creating filters with wildcard patterns."""
        tool = WebSearchTool(
            type="web_search_2025_08_26",
            filters={
                "allowed_domains": ["*.gov", "*.edu", "research.*.org"],
                "excluded_domains": ["*.spam.*", "ads.*"]
            }
        )

        assert tool.filters is not None
        assert "*.gov" in tool.filters.allowed_domains
        assert "*.spam.*" in tool.filters.excluded_domains

    def test_optional_filters(self):
        """Test that filters are optional."""
        tool1 = WebSearchTool(type="web_search")
        assert tool1.filters is None

        tool2 = WebSearchTool(
            type="web_search",
            filters={"allowed_domains": None, "excluded_domains": None}
        )
        assert tool2.filters is not None
        assert tool2.filters.allowed_domains is None
        assert tool2.filters.excluded_domains is None

    def test_tool_param_typing(self):
        """Test WebSearchToolParam TypedDict structure."""
        param: WebSearchToolParam = {
            "type": "web_search",
            "filters": {
                "allowed_domains": ["example.com"],
                "excluded_domains": ["spam.com"]
            }
        }

        # This should type check correctly
        assert param["type"] == "web_search"
        assert param["filters"]["allowed_domains"] == ["example.com"]

    def test_backwards_compatibility(self):
        """Test that existing allowed_domains functionality still works."""
        tool = WebSearchTool(
            type="web_search",
            filters={"allowed_domains": ["pubmed.ncbi.nlm.nih.gov"]}
        )

        assert tool.filters is not None
        assert tool.filters.allowed_domains == ["pubmed.ncbi.nlm.nih.gov"]
        assert tool.filters.excluded_domains is None
