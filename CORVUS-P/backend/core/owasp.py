# backend/core/owasp.py

OWASP_SEVERITY_MAP = {
    "critical": "Critical",
    "high": "High",
    "medium": "Medium",
    "low": "Low",
    "info": "Informational",
    "informational": "Informational"
}

OWASP_CATEGORIES = {
    "broken_access_control": {"code": "A01:2021", "name": "Broken Access Control"},
    "cryptographic_failures": {"code": "A02:2021", "name": "Cryptographic Failures"},
    "injection": {"code": "A03:2021", "name": "Injection"},
    "insecure_design": {"code": "A04:2021", "name": "Insecure Design"},
    "security_misconfiguration": {"code": "A05:2021", "name": "Security Misconfiguration"},
    "vulnerable_outdated_components": {"code": "A06:2021", "name": "Vulnerable and Outdated Components"},
    "auth_failures": {"code": "A07:2021", "name": "Identification and Authentication Failures"},
    "software_data_integrity_failures": {"code": "A08:2021", "name": "Software and Data Integrity Failures"},
    "logging_monitoring_failures": {"code": "A09:2021", "name": "Security Logging and Monitoring Failures"},
    "ssrf": {"code": "A10:2021", "name": "Server-Side Request Forgery (SSRF)"},
    "sensitive_data": {"code": "A02:2021", "name": "Cryptographic Failures"},
    "xss": {"code": "A03:2021", "name": "Injection"},
    "dos": {"code": "A04:2021", "name": "Insecure Design"},
}

def map_to_owasp(vuln_type: str) -> dict:
    """Memetakan tipe kerentanan ke kategori OWASP Top 10 2021."""
    v = vuln_type.lower()
    
    if any(x in v for x in ["broken_access", "idor", "traversal", "lfi", "rfi", "path", "admin", "panel"]):
        cat = "broken_access_control"
    elif any(x in v for x in ["sql", "xss", "injection", "template", "graphql", "xxe"]):
        cat = "injection"
    elif any(x in v for x in ["crypto", "sensitive", "secret", "token", "key", "jwt", "information_disclosure", "exposure"]):
        cat = "cryptographic_failures"
    elif any(x in v for x in ["design", "logic", "dos", "rate_limiting"]):
        cat = "insecure_design"
    elif any(x in v for x in ["config", "header", "clickjacking", "method", "cors", "hsts", "cookie"]):
        cat = "security_misconfiguration"
    elif any(x in v for x in ["vulnerable", "outdated", "cve"]):
        cat = "vulnerable_outdated_components"
    elif any(x in v for x in ["auth", "login", "password", "brute", "session", "logout"]):
        cat = "auth_failures"
    elif any(x in v for x in ["integrity", "deserialization"]):
        cat = "software_data_integrity_failures"
    elif any(x in v for x in ["log", "monitor", "audit"]):
        cat = "logging_monitoring_failures"
    elif any(x in v for x in ["ssrf", "open_redirect", "redirect"]):
        cat = "ssrf"
    else:
        cat = "security_misconfiguration" # Default better than injection

    return OWASP_CATEGORIES.get(cat, {"code": "A00:2021", "name": "General Vulnerability"})
