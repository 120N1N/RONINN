# backend/core/VulnCore/a08_data_integrity.py
import re
import uuid
import requests
from typing import List, Dict, Any
from urllib.parse import urlparse
from backend.core.VulnCore.base_scanner import BaseVulnScanner

class DataIntegrityFailures(BaseVulnScanner):
    OWASP_CODE = "A08:2021"
    CATEGORY_NAME = "Software and Data Integrity Failures"

    @classmethod
    def scan(cls, target_url: str, discovered_endpoints: List[str], scan_context: Dict[str, Any]) -> List[Dict]:
        findings = []

        try:
            resp = requests.get(target_url, timeout=7, verify=False)
            html = resp.text
            target_host = urlparse(target_url).netloc

            # 1. Deteksi Skrip Eksternal Tanpa Subresource Integrity (SRI)
            script_pattern = re.compile(r'<script\s+[^>]*src=["\'](https?://[^"\']+)["\'][^>]*>', re.IGNORECASE)
            scripts = script_pattern.finditer(html)

            unprotected_scripts = []
            for m in scripts:
                full_tag = m.group(0)
                src = m.group(1)
                parsed_src = urlparse(src)

                # Jika skrip berasal dari domain pihak ketiga (CDN)
                if parsed_src.netloc and parsed_src.netloc != target_host:
                    if "integrity=" not in full_tag.lower():
                        unprotected_scripts.append(src)

            if unprotected_scripts:
                sample_scripts = unprotected_scripts[:3]
                findings.append({
                    "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                    "name": "Missing Subresource Integrity (SRI) on External Scripts",
                    "type": "missing_subresource_integrity",
                    "severity": "LOW",
                    "endpoint": target_url,
                    "location": target_url,
                    "cvss": 4.2,
                    "description": f"Ditemukan {len(unprotected_scripts)} skrip JavaScript pihak ketiga yang dimuat tanpa atribut 'integrity'. Jika CDN pihak ketiga disusupi (supply chain attack), penyerang dapat mengeksekusi kode berbahaya pada browser pengguna.",
                    "remediation": "Sematkan atribut 'integrity' berupa hash kriptografi (sha384/sha512) dan atribut 'crossorigin=\"anonymous\"' pada semua tag skrip eksternal.",
                    "points": [f"Contoh skrip tanpa SRI: {', '.join(sample_scripts)}"]
                })

        except Exception:
            pass

        return findings
