from typing import List, Dict, Any
from backend.core.VulnCore.base_scanner import BaseVulnScanner

class SSRF(BaseVulnScanner):
    OWASP_CODE = "A10:2021"
    CATEGORY_NAME = "Server-Side Request Forgery"

    @classmethod
    def scan(cls, target_url: str, discovered_endpoints: List[str], scan_context: Dict[str, Any]) -> List[Dict]:
        findings = []
        # TODO: A10 (Mendeteksi SSRF, mengeksploitasi webhook proxy internal)
        return findings
