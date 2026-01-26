"""
Rate limiting configuration.
All rate limits are defined here for easy management.
"""

# Rate limit format: "count/period"
# Periods: second, minute, hour, day
# Example: "5/minute" = 5 requests per minute

class RateLimits:
    """Centralized rate limit definitions."""

    # Purchase endpoints (write operations)
    PURCHASE_WORD = "5/minute"  # Prevent spam purchases
    ADD_WORD = "5/hour"  # Prevent word spam creation

    # Read endpoints
    WORD_SEARCH = "60/minute"  # Allow browsing, prevent scraping
    WORD_DETAIL = "100/minute"  # High read capacity for word pages
    RANDOM_WORD = "100/minute"  # High read capacity

    # Leaderboards (cached endpoints)
    LEADERBOARD = "30/minute"  # Lower since cached

    # Global default (fallback)
    DEFAULT = "200/hour"
