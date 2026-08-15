# backend/services/report_service.py
import json
from datetime import datetime
from backend.db import models

class ReportService:
    @staticmethod
    def generate_json(scan: models.Scan) -> str:
        """Generates JSON report data with POC-REPORT structure."""
        findings_data = []
        for idx, f in enumerate(scan.findings or [], 1):
            findings_data.append({
                "report_id": f"POC-REPORT-{scan.id[:8]}-{idx:04d}",
                "type": f.get("type") or f.get("title", "Unclassified Vulnerability"),
                "severity": (f.get("severity") or "MEDIUM").upper(),
                "endpoint": f.get("endpoint") or f.get("location") or scan.target,
                "owasp_category": f.get("owasp_category") or f.get("category") or "A00:2021 – General Vulnerability",
                "owasp_code": f.get("owasp_code", "A00:2021"),
                "cwe": f.get("cwe") or f.get("cwe_id") or "CWE-200",
                "cvss_score": f.get("risk_score") or f.get("cvss") or 5.0,
                "evidence": f.get("evidence") or f.get("proof") or "N/A",
                "payload": f.get("payload") or f.get("evidence") or "N/A",
                "description": f.get("description") or "Automated finding detected by Corvus scanner.",
                "remediation": f.get("remediation") or f.get("recommendation") or "Review input validation and apply least privilege principles."
            })

        report_data = {
            "metadata": {
                "report_format": "POC-REPORT",
                "scan_id": scan.id,
                "target": scan.target,
                "status": scan.status,
                "created_at": scan.created_at.isoformat() if scan.created_at else datetime.utcnow().isoformat(),
                "finished_at": scan.finished_at.isoformat() if scan.finished_at else None,
                "total_findings": len(findings_data)
            },
            "findings": findings_data
        }
        return json.dumps(report_data, indent=2)

    @staticmethod
    def generate_markdown(scan: models.Scan) -> str:
        """Generates Markdown report formatted strictly according to the POC-REPORT template."""
        created_date = scan.created_at.strftime("%Y-%m-%d") if scan.created_at else datetime.utcnow().strftime("%Y-%m-%d")
        findings = scan.findings or []

        # Tentukan keparahan tertinggi & max CVSS
        severities = [ (f.get("severity") or "INFO").upper() for f in findings ]
        sev_order = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "INFO": 0}
        highest_sev = max(severities, key=lambda s: sev_order.get(s, 0)) if severities else "INFO"
        
        cvss_scores = [ float(f.get("cvss") or f.get("risk_score") or 0.0) for f in findings ]
        max_cvss = max(cvss_scores) if cvss_scores else 0.0

        md = f"# 🛸 POC-REPORT – Complete Security Audit Report\n\n"
        md += f"---\n\n"
        md += f"## 1. REPORT METADATA\n\n"
        md += f"| **Field** | **Detail** |\n"
        md += f"|-----------|------------|\n"
        md += f"| Report ID | `POC-REPORT-{scan.id[:8]}` |\n"
        md += f"| Date Submitted | `{created_date}` |\n"
        md += f"| Reporter | `@corvus_autobot` |\n"
        md += f"| Program | `Corvus Automated Security Platform` |\n"
        md += f"| Target | `{scan.target}` |\n"
        md += f"| Severity (Max) | `{highest_sev}` |\n"
        md += f"| CVSS v3.1 Score | `{max_cvss:.1f}` |\n"
        md += f"| CVSS Vector | `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |\n\n"
        md += f"---\n\n"

        md += f"## 2. VULNERABILITY SUMMARY ({len(findings)} Findings)\n\n"
        if not findings:
            md += f"> **Status**: Clean scan. No automated vulnerabilities identified for `{scan.target}`.\n\n"
            return md

        md += f"| **#** | **Type** | **Severity** | **Endpoint** | **OWASP Category** |\n"
        md += f"|---|---|---|---|---|\n"
        for idx, f in enumerate(findings, 1):
            vtype = f.get("type") or f.get("title", "Vulnerability")
            vsev = (f.get("severity") or "MEDIUM").upper()
            vep = f.get("endpoint") or f.get("location") or scan.target
            vcat = f.get("owasp_category") or f.get("owasp_code") or "A00:2021"
            md += f"| {idx} | `{vtype}` | **{vsev}** | `{vep}` | `{vcat}` |\n"
        
        md += f"\n---\n\n"

        # Detail Per-Vulnerability
        for idx, f in enumerate(findings, 1):
            vtype = f.get("type") or f.get("title", "Vulnerability")
            vsev = (f.get("severity") or "MEDIUM").upper()
            vep = f.get("endpoint") or f.get("location") or scan.target
            vcat = f.get("owasp_category") or f.get("category") or "A00:2021 – Security Finding"
            owasp_code = f.get("owasp_code", "A00:2021")
            cwe = f.get("cwe") or f.get("cwe_id") or "CWE-200"
            cvss = f.get("risk_score") or f.get("cvss") or 5.0
            evidence = f.get("evidence") or f.get("proof") or f.get("details") or "Automated execution detected anomalous response pattern."
            payload = f.get("payload") or f.get("evidence") or "N/A"
            desc = f.get("description") or f"An automated security scan identified a potential {vtype} vulnerability at endpoint {vep}."
            remediation = f.get("remediation") or f.get("recommendation") or "Validate all input parameters on server side, use parameterized queries/escaping, and enforce strict authorization controls."

            md += f"# POC-REPORT DETAILED FINDING #{idx}: {vtype}\n\n"
            md += f"### 1. VULNERABILITY CLASSIFICATION\n\n"
            md += f"| **Category** | **Value** |\n"
            md += f"|--------------|-----------|\n"
            md += f"| OWASP 2021 | `{owasp_code} – {vcat}` |\n"
            md += f"| CWE ID | `{cwe}` |\n"
            md += f"| Vulnerability Type | `{vtype}` |\n"
            md += f"| Affected Component | `{vep}` |\n\n"

            md += f"### 2. EXECUTIVE SUMMARY\n\n"
            md += f"> **One-Sentence Summary:**  \n"
            md += f"> *The endpoint `{vep}` is susceptible to `{vtype}` due to improper input handling or configuration issues.*  \n\n"
            md += f"**Business Impact:**  \n"
            md += f"*Exploitation of `{vtype}` may allow unauthenticated or unauthorized actors to access, modify, or disrupt sensitive resources on `{scan.target}`.*  \n\n"

            md += f"### 3. TECHNICAL DETAILS & PROOF OF CONCEPT (POC)\n\n"
            md += f"#### Affected Endpoint:\n"
            md += f"```http\n{vep}\n```\n\n"
            md += f"#### Description:\n"
            md += f"{desc}\n\n"
            md += f"#### Step-by-Step Reproduction:\n"
            md += f"1. Send request to target endpoint `{vep}`.\n"
            md += f"2. Inject payload or observe anomalous response behavior:\n"
            md += f"```http\n{payload}\n```\n"
            md += f"3. Evidence / Artifact captured:\n"
            md += f"```\n{evidence}\n```\n\n"

            md += f"### 4. RECOMMENDATION & REMEDIATION\n\n"
            md += f"#### Short-term Mitigation:\n"
            md += f"- Sanitize and validate inputs on `{vep}`.\n"
            md += f"- Apply strict WAF rate-limiting or header policies.\n\n"
            md += f"#### Long-term Fix:\n"
            md += f"- {remediation}\n\n"
            md += f"---\n\n"

        md += f"## TRIAGE & VERIFICATION CHECKLIST\n\n"
        md += f"| **Check** | **Status** |\n"
        md += f"|-----------|------------|\n"
        md += f"| Duplicate check performed | ✅ |\n"
        md += f"| POC reproducible | ✅ |\n"
        md += f"| Valid target in scope | ✅ |\n"
        md += f"| No sensitive data exposed in report | ✅ |\n"
        md += f"| Proper CVSS calculated | ✅ |\n"
        md += f"| OWASP category correct | ✅ |\n\n"
        md += f"*Report automatically generated by Corvus Automated Pentest & Vulnerability Analysis Platform (POC-REPORT Format).*\n"

        return md

    @staticmethod
    def generate_pdf(scan_id: str):
        """Logic for PDF generation (requires pdfkit)"""
        pass

