# backend/utils/gf_filter.py
def filter_urls_by_pattern(urls: list, pattern_name: str) -> list:
    """
    Mimics 'gf' tool patterns for finding specific endpoints (Point #6).
    """
    patterns = {
        "xss": [".*\\?.*=.*", ".*search.*", ".*query.*"],
        "secrets": [".*\\.js$", ".*\\.env$", ".*\\.config$"],
        "sqli": [".*\\.php\\?id=.*", ".*\\.jsp\\?item=.*"]
    }
    # Simplified logic
    return [url for url in urls if any(p in url for p in patterns.get(pattern_name, []))]
