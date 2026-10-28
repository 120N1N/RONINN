# backend/core/VulnCore/a10_ssrf.py
import uuid
import requests
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from backend.core.VulnCore.base_scanner import BaseVulnScanner

from backend.utils.asset_helper import is_static_asset

SSRF_PARAMS = ["url", "dest", "destination", "redirect", "redirect_url", "target", "uri", "proxy", "feed", "webhook", "fetch"]

class SSRF(BaseVulnScanner):
    OWASP_CODE = "A10:2021"
    CATEGORY_NAME = "Server-Side Request Forgery (SSRF)"

    @classmethod
    def scan(cls, target_url: str, discovered_endpoints: List[str], scan_context: Dict[str, Any]) -> List[Dict]:
        findings = []
        tested_params = set()

        endpoints_to_test = [ep for ep in discovered_endpoints if "?" in ep and not is_static_asset(ep)][:20]

        for ep in endpoints_to_test:
            parsed = urlparse(ep)
            params = parse_qs(parsed.query)

            for param, values in params.items():
                if any(k == param.lower() or f"{k}_" in param.lower() for k in SSRF_PARAMS):
                    param_key = f"{parsed.path}?{param}"
                    if param_key in tested_params:
                        continue
                    tested_params.add(param_key)

                    # Uji Open Redirect / URL Forwarding aman menggunakan domain netral
                    mutated = params.copy()
                    mutated[param] = ["https://example.com"]
                    test_url = urlunparse(parsed._replace(query=urlencode(mutated, doseq=True)))

                    try:
                        r = requests.get(test_url, timeout=5, allow_redirects=False, verify=False)
                        location_header = r.headers.get("Location", "")

                        if r.status_code in [301, 302, 303, 307, 308] and "example.com" in location_header:
                            findings.append({
                                "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                                "name": "Unvalidated Redirect (Open Redirect / Potential SSRF)",
                                "type": "open_redirect",
                                "severity": "MEDIUM",
                                "endpoint": test_url,
                                "location": test_url,
                                "cvss": 6.1,
                                "description": f"Parameter '{param}' menerima URL eksternal dan langsung mengalihkan pengguna (HTTP {r.status_code}) ke domain tersebut tanpa validasi whitelist origin.",
                                "remediation": "Terapkan whitelist ketat untuk nilai URL yang diizinkan, atau gunakan token pemetaan internal daripada menerima URL lengkap dari pengguna.",
                                "points": [f"Parameter: {param}", f"Header Location terefleksi: '{location_header}'"]
                            })
                        else:
                            # Catat sebagai potensi parameter penjemput resource (SSRF Surface) HANYA jika nilai aslinya menyerupai URL/path
                            original_val = values[0] if values else ""
                            if any(original_val.startswith(p) for p in ["http://", "https://", "//", "/"]) or ("." in original_val and "/" in original_val):
                                findings.append({
                                    "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                                    "name": "Potential Server-Side Fetch Parameter (SSRF Surface)",
                                    "type": "ssrf_potential_parameter",
                                    "severity": "LOW",
                                    "endpoint": ep,
                                    "location": ep,
                                    "cvss": 4.5,
                                    "description": f"Parameter '{param}' menerima format URL ('{original_val}') yang rentan disalahgunakan untuk serangan Server-Side Request Forgery.",
                                    "remediation": "Pastikan validasi skema (hanya http/https), blokir resolusi IP privat/loopback (127.0.0.1, 10.0.0.0/8, 192.168.0.0/16), dan nonaktifkan ikuti redirect otomatis.",
                                    "points": [f"Parameter: {param}", f"Nilai terdeteksi: {original_val}"]
                                })
                    except Exception:
                        pass

        return findings
