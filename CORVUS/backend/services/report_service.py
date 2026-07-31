# backend/services/report_service.py
import json
from backend.db import models

class ReportService:
    @staticmethod
    def generate_json(scan: models.Scan) -> str:
        """Generates JSON report data."""
        report_data = {
            "id": scan.id,
            "target": scan.target,
            "status": scan.status,
            "findings": [
                {
                    "type": f.get("type"),
                    "severity": f.get("severity"),
                    "endpoint": f.get("endpoint") or f.get("location"),
                    "owasp": f.get("owasp_category") or f.get("category"),
                    "owasp_code": f.get("owasp_code", "A00:2021"),
                    "risk": f.get("risk_score") or f.get("cvss")
                } for f in scan.findings
            ]
        }
        return json.dumps(report_data, indent=2)

    @staticmethod
    def generate_markdown(scan: models.Scan) -> str:
        """Generates Markdown report data."""
        md = f"# Security Audit Report: {scan.target}\n"
        md += f"- **Scan ID**: {scan.id}\n"
        md += f"- **Status**: {scan.status}\n"
        md += f"- **Timestamp**: {scan.finished_at}\n\n"
        md += "## Vulnerability Findings\n\n"
        
        for f in scan.findings:
            code = f.get("owasp_code", "A00:2021")
            name = f.get("owasp_category") or f.get("category")
            md += f"### {code} – {name}\n"
            md += f"- **Type**: {f.get('type')}\n"
            md += f"- **Severity**: {f.get('severity')}\n"
            md += f"- **Endpoint**: {f.get('endpoint') or f.get('location')}\n"
            md += f"- **Risk Score**: {f.get('risk_score') or f.get('cvss')}\n"
            md += f"- **Description**: {f.get('description', 'N/A')}\n\n"
        
        return md

    @staticmethod
    def generate_pdf(scan_id: str):
        """Logic for PDF generation (requires pdfkit)"""
        pass
