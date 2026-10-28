# backend/core/VulnCore/a07_auth_failures.py
import uuid
import requests
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs
from backend.core.VulnCore.base_scanner import BaseVulnScanner

from backend.utils.asset_helper import is_static_asset

class IdentificationAuthFailures(BaseVulnScanner):
    OWASP_CODE = "A07:2021"
    CATEGORY_NAME = "Identification and Authentication Failures"

    @classmethod
    def scan(cls, target_url: str, discovered_endpoints: List[str], scan_context: Dict[str, Any]) -> List[Dict]:
        findings = []

        # 1. Cek Parameter Query Mengandung Session Token / Kredensial
        all_urls = [target_url] + [ep for ep in discovered_endpoints if not is_static_asset(ep)][:30]
        token_keywords = ["session", "token", "auth", "jwt", "apikey", "access_token", "secret", "sessionid", "session_id"]

        for ep in all_urls:
            parsed = urlparse(ep)
            params = parse_qs(parsed.query)
            for param, values in params.items():
                if any(k == param.lower() or f"{k}_" in param.lower() for k in token_keywords):
                    val = values[0] if values else ""
                    # Abaikan flag boolean trivial seperti ?auth=true atau ?token=1
                    if val.lower() in ["true", "false", "0", "1", "yes", "no", ""] or len(val) < 8:
                        continue

                    findings.append({
                        "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                        "name": "Session Token Exposed in URL Query String",
                        "type": "token_in_url",
                        "severity": "HIGH",
                        "endpoint": ep,
                        "location": ep,
                        "cvss": 7.1,
                        "description": f"Token otentikasi atau session identifier dilewatkan melalui query string URL ('?{param}={val[:4]}...'). Ini berisiko bocor melalui log server, riwayat browser, dan header Referer.",
                        "remediation": "Kirimkan token otentikasi melalui HTTP Request Header (misal 'Authorization: Bearer <token>') atau cookie HttpOnly, bukan parameter URL.",
                        "points": [f"Parameter: {param}", "Token autentikasi terbuka di URL"]
                    })
                    break

        # 2. Cek Cookie Sensitif tanpa HttpOnly
        try:
            resp = requests.get(target_url, timeout=7, verify=False)
            set_cookie_raw = resp.headers.get("Set-Cookie", "")
            if set_cookie_raw:
                cookies = [c.strip() for c in set_cookie_raw.split(",") if "=" in c]
                for c in cookies:
                    c_name = c.split("=")[0].strip()
                    if any(s in c_name.lower() for s in ["sess", "auth", "token", "jwt", "id", "login"]):
                        if "httponly" not in c.lower():
                            findings.append({
                                "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                                "name": "Session Cookie Missing 'HttpOnly' Flag",
                                "type": "cookie_missing_httponly",
                                "severity": "MEDIUM",
                                "endpoint": target_url,
                                "location": target_url,
                                "cvss": 6.0,
                                "description": f"Cookie sesi '{c_name}' tidak memiliki flag 'HttpOnly'. Hal ini memungkinkan skrip JavaScript berbahaya (XSS) membaca nilai cookie secara langsung.",
                                "remediation": "Tambahkan direktif '; HttpOnly' pada seluruh pembuatan Set-Cookie yang memuat sesi atau token otentikasi.",
                                "points": [f"Cookie: {c_name}", "Flag HttpOnly tidak disematkan"]
                            })
                            break
        except Exception:
            pass

        return findings
