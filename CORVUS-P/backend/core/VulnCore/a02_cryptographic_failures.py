# backend/core/VulnCore/a02_cryptographic_failures.py
import uuid
import requests
from typing import List, Dict, Any
from urllib.parse import urlparse
from backend.core.VulnCore.base_scanner import BaseVulnScanner

class CryptographicFailures(BaseVulnScanner):
    OWASP_CODE = "A02:2021"
    CATEGORY_NAME = "Cryptographic Failures"

    @classmethod
    def scan(cls, target_url: str, discovered_endpoints: List[str], scan_context: Dict[str, Any]) -> List[Dict]:
        findings = []
        all_urls = [target_url] + discovered_endpoints[:25]
        parsed_target = urlparse(target_url)

        # 1. Cek Protokol Plaintext (HTTP alih-alih HTTPS)
        if parsed_target.scheme == "http":
            findings.append({
                "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                "name": "Cleartext Transmission over HTTP",
                "type": "insecure_transport_http",
                "severity": "HIGH",
                "endpoint": target_url,
                "location": target_url,
                "cvss": 7.4,
                "description": "Lalu lintas web ditransmisikan tanpa enkripsi TLS/HTTPS. Komunikasi rentan terhadap serangan Man-in-the-Middle (MitM) dan penyadapan jaringan.",
                "remediation": "Terapkan sertifikat TLS/SSL (misal via Let's Encrypt) dan lakukan redirect permanen (301) dari HTTP ke HTTPS.",
                "points": ["Skema protokol target menggunakan HTTP mentah", "Data sensitif dan kredensial terancam terkompromi di jaringan publik"]
            })

        # 2. Cek HSTS (Strict-Transport-Security) & Cookie Security
        try:
            resp = requests.get(target_url, timeout=7, allow_redirects=True, verify=False)
            headers = resp.headers

            # Cek HSTS jika target berbasis HTTPS
            if parsed_target.scheme == "https":
                hsts = headers.get("Strict-Transport-Security")
                if not hsts:
                    findings.append({
                        "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                        "name": "Missing Strict-Transport-Security (HSTS)",
                        "type": "missing_hsts_header",
                        "severity": "MEDIUM",
                        "endpoint": target_url,
                        "location": target_url,
                        "cvss": 5.3,
                        "description": "Header Strict-Transport-Security tidak ditemukan pada respons server HTTPS. Hal ini memungkinkan serangan SSL-stripping.",
                        "remediation": "Tambahkan header 'Strict-Transport-Security: max-age=31536000; includeSubDomains; preload' pada konfigurasi web server.",
                        "points": ["Header Strict-Transport-Security absen dari HTTP response", "Koneksi dapat diturunkan paksa ke HTTP polos oleh perantara MitM"]
                    })

            # Cek Cookie tanpa flag Secure
            set_cookie_headers = resp.headers.get("Set-Cookie", "")
            if set_cookie_headers:
                raw_cookies = [c.strip() for c in set_cookie_headers.split(",") if "=" in c]
                for cookie_str in raw_cookies:
                    c_name = cookie_str.split("=")[0].strip()
                    if any(s in c_name.lower() for s in ["sess", "auth", "token", "jwt", "id", "user"]):
                        if "secure" not in cookie_str.lower():
                            findings.append({
                                "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                                "name": "Sensitive Cookie Missing 'Secure' Flag",
                                "type": "cookie_missing_secure",
                                "severity": "MEDIUM",
                                "endpoint": target_url,
                                "location": target_url,
                                "cvss": 5.0,
                                "description": f"Cookie sensitif '{c_name}' tidak dilengkapi flag 'Secure', memungkinkan transmisi via koneksi HTTP tidak terenkripsi.",
                                "remediation": "Tambahkan atribut '; Secure; SameSite=Lax' pada konfigurasi Set-Cookie.",
                                "points": [f"Cookie: {c_name}", "Flag Secure tidak terpasang"]
                            })
                            break
        except Exception:
            pass

        return findings
