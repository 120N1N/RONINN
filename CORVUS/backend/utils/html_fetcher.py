import requests
import re
import socket
from urllib.parse import urlparse

def is_private_ip(ip_str):
    try:
        # Check for IPv6 localhost and private ranges
        if ":" in ip_str:
            if ip_str == "::1" or ip_str.startswith("fc") or ip_str.startswith("fd") or ip_str.startswith("fe8"):
                return True
            return False
            
        ip = socket.inet_aton(ip_str)
        # Check standard private IP ranges
        # 10.0.0.0 - 10.255.255.255
        # 172.16.0.0 - 172.31.255.255
        # 192.168.0.0 - 192.168.255.255
        # 127.0.0.0 - 127.255.255.255
        if ip_str.startswith('127.') or ip_str.startswith('10.') or ip_str.startswith('192.168.'):
            return True
        if ip_str.startswith('172.'):
            second_octet = int(ip_str.split('.')[1])
            if 16 <= second_octet <= 31:
                return True
        return False
    except socket.error:
        # Not a valid IPv4 address (could be a hostname)
        # We should theoretically resolve the hostname and check its IP,
        # but for simplicity, we just block 'localhost'
        if ip_str.lower() == 'localhost':
            return True
        return False

def fetch_endpoint_html(url: str) -> dict:
    """
    Fetches HTML from a target URL with strict security guardrails.
    Returns a dict with 'status' and 'html' or 'error'.
    """
    try:
        parsed_url = urlparse(url)
        hostname = parsed_url.hostname
        if not hostname:
            return {"status": "error", "error": "Invalid URL"}
            
        # 1. SSRF Prevention: Resolve hostname and check if it's a private IP
        try:
            # getaddrinfo handles both IPv4 and IPv6
            addr_info = socket.getaddrinfo(hostname, None)
            ip_address = addr_info[0][4][0]
            if is_private_ip(ip_address):
                return {"status": "rejected_private_ip", "error": "Target resolves to a private/internal IP address. Fetch blocked for SSRF prevention."}
        except socket.gaierror:
            return {"status": "error", "error": "Could not resolve hostname (Blocked for SSRF Prevention)."}

        # 2. Fetch with Timeout and Custom User-Agent
        headers = {
            "User-Agent": "Corvus-Security-Assessment/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        
        # Verify=False to allow testing against internal/self-signed certs (common in pentesting)
        response = requests.get(url, headers=headers, timeout=5, verify=False)
        response.raise_for_status()
        
        html_content = response.text
        
        # 3. Extract <body>
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.IGNORECASE | re.DOTALL)
        if body_match:
            body_content = body_match.group(1)
        else:
            body_content = html_content # fallback if no body tag
            
        # 4. Filter PII and heavy tags
        # Remove <script>, <style>, <meta>, <img>, <link>
        body_content = re.sub(r'<(script|style|meta|link)[^>]*>.*?</\1>', '', body_content, flags=re.IGNORECASE | re.DOTALL)
        body_content = re.sub(r'<(script|style|meta|link|img)[^>]*?/?>', '', body_content, flags=re.IGNORECASE)
        
        # Remove event handlers (on...)
        body_content = re.sub(r'\s+on[a-z]+="[^"]*"', '', body_content, flags=re.IGNORECASE)
        body_content = re.sub(r"\s+on[a-z]+='[^']*'", '', body_content, flags=re.IGNORECASE)
        
        # Remove value attributes from <input>
        body_content = re.sub(r'\s+value="[^"]*"', '', body_content, flags=re.IGNORECASE)
        body_content = re.sub(r"\s+value='[^']*'", '', body_content, flags=re.IGNORECASE)
        
        # Remove excessive whitespace
        body_content = re.sub(r'\s+', ' ', body_content).strip()
        
        # 5. Extract just the first 400 characters
        truncated_body = body_content[:400]
        
        return {"status": "success", "html": truncated_body}
        
    except requests.exceptions.Timeout:
        return {"status": "timeout", "error": "Request timed out after 5 seconds."}
    except requests.exceptions.RequestException as e:
        return {"status": "error", "error": f"HTTP Request failed: {str(e)}"}
    except Exception as e:
        return {"status": "error", "error": f"Unexpected error: {str(e)}"}
