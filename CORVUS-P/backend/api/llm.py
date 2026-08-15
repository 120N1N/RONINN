from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import json
import hashlib
import socket
from urllib.parse import urlparse

import re
import redis
from backend.config import settings

# Semantic cache using Redis
try:
    semantic_cache = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception:
    semantic_cache = None
from backend.db.database import get_db
from backend.db import models
from backend.core import auth
from backend.utils.encryption import encrypt_api_key, decrypt_api_key
from backend.core import llm_providers
from backend.utils import html_fetcher
from backend.core.ai_brain import AIBrainLoader, AIBrainValidator
from backend.core.ai_brain_advisor import AIBrainAdvisor

router = APIRouter(prefix="/llm", tags=["LLM Integrations"])

def is_deep_validate_allowed(vuln_type: str) -> bool:
    """
    Strict whitelist and blacklist for Deep Validate (Agentic Fetching).
    Only allows client-side vulnerabilities. Rejects destructive ones.
    """
    vuln_type_lower = vuln_type.lower()
    
    # Blacklist (Highest Priority)
    blacklist = ["sql", "rce", "command", "injection", "ssrf", "xxe", "ssti", "lfi", "rfi"]
    for blocked in blacklist:
        if blocked in vuln_type_lower:
            return False
            
    # Whitelist
    whitelist = ["xss", "cross-site scripting", "open redirect", "cors", "clickjacking", "information disclosure"]
    for allowed in whitelist:
        if allowed in vuln_type_lower:
            return True
            
    return False

# --- schemas ---
class LLMKeyCreate(BaseModel):
    provider: str
    name: Optional[str] = None
    api_key: str
    model: Optional[str] = None

class LLMKeyTestRequest(BaseModel):
    provider: str
    api_key: str
    model: Optional[str] = None

class LLMKeyResponse(BaseModel):
    id: int
    provider: str
    name: Optional[str]
    masked_key: str
    model: Optional[str]
    is_active: bool
    created_at: datetime

    model_config = {
        "from_attributes": True,
        "protected_namespaces": ()
    }

class VulnerabilityPayload(BaseModel):
    type: str
    severity: str
    endpoint: str
    evidence: Optional[str] = ""
    caido_request_verb: Optional[str] = "GET"
    caido_param_count: Optional[int] = 0
    caido_auth_headers_present: Optional[int] = 0
    caido_content_type: Optional[str] = "other"
    caido_response_size_mean: Optional[float] = 1000.0
    caido_response_size_std: Optional[float] = 100.0
    caido_status_codes_seen: Optional[List[int]] = [200]
    caido_endpoint_depth: Optional[int] = 1

class LLMAnalyzeRequest(BaseModel):
    vulnerability: VulnerabilityPayload
    action: str # "explain", "remediate", "summarize", "tp_fp_assist", "analyze_all", "deep_validate"
    user_prompt: Optional[str] = ""

class ToolAdviseRequest(BaseModel):
    target: str
    scan_mode: str
    target_info: Optional[Dict] = None

class ValidateWithCaidoRequest(BaseModel):
    finding: Dict
    caido_profile: Optional[Dict] = None

class UsefulnessRatingRequest(BaseModel):
    rating: int # 1 to 5
    feedback: Optional[str] = ""
    finding_id: Optional[str] = ""
    action: str

# --- utilities ---
def mask_key(api_key: str, provider: str) -> str:
    """Mask key, showing only the last 4 characters"""
    clean_k = api_key.strip()
    if len(clean_k) <= 6:
        return "sk-..." + clean_k[-2:]
    return f"{clean_k[:3]}-...{clean_k[-4:]}"

# --- routes ---

# API Key endpoints have been removed as the system now uses a centralized Qwen API key.

@router.get("/status")
def get_llm_status():
    return {"has_keys": True, "providers": ["qwen"]}

@router.post("/evaluate")
def evaluate_llm_usefulness(
    req: UsefulnessRatingRequest,
    current_user: models.User = Depends(auth.get_current_user)
):
    print(f"[LLM EVALUATION] Analyst {current_user.username} rated LLM analysis on {req.action} as usefulness={req.rating}/5. Feedback: {req.feedback or 'None'}")
    return {"status": "ok", "message": "Thank you for your feedback! Usefulness rating submitted."}

@router.post("/advise-tools")
def advise_tools(
    request: ToolAdviseRequest,
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    AI-BRAIN memberikan rekomendasi tools berdasarkan target dan mode scan.
    """
    prompt = AIBrainAdvisor.build_advisor_prompt(
        target=request.target,
        scan_mode=request.scan_mode,
        target_info=request.target_info
    )
    
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": f"Berikan rekomendasi tools untuk target: {request.target}"}
    ]
    
    response = llm_providers.call_llm(messages)
    
    try:
        if "content" in response and "```json" in response["content"]:
            json_str = response["content"].split("```json")[1].split("```")[0].strip()
            return {"status": "success", "data": json.loads(json_str)}
        elif "content" in response and "{" in response["content"]:
            json_str = response["content"][response["content"].find("{"):response["content"].rfind("}")+1]
            return {"status": "success", "data": json.loads(json_str)}
    except:
        pass
    
    return response

@router.post("/validate-with-caido")
def validate_with_caido(
    request: ValidateWithCaidoRequest,
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Validasi temuan menggunakan AI-BRAIN + data traffic Caido.
    """
    # Semantic Caching
    cache_key_data = json.dumps(request.finding, sort_keys=True) + json.dumps(request.caido_profile or {}, sort_keys=True)
    cache_key = hashlib.sha256(cache_key_data.encode()).hexdigest()
    
    if semantic_cache:
        cached_data = semantic_cache.get(cache_key)
        if cached_data:
            print(f"[SEMANTIC CACHE HIT] {cache_key}")
            return {"status": "success", "data": json.loads(cached_data), "cached": True}
    
    validation_prompt = AIBrainValidator.build_validation_prompt(
        finding=request.finding,
        caido_profile=request.caido_profile
    )
    
    messages = [
        {"role": "system", "content": validation_prompt},
        {"role": "user", "content": "Validasi temuan di atas sesuai SOP HunterFlowX. Berikan JSON."}
    ]
    
    response = llm_providers.call_llm(messages)
    
    try:
        if "content" in response and "```json" in response["content"]:
            json_str = response["content"].split("```json")[1].split("```")[0].strip()
            parsed = json.loads(json_str)
            if semantic_cache:
                semantic_cache.setex(cache_key, 3600, json.dumps(parsed))
            return {"status": "success", "data": parsed, "cached": False}
        elif "content" in response and "{" in response["content"]:
            json_str = response["content"][response["content"].find("{"):response["content"].rfind("}")+1]
            parsed = json.loads(json_str)
            if semantic_cache:
                semantic_cache.setex(cache_key, 3600, json.dumps(parsed))
            return {"status": "success", "data": parsed, "cached": False}
    except:
        pass
        
    return response

@router.post("/analyze")
def analyze_with_ai_brain(
    req: LLMAnalyzeRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """
    Analisis temuan dengan bantuan AI-BRAIN (Explain/Remediate/Summarize).
    """

    vuln_type = req.vulnerability.type
    ai_brain_context = AIBrainLoader.load_for_vuln(vuln_type)
    agents = AIBrainLoader.load_agents()
    
    system_prompt = f"{agents}\n\n## SOP HunterFlowX\n{ai_brain_context}\n\n## Instruksi\nAnda adalah security analyst yang mengikuti SOP HunterFlowX.\n"
    
    # Original logic for actions (explain, remediate, etc.)
    action_clean = req.action.lower().strip()
    vuln = req.vulnerability
    
    verb = vuln.caido_request_verb or "GET"
    param_count = vuln.caido_param_count or 0
    auth_headers = vuln.caido_auth_headers_present
    content_type = vuln.caido_content_type or "other"
    size_mean = vuln.caido_response_size_mean or 1000.0
    size_std = vuln.caido_response_size_std or 100.0
    status_codes = vuln.caido_status_codes_seen or [200]
    depth = vuln.caido_endpoint_depth or 1
    
    user_prompt = req.user_prompt or ""
    
    if not user_prompt:
        if action_clean in ["tp_fp_assist", "classify"]:
            user_prompt = (
                "Berdasarkan data berikut, tentukan apakah temuan ini True Positive atau False Positive. Berikan confidence 0-100% dan alasan.\n\n"
                f"Temuan:\n- Type: {vuln.type}\n- Severity: {vuln.severity}\n- Endpoint: {vuln.endpoint}\n- Evidence: {vuln.evidence}\n\n"
            )
        elif action_clean == "explain":
            poc_template = """# 🛸 POC-REPORT – Vulnerability Report

## 1. REPORT METADATA

| **Field** | **Detail** |
|-----------|------------|
| Report ID | `POC-REPORT-{YEAR}-{RANDOM_ID}` |
| Date Submitted | `{CURRENT_DATE}` |
| Reporter | `Corvus AI Brain` |
| Program | `Corvus Security` |
| Target | `{TARGET_URL}` |
| Severity (Self) | `{Severity}` |
| CVSS v3.1 Score | `{CVSS_SCORE}` |
| CVSS Vector | `{CVSS_VECTOR_STRING}` |

---

## 2. VULNERABILITY CLASSIFICATION

| **Category** | **Value** |
|--------------|-----------|
| OWASP 2021 | `{AXX:2021}` |
| CWE ID | `{CWE-XXX}` |
| CAPEC ID | `{CAPEC-XXX}` |
| Vulnerability Type | `{VULN_TYPE}` |
| Affected Component | `{ENDPOINT}` |

---

## 3. EXECUTIVE SUMMARY

> **One-Sentence Summary:**
> *{Brief summary}*

**Business Impact:**
*{Detailed explanation}*

**Attack Complexity:**
*{Simple / Moderate / Complex}*

---

## 4. TECHNICAL DETAILS

### 4.1 Affected Endpoints
• {ENDPOINT}

### 4.2 Prerequisites
- [ ] Requirements

### 4.3 Vulnerability Description
*{Detailed technical breakdown}*

---

## 5. PROOF OF CONCEPT (POC)

### 5.1 Step-by-Step Reproduction
{Provide step-by-step HTTP requests/responses or execution code snippets. Use markdown codes}

### 5.2 POC Artifacts
[✓] Evidence: {EVIDENCE}

### 5.3 Payload Used
{PAYLOAD_USED}

---
## 6. IMPACT ANALYSIS
{Describe Confidentiality, Integrity, Availability, Privacy, Financial, Reputational}

---
## 7. OWASP RISK RATING
{Assess Threat Agent, Attack Vector, Vulnerability Prevalence, Technical Impact, Business Impact}

---
## 8. RECOMMENDATION & REMEDIATION

### 8.1 Short-term Fix (Immediate)
- {Step 1}

### 8.2 Long-term Fix (Strategic)
- {Step 1}

### 8.3 Code-Level Fix
// Vulnerable Code
{VULNERABLE_CODE_SNIPPET}

// Fixed Code
{SECURE_CODE_SNIPPET}

---
## 9. EVIDENCE & SUPPORTING MATERIALS
{Extra notes, related endpoints}

---
## 10. TRIAGE CHECKLIST (Internal)
- [x] Duplicate check performed
- [x] POC reproducible
- [x] Valid target in scope
- [x] No sensitive data exposed in report
- [x] Proper CVSS calculated
- [x] OWASP category correct"""

            user_prompt = f"Anda adalah Expert Cybersecurity Auditor. Buatlah Laporan Analisis Detail (POC-REPORT) murni mengikuti template markdown di bawah untuk kerentanan {vuln.type} pada endpoint {vuln.endpoint} dengan severity {vuln.severity}. Gunakan evidence berikut: {vuln.evidence}.\n\nJika ada data yang hilang (seperti CVSS, CWE, CAPEC, HTTP Request), buat estimasi profesional sesuai standar industri. Ganti semua placeholder {{...}} dengan data yang relevan.\n\nTemplate:\n{poc_template}"
        elif action_clean == "remediate":
            user_prompt = f"Berikan rekomendasi perbaikan untuk kerentanan {vuln.type} pada endpoint {vuln.endpoint}."
        elif action_clean == "summarize":
            user_prompt = f"Rangkum temuan berikut dalam 3 kalimat: {vuln.type} pada {vuln.endpoint}, severity {vuln.severity}, evidence: {vuln.evidence}."
        elif action_clean == "analyze_all":
            user_prompt = f"Lakukan analisis komprehensif pada temuan: {vuln.type} di {vuln.endpoint}. Berikan penjelasan, ringkasan, TP/FP rating, dan remediasi."
        elif action_clean == "deep_validate":
            if not is_deep_validate_allowed(vuln.type):
                raise HTTPException(status_code=400, detail="Deep Validate tidak tersedia (Risiko Destruktif).")
            
            # SSRF Protection: Cegah resolve IP internal
            try:
                parsed_url = urlparse(vuln.endpoint)
                ip = socket.gethostbyname(parsed_url.hostname)
                if ip.startswith("10.") or ip.startswith("192.168.") or ip.startswith("127.") or ip.startswith("169.254."):
                    raise HTTPException(status_code=400, detail="SSRF Protection: Private/Internal IPs are blocked.")
            except Exception as e:
                pass # Biarkan exception HTTPException lolos, tangkap exception hostname
                if isinstance(e, HTTPException):
                    raise e
            
            # Rate Limiting
            five_seconds_ago = datetime.utcnow().timestamp() - 5
            recent_log = db.query(models.DeepValidateLog).filter(
                models.DeepValidateLog.user_id == current_user.id
            ).order_by(models.DeepValidateLog.timestamp.desc()).first()
            
            if recent_log and recent_log.timestamp.timestamp() > five_seconds_ago:
                raise HTTPException(status_code=429, detail="Too many requests. Harap tunggu 5 detik.")
                
            fetch_result = html_fetcher.fetch_endpoint_html(vuln.endpoint)
            fetch_status = fetch_result["status"]
            
            log_entry = models.DeepValidateLog(
                user_id=current_user.id,
                target=vuln.endpoint.split('/')[2] if '//' in vuln.endpoint else vuln.endpoint,
                endpoint=vuln.endpoint,
                status=fetch_status
            )
            db.add(log_entry)
            db.commit()
            
            if fetch_status == "success":
                # Sanitize and limit tokens to avoid exceeding context window
                html_content = fetch_result['html']
                stripped_html = re.sub(r'<[^>]+>', ' ', html_content)
                stripped_html = ' '.join(stripped_html.split())
                if len(stripped_html) > 3000:
                    stripped_html = stripped_html[:3000] + "\n...[TRUNCATED]"
                
                user_prompt = f"Validasi Agentic HTML:\n- Type: {vuln.type}\n- Endpoint: {vuln.endpoint}\n- Evidence: {vuln.evidence}\n\nCuplikan HTML:\n```html\n{stripped_html}\n```\nApakah True Positive atau False Positive?"
            else:
                user_prompt = f"Validasi teoritis:\n- Type: {vuln.type}\n- Endpoint: {vuln.endpoint}\n- Evidence: {vuln.evidence}\nStatus Fetching: GAGAL ({fetch_status}).\nTentukan kemungkinan TP/FP."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    target_ai = "gemini" if action_clean in ["deep_validate", "tp_fp_assist", "analyze_all", "explain", "classify"] else "qwen"
    response = llm_providers.call_llm(messages, target_ai=target_ai)
    
    if action_clean == "deep_validate":
        response["fetch_status"] = locals().get("fetch_status", "unknown")
        
    return response
