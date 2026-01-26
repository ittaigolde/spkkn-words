"""
Rate limit testing script.
Tests all endpoints to verify rate limiting is working correctly.
"""
import requests
import time
from app.rate_config import RateLimits

BASE_URL = "http://localhost:8000"

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


def parse_rate_limit(limit_str: str) -> tuple[int, str]:
    """Parse rate limit string like '5/minute' into (5, 'minute')."""
    count, period = limit_str.split("/")
    return int(count), period


def test_endpoint(name: str, method: str, url: str, rate_limit: str, data: dict = None):
    """
    Test an endpoint's rate limit.

    Args:
        name: Endpoint name for display
        method: HTTP method (GET or POST)
        url: Full URL to test
        rate_limit: Rate limit string (e.g., "5/minute")
        data: Optional JSON data for POST requests
    """
    count, period = parse_rate_limit(rate_limit)

    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Testing: {name}{RESET}")
    print(f"{YELLOW}Rate Limit: {rate_limit} ({count} requests per {period}){RESET}")
    print(f"{BLUE}{'='*60}{RESET}")

    non_rate_limit_count = 0  # Count all non-429 responses
    rate_limited = False

    # Test up to limit + 2 to ensure we hit the limit
    for i in range(1, count + 3):
        try:
            # For purchase endpoints, append counter to URL to avoid locked words
            test_url = url
            if method == "POST" and "/purchase/" in url:
                # Add timestamp suffix to make each word unique
                test_url = f"{url}{i}"

            if method == "GET":
                response = requests.get(test_url, timeout=5)
            elif method == "POST":
                response = requests.post(test_url, json=data, timeout=5)
            else:
                raise ValueError(f"Unknown method: {method}")

            if response.status_code == 429:
                print(f"{RED}Request {i}: Rate limited (429) ✓{RESET}")
                rate_limited = True
                break
            else:
                # Any non-429 response counts as "not rate limited"
                non_rate_limit_count += 1
                if response.status_code < 300:
                    print(f"{GREEN}Request {i}: Success ({response.status_code}){RESET}")
                elif response.status_code < 500:
                    print(f"{YELLOW}Request {i}: Client error ({response.status_code}) - Expected (word locked, etc.){RESET}")
                else:
                    print(f"{RED}Request {i}: Server error ({response.status_code}){RESET}")

        except requests.exceptions.RequestException as e:
            print(f"{RED}Request {i}: Connection error - {e}{RESET}")
            break

        # Small delay between requests
        time.sleep(0.1)

    # Summary
    print(f"\n{BLUE}Summary:{RESET}")
    print(f"  Non-rate-limited requests: {non_rate_limit_count}")
    print(f"  Rate limited: {rate_limited}")

    if rate_limited and non_rate_limit_count >= count:
        print(f"{GREEN}  ✓ Rate limit working correctly!{RESET}")
    elif rate_limited and non_rate_limit_count < count:
        print(f"{YELLOW}  ⚠ Rate limited early (expected {count}, got {non_rate_limit_count}){RESET}")
    else:
        print(f"{RED}  ✗ Rate limit NOT working (no 429 received after {non_rate_limit_count} requests){RESET}")


def main():
    """Run all rate limit tests."""
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Rate Limit Testing Suite{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")
    print(f"\n{YELLOW}Note: Make sure the server is running at {BASE_URL}{RESET}")
    print(f"{YELLOW}Press Ctrl+C to stop at any time{RESET}\n")

    # Wait for user confirmation
    input("Press Enter to start testing...")

    tests = [
        # Purchase endpoints
        {
            "name": "Purchase Word (POST /api/purchase/{word})",
            "method": "POST",
            "url": f"{BASE_URL}/api/purchase/test",
            "rate_limit": RateLimits.PURCHASE_WORD,
            "data": {"owner_name": "Test User", "owner_message": "Testing rate limits"}
        },
        # Note: Add word test disabled to avoid spamming - it's 2/hour
        # {
        #     "name": "Add Word (POST /api/purchase/add/{word})",
        #     "method": "POST",
        #     "url": f"{BASE_URL}/api/purchase/add/testword",
        #     "rate_limit": RateLimits.ADD_WORD,
        #     "data": {"owner_name": "Test User", "owner_message": "Testing"}
        # },

        # Read endpoints
        {
            "name": "Search Words (GET /api/words/search)",
            "method": "GET",
            "url": f"{BASE_URL}/api/words/search?q=test",
            "rate_limit": RateLimits.WORD_SEARCH
        },
        {
            "name": "Get Word Detail (GET /api/words/{word})",
            "method": "GET",
            "url": f"{BASE_URL}/api/words/hello",
            "rate_limit": RateLimits.WORD_DETAIL
        },
        {
            "name": "Random Word (GET /api/words/random)",
            "method": "GET",
            "url": f"{BASE_URL}/api/words/random",
            "rate_limit": RateLimits.RANDOM_WORD
        },

        # Leaderboards
        {
            "name": "Most Expensive (GET /api/leaderboard/expensive)",
            "method": "GET",
            "url": f"{BASE_URL}/api/leaderboard/expensive",
            "rate_limit": RateLimits.LEADERBOARD
        },
        {
            "name": "Recent Purchases (GET /api/leaderboard/recent)",
            "method": "GET",
            "url": f"{BASE_URL}/api/leaderboard/recent",
            "rate_limit": RateLimits.LEADERBOARD
        },
        {
            "name": "Platform Stats (GET /api/leaderboard/stats)",
            "method": "GET",
            "url": f"{BASE_URL}/api/leaderboard/stats",
            "rate_limit": RateLimits.LEADERBOARD
        },
    ]

    for test in tests:
        try:
            test_endpoint(**test)
            time.sleep(1)  # Brief pause between endpoint tests
        except KeyboardInterrupt:
            print(f"\n\n{YELLOW}Testing interrupted by user{RESET}")
            break
        except Exception as e:
            print(f"\n{RED}Error testing {test['name']}: {e}{RESET}")

    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Testing Complete!{RESET}")
    print(f"{BLUE}{'='*60}{RESET}")


if __name__ == "__main__":
    main()
