import time
import random
import uuid
import json
import os
try:
    import numpy as np
except ImportError:
    np = None
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
from backend.utils.parser import Parser
from backend.core.ai_brain_advisor import AIBrainAdvisor
from backend.core.ai_brain import AIBrainValidator
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
            if not scan.logs:
                scan.logs = []
            db.commit()

            def emit_log(msg: str):
                ts = datetime.utcnow().strftime("%H:%M:%S")
                line = f"[{ts}] {msg}"
                print(line)
                try:
                    if scan:
                        curr = list(scan.logs or [])
                        curr.append(line)
                        if len(curr) > 600:
                            curr = curr[-600:]
                        scan.logs = curr
                        db.commit()
                except Exception:
                    pass
                try:
                    from backend.api.websocket import broadcast_scan_log_sync
                    broadcast_scan_log_sync(scan_id, line)
                except Exception:
                    pass

            def sync_findings(raw_list):
                try:
                    if scan and raw_list:
                        deduped = Normalizer.deduplicate(list(raw_list), db=db, scan_id=scan_id)
                        scan.findings = deduped
                        db.commit()
                except Exception as sync_e:
                    print(f"[-] Intermediate sync error: {sync_e}")

            emit_log(f"=== CORVUS SCAN ENGINE STARTED ===")
            emit_log(f"[*] Target: {target} | Mode: {mode.upper()} | ID: {scan_id[:8]}")

            # Phase 0: SECURITY VALIDATION (Anti-SSRF & Anti-Command Injection)
            try:
                from backend.utils.security import SecurityValidator
                target = SecurityValidator.validate_target(target)
                emit_log(f"[✓] Phase 0: Target security & Anti-SSRF validation passed ({target})")
            except ValueError as security_err:
                scan.status = "FAILED"
                scan.current_step = f"ABORTED: {str(security_err)}"
                scan.findings = []
                db.commit()
                emit_log(f"[!] SCAN ABORTED: {str(security_err)}")
                return

            time.sleep(0.5)

            # --- AI-BRAIN PRE-SCAN ADVISOR ---
            emit_log("[*] Phase 0.5: AI-BRAIN PRE-SCAN ADVISOR")
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
                    
                    emit_log(f"    [AI-Brain] Recommended tools: {advisor_recommendations.get('recommended_tools', [])}")
                    emit_log(f"    [AI-Brain] Reasoning: {advisor_recommendations.get('reasoning', '')[:100]}...")
                except Exception as adv_err:
                    emit_log(f"    [AI-Brain] [!] Error during advisor phase: {adv_err}")
            else:
                emit_log(f"    [AI-Brain] Mode '{mode}' does not require pre-scan advisor. Continuing...")

            # Phase 1: RECONNAISSANCE
            if mode == "quick":
                emit_log("[*] Phase 1: Reconnaissance skipped (Quick mode)")
                scan.current_step = "RECONNAISSANCE: SKIPPED (QUICK)"
                scan.progress = 20
                db.commit()
            else:
                emit_log(f"[*] Phase 1: RECONNAISSANCE & ASSET DISCOVERY on {target}")
                scan.current_step = "RECONNAISSANCE: DNS & WHOIS LOOKUP"
                scan.progress = 10
                db.commit()
                
                try:
                    from backend.core.recon import run_recon
                    emit_log(f"    [recon] Running full reconnaissance on {target}...")
                    recon_data = run_recon(target)
                    scan.recon = recon_data
                    
                    # Log summary
                    ip_addr = recon_data.get("tested_address", "—")
                    open_ports = len(recon_data.get("ports", {}).get("list", []))
                    whois_reg = recon_data.get("whois", {}).get("registrar", "—")
                    ping_loss = recon_data.get("ping", {}).get("loss", "—")
                    
                    emit_log(f"    [recon] DNS Resolved: {ip_addr}")
                    emit_log(f"    [recon] WHOIS Registrar: {whois_reg}")
                    emit_log(f"    [recon] Ping Loss: {ping_loss}")
                    emit_log(f"    [recon] Open Ports: {open_ports}")
                    
                    scan.current_step = "RECONNAISSANCE: COMPLETE"
                    scan.progress = 20
                    db.commit()
                except Exception as recon_err:
                    emit_log(f"    [recon] [!] Recon error: {recon_err}")
                    scan.recon = {"error": str(recon_err)}
                    scan.current_step = "RECONNAISSANCE: PARTIAL (ERROR)"
                    scan.progress = 20
                    db.commit()

            
            # Phase 2: DISCOVERY (GO KATANA DENGAN PYTHON NATIVE FALLBACK)
            base_url = target if target.startswith("http") else f"http://{target}"
            emit_log(f"[*] Phase 2: DISCOVERY & ROUTE ENUMERATION on {base_url}")
            scan.current_step = "DISCOVERY: URL & ENDPOINT ENUMERATION"
            scan.progress = 40
            db.commit()
            time.sleep(0.5)
            
            import shutil
            discovered = [base_url]
            katana_installed = bool(shutil.which("katana"))
            
            if katana_installed:
                try:
                    katana_depth = "1" if mode == "quick" else ("3" if mode in ["deep", "full"] else "2")
                    katana_crawl_dur = "25s" if mode == "quick" else ("90s" if mode in ["deep", "full"] else "45s")
                    katana_cmd = [
                        "katana", "-u", base_url, "-silent",
                        "-depth", katana_depth,
                        "-crawl-duration", katana_crawl_dur,
                        "-timeout", "5",
                        "-field-scope", "fqdn",
                        "-concurrency", "10",
                        "-rate-limit", "40"
                    ]
                    emit_log(f"    [discovery:Katana] Running Katana (depth {katana_depth}, max {katana_crawl_dur}) on {base_url}...")
                    katana_timeout_secs = 35 if mode == "quick" else (100 if mode in ["deep", "full"] else 55)
                    katana_out = Executor.run(katana_cmd, timeout=katana_timeout_secs, scan_id=scan_id, tool_name="katana")
                    if katana_out:
                        for line in katana_out.strip().split('\n'):
                            line_str = line.strip()
                            if line_str and line_str.startswith("http") and line_str not in discovered:
                                discovered.append(line_str)
                    emit_log(f"    [discovery:Katana] Discovered {len(discovered)} endpoints/routes.")
                    scan.tool_outputs["Asset & Route Discovery"] = {
                        "status": "Sukses (Go Katana)",
                        "summary": f"{len(discovered)} Endpoint Ditemukan via Katana",
                        "log_path": f"/api/scans/{scan_id}/tools/katana/log"
                    }
                except Exception as e:
                    emit_log(f"    [!] Katana discovery notice: {e}. Falling back to native crawler.")

            # Fallback jika Katana tidak terpasang ATAU Katana tidak berhasil menemukan rute (hanya root)
            if len(discovered) <= 1:
                emit_log(f"    [discovery:Crawler] Running Native Python Web Crawler for {base_url}...")
                try:
                    import re
                    import requests
                    from urllib.parse import urljoin, urlparse
                    
                    target_host = urlparse(base_url).netloc
                    # Probing direct endpoint standar dan direktori umum
                    common_paths = [
                        "/robots.txt", "/sitemap.xml", "/login", "/admin", "/administrator",
                        "/api", "/api/v1", "/api/v2", "/swagger", "/docs", "/config.json"
                    ]
                    for path in common_paths:
                        discovered.append(urljoin(base_url, path))
                    
                    resp = requests.get(base_url, timeout=6, verify=False, allow_redirects=True)
                    if resp.status_code == 200:
                        hrefs = re.findall(r'(?:href|src|action)=["\']([^"\']+)["\']', resp.text, re.IGNORECASE)
                        max_links = 15 if mode == "quick" else (60 if mode in ["deep", "full"] else 30)
                        for h in hrefs:
                            if h.startswith(('#', 'javascript:', 'mailto:')): continue
                            full_url = urljoin(base_url, h)
                            if urlparse(full_url).netloc == target_host and full_url not in discovered:
                                discovered.append(full_url)
                                if len(discovered) >= max_links:
                                    break
                    emit_log(f"    [discovery:Crawler] Discovered {len(discovered)} endpoints via native crawler.")
                    scan.tool_outputs["Asset & Route Discovery"] = {
                        "status": "Sukses (Python Crawler)",
                        "summary": f"{len(discovered)} Endpoint Ditemukan via Native Crawler",
                        "log_path": None
                    }
                except Exception as py_crawl_err:
                    emit_log(f"    [!] Python crawler error: {py_crawl_err}")
                    scan.tool_outputs["Asset & Route Discovery"] = {
                        "status": "Parsial",
                        "summary": f"{len(discovered)} Endpoint Dasar",
                        "log_path": None
                    }
                        
            # Klasifikasi Rute: Pisahkan endpoint aplikasi dinamis dengan static assets (JS, CSS, images, dll)
            from backend.utils.asset_helper import classify_discovered_urls, is_static_asset
            dynamic_endpoints, discovered_js_assets, other_static_assets = classify_discovered_urls(discovered)
            emit_log(f"    [discovery:AssetClassification] Discovered: {len(dynamic_endpoints)} app/API routes, {len(discovered_js_assets)} JavaScript assets, {len(other_static_assets)} static files.")

            # Execute Caido passive profile / heuristic metadata approximation
            emit_log(f"    [caido] Generating passive traffic profiles for {len(discovered)} endpoints...")
            from backend.utils.caido_profiler import get_profiler
            profiler = get_profiler()
            profiler.run_passive_profile(scan_id, target, discovered)
            emit_log(f"    [caido] Passive profile generated.")

            raw_findings = []
            base_url = target if target.startswith("http") else f"http://{target}"

            # Phase 3: EXTERNAL SECURITY TOOLS (GO ENGINE)
            if mode == "quick":
                emit_log("[*] Phase 3: External tools scan skipped (Quick mode)")
                scan.current_step = "VULN SCANNING: SKIPPED (QUICK)"
                scan.progress = 60
                db.commit()
            else:
                emit_log("[*] Phase 3: EXTERNAL SECURITY TOOLS SCANNING (Nuclei / Dalfox)")
                missing_tools = []
                for t in ["nuclei", "dalfox"]:
                    if not shutil.which(t): missing_tools.append(t)
                
                scan.current_step = "VULNERABILITY SCANNING: GO TOOLS (NUCLEI & DALFOX)"
                scan.progress = 60
                db.commit()
                
                try:
                    if "nuclei" not in missing_tools:
                        emit_log(f"    [nuclei] Running Nuclei security templates on {base_url}...")
                        nuclei_out = Executor.run(["nuclei", "-u", base_url, "-j", "-disable-update-check"], scan_id=scan_id, tool_name="nuclei")
                        nuclei_findings = Parser.parse_nuclei(nuclei_out) if nuclei_out else []
                        if nuclei_findings:
                            raw_findings.extend(nuclei_findings)
                            sync_findings(raw_findings)
                            emit_log(f"    [nuclei] [!] Found {len(nuclei_findings)} potential vulnerabilities!")
                        else:
                            emit_log("    [nuclei] No template matches found.")
                        scan.tool_outputs["Automated Vulnerability Scan"] = {
                            "status": "Sukses (Go Nuclei)",
                            "summary": f"{len(nuclei_findings)} Kerentanan Terdeteksi",
                            "log_path": f"/api/scans/{scan_id}/tools/nuclei/log"
                        }
                    else:
                        emit_log("    [nuclei] Go Nuclei binary not present in OS. Delegating to VulnCore.")
                        scan.tool_outputs["Automated Vulnerability Scan"] = {
                            "status": "Dialihkan (Python Native)",
                            "summary": "Biner Go Nuclei tidak ada; dialihkan ke VulnCore",
                            "log_path": None
                        }
                    
                    if "dalfox" not in missing_tools:
                        from backend.utils.asset_helper import is_static_asset
                        param_candidates = [ep for ep in discovered if "?" in ep and not is_static_asset(ep)]
                        if param_candidates:
                            dalfox_target = param_candidates[0]
                            emit_log(f"    [dalfox] Running Dalfox XSS scanner on parameterized endpoint: {dalfox_target}...")
                            dalfox_cmd = [
                                "dalfox", "url", dalfox_target,
                                "--silence",
                                "--timeout", "5",
                                "--delay", "50",
                                "--mining-dict=false",
                                "--skip-bav",
                                "--skip-grepping"
                            ]
                            dalfox_out = Executor.run(dalfox_cmd, timeout=45, scan_id=scan_id, tool_name="dalfox")
                            dalfox_findings = Parser.parse_dalfox(dalfox_out) if dalfox_out else []
                            if dalfox_findings:
                                raw_findings.extend(dalfox_findings)
                                sync_findings(raw_findings)
                                emit_log(f"    [dalfox] [!] Found {len(dalfox_findings)} potential XSS vectors!")
                            else:
                                emit_log("    [dalfox] No XSS vulnerabilities found.")
                            scan.tool_outputs["Client-Side Fuzzing Engine"] = {
                                "status": "Sukses (Go Dalfox)",
                                "summary": f"{len(dalfox_findings)} Potensi XSS Ditemukan",
                                "log_path": f"/api/scans/{scan_id}/tools/dalfox/log"
                            }
                        else:
                            emit_log("    [dalfox] No parameterized query endpoints found. Skipping blind XSS fuzzing.")
                            scan.tool_outputs["Client-Side Fuzzing Engine"] = {
                                "status": "Dilewati",
                                "summary": "Tidak ada endpoint berparameter query; dialihkan ke VulnCore A03",
                                "log_path": None
                            }
                    else:
                        emit_log("    [dalfox] Go Dalfox binary not present. Delegating to VulnCore A03.")
                        scan.tool_outputs["Client-Side Fuzzing Engine"] = {
                            "status": "Dialihkan (Python Native)",
                            "summary": "Biner Go Dalfox tidak ada; dialihkan ke VulnCore A03",
                            "log_path": None
                        }
                except Exception as tool_err: 
                    emit_log(f"    [!] Error running external tools: {tool_err}")

            # Phase 4: ASSET ANALYST - STATIC JAVASCRIPT SECRET & ENDPOINT EXTRACTION
            emit_log("[*] Phase 4: ASSET ANALYST - STATIC JAVASCRIPT SECRET & SENSITIVE ROUTE EXTRACTION")
            scan.current_step = "ASSET ANALYST: JAVASCRIPT RECON & SECRET DISCOVERY"
            scan.progress = 70
            db.commit()
            
            # Gabungkan fallback umum dengan semua file JS yang terdeteksi dari crawler / directory bruteforce
            fallback_js_paths = ["/assets/app.js", "/js/app.js", "/static/js/main.js", "/app.js"]
            all_js_urls = [f"{base_url}{p}" for p in fallback_js_paths]
            all_js_urls.extend(discovered_js_assets)
            
            unique_js_urls = []
            seen_js = set()
            for u in all_js_urls:
                if u not in seen_js:
                    seen_js.add(u)
                    unique_js_urls.append(u)

            found_js_secrets = 0
            new_api_routes_found = 0
            
            import requests
            for test_url in unique_js_urls[:15]:
                emit_log(f"    [AssetAnalyst] Inspecting JS asset: {test_url}...")
                try:
                    resp = requests.get(test_url, timeout=5, verify=False)
                    if resp.status_code == 200 and resp.text:
                        # 1. Ekstraksi kredensial, token, dan rahasia
                        js_findings = jssecret.extract_secrets(resp.text, test_url)
                        if js_findings:
                            raw_findings.extend(js_findings)
                            sync_findings(raw_findings)
                            found_js_secrets += len(js_findings)

                        # 2. Ekstraksi rute API tersembunyi di dalam bundle JS
                        import re
                        from urllib.parse import urljoin
                        extracted_routes = re.findall(r'["\'](/(?:api|v[0-9]|admin|auth|user|order|checkout|profile|dashboard)[a-zA-Z0-9_\-/]*)["\']', resp.text)
                        for r in extracted_routes:
                            full_route = urljoin(base_url, r)
                            if full_route not in dynamic_endpoints and not is_static_asset(full_route):
                                dynamic_endpoints.append(full_route)
                                new_api_routes_found += 1

                        # 3. Cek Source Map (.map) yang terekspos
                        try:
                            map_url = f"{test_url}.map"
                            m_resp = requests.head(map_url, timeout=3, verify=False)
                            if m_resp.status_code == 200:
                                raw_findings.append({
                                    "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                                    "name": "Exposed JavaScript Source Map",
                                    "type": "exposed_source_map",
                                    "severity": "LOW",
                                    "endpoint": map_url,
                                    "location": map_url,
                                    "cvss": 3.7,
                                    "description": f"File source map '{map_url}' dapat diakses secara publik. Ini memungkinkan penyerang merekonstruksi source code aplikasi asli (unminified).",
                                    "remediation": "Hapus file source map (.map) dari server produksi atau batasi akses hanya untuk tim internal.",
                                    "points": ["Source map file (.map) exposed on production server"]
                                })
                                sync_findings(raw_findings)
                        except Exception:
                            pass
                except Exception:
                    pass
                    
            emit_log(f"    [AssetAnalyst] Finished. Extracted {found_js_secrets} secrets and discovered {new_api_routes_found} hidden API routes from JS assets.")
            scan.tool_outputs["Static JavaScript Analysis"] = {
                "status": "Sukses",
                "summary": f"{found_js_secrets} Kredensial, {new_api_routes_found} Rute API Terungkap",
                "log_path": None
            }

            # Phase 5: CUSTOM SAFE VULN CHECKS
            if settings.ENABLE_CUSTOM_VULNS:
                emit_log("[*] Phase 5: CUSTOM SAFE HEURISTIC AUDIT MODULES")
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
                    emit_log(f"    [custom-check] Running: {func_name} on {base_url}...")
                    try:
                        results = check_func(base_url)
                        if results:
                            # Filter False Positives using ExistenceChecker
                            valid_results = []
                            for res in results:
                                if ExistenceChecker.is_really_vulnerable(res):
                                    valid_results.append(res)
                                else:
                                    emit_log(f"                   [FP-FILTER] Filtered out soft/non-vulnerable: {res.get('location') or res.get('endpoint')}")
                            
                            if valid_results:
                                emit_log(f"                   [!] DETECTED: {len(valid_results)} verified issues in {func_name}")
                            
                            for res in valid_results:
                                owasp_data = map_to_owasp(res["type"])
                                res["id"] = f"COR-{uuid.uuid4().hex[:6].upper()}"
                                res["category"] = owasp_data["name"]
                                res["owasp_code"] = owasp_data["code"]
                                res["cvss"] = res.get("cvss", 1.0)
                                raw_findings.append(res)
                            
                            sync_findings(raw_findings)
                    except Exception as check_err:
                        emit_log(f"                   [ERROR] in module {func_name}: {str(check_err)}")
                        
                scan.tool_outputs["Heuristic Security Audit"] = {
                    "status": "Sukses",
                    "summary": f"Selesai menjalankan 10 custom audit modules",
                    "log_path": None
                }

            # Phase 5.5: VULNCORE (PYTHON OWASP ENGINE)
            # Dijalankan untuk semua mode (quick, normal, deep) dengan intensitas yang disesuaikan
            emit_log(f"[*] Phase 5.5: EXECUTING VULNCORE OWASP ENGINE (MODE: {mode.upper()})")
            scan.current_step = f"VULNCORE OWASP ENGINE: {mode.upper()}"
            db.commit()
            
            scan_context = {
                "mode": mode,
                "user_key": None
            }
            # Kirimkan HANYA dynamic_endpoints (BUKAN file statis .js, .css, dll)
            # Ini memastikan file JS tidak akan diuji IDOR/BOLA/Admin interface
            vulncore_endpoints = [ep for ep in dynamic_endpoints if not is_static_asset(ep)]
            if not vulncore_endpoints:
                vulncore_endpoints = [base_url]

            logic_findings = VulnManager.run_all_modules(base_url, vulncore_endpoints, scan_context)
            
            if logic_findings:
                emit_log(f"    [VulnCore] [!] Discovered {len(logic_findings)} potential OWASP vulnerabilities!")
                raw_findings.extend(logic_findings)
                sync_findings(raw_findings)
            else:
                emit_log("    [VulnCore] No vulnerabilities found from VulnCore modules.")
                
            scan.tool_outputs["VulnCore Modular Check"] = {
                "status": "Sukses (Python Engine)",
                "summary": f"{len(logic_findings)} Modul OWASP Terdeteksi",
                "log_path": None
            }

            # Phase 6: AI VALIDATION & FALSE POSITIVE FILTERING (Confidence Score Engine)
            # Implementasi sesuai Bab 4: CS = (0.50 * P_RF) + (0.30 * S_tool) + (0.20 * V_DOM)
            emit_log("[*] Phase 6: AI-BRAIN CONFIDENCE SCORE ENGINE & FALSE POSITIVE FILTERING")
            scan.current_step = "AI VALIDATION: CONFIDENCE SCORE CALCULATION"
            db.commit()

            # Phase 5.5: RANDOM FOREST & COMPOSITE CONFIDENCE SCORE ENGINE
            print(f"[*] Phase 5.5: RANDOM FOREST CONFIDENCE SCORE ENGINE EVALUATION")
            from backend.core.confidence import get_active_rf_model, extract_finding_features
            from backend.core.ml import MLEngine
            from backend.core.dom_validator import DOMValidator
            import pandas as pd
            import numpy as np

            rf_model, rf_model_meta = get_active_rf_model(db)
            if rf_model and raw_findings:
                model_name = rf_model_meta.get("name") if rf_model_meta else "Random Forest"
                emit_log(f"    [cs-engine] Random Forest Model active: {model_name}. Calculating Confidence Scores...")
                try:
                    feature_names = list(getattr(rf_model, 'feature_names_in_', []))
                    if not feature_names:
                        feature_names = [
                            'severity_score', 'tool_source', 'owasp_category', 'endpoint_depth',
                            'has_payload', 'response_length', 'caido_request_verb', 'caido_param_count',
                            'caido_auth_headers_present', 'caido_content_type', 'caido_response_size_mean',
                            'caido_response_size_std', 'caido_status_codes_seen', 'caido_endpoint_depth'
                        ]
                    
                    rows = [extract_finding_features(f, feature_names) for f in raw_findings]
                    features_df = pd.DataFrame(rows, columns=feature_names)
                    
                    # 1. P_RF (Probabilitas Random Forest)
                    probas = rf_model.predict_proba(features_df)
                    proba_class_1 = probas[:, 1] if probas.shape[1] > 1 else probas[:, 0]
                    preds = rf_model.predict(features_df)
                    
                    # 2. S_tool, V_DOM, & Composite Confidence Score
                    for i, finding in enumerate(raw_findings):
                        p_rf = float(proba_class_1[i])
                        
                        # S_tool: Konsensus multi-tools (0.2 - 1.0)
                        src = str(finding.get("source", "")).strip()
                        if "," in src:
                            s_tool = min(1.0, len(src.split(",")) / 3.0)
                        elif "/" in src:
                            s_tool = 0.6
                        else:
                            s_tool = 0.4
                            
                        # V_DOM: Playwright DOM validation untuk XSS / reflected
                        v_dom = 0
                        vuln_text = (str(finding.get("type", "")) + " " + str(finding.get("name", ""))).lower()
                        if "xss" in vuln_text or "reflected" in vuln_text:
                            ep = finding.get("endpoint") or finding.get("location", "")
                            pay = finding.get("payload") or finding.get("evidence", "")
                            if ep and pay and "http" in ep:
                                try:
                                    v_dom = int(DOMValidator.validate_xss(ep, str(pay)))
                                except Exception:
                                    v_dom = 0
                                    
                        # Composite Formula: CS = (0.50 * P_RF) + (0.30 * S_tool) + (0.20 * V_DOM)
                        cs = MLEngine.calculate_confidence_score(p_rf, s_tool, v_dom)
                        pred_class = "Valid Finding" if (preds[i] == 1 or p_rf >= 0.5 or cs >= 0.5) else "False Positive"
                        
                        finding["confidence_score"] = round(cs * 100.0, 1)
                        finding["p_rf"] = round(p_rf * 100.0, 1)
                        finding["rf_validation"] = {
                            "model_name": model_name,
                            "p_rf": round(p_rf, 4),
                            "p_rf_pct": round(p_rf * 100.0, 1),
                            "s_tool": round(s_tool, 4),
                            "v_dom": v_dom,
                            "confidence_score": round(cs, 4),
                            "confidence_pct": round(cs * 100.0, 1),
                            "predicted_class": pred_class
                        }
                    emit_log(f"    [cs-engine] Random Forest evaluated {len(raw_findings)} findings successfully.")
                except Exception as ai_err:
                    emit_log(f"    [cs-engine] [!] Warning during RF evaluation: {str(ai_err)}")
            else:
                emit_log("    [cs-engine] No active Random Forest model found on system.")

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
                
                # Pertahankan endpoint dan location asli yang diuji tanpa fabrikasi rute palsu
                if not f.get("location"):
                    f["location"] = base_url
                f["endpoint"] = f.get("location", f.get("endpoint", base_url))

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
                emit_log("[*] Phase 6.5: AI-BRAIN HUNTERFLOWX SECURITY ANALYST VALIDATION")
                scan.current_step = "AI-BRAIN: DEEP VALIDATION"
                db.commit()
                
                # Severity threshold and limit based on scan mode
                if mode == "quick":
                    allowed_severities = ["CRITICAL", "HIGH"]
                    max_validations = 2
                elif mode in ["standard", "normal"]:
                    allowed_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL", "INFO"]
                    max_validations = 8
                else: # mode == "deep" atau "full"
                    allowed_severities = ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL", "INFO"]
                    max_validations = 25
                
                validations_done = 0
                for f in raw_findings:
                    if validations_done >= max_validations:
                        break
                    sev = f.get("severity", "").upper()
                    # Skip findings that don't match criteria
                    if sev not in allowed_severities:
                        continue 
                        
                    f_name = f.get("name") or f.get("type", "Finding")
                    f_loc = f.get("location") or f.get("endpoint", "")

                    # Safety check: Jika lokasi adalah file statis (misal .js) dan temuan mengklaim IDOR/BOLA/Admin panel, lewati
                    if is_static_asset(f_loc) and any(k in str(f_name).lower() or k in str(f.get("type", "")).lower() or k in str(f.get("description", "")).lower() for k in ["idor", "bola", "admin"]):
                        continue

                    emit_log(f"    [AI-Analyst] Validating: {f_name} at {f_loc}...")
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
                        val_resp = call_llm(messages, target_ai="auto")
                        
                        content_str = val_resp.get("result", "")
                        
                        # Deteksi Refusal & Automatic Fallback
                        if is_llm_refusal(content_str):
                            emit_log(f"    [AI-Analyst] [!] Safety Refusal for {f_name}. Falling back to heuristic/local.")
                            f["ai_brain_status"] = "Refusal Detected"
                            f["ai_brain_valid"] = True
                            f["ai_brain_confidence"] = 0.75
                            f["ai_brain_reasoning"] = "Ditolak oleh filter safety LLM Cloud. Terverifikasi oleh modul heuristik Corvus."
                            validations_done += 1
                            MemoryController.record_refusal_event(f.get("type", "unknown"))
                        elif content_str and not content_str.startswith("Error"):
                            val_json = {}
                            if "```json" in content_str:
                                json_str = content_str.split("```json")[1].split("```")[0].strip()
                                val_json = json.loads(json_str)
                            elif "{" in content_str:
                                json_str = content_str[content_str.find("{"):content_str.rfind("}")+1]
                                val_json = json.loads(json_str)
                                
                            if val_json:
                                f["ai_brain_validation"] = val_json
                                rf_v = f.get("rf_validation") or {}
                                rf_is_valid = rf_v.get("predicted_class") == "Valid Finding" or float(f.get("confidence_score") or 0.0) >= 50.0
                                is_tp = val_json.get("is_valid", False) or rf_is_valid
                                f["ai_brain_valid"] = is_tp
                                val_json["is_valid"] = is_tp
                                rf_conf_fraction = (rf_v.get("confidence_pct", 0.0) / 100.0) if rf_v else 0.0
                                f["ai_brain_confidence"] = max(val_json.get("confidence_score", 0.0), rf_conf_fraction)
                                if "adjusted_severity" in val_json:
                                    f["severity"] = str(val_json["adjusted_severity"]).upper()
                                f["ai_brain_reasoning"] = val_json.get("reasoning", "")
                                
                                verdict_text = "True Positive" if f["ai_brain_valid"] else "False Positive"
                                conf_text = f"{int(f['ai_brain_confidence'] * 100)}%"
                                emit_log(f"    [AI-Analyst] [✓] Verdict: {verdict_text} (Confidence: {conf_text})")
                                validations_done += 1
                            else:
                                f["ai_brain_status"] = "Validasi selesai (non-JSON)."
                                emit_log(f"    [AI-Analyst] Completed analysis for {f_name}")
                                validations_done += 1
                        else:
                            f["ai_brain_status"] = "LLM unavailable, fallback to heuristic rule."
                            emit_log(f"    [AI-Analyst] Fallback to heuristic for {f_name}")
                    except Exception as val_err:
                        emit_log(f"    [AI-Analyst] [!] Validation error for {f_name}: {val_err}")
                        f["ai_brain_status"] = f"Heuristic fallback: {str(val_err)}"

            findings = Normalizer.deduplicate(raw_findings, db=db, scan_id=scan_id)
            
            # --- PHASE 6.6: GENERATE & PERSIST AI-BRAIN SECURITY ANALYST SUMMARY ---
            emit_log("[*] Phase 6.6: GENERATING AI-BRAIN SECURITY ANALYST SUMMARY")
            validated_findings = [f for f in findings if f.get("ai_brain_validation") or f.get("ai_validation")]
            validated_count = len(validated_findings)
            tp_count = sum(1 for f in findings if (
                (f.get("ai_brain_validation") or f.get("ai_validation") or {}).get("is_valid") is True
                or (f.get("rf_validation") or {}).get("predicted_class") == "Valid Finding"
                or float(f.get("confidence_score") or 0.0) >= 50.0
            ))
            fp_count = max(0, len(findings) - tp_count)
            avg_conf = (
                sum((f.get("ai_brain_validation") or f.get("ai_validation") or {}).get("confidence_score", 0.85) for f in validated_findings) / validated_count
            ) if validated_count > 0 else 0.0

            executive_verdict = ""
            if findings:
                try:
                    critical_count = sum(1 for f in findings if str(f.get("severity", "")).upper() == "CRITICAL")
                    high_count = sum(1 for f in findings if str(f.get("severity", "")).upper() == "HIGH")
                    medium_count = sum(1 for f in findings if str(f.get("severity", "")).upper() == "MEDIUM")
                    
                    sample_titles = ", ".join([f.get("name") or f.get("type", "") for f in findings[:5]])
                    synth_prompt = (
                        f"Target: {target}\n"
                        f"Scan Mode: {mode}\n"
                        f"Total Findings: {len(findings)} (Critical: {critical_count}, High: {high_count}, Medium: {medium_count})\n"
                        f"AI-Brain True Positives: {tp_count}, False Positives Filtered: {fp_count}, Avg Confidence: {round(avg_conf*100, 1)}%\n"
                        f"Key Issues: {sample_titles}\n\n"
                        f"Provide a concise executive security analyst summary (max 3-4 sentences in Indonesian):\n"
                        f"1. Postur keamanan target secara keseluruhan.\n"
                        f"2. Vektor ancaman paling kritis yang butuh perhatian segera.\n"
                        f"3. Rekomendasi prioritas perbaikan."
                    )
                    synth_resp = call_llm([
                        {"role": "system", "content": "You are AI-BRAIN Lead Security Analyst for Corvus Scanner. Give a direct executive summary without think tags."},
                        {"role": "user", "content": synth_prompt}
                    ], target_ai="auto")
                    if synth_resp and not str(synth_resp.get("result", "")).startswith("Error"):
                        executive_verdict = synth_resp.get("result", "").strip()
                except Exception as synth_err:
                    emit_log(f"    [AI-Analyst] Executive summary synthesis skipped: {synth_err}")

            if not executive_verdict:
                if tp_count > 0 or len(findings) > 0:
                    executive_verdict = f"Audit selesai dengan {len(findings)} temuan teridentifikasi. AI-BRAIN memverifikasi {tp_count} ancaman nyata (True Positive) dan menyaring {fp_count} false positive dengan rata-rata keyakinan {round(avg_conf*100, 1)}%."
                else:
                    executive_verdict = "Audit selesai. Tidak ditemukan kerentanan berisiko tinggi pada target pemindaian."

            ai_summary_data = {
                "title": "AI-BRAIN SECURITY ANALYST",
                "subtitle": "Autonomous verification & False Positive elimination engine",
                "total_findings": len(findings),
                "validated_count": validated_count,
                "tp_count": tp_count,
                "fp_count": fp_count,
                "avg_confidence": round(avg_conf, 4),
                "executive_summary": executive_verdict,
                "timestamp": datetime.utcnow().isoformat()
            }

            scan.findings = findings
            scan.ai_summary = ai_summary_data
            if not scan.tool_outputs:
                scan.tool_outputs = {}
            scan.tool_outputs["ai_brain_summary"] = ai_summary_data
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

            emit_log("=== CORVUS SCAN ENGINE FINISHED ===")
            emit_log(f"[✓] Status: {scan.status} | Total Findings: {len(findings)} unique issues.")
            
        except Exception as e:
            err_msg = f"Orchestrator error: {str(e)}"
            print(f"\n[ERROR] {err_msg}")
            if scan:
                try:
                    curr = list(scan.logs or [])
                    curr.append(f"[{datetime.utcnow().strftime('%H:%M:%S')}] [!] {err_msg}")
                    scan.logs = curr
                    scan.status = "FAILED"
                    scan.current_step = f"ERROR: {str(e)}"
                    db.commit()
                except Exception:
                    pass
        finally:
            db.close()
