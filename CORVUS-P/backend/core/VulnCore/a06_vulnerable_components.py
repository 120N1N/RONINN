# backend/core/VulnCore/a06_vulnerable_components.py
import re
import uuid
import requests
from typing import List, Dict, Any
from backend.core.VulnCore.base_scanner import BaseVulnScanner

OUTDATED_JS_LIBS = [
    (r"jquery[.-](1\.[0-9]+\.[0-9]+|2\.[0-9]+\.[0-9]+|3\.[0-4]\.[0-9]+)", "Outdated jQuery Library (< 3.5.0)", "CVE-2020-11022 / CVE-2020-11023 (Cross-Site Scripting via htmlPrefilter)"),
    (r"bootstrap[.-](3\.[0-9]+\.[0-9]+|4\.[0-3]\.[0-9]+)", "Outdated Bootstrap Framework (< 4.4.0)", "CVE-2019-8331 (XSS in tooltip/popover)"),
    (r"angular[.-](1\.[0-7]\.[0-9]+)", "Outdated AngularJS v1.x (End-of-Life)", "AngularJS 1.x is End-of-Life and vulnerable to client-side template injection"),
]

class VulnerableComponents(BaseVulnScanner):
    OWASP_CODE = "A06:2021"
    CATEGORY_NAME = "Vulnerable and Outdated Components"

    @classmethod
    def scan(cls, target_url: str, discovered_endpoints: List[str], scan_context: Dict[str, Any]) -> List[Dict]:
        findings = []

        try:
            resp = requests.get(target_url, timeout=7, verify=False)
            headers = resp.headers
            body = resp.text

            # 1. Audit Header Server & X-Powered-By Version Exposure
            server_banner = headers.get("Server", "")
            powered_by = headers.get("X-Powered-By", "")

            # Deteksi jika ada angka versi di banner
            for header_name, banner_val in [("Server", server_banner), ("X-Powered-By", powered_by)]:
                if banner_val and any(char.isdigit() for char in banner_val):
                    findings.append({
                        "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                        "name": f"Detailed Technology Version Disclosure in {header_name}",
                        "type": "technology_version_disclosure",
                        "severity": "LOW",
                        "endpoint": target_url,
                        "location": target_url,
                        "cvss": 4.3,
                        "description": f"Header '{header_name}' membocorkan versi detail perangkat lunak: '{banner_val}'. Informasi ini mempermudah penyerang menargetkan eksploit CVE spesifik.",
                        "remediation": f"Sembunyikan atau samarkan header '{header_name}' (misal 'ServerTokens Prod' di Apache atau 'server_tokens off' di Nginx).",
                        "points": [f"Header: {header_name}", f"Nilai terdeteksi: {banner_val}"]
                    })

            # 2. Audit Client-side JavaScript Libraries
            for pattern, lib_title, vuln_reason in OUTDATED_JS_LIBS:
                matches = re.findall(pattern, body, re.IGNORECASE)
                if matches:
                    matched_version = matches[0]
                    findings.append({
                        "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                        "name": lib_title,
                        "type": "vulnerable_javascript_library",
                        "severity": "MEDIUM",
                        "endpoint": target_url,
                        "location": target_url,
                        "cvss": 6.1,
                        "description": f"Aplikasi memuat pustaka JavaScript usang ({matched_version}) yang memiliki kerentanan keamanan publik yang diketahui: {vuln_reason}.",
                        "remediation": "Perbarui dependensi pustaka JavaScript klien ke versi stabil terbaru dan terapkan alat audit paket berkala.",
                        "points": [f"Pustaka: {lib_title}", f"Versi terdeteksi: {matched_version}", f"Alasan: {vuln_reason}"]
                    })

        except Exception:
            pass

        return findings
