import re
import logging
from typing import List, Dict

logger = logging.getLogger("corvus.jssecret")

# Enhanced patterns for secret discovery
PATTERNS = {
    "api_key": r'(?i)(api_key|apikey|secret|token|auth|bearer|access_key)\s*[:=]\s*["\']([A-Za-z0-9_\-\.]{10,})["\']',
    "jwt": r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',
    "private_key": r'-----BEGIN (RSA|EC|DSA|OPENSSH) PRIVATE KEY-----',
    "google_api": r'AIza[0-9A-Za-z-_]{35}',
    "aws_key": r'AKIA[0-9A-Z]{16}',
    "slack_token": r'xox[bapz]-[0-9]{12}-[a-zA-Z0-9]{24}',
    "internal_url": r'https?://(?:10|127|172|192)\.\d+\.\d+\.\d+(?::\d+)?(?:/[^\s"\']*)?'
}

def extract_secrets(js_content: str, source_url: str) -> List[Dict]:
    """
    Extracts secrets from JS content using regex patterns.
    """
    findings = []
    
    for label, pattern in PATTERNS.items():
        matches = re.finditer(pattern, js_content)
        for match in matches:
            finding_text = match.group()
            # Truncate if too long to avoid DB bloat
            if len(finding_text) > 255:
                finding_text = finding_text[:252] + "..."
                
            findings.append({
                "type": "sensitive_data_exposure_external_js",
                "subtype": label,
                "source": source_url,
                "match": finding_text,
                "confidence": 0.9,
                "severity": "HIGH" if label != "internal_url" else "MEDIUM"
            })
            
    # Deduplicate findings in same file
    unique_findings = []
    seen = set()
    for f in findings:
        key = (f["subtype"], f["match"])
        if key not in seen:
            unique_findings.append(f)
            seen.add(key)
            
    return unique_findings
