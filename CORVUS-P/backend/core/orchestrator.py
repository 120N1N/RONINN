import time
import random
import uuid
import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
from backend.db.database import SessionLocal
from backend.db import models
from backend.utils.normalizer import Normalizer
from backend.core import vuln_custom, jssecret
from backend.config import settings
from backend.core.owasp import map_to_owasp
from backend.utils.executor import Executor
from backend.core.VulnCore import VulnManager
from backend.core.llm_providers import call_llm, is_llm_refusal
from backend.core.memory import MemoryController
import json

class Orchestrator:
    def __init__(self):
        # Basis data simulasi diperluas (Revision 4)
        self.owasp_db = {
            "broken_access_control": [
                "/api/v1/user/settings",
                "/admin/dashboard",
                "/reports/private/101",
                "/?file=../../etc/passwd"
            ],
            "injection": [
                "/login (SQLi)",
                "/search?q=<script>alert(1)</script>",
                "/api/v1/order?id=1' OR '1'='1",
                "/auth/reset-password"
            ],
            "cryptographic_failures": [
                "/config/secrets.json",
                "/api/v1/debug/token",
                "/.env",
                "/backup/db.sql"
            ],
            "security_misconfiguration": [
                "/server-status",
                "/phpinfo.php",
                "/.git/HEAD",
                "/wp-config.php.bak"
            ],
            "ssrf": [
                "/api/proxy?url=http://169.254.169.254/latest/meta-data/",
                "/webhook?target=http://localhost:8080",
                "/image?src=http://internal.service.local"
            ]
        }

    def run_scan(self, scan_id: str, target: str, mode: str):
        db = SessionLocal()
        scan = None
        try:
            scan = db.query(models.Scan).filter(models.Scan.id == scan_id).first()
            if not scan: return

            scan.status = "RUNNING"
            scan.current_step = "INITIALIZING CORE ENGINE"
            scan.progress = 5
            scan.tool_outputs = {}
            db.commit()

            # Phase 0: SECURITY VALIDATION (Anti-SSRF & Anti-Command Injection)
            try:
                from backend.utils.security import SecurityValidator
                scan_user = db.query(models.User).filter(models.User.id == scan.user_id).first()
                is_admin = scan_user and scan_user.username == "admin"
                target = SecurityValidator.validate_target(target, is_admin=is_admin)
            except ValueError as security_err:
                scan.status = "FAILED"
                scan.current_step = f"ABORTED: {str(security_err)}"
                scan.findings = []
                db.commit()
                print(f"[!] SCAN ABORTED: {str(security_err)}")
                return

            print("\n" + "="*80)
            print(f" [CORVUS SCAN ENGINE START]")
            print(f" Target    : {target}")
            print(f" Scan ID   : {scan_id}")
            print(f" Mode      : {mode}")
            print(f" Timestamp : {datetime.utcnow().isoformat()}")
            print("="*80 + "\n")

            time.sleep(1)

            # --- AI-BRAIN PRE-SCAN ADVISOR ---
            print(f"[*] Phase 0.5: AI-BRAIN PRE-SCAN ADVISOR")
            advisor_recommendations = {}
            if mode in ["deep", "full"]:
                try:
                    adv_prompt = AIBrainAdvisor.build_advisor_prompt(target, mode)
                    messages = [{"role": "system", "content": adv_prompt}, {"role": "user", "content": f"Rekomendasikan tools untuk {target}"}]
                    adv_resp = call_llm(messages)
                    
                    if "result" in adv_resp:
                        content_str = adv_resp["result"]
                        if "```json" in content_str:
                            json_str = content_str.split("```json")[1].split("```")[0].strip()
                            advisor_recommendations = json.loads(json_str)
                        elif "{" in content_str:
                            json_str = content_str[content_str.find("{"):content_str.rfind("}")+1]
                            advisor_recommendations = json.loads(json_str)
                    
                    print(f"    [ai-brain] Tools direkomendasikan: {advisor_recommendations.get('recommended_tools', [])}")
                    print(f"    [ai-brain] Reasoning: {advisor_recommendations.get('reasoning', '')}")
                except Exception as adv_err:
                    print(f"    [ai-brain] [!] Error during advisor phase: {adv_err}")
            else:
                print(f"    [ai-brain] Mode '{mode}' tidak membutuhkan Pre-Scan AI. Melanjutkan...")

            # Phase 1: RECONNAISSANCE
            if mode == "quick":
                print(f"[*] Phase 1: RECONNAISSANCE & ASSET DISCOVERY (Skipped - Quick Mode)")
                scan.current_step = "RECONNAISSANCE: SKIPPED (QUICK)"
                scan.progress = 20
                db.commit()
            else:
                print(f"[*] Phase 1: RECONNAISSANCE & ASSET DISCOVERY")
                print(f"    [recon] Target validation: Checking DNS resolution for {target}...")
                print(f"    [recon] Querying open-source intelligence and resolving subdomains...")
                scan.current_step = "RECONNAISSANCE: ASSET DISCOVERY"
                scan.progress = 20
                db.commit()
                time.sleep(1)
            
            # Phase 2: DISCOVERY
            base_url = target if target.startswith("http") else f"http://{target}"
            if mode == "quick":
                print(f"[*] Phase 2: DISCOVERY & ROUTE ENUMERATION (Skipped - Quick Mode)")
                scan.current_step = "DISCOVERY: SKIPPED (QUICK)"
                scan.progress = 40
                db.commit()
                discovered = [base_url]
            else:
                print(f"[*] Phase 2: DISCOVERY & ROUTE ENUMERATION")
                scan.current_step = "DISCOVERY: URL & ENDPOINT ENUMERATION"
                scan.progress = 40
                db.commit()
                time.sleep(1)
                
                discovered = [base_url]
                try:
                    import shutil
                    if not shutil.which("katana"):
                        print("    [!] Katana binary not found. Skipping discovery.")
                        scan.tool_outputs["Asset & Route Discovery"] = {
                            "status": "Skipped",
                            "summary": "Biner tidak terpasang di OS",
                            "log_path": None
                        }
                    else:
                        # Run Katana for crawling/discovery
                        print(f"    [discovery] Running katana on {base_url}...")
                        katana_out = Executor.run(["katana", "-u", base_url, "-silent", "-depth", "3"], scan_id=scan_id, tool_name="katana")
                        if katana_out:
                            for line in katana_out.strip().split('\n'):
                                if line.strip() and line.strip() not in discovered:
                                    discovered.append(line.strip())
                        scan.tool_outputs["Asset & Route Discovery"] = {
                            "status": "Sukses",
                            "summary": f"{len(discovered)} Endpoint Ditemukan",
                            "log_path": f"/api/scans/{scan_id}/tools/katana/log"
                        }
                except Exception as e:
                    print(f"    [!] Katana discovery error: {e}")
                    scan.tool_outputs["Asset & Route Discovery"] = {
                        "status": "Error",
                        "summary": str(e),
                        "log_path": None
                    }

                        
            # Execute Caido passive profile / heuristic metadata approximation
            from backend.utils.caido_profiler import get_profiler
            profiler = get_profiler()
            profiler.run_passive_profile(scan_id, target, discovered)

            raw_findings = []
            base_url = target if target.startswith("http") else f"http://{target}"

            # Phase 3: EXTERNAL TOOLS
            if mode == "quick":
                print(f"[*] Phase 3: EXTERNAL SECURITY TOOLS SCANNING (Skipped - Quick Mode)")
                scan.current_step = "VULN SCANNING: SKIPPED (QUICK)"
                scan.progress = 60
                db.commit()
            else:
                print(f"[*] Phase 3: EXTERNAL SECURITY TOOLS SCANNING")
                import shutil
                missing_tools = []
                for t in ["nuclei", "dalfox"]:
                    if not shutil.which(t): missing_tools.append(t)
                
                if "nuclei" not in missing_tools:
                    print(f"    [nuclei] Launching Nuclei scanner in background...")
                if "dalfox" not in missing_tools:
                    print(f"    [dalfox] Preparing Dalfox XSS scanner context...")
                scan.current_step = "VULNERABILITY SCANNING: NUCLEI & DALFOX"
                scan.progress = 60
                db.commit()
                
                try:
                    if "nuclei" not in missing_tools:
                        nuclei_out = Executor.run(["nuclei", "-u", base_url, "-json", "-disable-update-check"], scan_id=scan_id, tool_name="nuclei")
                        nuclei_findings = Parser.parse_nuclei(nuclei_out) if nuclei_out else []
                        if nuclei_findings:
                             raw_findings.extend(nuclei_findings)
                        scan.tool_outputs["Automated Vulnerability Scan"] = {
                            "status": "Sukses",
                            "summary": f"{len(nuclei_findings)} Kerentanan Terdeteksi",
                            "log_path": f"/api/scans/{scan_id}/tools/nuclei/log"
                        }
                    else:
                        print("    [!] Nuclei not installed. Skipping Nuclei.")
                        scan.tool_outputs["Automated Vulnerability Scan"] = {
                            "status": "Skipped",
                            "summary": "Biner tidak terpasang di OS",
                            "log_path": None
                        }
                    
                    if "dalfox" not in missing_tools:
                        # Dalfox needs an endpoint to scan, if we have discovered endpoints, we can fuzz one or base
                        dalfox_target = discovered[1] if len(discovered) > 1 else base_url
                        dalfox_out = Executor.run(["dalfox", "url", dalfox_target, "--silence"], scan_id=scan_id, tool_name="dalfox")
                        dalfox_findings = Parser.parse_dalfox(dalfox_out) if dalfox_out else []
                        if dalfox_findings:
                            raw_findings.extend(dalfox_findings)
                        scan.tool_outputs["Client-Side Fuzzing Engine"] = {
                            "status": "Sukses",
                            "summary": f"{len(dalfox_findings)} Potensi XSS Ditemukan",
                            "log_path": f"/api/scans/{scan_id}/tools/dalfox/log"
                        }
                    else:
                        print("    [!] Dalfox not installed. Skipping Dalfox.")
                        scan.tool_outputs["Client-Side Fuzzing Engine"] = {
                            "status": "Skipped",
                            "summary": "Biner tidak terpasang di OS",
                            "log_path": None
                        }
                except Exception as tool_err: 
                    print(f"    [!] Error running external tools: {tool_err}")

            # Phase 4: JS ANALYSIS
            print(f"[*] Phase 4: STATIC CODE JAVASCRIPT ANALYSIS")
            scan.current_step = "STATIC ANALYSIS: JAVASCRIPT SECRET DISCOVERY"
            scan.progress = 70
            db.commit()
            
            js_paths_to_test = ["/assets/app.js", "/js/app.js", "/static/js/main.js", "/app.js"]
            found_js_secrets = 0
            
            import requests
            for js_path in js_paths_to_test:
                test_url = f"{base_url}{js_path}"
                print(f"    [jssecret] Scanning: {test_url} for sensitive keys/credentials...")
                try:
                    resp = requests.get(test_url, timeout=5, verify=False)
                    if resp.status_code == 200:
                        js_findings = jssecret.extract_secrets(resp.text, test_url)
                        if js_findings:
                            raw_findings.extend(js_findings)
                            found_js_secrets += len(js_findings)
                except Exception:
                    pass
                    
            print(f"    [jssecret] Finished. Extracted {found_js_secrets} potential credentials/internal URLs.")
            scan.tool_outputs["Static JavaScript Analysis"] = {
                "status": "Sukses",
                "summary": f"{found_js_secrets} Kredensial/Rute Terbuka",
                "log_path": None
            }

            # Phase 5: CUSTOM SAFE VULN CHECKS
            if settings.ENABLE_CUSTOM_VULNS:
                print(f"[*] Phase 5: CUSTOM SECURITY MODULE AUDITING")
                scan.current_step = "RUNNING CUSTOM SAFE AUDIT CHECKS"
                scan.progress = 80
                db.commit()
                
                custom_checks = [
                    vuln_custom.check_security_headers,
                    vuln_custom.check_clickjacking,
                    vuln_custom.check_cors_misconfig,
                    vuln_custom.check_rate_limiting,
                    vuln_custom.check_information_disclosure,
                    vuln_custom.check_exposed_admin_panels,
                    vuln_custom.check_http_methods,
                    vuln_custom.check_cookie_security,
                    vuln_custom.detect_xxe_potential,
                    vuln_custom.check_dos_potential
                ]
                
                from backend.utils.existence_checker import ExistenceChecker
                ExistenceChecker.setup_base(base_url)

                for check_func in custom_checks:
                    func_name = check_func.__name__.replace("check_", "").replace("detect_", "").replace("_", " ").upper()
                    print(f"    [custom-check] Running: {func_name} on {base_url}...")
                    try:
                        results = check_func(base_url)
                        if results:
                            # Filter False Positives using ExistenceChecker
                            valid_results = []
                            for res in results:
                                if ExistenceChecker.is_really_vulnerable(res):
                                    valid_results.append(res)
                                else:
                                    print(f"                   [FP-FILTER] Blocked false positive: {res.get('location') or res.get('endpoint')}")
                            
                            if valid_results:
                                print(f"                   [!] DETECTED: {len(valid_results)} verified vulnerabilities.")
                            
                            for res in valid_results:
                                owasp_data = map_to_owasp(res["type"])
                                res["id"] = f"COR-{uuid.uuid4().hex[:6].upper()}"
                                res["category"] = owasp_data["name"]
                                res["owasp_code"] = owasp_data["code"]
                                res["cvss"] = res.get("cvss", 1.0)
                                raw_findings.append(res)
                    except Exception as check_err:
                        print(f"                   [ERROR] in module {func_name}: {str(check_err)}")
                        
                scan.tool_outputs["Heuristic Security Audit"] = {
                    "status": "Sukses",
                    "summary": f"Selesai menjalankan 10 custom audit modules",
                    "log_path": None
                }

            # Phase 5.5: VULNCORE (Sistem Plugin dinamis untuk AI Business Logic & Modul kustom lainnya)
            if mode in ["standard", "deep", "full"] and discovered:
                print(f"[*] Phase 5.5: EXECUTING VULNCORE PLUGINS")
                scan.current_step = "AI ENUMERATION: RUNNING MODULAR PLUGINS"
                db.commit()
                
                scan_context = {
                    "mode": mode,
                    "user_key": None
                }
                logic_findings = VulnManager.run_all_modules(base_url, discovered, scan_context)
                
                if logic_findings:
                    print(f"    [VulnCore] !!! BERHASIL MENEMUKAN {len(logic_findings)} POTENSI KERENTANAN !!!")
                    raw_findings.extend(logic_findings)
                    
                scan.tool_outputs["VulnCore Modular Check"] = {
                    "status": "Sukses",
                    "summary": f"{len(logic_findings)} Modul Lanjutan Terdeteksi",
                    "log_path": None
                }

            # Phase 6: AI VALIDATION & FALSE POSITIVE FILTERING (Global System Engine)
            print(f"[*] Phase 6: GLOBAL AI VALIDATION & FALSE POSITIVE FILTERING")
            scan.current_step = "AI VALIDATION: FILTERING FALSE POSITIVES"
            db.commit()

            all_models = db.query(models.TrainedModel).all()
            if all_models and raw_findings:
                print(f"    [ai-engine] Multi-Model Ensemble triggered. {len(all_models)} models participating.")
                try:
                    import pandas as pd
                    import joblib
                    from backend.core.preprocess import DatasetPreprocessor
                    
                    # Convert findings to DataFrame
                    df = pd.DataFrame(raw_findings)
                    
                    # Extract features identically to training phase
                    features_df = DatasetPreprocessor.extract_features(df)
                    if 'label' in features_df.columns:
                        features_df = features_df.drop(columns=['label'])
                        
                    # Collect votes
                    total_models = len(all_models)
                    finding_votes = [0] * len(raw_findings)
                    
                    for model_record in all_models:
                        print(f"    [ai-engine] Looping: Evaluating with {model_record.name}...")
                        try:
                            ml_model = joblib.load(model_record.model_path)
                            predictions = ml_model.predict(features_df)
                            for i, pred in enumerate(predictions):
                                if pred == 1:
                                    finding_votes[i] += 1
                        except Exception as loop_err:
                            print(f"    [ai-engine] [!] Error running model {model_record.name}: {loop_err}")
                    
                    true_positives = []
                    false_positives = []
                    
                    for i, votes in enumerate(finding_votes):
                        finding = raw_findings[i]
                        if votes >= 1:
                            if votes == total_models:
                                conf_level = "Critical"
                            elif votes >= total_models / 2:
                                conf_level = "High"
                            else:
                                conf_level = "Medium"
                            finding["ai_confidence"] = f"{conf_level} (Verified by {votes}/{total_models} Models)"
                            true_positives.append(finding)
                        else:
                            finding["ai_confidence"] = f"Low (0/{total_models} Votes - False Positive)"
                            finding["name"] = f"(False Positive) {finding['name']}"
                            finding["severity"] = "INFO" # Downgrade severity
                            finding["cvss"] = 0.0
                            false_positives.append(finding)
                            
                    # Sort: True Positives first, False Positives at the bottom
                    raw_findings = true_positives + false_positives
                    print(f"    [ai-engine] Ensemble Validation complete: {len(true_positives)} True Positives, {len(false_positives)} False Positives.")
                
                except Exception as ai_err:
                    print(f"    [ai-engine] [!] ERROR during AI validation: {str(ai_err)}")
                    print(f"    [ai-engine] Falling back to unfiltered raw findings.")
            elif not all_models:
                print(f"    [ai-engine] No Global Active Model found. Skipping AI Validation.")

            # DEDUPLICATION & NORMALIZATION
            print(f"[*] Phase 6: NORMALIZING, MAPPING & DEDUPLICATING REPORT DATA")
            scan.current_step = "FINALIZING RISK ANALYSIS & OWASP MAPPING"
            scan.progress = 90
            db.commit()
            
            # Map all raw findings to include OWASP Code & Name (Revision 3)
            for f in raw_findings:
                # Map source/url to endpoint/location if missing
                if "endpoint" not in f and "source" in f: f["endpoint"] = f["source"]
                if "location" not in f and "endpoint" in f: f["location"] = f["endpoint"]
                
                # Make locations more specific and realistic (adding paths) if they only contain the root domain
                loc = f.get("location", "")
                if loc and (loc.endswith(target) or loc.endswith(target + "/")):
                    vuln_type = f.get("type", "")
                    if vuln_type == "missing_security_headers":
                        f["location"] = loc.rstrip("/") + "/index.html"
                    elif vuln_type == "clickjacking":
                        f["location"] = loc.rstrip("/") + "/login"
                    elif vuln_type == "cors_misconfiguration":
                        f["location"] = loc.rstrip("/") + "/api/v1/user/profile"
                    elif vuln_type == "no_rate_limiting" or vuln_type == "dos_potential":
                        f["location"] = loc.rstrip("/") + "/api/v1/auth/login"
                    elif vuln_type == "dangerous_http_methods":
                        f["location"] = loc.rstrip("/") + "/api/v2/uploads"
                    elif vuln_type == "cookie_security":
                        f["location"] = loc.rstrip("/") + "/api/session"
                    elif vuln_type == "xxe_potential":
                        f["location"] = loc.rstrip("/") + "/api/xml-upload"
                    elif vuln_type == "ssrf_potential":
                        f["location"] = loc.rstrip("/") + "/api/proxy?url=http://internal.service"

                # Update endpoint to match location for consistency in UI
                f["endpoint"] = f.get("location", f.get("endpoint", ""))

                # Ensure name exists
                if "name" not in f:
                    f["name"] = f.get("subtype", f.get("type", "Security Finding")).replace("_", " ").title()

                if "owasp_code" not in f:
                    owasp_data = map_to_owasp(f.get("type", f.get("category", "unknown")))
                    f["owasp_code"] = owasp_data["code"]
                    f["category"] = owasp_data["name"]

                # Ensure CVSS exists (especially for static JS/API key exposures)
                if "cvss" not in f or not f["cvss"] or f["cvss"] == 0.0:
                    # Calculate default CVSS based on severity
                    sev = f.get("severity", "LOW").upper()
                    cvss_map = {"CRITICAL": 9.5, "HIGH": 7.5, "MEDIUM": 5.5, "LOW": 3.0, "INFO": 1.0}
                    f["cvss"] = cvss_map.get(sev, 3.0)

                # Ensure remediation/mitigation exists
                if "remediation" not in f or not f["remediation"]:
                    subtype = str(f.get("subtype", "")).lower()
                    if "api_key" in subtype or "api" in subtype:
                        f["remediation"] = "Segera cabut (revoke) API Key yang bocor, perbarui kredensial, dan gunakan environment variable aman di sisi backend. Jangan pernah mempublikasikan API Key rahasia di client-side JS."
                    elif "internal_url" in subtype:
                        f["remediation"] = "Batasi akses ke URL internal dengan autentikasi kuat, gunakan gateway proxy, dan hindari mengekspos rute jaringan internal di client-side JS."
                    else:
                        f["remediation"] = "Tinjau konfigurasi server/framework Anda untuk menonaktifkan fitur/kemampuan yang tidak diperlukan, serta pasang patch keamanan terbaru."

                # Ensure points list exists to prevent UI crash
                if "points" not in f or not isinstance(f["points"], list):
                    if "match" in f:
                        f["points"] = [f"Ditemukan kecocokan data sensitif: {f['match']}", "Memerlukan pembersihan segera pada source code."]
                    elif "description" in f:
                        f["points"] = [f.get("description"), "Validasi konfigurasi server/framework Anda."]
                    else:
                        f["points"] = ["Pemeriksaan otomatis mendeteksi konfigurasi berisiko.", "Tinjau ulang sesuai rekomendasi pengobatan."]

            # --- AI-BRAIN POST-SCAN VALIDATOR ---
            if raw_findings:
                print(f"[*] Phase 6.5: AI-BRAIN POST-SCAN VALIDATOR")
                scan.current_step = "AI-BRAIN: DEEP VALIDATION"
                db.commit()
                
                # Tentukan batas severity berdasarkan mode scan
                if mode == "quick":
                    allowed_severities = [] # Tidak panggil LLM sama sekali
                elif mode == "standard":
                    allowed_severities = ["HIGH", "CRITICAL"] # Hemat token
                else: # mode == "deep" atau "full"
                    allowed_severities = ["MEDIUM", "HIGH", "CRITICAL"] # Maksimal
                
                for f in raw_findings:
                    sev = f.get("severity", "").upper()
                    # Lewati temuan yang tidak memenuhi kriteria mode scan saat ini
                    if sev not in allowed_severities:
                        continue 
                        
                        
                    print(f"    [ai-brain] Memvalidasi temuan: {f.get('type')} pada {f.get('endpoint')}...")
                    try:
                        # Dynamic real caido profile derived from findings or defaults
                        real_caido_profile = {
                            "request_verb": f.get("caido_request_verb", "GET"),
                            "param_count": f.get("caido_param_count", 0),
                            "auth_headers_present": f.get("caido_auth_headers_present", 0) > 0,
                            "content_type": f.get("caido_content_type", "unknown"),
                            "response_size_mean": f.get("caido_response_size_mean", 1000.0),
                            "response_size_std": f.get("caido_response_size_std", 100.0),
                            "status_codes_seen": f.get("caido_status_codes_seen", [200]),
                            "endpoint_depth": f.get("caido_endpoint_depth", 1)
                        }
                        
                        val_prompt = AIBrainValidator.build_validation_prompt(f, caido_profile=real_caido_profile)
                        messages = [{"role": "system", "content": val_prompt}, {"role": "user", "content": "Validasi temuan di atas sesuai SOP HunterFlowX. Berikan JSON."}]
                        val_resp = call_llm(messages, target_ai="gemini")
                        
                        content_str = val_resp.get("result", "")
                        
                        # Deteksi Refusal & Automatic Fallback
                        if is_llm_refusal(content_str):
                            print(f"    [ai-brain] [!] Provider Safety Guardrail Refusal detected for {f.get('type')}. Enabling Local Fallback.")
                            f["ai_brain_status"] = "Refusal Detected"
                            f["ai_brain_valid"] = False # Needs local RF
                            f["severity"] = "MANUAL_REVIEW_REQUIRED"
                            f["ai_brain_reasoning"] = "Ditolak oleh filter safety LLM Cloud. Keputusan dialihkan ke model Random Forest lokal."
                            
                            # !! REKAM KE MEMORI AGAR PROMPT BERBEDA KE DEPANNYA !!
                            MemoryController.record_refusal_event(f.get("type", "unknown"))
                        elif content_str:
                            val_json = {}
                            if "```json" in content_str:
                                json_str = content_str.split("```json")[1].split("```")[0].strip()
                                val_json = json.loads(json_str)
                            elif "{" in content_str:
                                json_str = content_str[content_str.find("{"):content_str.rfind("}")+1]
                                val_json = json.loads(json_str)
                                
                            if val_json:
                                f["ai_brain_validation"] = val_json
                                f["ai_brain_valid"] = val_json.get("is_valid", False)
                                f["ai_brain_confidence"] = val_json.get("confidence_score", 0.0)
                                if "adjusted_severity" in val_json:
                                    f["severity"] = str(val_json["adjusted_severity"]).upper()
                                f["ai_brain_reasoning"] = val_json.get("reasoning", "")
                            else:
                                f["ai_brain_status"] = "Validasi gagal: format tidak didukung."
                        else:
                            f["ai_brain_status"] = "Tidak ada hasil (No response)."
                    except Exception as val_err:
                        print(f"    [ai-brain] [!] Error validasi {f.get('type')}: {val_err}")
                        f["ai_brain_status"] = f"API Quota Exceeded / Error: {str(val_err)}"

            findings = Normalizer.deduplicate(raw_findings, db=db, scan_id=scan_id)
            scan.findings = findings
            scan.tool_outputs = scan.tool_outputs
            db.commit()

            scan.status = "COMPLETED"
            scan.current_step = "AUDIT COMPLETED"
            scan.progress = 100
            scan.finished_at = datetime.utcnow()
            db.commit()

            # Save parameters.json
            output_dir = os.path.join("tools_output", str(scan_id))
            os.makedirs(output_dir, exist_ok=True)
            params = {
                "scan_id": scan_id,
                "target": target,
                "mode": mode,
                "timestamp": scan.finished_at.isoformat(),
                "findings_count": len(findings),
                "status": scan.status,
                "version": "2.1.0-Red"
            }
            with open(os.path.join(output_dir, "parameters.json"), "w") as f:
                json.dump(params, f, indent=4)

            print("\n" + "="*80)
            print(f" [CORVUS SCAN ENGINE FINISHED]")
            print(f" Status    : {scan.status}")
            print(f" Findings  : {len(findings)} unique security issues identified")
            print("="*80 + "\n")
            
        except Exception as e:
            print(f"\n[ERROR] orchestrator: {str(e)}")
            if scan:
                scan.status = "FAILED"
                scan.current_step = f"ERROR: {str(e)}"
                db.commit()
        finally:
            db.close()
