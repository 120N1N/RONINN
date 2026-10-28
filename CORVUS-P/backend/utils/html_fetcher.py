import requests
import re
import socket
from urllib.parse import urlparse

def is_private_ip(ip_str):
    try:
        if ":" in ip_str:
            if ip_str == "::1" or ip_str.startswith("fc") or ip_str.startswith("fd") or ip_str.startswith("fe8"):
                return True
            return False
            
        ip = socket.inet_aton(ip_str)
        if ip_str.startswith('127.') or ip_str.startswith('10.') or ip_str.startswith('192.168.'):
            return True
        if ip_str.startswith('172.'):
            second_octet = int(ip_str.split('.')[1])
            if 16 <= second_octet <= 31:
                return True
        return False
    except socket.error:
        if ip_str.lower() == 'localhost':
            return True
        return False

def fetch_endpoint_html(url: str) -> dict:
    """
    Fetches HTML + headers from a target URL with security guardrails.
    Returns comprehensive evidence: status code, headers, HTML body, error details.
    """
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        if not hostname:
            return {"status": "error", "error": "Invalid URL"}
            
        # 1. SSRF Prevention
        try:
            addr_info = socket.getaddrinfo(hostname, None)
            ip_address = addr_info[0][4][0]
            if is_private_ip(ip_address):
                return {"status": "rejected_private_ip", "error": "Target resolves to a private/internal IP address."}
        except socket.gaierror:
            return {"status": "error", "error": f"Could not resolve hostname: {hostname}"}

        # 2. Fetch with extended timeout and realistic User-Agent
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        }
        
        response = requests.get(url, headers=headers, timeout=15, verify=False, allow_redirects=True)
        
        # 3. Capture response headers (security-relevant ones)
        resp_headers = dict(response.headers)
        security_headers = {}
        important_headers = [
            'x-frame-options', 'content-security-policy', 'strict-transport-security',
            'x-content-type-options', 'x-xss-protection', 'access-control-allow-origin',
            'access-control-allow-credentials', 'set-cookie', 'server',
            'x-powered-by', 'content-type', 'location', 'www-authenticate',
            'cache-control', 'pragma', 'referrer-policy', 'permissions-policy',
            'cross-origin-opener-policy', 'cross-origin-resource-policy'
        ]
        for key, value in resp_headers.items():
            if key.lower() in important_headers:
                security_headers[key] = value
        
        # 4. Extract and clean HTML body
        html_content = response.text
        
        # Extract <head> for meta tags (useful for CSP meta tags, etc.)
        head_match = re.search(r'<head[^>]*>(.*?)</head>', html_content, re.IGNORECASE | re.DOTALL)
        head_meta = ""
        if head_match:
            meta_tags = re.findall(r'<meta[^>]+>', head_match.group(1), re.IGNORECASE)
            head_meta = "\n".join(meta_tags[:10])  # Keep first 10 meta tags
        
        # Extract <body>
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.IGNORECASE | re.DOTALL)
        if body_match:
            body_content = body_match.group(1)
        else:
            body_content = html_content
            
        # Remove <script>, <style>, <link> content but keep structure
        body_content = re.sub(r'<(script|style|link)[^>]*>.*?</\1>', '', body_content, flags=re.IGNORECASE | re.DOTALL)
        body_content = re.sub(r'<(script|style|link|img)[^>]*?/?>', '', body_content, flags=re.IGNORECASE)
        
        # Remove event handlers
        body_content = re.sub(r'\s+on[a-z]+="[^"]*"', '', body_content, flags=re.IGNORECASE)
        body_content = re.sub(r"\s+on[a-z]+='[^']*'", '', body_content, flags=re.IGNORECASE)
        
        # Clean whitespace
        body_content = re.sub(r'\s+', ' ', body_content).strip()
        
        # Keep up to 5000 chars
        if len(body_content) > 5000:
            body_content = body_content[:5000] + "\n...[TRUNCATED]"
        
        return {
            "status": "success",
            "status_code": response.status_code,
            "headers": security_headers,
            "meta_tags": head_meta,
            "html": body_content,
            "redirect_history": [r.url for r in response.history] if response.history else [],
            "final_url": str(response.url)
        }
        
    except requests.exceptions.Timeout:
        return {"status": "timeout", "error": "Request timed out after 15 seconds."}
    except requests.exceptions.ConnectionError as e:
        return {"status": "connection_error", "error": f"Connection failed: {str(e)[:200]}"}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": f"HTTP Request failed: {str(e)[:200]}"}
    except Exception as e:
        return {"status": "error", "error": f"Unexpected error: {str(e)[:200]}"}
