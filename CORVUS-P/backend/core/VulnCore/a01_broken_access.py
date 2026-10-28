import uuid
from typing import List, Dict, Any
from backend.core.VulnCore.base_scanner import BaseVulnScanner
from backend.utils.asset_helper import is_static_asset

class BrokenAccessControl(BaseVulnScanner):
    OWASP_CODE = "A01:2021"
    CATEGORY_NAME = "Broken Access Control"

    @classmethod
    def scan(cls, target_url: str, discovered_endpoints: List[str], scan_context: Dict[str, Any]) -> List[Dict]:
        findings = []
        
        from backend.utils.existence_checker import ExistenceChecker
        
        # Contoh 1: Heuristik Statis. Mencari endpoint sensitif
        for endpoint in discovered_endpoints:
            if is_static_asset(endpoint):
                continue
            if any(path in endpoint for path in ["/admin", "/superuser", "/private/"]):
                finding = {
                    "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                    "name": "Exposed Administrative Interface",
                    "type": "exposed_admin_panel",
                    "severity": "HIGH",
                    "endpoint": endpoint,
                    "location": endpoint,
                    "cvss": 7.5,
                    "description": "Antarmuka administratif terdeteksi dapat diakses dari jaringan publik. Ini adalah ancaman BFLA (Broken Function Level Authorization).",
                    "remediation": "Gunakan whitelisting IP lokal dan validasikan identitas admin pada setiap permintaan.",
                    "points": ["Rute sensitif ditemukan di peta direktori/API", "Memungkinkan eksploitasi paksa (Brute Force)"]
                }
                
                if ExistenceChecker.is_really_vulnerable(finding):
                    findings.append(finding)
                
        # (Nanti di sini bisa memuat tools khusus ACL juga, seperti memanggil AuthAnalyzer)
        
        return findings
