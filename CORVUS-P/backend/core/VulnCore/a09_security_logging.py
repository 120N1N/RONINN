# backend/core/VulnCore/a09_security_logging.py
import uuid
import requests
from typing import List, Dict, Any
from backend.core.VulnCore.base_scanner import BaseVulnScanner

STACKTRACE_SIGNATURES = [
    "traceback (most recent call last):",
    "exception in thread",
    "fatal error:",
    "stack trace:",
    "at org.springframework.",
    "laravel\\framework",
    "microsoft.aspnetcore",
    "django.core.exceptions"
]

class SecurityLoggingFailures(BaseVulnScanner):
    OWASP_CODE = "A09:2021"
    CATEGORY_NAME = "Security Logging and Monitoring Failures"

    @classmethod
    def scan(cls, target_url: str, discovered_endpoints: List[str], scan_context: Dict[str, Any]) -> List[Dict]:
        findings = []

        # 1. Uji Penanganan Error Kritis & Kebocoran Stacktrace Internal
        test_endpoints = [target_url] + [ep for ep in discovered_endpoints if "/api/" in ep][:5]

        for ep in test_endpoints:
            try:
                # Kirim request dengan format sengaja anomali (header/karakter khusus)
                r = requests.get(f"{ep}?corvus_debug_test=%00%27%22", timeout=5, verify=False)
                body_lower = r.text.lower()

                if r.status_code >= 500:
                    matched_sig = next((sig for sig in STACKTRACE_SIGNATURES if sig in body_lower), None)
                    if matched_sig:
                        findings.append({
                            "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                            "name": "Unhandled Exception and Internal Stack Trace Disclosure",
                            "type": "verbose_error_stacktrace",
                            "severity": "MEDIUM",
                            "endpoint": ep,
                            "location": ep,
                            "cvss": 5.3,
                            "description": f"Server mengembalikan HTTP {r.status_code} beserta jejak tumpukan kode internal (stack trace). Hal ini mengindikasikan kegagalan penanganan pengecualian (exception handling) dan pembocoran struktur internal.",
                            "remediation": "Terapkan global error handler terpusat yang mencatat detail error ke sistem logging internal dan hanya mengembalikan pesan error generik yang ramah pengguna.",
                            "points": [f"Status HTTP: {r.status_code}", f"Pola stack trace terdeteksi: '{matched_sig}'"]
                        })
                        break
            except Exception:
                pass

        return findings
