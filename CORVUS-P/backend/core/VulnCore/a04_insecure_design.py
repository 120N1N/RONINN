# backend/core/VulnCore/a04_insecure_design.py
import re
import uuid
import time
import requests
from typing import List, Dict, Any
from backend.core.VulnCore.base_scanner import BaseVulnScanner

from backend.utils.asset_helper import is_static_asset

class InsecureDesign(BaseVulnScanner):
    OWASP_CODE = "A04:2021"
    CATEGORY_NAME = "Insecure Design"

    @classmethod
    def scan(cls, target_url: str, discovered_endpoints: List[str], scan_context: Dict[str, Any]) -> List[Dict]:
        findings = []

        # 1. Deteksi Pola Sequential Integer ID (Insecure Direct Object Reference risk by design)
        # Abaikan semua file statis (.js, .css, dll) agar tidak memicu False Positive IDOR
        sequential_pattern = re.compile(r'/([a-zA-Z_-]+)/(\d{1,6})(/|$)')
        flagged_seq = set()
        static_resource_names = {
            "static", "assets", "v1", "v2", "chunk", "chunks", "dist",
            "build", "js", "css", "images", "img", "fonts", "scripts",
            "vendor", "bundles", "public"
        }

        for ep in discovered_endpoints:
            # Lewati jika URL mengarah ke file statis (misal file .js)
            if is_static_asset(ep):
                continue

            match = sequential_pattern.search(ep)
            if match:
                resource_name = match.group(1)
                if resource_name not in flagged_seq and resource_name.lower() not in static_resource_names:
                    flagged_seq.add(resource_name)
                    findings.append({
                        "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                        "name": "Predictable Sequential Resource Identifier",
                        "type": "predictable_resource_id",
                        "severity": "LOW",
                        "endpoint": ep,
                        "location": ep,
                        "cvss": 4.3,
                        "description": f"Endpoint menggunakan pola identifier sequential integer '/{resource_name}/{match.group(2)}'. Ini memudahkan penyerang melakukan enumerasi massal seluruh rekaman data (BOLA/IDOR by design).",
                        "remediation": "Gunakan UUID v4 atau cryptographically secure random slugs alih-alih auto-incrementing integer ID untuk entitas publik.",
                        "points": [f"Resource terdeteksi: {resource_name}", "Format ID: auto-incrementing integer"]
                    })

        # 2. Cek Proteksi Anti-Automation / Rate Limiting pada Rute Kritis (Login, Register, Password Reset)
        sensitive_routes = [ep for ep in discovered_endpoints if any(k in ep.lower() for k in ["login", "signin", "register", "forgot", "reset-password"])]
        if not sensitive_routes:
            sensitive_routes = [f"{target_url.rstrip('/')}/login"]

        for route in sensitive_routes[:2]:
            try:
                # Pastikan rute benar-benar ada (status 200) dan memiliki form/indikator otentikasi nyata
                init_check = requests.get(route, timeout=5, verify=False)
                if init_check.status_code != 200:
                    continue
                content_lower = init_check.text.lower()
                if not any(k in content_lower for k in ["password", "login", "signin", "kata sandi", "<input"]):
                    continue

                # Kirim 6 request cepat untuk verifikasi proteksi throttling
                status_codes = []
                for _ in range(6):
                    r = requests.get(route, timeout=5, verify=False)
                    status_codes.append(r.status_code)
                    time.sleep(0.1)

                # Jika tidak pernah mengembalikan 429 dan respons konsisten 200 tanpa header rate-limit
                if 429 not in status_codes and all(c == 200 for c in status_codes):
                    findings.append({
                        "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                        "name": "Lack of Rate Limiting on Sensitive Endpoint",
                        "type": "missing_rate_limiting",
                        "severity": "MEDIUM",
                        "endpoint": route,
                        "location": route,
                        "cvss": 5.3,
                        "description": f"Endpoint sensitif '{route}' tidak menerapkan pembatasan laju permintaan (rate limiting) atau mekanisme anti-bruteforce.",
                        "remediation": "Terapkan IP-based rate limiting (misal HTTP 429 Too Many Requests), sliding window throttling, atau CAPTCHA setelah kegagalan berulang.",
                        "points": [f"Target: {route}", "6 permintaan berturut-turut diterima tanpa respon throttling HTTP 429"]
                    })
                    break
            except Exception:
                pass

        return findings
