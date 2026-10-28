# backend/core/VulnCore/a05_security_misconfiguration.py
import uuid
import requests
from typing import List, Dict, Any
from backend.core.VulnCore.base_scanner import BaseVulnScanner

class SecurityMisconfiguration(BaseVulnScanner):
    OWASP_CODE = "A05:2021"
    CATEGORY_NAME = "Security Misconfiguration"

    @classmethod
    def scan(cls, target_url: str, discovered_endpoints: List[str], scan_context: Dict[str, Any]) -> List[Dict]:
        findings = []

        try:
            resp = requests.get(target_url, timeout=7, verify=False)
            headers = resp.headers

            # 1. Audit Security Headers
            missing_headers = []
            expected_headers = {
                "Content-Security-Policy": "Mencegah eksekusi skrip berbahaya dan XSS.",
                "X-Content-Type-Options": "Mencegah MIME type sniffing browser.",
                "X-Frame-Options": "Mencegah serangan pembingkaian Clickjacking.",
                "Referrer-Policy": "Mengontrol pembocoran data referrer ke domain eksternal.",
                "Permissions-Policy": "Membatasi akses fitur hardware browser (kamera, mikrofon, geolokasi)."
            }

            for h, purpose in expected_headers.items():
                if h not in headers:
                    missing_headers.append(h)

            if missing_headers:
                findings.append({
                    "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                    "name": "Missing HTTP Security Headers",
                    "type": "missing_security_headers",
                    "severity": "LOW",
                    "endpoint": target_url,
                    "location": target_url,
                    "cvss": 4.0,
                    "description": f"Server tidak menyertakan header keamanan esensial: {', '.join(missing_headers)}.",
                    "remediation": "Konfigurasikan web server (Nginx/Apache/Caddy) untuk menyertakan header keamanan standar (CSP, X-Content-Type-Options, dll).",
                    "points": [f"Header yang hilang: {', '.join(missing_headers)}"]
                })

            # 2. CORS Misconfiguration Check
            cors_headers = {"Origin": "https://corvus-untrusted-origin.com"}
            try:
                cors_resp = requests.options(target_url, headers=cors_headers, timeout=5, verify=False)
                allow_origin = cors_resp.headers.get("Access-Control-Allow-Origin")
                allow_cred = cors_resp.headers.get("Access-Control-Allow-Credentials", "").lower()

                if allow_origin == "https://corvus-untrusted-origin.com" or (allow_origin == "*" and allow_cred == "true"):
                    findings.append({
                        "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                        "name": "Overly Permissive CORS Policy",
                        "type": "cors_misconfiguration",
                        "severity": "MEDIUM",
                        "endpoint": target_url,
                        "location": target_url,
                        "cvss": 6.5,
                        "description": f"Aplikasi merefleksikan Origin sembarang ('{allow_origin}') pada header Access-Control-Allow-Origin, memungkinkan situs jahat membaca data privat lintas domain.",
                        "remediation": "Batasi nilai Access-Control-Allow-Origin hanya untuk domain tepercaya (whitelist) dan hindari penggunaan wildcard dengan kredensial.",
                        "points": [f"Origin diizinkan: {allow_origin}", f"Credentials: {allow_cred}"]
                    })
            except Exception:
                pass

        except Exception:
            pass

        # 3. Directory Listing & Debug Probe
        test_paths = [
            ("/static/", "static directory"),
            ("/uploads/", "uploads directory"),
            ("/assets/", "assets directory"),
            ("/.git/config", "exposed git repository"),
            ("/phpinfo.php", "phpinfo page")
        ]

        base = target_url.rstrip("/")
        for path, label in test_paths:
            try:
                probe_url = f"{base}{path}"
                r = requests.get(probe_url, timeout=5, verify=False)
                text_lower = r.text.lower()

                if r.status_code == 200:
                    # Directory Listing
                    if any(sig in text_lower for sig in ["index of /", "directory listing for", "<title>index of"]):
                        findings.append({
                            "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                            "name": f"Directory Listing Enabled ({label})",
                            "type": "directory_listing",
                            "severity": "MEDIUM",
                            "endpoint": probe_url,
                            "location": probe_url,
                            "cvss": 5.3,
                            "description": f"Direktori '{path}' mengekspos daftar file internal kepada publik melalui mekanisme directory listing bawaan server.",
                            "remediation": "Nonaktifkan fitur auto-indexing pada web server ('Options -Indexes' di Apache atau matikan 'autoindex' di Nginx).",
                            "points": [f"Path: {path}", "Indeks direktori publik terdeteksi"]
                        })

                    # Sensitive File Leakage
                    if path == "/.git/config" and "[core]" in r.text:
                        findings.append({
                            "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                            "name": "Exposed Git Repository Configuration",
                            "type": "information_disclosure",
                            "severity": "HIGH",
                            "endpoint": probe_url,
                            "location": probe_url,
                            "cvss": 7.5,
                            "description": "Folder .git/config dapat diakses publik, memungkinkan penyerang mengunduh seluruh source code dan riwayat commit aplikasi.",
                            "remediation": "Blokir akses publik ke semua folder dan file tersembunyi (dotfiles) seperti '/.git' pada level web server.",
                            "points": [f"Path: {path}", "Konfigurasi repositori Git ditemukan"]
                        })

                    if path == "/phpinfo.php" and "php version" in text_lower:
                        findings.append({
                            "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                            "name": "Exposed PHP Information Page (phpinfo)",
                            "type": "information_disclosure",
                            "severity": "MEDIUM",
                            "endpoint": probe_url,
                            "location": probe_url,
                            "cvss": 5.3,
                            "description": "Halaman phpinfo() terekspos ke publik, membocorkan rincian arsitektur server, variabel lingkungan, dan ekstensi yang terpasang.",
                            "remediation": "Hapus file phpinfo.php dari server produksi.",
                            "points": [f"Path: {path}", "PHP Information page ditemukan"]
                        })
            except Exception:
                pass

        return findings
