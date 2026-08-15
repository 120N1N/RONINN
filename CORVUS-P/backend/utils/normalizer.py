import hashlib
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from backend.db import models

class Normalizer:
    @staticmethod
    def normalize_severity(severity: str) -> str:
        from backend.core.owasp import OWASP_SEVERITY_MAP
        s = severity.lower().strip()
        return OWASP_SEVERITY_MAP.get(s, "Informational")

    @staticmethod
    def generate_finding_hash(finding: Dict[str, Any]) -> str:
        """Generates a hash to identify duplicate findings."""
        # Significant fields: endpoint, type, source/parameter
        endpoint = finding.get("endpoint") or finding.get("location", "")
        vuln_type = finding.get("type") or finding.get("name", "")
        param = finding.get("parameter") or ""
        data = f"{endpoint}|{vuln_type}|{param}"
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def deduplicate(findings: List[Dict[str, Any]], db: Session = None, scan_id: str = None) -> List[Dict[str, Any]]:
        import os
        import json
        
        caido_profile = {}
        if scan_id:
            profile_path = os.path.join("tools_output", str(scan_id), "caido_profile.json")
            if os.path.exists(profile_path):
                try:
                    with open(profile_path, "r") as pf:
                        caido_profile = json.load(pf)
                except Exception as e:
                    print(f"[-] Normalizer: Error loading caido profile: {str(e)}")

        unique_findings = {}
        for f in findings:
            f_hash = Normalizer.generate_finding_hash(f)
            if f_hash not in unique_findings:
                f["severity"] = Normalizer.normalize_severity(f.get("severity", "INFO"))
                
                # Enrich with Caido profile features
                endpoint = f.get("endpoint") or f.get("location", "")
                profile = caido_profile.get(endpoint)
                if not profile and endpoint:
                    clean_endpoint = endpoint.split("?")[0].rstrip("/")
                    for k, v in caido_profile.items():
                        if k.split("?")[0].rstrip("/") == clean_endpoint:
                            profile = v
                            break
                            
                if not profile:
                    profile = {
                        "request_verb": "GET",
                        "param_count": 0,
                        "auth_headers_present": 0,
                        "content_type": "other",
                        "response_size_mean": 1000.0,
                        "response_size_std": 100.0,
                        "status_codes_seen": [200],
                        "endpoint_depth": max(1, len([p for p in endpoint.split("/") if p]) - 2 if "://" in endpoint else len([p for p in endpoint.split("/") if p]))
                    }
                
                f["caido_request_verb"] = profile.get("request_verb", "GET")
                f["caido_param_count"] = profile.get("param_count", 0)
                f["caido_auth_headers_present"] = profile.get("auth_headers_present", 0)
                f["caido_content_type"] = profile.get("content_type", "other")
                f["caido_response_size_mean"] = profile.get("response_size_mean", 1000.0)
                f["caido_response_size_std"] = profile.get("response_size_std", 100.0)
                f["caido_status_codes_seen"] = profile.get("status_codes_seen", [200])
                f["caido_endpoint_depth"] = profile.get("endpoint_depth", 1)

                # Cross-scan deduplication logic
                if db and scan_id:
                    fingerprint = db.query(models.VulnerabilityFingerprint).filter(
                        models.VulnerabilityFingerprint.fingerprint == f_hash
                    ).first()
                    
                    if fingerprint:
                        if fingerprint.last_seen_scan_id != scan_id:
                            f["is_duplicate"] = True
                            f["original_scan_id"] = fingerprint.first_seen_scan_id
                            fingerprint.last_seen_scan_id = scan_id
                    else:
                        new_fp = models.VulnerabilityFingerprint(
                            fingerprint=f_hash,
                            first_seen_scan_id=scan_id,
                            last_seen_scan_id=scan_id
                        )
                        db.add(new_fp)
                        f["is_duplicate"] = False
                
                unique_findings[f_hash] = f
        
        if db:
            db.commit()
            
        return list(unique_findings.values())
