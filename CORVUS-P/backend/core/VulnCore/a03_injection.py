# backend/core/VulnCore/a03_injection.py
import uuid
import requests
from typing import List, Dict, Any
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from backend.core.VulnCore.base_scanner import BaseVulnScanner

SQL_ERRORS = [
    "you have an error in your sql syntax",
    "warning: mysql_",
    "unclosed quotation mark after the character string",
    "pg_query()",
    "psycopg2.operationalerror",
    "ora-01756",
    "sqlite3.operationalerror",
    "microsoft ole db provider for sql server",
    "syntax error in string in query expression",
    "invalid sql statement"
]

from backend.utils.asset_helper import is_static_asset

class Injection(BaseVulnScanner):
    OWASP_CODE = "A03:2021"
    CATEGORY_NAME = "Injection"

    @classmethod
    def scan(cls, target_url: str, discovered_endpoints: List[str], scan_context: Dict[str, Any]) -> List[Dict]:
        findings = []
        tested_params = set()

        endpoints_to_test = [ep for ep in discovered_endpoints if "?" in ep and not is_static_asset(ep)][:15]
        if not endpoints_to_test and "?" in target_url and not is_static_asset(target_url):
            endpoints_to_test = [target_url]

        for url in endpoints_to_test:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)

            for param, values in params.items():
                param_key = f"{parsed.path}?{param}"
                if param_key in tested_params:
                    continue
                tested_params.add(param_key)

                original_val = values[0] if values else "1"

                # 1. Safe Canary Check for Reflected Input / XSS Potential
                canary_token = f"crvcanary{uuid.uuid4().hex[:6]}"
                mutated_query = params.copy()
                mutated_query[param] = [f"{original_val}{canary_token}"]
                test_url = urlunparse(parsed._replace(query=urlencode(mutated_query, doseq=True)))

                try:
                    r = requests.get(test_url, timeout=6, verify=False)
                    if canary_token in r.text:
                        findings.append({
                            "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                            "name": "Reflected Input Parameter (Potential XSS)",
                            "type": "reflected_xss_potential",
                            "severity": "MEDIUM",
                            "endpoint": test_url,
                            "location": test_url,
                            "cvss": 6.1,
                            "description": f"Nilai parameter '{param}' direfleksikan secara langsung ke dalam respons HTML tanpa sanitasi atau encoding yang memadai.",
                            "remediation": f"Terapkan kontekstual HTML-encoding pada nilai input parameter '{param}' sebelum ditampilkan di browser.",
                            "points": [f"Parameter: {param}", f"Token unik {canary_token} terpantul mentah di dalam respons HTTP"]
                        })
                except Exception:
                    pass

                # 2. Benign SQL Error Probe
                mutated_sql = params.copy()
                mutated_sql[param] = [f"{original_val}'"]
                test_sql_url = urlunparse(parsed._replace(query=urlencode(mutated_sql, doseq=True)))

                try:
                    r_sql = requests.get(test_sql_url, timeout=6, verify=False)
                    body_lower = r_sql.text.lower()
                    matched_err = next((err for err in SQL_ERRORS if err in body_lower), None)

                    if matched_err:
                        findings.append({
                            "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                            "name": "Database Error Leakage (SQL Injection Indicator)",
                            "type": "sql_injection_indicator",
                            "severity": "HIGH",
                            "endpoint": test_sql_url,
                            "location": test_sql_url,
                            "cvss": 8.2,
                            "description": f"Aplikasi membocorkan pesan error database mentah saat menerima karakter petik pada parameter '{param}'. Mengindikasikan potensi kerentanan SQL Injection.",
                            "remediation": "Gunakan Parameterized Queries (Prepared Statements) atau ORM resmi, serta nonaktifkan pesan error database di lingkungan produksi.",
                            "points": [f"Parameter: {param}", f"Deteksi string error database: '{matched_err}'"]
                        })
                except Exception:
                    pass

                # 3. SSTI Arithmetic Probe (Server-Side Template Injection)
                mutated_ssti = params.copy()
                mutated_ssti[param] = ["{{47*53}}"]
                test_ssti_url = urlunparse(parsed._replace(query=urlencode(mutated_ssti, doseq=True)))

                try:
                    r_ssti = requests.get(test_ssti_url, timeout=6, verify=False)
                    if "2491" in r_ssti.text and "2491" not in r.text:
                        findings.append({
                            "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                            "name": "Server-Side Template Injection (SSTI)",
                            "type": "ssti_potential",
                            "severity": "CRITICAL",
                            "endpoint": test_ssti_url,
                            "location": test_ssti_url,
                            "cvss": 9.3,
                            "description": f"Ekspresi template aritmatika '{{47*53}}' dieksekusi di server dan mengembalikan hasil kalkulasi '2491' pada parameter '{param}'.",
                            "remediation": "Gunakan sandboxed template rendering dan hindari konkatenasi string input pengguna langsung ke dalam engine template.",
                            "points": [f"Parameter: {param}", "Ekspresi aritmatika template berhasil dievaluasi oleh server"]
                        })
                except Exception:
                    pass

        return findings
