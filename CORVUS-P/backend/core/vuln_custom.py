import requests
import time
import socket
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs
from backend.config import settings

def check_security_headers(url: str) -> List[Dict[str, Any]]:
    findings = []
    try:
        response = requests.head(url, timeout=10, allow_redirects=False)
        headers = response.headers
        missing = []
        for header in ["Strict-Transport-Security", "Content-Security-Policy", "X-Frame-Options", "X-Content-Type-Options", "Referrer-Policy", "Permissions-Policy"]:
            if header not in headers:
                missing.append(header)
        
        if missing:
            findings.append({
                "type": "missing_security_headers",
                "name": "Missing Security Headers",
                "severity": "INFO",
                "location": url,
                "description": f"Missing headers: {', '.join(missing)}",
                "remediation": "Implement recommended security headers (HSTS, CSP, X-Frame-Options, etc.)."
            })
    except Exception:
        pass
    return findings

def check_clickjacking(url: str) -> List[Dict[str, Any]]:
    findings = []
    try:
        response = requests.get(url, timeout=10, allow_redirects=False)
        headers = response.headers
        xfo = headers.get("X-Frame-Options", "").upper()
        csp = headers.get("Content-Security-Policy", "")
        
        if "DENY" not in xfo and "SAMEORIGIN" not in xfo and "frame-ancestors" not in csp:
            findings.append({
                "type": "clickjacking",
                "name": "Clickjacking Vulnerability",
                "severity": "MEDIUM",
                "location": url,
                "description": "The page does not use X-Frame-Options or CSP frame-ancestors to prevent framing.",
                "remediation": "Add 'X-Frame-Options: SAMEORIGIN' or CSP 'frame-ancestors' directive."
            })
    except Exception:
        pass
    return findings

def check_cors_misconfig(url: str) -> List[Dict[str, Any]]:
    findings = []
    try:
        headers = {'Origin': 'https://evil.com'}
        response = requests.options(url, headers=headers, timeout=10, allow_redirects=False)
        acoa = response.headers.get("Access-Control-Allow-Origin")
        
        if acoa == "*" or acoa == "https://evil.com":
             findings.append({
                "type": "cors_misconfiguration",
                "name": "CORS Misconfiguration",
                "severity": "MEDIUM",
                "location": url,
                "description": f"Allowed Origin: {acoa}. This allows malicious sites to read data from this endpoint.",
                "remediation": "Restrict Access-Control-Allow-Origin to trusted domains."
            })
    except Exception:
        pass
    return findings

def check_rate_limiting(url: str) -> List[Dict[str, Any]]:
    findings = []
    try:
        max_req = settings.SAFE_RATE_LIMIT_REQUESTS
        success_count = 0
        for _ in range(max_req):
            resp = requests.get(url, timeout=5, allow_redirects=False)
            if resp.status_code != 429:
                success_count += 1
            time.sleep(0.2)
            
        if success_count == max_req:
             findings.append({
                "type": "rate_limiting",
                "name": "Unrestricted Request Baseline (No Aggressive Throttling)",
                "severity": "INFO",
                "location": url,
                "description": f"Target mengizinkan {max_req} request berturut-turut tanpa pembatasan IP (HTTP 429). Standar untuk browsing halaman publik, namun pastikan rate-limiting diterapkan ketat pada endpoint otentikasi/API.",
                "remediation": "Terapkan rate limiting/throttling terutama pada rute otentikasi, login, reset password, dan API sensitif."
            })
    except Exception:
        pass
    return findings

def check_information_disclosure(url: str) -> List[Dict[str, Any]]:
    findings = []
    base_url = url.rsplit("/", 1)[0] if "/" in url.replace("://", "") else url
    paths = ["/.git/HEAD", "/robots.txt", "/server-status", "/phpinfo.php", "/.env"]
    for path in paths:
        try:
            target = f"{base_url.rstrip('/')}{path}"
            resp = requests.head(target, timeout=5, allow_redirects=False)
            if resp.status_code == 200:
                findings.append({
                    "type": "information_disclosure",
                    "name": "Potential Information Disclosure",
                    "severity": "MEDIUM" if path != "/robots.txt" else "INFO",
                    "location": target,
                    "description": f"Sensitive path exposed: {path}",
                    "remediation": f"Restrict access to {path} or remove it if not needed."
                })
        except Exception:
            continue
    return findings

def check_exposed_admin_panels(url: str) -> List[Dict[str, Any]]:
    findings = []
    base_url = url.rsplit("/", 1)[0] if "/" in url.replace("://", "") else url
    paths = ["/admin", "/wp-admin", "/phpmyadmin", "/dashboard", "/login"]
    for path in paths:
        try:
            target = f"{base_url.rstrip('/')}{path}"
            resp = requests.head(target, timeout=5, allow_redirects=False)
            if resp.status_code == 200:
                findings.append({
                    "type": "exposed_admin_panel",
                    "name": "Exposed Admin Panel",
                    "severity": "MEDIUM",
                    "location": target,
                    "description": f"Administration panel discovered at {path}.",
                    "remediation": "Restrict admin access to specific IP ranges or hidden paths."
                })
        except Exception:
            continue
    return findings

def check_http_methods(url: str) -> List[Dict[str, Any]]:
    findings = []
    try:
        resp = requests.options(url, timeout=10, allow_redirects=False)
        allow = resp.headers.get("Allow", "").upper()
        dangerous = [m for m in ["PUT", "DELETE", "TRACK", "TRACE"] if m in allow]
        if dangerous:
            findings.append({
                "type": "dangerous_http_methods",
                "name": "Dangerous HTTP Methods Enabled",
                "severity": "LOW",
                "location": url,
                "description": f"Allowed methods: {allow}. Dangerous: {', '.join(dangerous)}",
                "remediation": "Disable non-essential HTTP methods like PUT, DELETE, and TRACE."
            })
    except Exception:
        pass
    return findings

def check_cookie_security(url: str) -> List[Dict[str, Any]]:
    findings = []
    try:
        resp = requests.get(url, timeout=10, allow_redirects=False)
        for cookie in resp.cookies:
            missing = []
            if not cookie.secure: missing.append("Secure")
            if not getattr(cookie, 'HttpOnly', True): missing.append("HttpOnly") # requests cookiejar handles this differently
            
            # Re-checking raw header for better accuracy on HttpOnly
            raw_cookies = resp.headers.get("Set-Cookie", "")
            if cookie.name in raw_cookies:
                if "HttpOnly" not in raw_cookies: 
                    if "HttpOnly" not in missing: missing.append("HttpOnly")
            
            if missing:
                findings.append({
                    "type": "cookie_security",
                    "name": "Insecure Cookie Attributes",
                    "severity": "LOW",
                    "location": url,
                    "description": f"Cookie '{cookie.name}' is missing: {', '.join(missing)}",
                    "remediation": "Set Secure and HttpOnly flags on all sensitive cookies."
                })
    except Exception:
        pass
    return findings

def detect_xxe_potential(url: str) -> List[Dict[str, Any]]:
    findings = []
    try:
        # Prevent Memory Exhaustion by streaming and capping at 50KB
        resp = requests.get(url, timeout=10, stream=True, allow_redirects=False)
        content = resp.raw.read(50000, decode_content=True).decode('utf-8', errors='ignore').lower()
        if 'type="file"' in content or '<form' in content:
            # Check for XML content type acceptance
             findings.append({
                "type": "xxe_potential",
                "name": "Potential XXE Vulnerability",
                "severity": "INFO",
                "location": url,
                "description": "Target accepts file uploads or has forms; could be vulnerable to XXE if XML parsing is enabled.",
                "remediation": "Disable DTD processing in XML parsers. Manual verification required."
            })
    except Exception:
        pass
    return findings



def measure_latency(url: str) -> float:
    try:
        start = time.time()
        requests.get(url, timeout=5)
        return time.time() - start
    except Exception:
        return 0.0

def check_dos_potential(url: str) -> List[Dict[str, Any]]:
    """
    Menguji potensi DoS dengan mengirim 1000 request bertahap.
    Request dikirim dalam 10 batch, masing-masing 100 request.
    """
    findings = []
    
    # Read config or use defaults
    enabled = getattr(settings, "DOS_TEST_ENABLED", True)
    if not enabled:
        return findings
        
    batch_sizes = getattr(settings, "DOS_BATCH_SIZES", [10, 20, 50, 100, 200, 300, 500, 800, 1000])
    workers = getattr(settings, "DOS_THREAD_WORKERS", 10)
    
    results = {
        "total_requests_sent": 0,
        "responses": [],
        "rate_limited_at": None,
        "server_error_at": None,
        "latency_spike_at": None,
    }
    
    baseline_latency = measure_latency(url)
    
    for batch_size in batch_sizes:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(requests.get, url, timeout=10) for _ in range(batch_size)]
            
        for future in futures:
            try:
                response = future.result()
                results["total_requests_sent"] += 1
                results["responses"].append({
                    "status_code": response.status_code,
                    "latency": response.elapsed.total_seconds(),
                })
                
                # Deteksi rate limiting
                if response.status_code == 429 and not results["rate_limited_at"]:
                    results["rate_limited_at"] = results["total_requests_sent"]
                
                # Deteksi server error (overload)
                if response.status_code >= 500 and not results["server_error_at"]:
                    results["server_error_at"] = results["total_requests_sent"]
                    
            except Exception:
                results["responses"].append({"status_code": 0, "latency": None})
        
        time.sleep(0.1)  # Jeda antar batch
    
    # Analisis hasil
    if results["rate_limited_at"]:
        severity = "Low"
        finding_type = "rate_limiting_detected"
        description = f"Rate limiting terdeteksi setelah {results['rate_limited_at']} request"
    elif results["server_error_at"]:
        severity = "High"
        finding_type = "dos_potential_critical"
        description = f"Server mulai error setelah {results['server_error_at']} request"
    else:
        severity = "Medium"
        finding_type = "no_rate_limiting"
        description = "Tidak ada rate limiting terdeteksi setelah 1000 request"
    
    findings.append({
        "type": finding_type,
        "severity": severity,
        "source": "dos_validator",
        "endpoint": url,
        "description": description,
        "details": results,
    })
    
    return findings


def extract_url_parameters(url: str) -> List[str]:
    parsed = urlparse(url)
    return list(parse_qs(parsed.query).keys())

def test_ssrf_internal(url: str, param: str) -> bool:
    try:
        # Simplified internal test
        target_url = url.replace(f"{param}=", f"{param}=http://127.0.0.1")
        resp = requests.get(target_url, timeout=5)
        if "root:x:0:0" in resp.text or "localhost" in resp.text.lower():
            return True
    except:
        pass
    return False

def test_ssrf_user_redirect(url: str, param: str) -> bool:
    try:
        # Simplified user redirect test
        target_url = url.replace(f"{param}=", f"{param}=http://example.com")
        resp = requests.get(target_url, timeout=5, allow_redirects=False)
        if resp.status_code in [301, 302, 307, 308] and "example.com" in resp.headers.get("Location", ""):
            return True
    except:
        pass
    return False

def check_ssrf_vulnerability(url: str, user_id: int = None) -> List[Dict[str, Any]]:
    """
    Deteksi potensi SSRF dengan menguji parameter URL.
    SSRF dibagi menjadi 2 kategori:
    1. SSRF Internal (server-side) → High
    2. SSRF User (client-side / user-controlled redirect) → Medium
    """
    findings = []
    params = extract_url_parameters(url)
    
    for param in params:
        # Uji 1: Coba akses internal (hanya untuk SSRF Internal)
        internal_test = test_ssrf_internal(url, param)
        if internal_test:
            findings.append({
                "type": "ssrf_internal",
                "severity": "High",
                "source": "ssrf_validator",
                "endpoint": url,
                "parameter": param,
                "description": f"Parameter {param} dapat digunakan untuk mengakses resource internal",
            })
        
        # Uji 2: Cek redirect ke URL eksternal (SSRF User)
        user_test = test_ssrf_user_redirect(url, param)
        if user_test:
            findings.append({
                "type": "ssrf_user",
                "severity": "Medium",
                "source": "ssrf_validator",
                "endpoint": url,
                "parameter": param,
                "description": f"Parameter {param} dapat dimanipulasi user untuk redirect ke URL eksternal",
            })
    
    return findings
