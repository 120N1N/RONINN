from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import json
import hashlib
import os
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
    Controls which vulnerability types can use Deep Validate (Agentic Fetching).
    Allow by default. Only block types where fetching could trigger destructive 
    server-side exploitation (e.g., SQLi payload execution, RCE).
    """
    vuln_type_lower = vuln_type.lower()
    
    # Blacklist: Only truly destructive server-side exploits
    blacklist = ["rce", "remote code execution", "command injection"]
    for blocked in blacklist:
        if blocked in vuln_type_lower:
            return False
            
    return True

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
    key_id: Optional[int] = 1

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

# Returning mock keys for frontend UI and multi-LLM load balancing.
@router.get("/keys")
def get_llm_keys(current_user: models.User = Depends(auth.get_current_user)):
    return [
        {"id": 1, "provider": "gemini", "name": "Google Gemini", "masked_key": "AI-****", "model": "gemini-3.5-flash-lite", "is_active": True},
        {"id": 2, "provider": "river", "name": "River.ai (Qwen3.5-9B)", "masked_key": "rv-****", "model": os.getenv("RIVER_MODEL", "Qwen/Qwen3.5-9B"), "is_active": True},
        {"id": 3, "provider": "openrouter", "name": "OpenRouter", "masked_key": "sk-or-****", "model": "gemini-2.0-flash", "is_active": True}
    ]

@router.get("/status")
def get_llm_status(current_user: models.User = Depends(auth.get_current_user)):
    return {"has_keys": True, "providers": ["gemini", "river", "openrouter"]}

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
        content = response.get("result") or response.get("content", "")
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
            return {"status": "success", "data": json.loads(json_str)}
        elif "{" in content:
            json_str = content[content.find("{"):content.rfind("}")+1]
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
        content = response.get("result") or response.get("content", "")
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
            parsed = json.loads(json_str)
            if semantic_cache:
                semantic_cache.setex(cache_key, 3600, json.dumps(parsed))
            return {"status": "success", "data": parsed, "cached": False}
        elif "{" in content:
            json_str = content[content.find("{"):content.rfind("}")+1]
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
    
    system_prompt = (
        f"{agents}\n\n"
        f"## Konteks Keamanan\n{ai_brain_context}\n\n"
        "## Instruksi Output\n"
        "Anda adalah senior cybersecurity analyst profesional.\n"
        "ATURAN FORMAT OUTPUT:\n"
        "- DILARANG menggunakan tabel markdown (|---|). Gunakan bullet points atau daftar bernomor.\n"
        "- DILARANG menyebut nama framework internal, SOP internal, atau metodologi internal apapun.\n"
        "- Gunakan bahasa Indonesia yang jelas dan profesional.\n"
        "- Fokus pada hasil analisis yang actionable dan evidence-based.\n"
        "- Berikan verdict yang tegas: True Positive, False Positive, atau Inconclusive.\n"
    )
    
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
- **Report ID:** POC-REPORT-{YEAR}-{RANDOM_ID}
- **Date:** {CURRENT_DATE}
- **Reporter:** Corvus AI Brain
- **Target:** {TARGET_URL}
- **Severity:** {Severity}
- **CVSS v3.1 Score:** {CVSS_SCORE}
- **CVSS Vector:** {CVSS_VECTOR_STRING}

---

## 2. VULNERABILITY CLASSIFICATION
- **OWASP 2021:** {AXX:2021}
- **CWE ID:** {CWE-XXX}
- **CAPEC ID:** {CAPEC-XXX}
- **Vulnerability Type:** {VULN_TYPE}
- **Affected Component:** {ENDPOINT}

---

## 3. EXECUTIVE SUMMARY

> **One-Sentence Summary:**
> *{Brief summary}*

**Business Impact:**
*{Detailed explanation}*

**Attack Complexity:** *{Simple / Moderate / Complex}*

---

## 4. TECHNICAL DETAILS

### 4.1 Affected Endpoints
- {ENDPOINT}

### 4.2 Prerequisites
- {Requirements}

### 4.3 Vulnerability Description
*{Detailed technical breakdown}*

---

## 5. PROOF OF CONCEPT (POC)

### 5.1 Step-by-Step Reproduction
{Provide step-by-step HTTP requests/responses. Use markdown code blocks}

### 5.2 POC Artifacts
- Evidence: {EVIDENCE}

### 5.3 Payload Used
```
{PAYLOAD_USED}
```

---

## 6. IMPACT ANALYSIS
- **Confidentiality:** {impact}
- **Integrity:** {impact}
- **Availability:** {impact}

---

## 7. RECOMMENDATION & REMEDIATION

### 7.1 Short-term Fix (Immediate)
- {Step 1}

### 7.2 Long-term Fix (Strategic)
- {Step 1}

### 7.3 Code-Level Fix
```
// Vulnerable Code
{VULNERABLE_CODE_SNIPPET}

// Fixed Code
{SECURE_CODE_SNIPPET}
```

---

## 8. TRIAGE CHECKLIST
- [x] Duplicate check performed
- [x] POC reproducible
- [x] Valid target in scope
- [x] Proper CVSS calculated"""

            user_prompt = f"Anda adalah Expert Cybersecurity Auditor. Buatlah Laporan Analisis Detail (POC-REPORT) mengikuti template di bawah untuk kerentanan {vuln.type} pada endpoint {vuln.endpoint} dengan severity {vuln.severity}. Gunakan evidence berikut: {vuln.evidence}.\n\nJIKA ada data yang hilang (seperti CVSS, CWE, CAPEC), buat estimasi profesional sesuai standar industri. Ganti semua placeholder dengan data yang relevan.\n\nINGAT: JANGAN gunakan tabel markdown. Gunakan bullet points dan daftar bernomor saja.\n\nTemplate:\n{poc_template}"
        elif action_clean == "remediate":
            user_prompt = (
                f"Berikan rekomendasi perbaikan detail untuk kerentanan berikut:\n"
                f"- Tipe: {vuln.type}\n- Endpoint: {vuln.endpoint}\n- Severity: {vuln.severity}\n- Evidence: {vuln.evidence}\n\n"
                "Format output:\n"
                "1. **Ringkasan Masalah** - Jelaskan secara singkat kerentanan ini\n"
                "2. **Perbaikan Segera** - Langkah-langkah yang bisa langsung diterapkan\n"
                "3. **Perbaikan Jangka Panjang** - Solusi arsitektural\n"
                "4. **Contoh Kode** - Berikan contoh kode perbaikan jika relevan\n\n"
                "JANGAN gunakan tabel markdown."
            )
        elif action_clean == "summarize":
            user_prompt = (
                f"Rangkum temuan keamanan berikut secara ringkas dan jelas:\n"
                f"- Tipe: {vuln.type}\n- Endpoint: {vuln.endpoint}\n- Severity: {vuln.severity}\n- Evidence: {vuln.evidence}\n\n"
                "Berikan dalam format:\n"
                "1. **Deskripsi** - Apa kerentanannya (2-3 kalimat)\n"
                "2. **Risiko** - Dampak jika dieksploitasi\n"
                "3. **Verdict** - True Positive / False Positive / Inconclusive + alasan singkat\n\n"
                "JANGAN gunakan tabel markdown."
            )
        elif action_clean == "analyze_all":
            user_prompt = (
                f"Lakukan analisis komprehensif pada temuan keamanan berikut:\n"
                f"- Tipe: {vuln.type}\n- Endpoint: {vuln.endpoint}\n- Severity: {vuln.severity}\n- Evidence: {vuln.evidence}\n\n"
                "Berikan analisis dalam format:\n\n"
                "**1. PENJELASAN KERENTANAN**\n"
                "Jelaskan apa itu kerentanan ini, bagaimana cara kerjanya, dan mengapa berbahaya.\n\n"
                "**2. VERDICT (TRUE POSITIVE / FALSE POSITIVE)**\n"
                "- Verdict: [TP/FP/Inconclusive]\n"
                "- Confidence: [0-100%]\n"
                "- Alasan: [penjelasan singkat]\n\n"
                "**3. BUKTI & VALIDASI**\n"
                "Jelaskan evidence yang mendukung verdict.\n\n"
                "**4. DAMPAK**\n"
                "Jelaskan dampak jika kerentanan ini dieksploitasi.\n\n"
                "**5. REMEDIASI**\n"
                "Berikan langkah-langkah perbaikan yang spesifik.\n\n"
                "**6. POC (Proof of Concept)**\n"
                "Berikan contoh POC sederhana (curl command, HTML snippet, atau payload) yang bisa digunakan untuk memverifikasi kerentanan ini.\n\n"
                "JANGAN gunakan tabel markdown. JANGAN menyebut nama SOP/framework internal apapun."
            )
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
                pass
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
                html_content = fetch_result['html']
                resp_headers = fetch_result.get('headers', {})
                meta_tags = fetch_result.get('meta_tags', '')
                status_code = fetch_result.get('status_code', 'unknown')
                final_url = fetch_result.get('final_url', vuln.endpoint)
                redirects = fetch_result.get('redirect_history', [])
                
                # Format headers for LLM
                headers_text = "\n".join([f"  {k}: {v}" for k, v in resp_headers.items()]) if resp_headers else "  (tidak ada security headers terdeteksi)"
                redirects_text = " -> ".join([str(r) for r in redirects]) if redirects else "Tidak ada redirect"
                today_str = datetime.utcnow().strftime("%Y-%m-%d")
                user_prompt = (
                    f"Anda adalah Security Assessment Engine. Susun laporan Deep Validation secara lengkap dan profesional dengan struktur persis seperti di bawah ini:\n\n"
                    f"# Laporan Assessment Keamanan\n\n"
                    f"**Target:** {vuln.endpoint}\n"
                    f"**Tanggal:** {today_str}\n"
                    f"**Tools:** Automated Security Engine\n"
                    f"**Jenis Assessment:** Deep Validation - {vuln.type}\n"
                    f"**ID Laporan:** SEC-{today_str}-001\n\n"
                    f"---\n\n"
                    f"## 1. RINGKASAN EKSEKUTIF\n\n"
                    f"- **Status Pengujian:** SELESAI\n"
                    f"- **Kerentanan Ditemukan:** [YA / TIDAK / BELUM TERKONFIRMASI]\n"
                    f"- **Tingkat Risiko:** {vuln.severity}\n"
                    f"- **Tingkat Keyakinan:** [Persentase Keyakinan, misal 95%]\n"
                    f"- **Jenis Kerentanan:** {vuln.type}\n"
                    f"- **CWE:** [Sebutkan CWE terkait, misal CWE-1021]\n\n"
                    f"**Kesimpulan Singkat:**\n"
                    f"[Jelaskan ringkasan 2-3 kalimat mengenai kondisi endpoint dan risiko nyatanya]\n\n"
                    f"---\n\n"
                    f"## 2. BUKTI RUNTIME (EVIDENCE)\n\n"
                    f"### A. HTTP Request & Response\n"
                    f"**Data Real Runtime yang Diterima:**\n"
                    f"- HTTP Status Code: {status_code}\n"
                    f"- Final URL: {final_url}\n"
                    f"- Redirects: {redirects_text}\n\n"
                    f"**Response Headers Terdeteksi:**\n"
                    f"```http\n"
                    f"{headers_text}\n"
                    f"```\n\n"
                    f"**Cuplikan HTML Target:**\n"
                    f"```html\n"
                    f"{html_content[:2500]}\n"
                    f"```\n\n"
                    f"**Kesimpulan dari Header / Evidence:**\n"
                    f"[Analisis status header proteksi apakah terpasang atau MISSING]\n\n"
                    f"### B. Uji Proof of Concept (PoC)\n"
                    f"**Kode PoC Siap Pakai:**\n"
                    f"[Berikan kode HTML/curl/script PoC lengkap yang relevan dengan jenis kerentanan {vuln.type}]\n\n"
                    f"**Hasil Uji yang Diharapkan:**\n"
                    f"- [Poin-poin hasil uji validasi yang dapat diobservasi]\n\n"
                    f"### C. Screenshot / Visual Proof Note\n"
                    f"Visual proof dapat direproduksi dengan menjalankan kode PoC di atas pada browser lokal.\n\n"
                    f"---\n\n"
                    f"## 3. METODOLOGI PENGUJIAN\n\n"
                    f"1. Verifikasi Akses Endpoint: Akses HTTP ke target ({status_code})\n"
                    f"2. Inspeksi Response Header: Pemeriksaan header keamanan relevan\n"
                    f"3. Validasi Konten & Context: Analisis payload dan respons HTML\n"
                    f"4. Pengujian PoC: Uji reproduksi serangan\n"
                    f"5. Verifikasi False Positive: Memastikan respons bukan berasal dari CDN cache atau generic error\n\n"
                    f"---\n\n"
                    f"## 4. DETAIL TEMUAN\n\n"
                    f"### Identifikasi Kerentanan\n"
                    f"- **Nama Kerentanan:** {vuln.type}\n"
                    f"- **Severity:** {vuln.severity}\n"
                    f"- **Endpoint Terpengaruh:** {vuln.endpoint}\n"
                    f"- **Scanner Evidence:** {vuln.evidence}\n\n"
                    f"### Deskripsi Mendalam\n"
                    f"[Jelaskan secara teknis mengapa celah ini terjadi dan mekanismenya]\n\n"
                    f"### Dampak Potensial\n"
                    f"[Jelaskan dampak eksploitasi terhadap kerahasiaan, integritas, dan ketersediaan data/akun]\n\n"
                    f"### Rekayasa Skenario Serangan (Attack Scenario)\n"
                    f"[Jelaskan langkah demi langkah bagaimana penyerang mengeksploitasi celah ini]\n\n"
                    f"---\n\n"
                    f"## 5. REKOMENDASI PERBAIKAN\n\n"
                    f"### Langkah Remediasi Teknis\n"
                    f"[Berikan contoh konfigurasi server spesifik seperti Nginx, Apache, atau kode aplikasi]\n\n"
                    f"### Prioritas & Timeline\n"
                    f"- Prioritas Tinggi: Terapkan konfigurasi mitigasi utama segera\n"
                    f"- Prioritas Sedang: Uji menyeluruh seluruh sub-path dan domain\n\n"
                    f"### Cara Verifikasi Perbaikan\n"
                    f"Gunakan perintah curl berikut setelah konfigurasi diterapkan:\n"
                    f"```bash\n"
                    f"curl -I -s \"{vuln.endpoint}\"\n"
                    f"```\n\n"
                    f"---\n\n"
                    f"## 6. LAMPIRAN (RAW DATA)\n\n"
                    f"### A. Raw Response Summary\n"
                    f"Endpoint: {vuln.endpoint}\n"
                    f"Status: {status_code}\n\n"
                    f"### B. Lingkungan Pengujian\n"
                    f"- Tanggal & Waktu: {today_str}\n"
                    f"- Target URL: {vuln.endpoint}\n\n"
                    f"---\n\n"
                    f"## 7. STATUS AKHIR (FINAL VERDICT)\n\n"
                    f"- **Verdict:** [TRUE POSITIVE / FALSE POSITIVE / INCONCLUSIVE]\n"
                    f"- **Confidence:** [0-100%]\n"
                    f"- **Alasan Final:** [Kesimpulan akhir berdasarkan bukti]\n\n"
                    f"JANGAN sebut nama SOP/framework internal apapun."
                )
            else:
                error_msg = fetch_result.get('error', 'Unknown error')
                today_str = datetime.utcnow().strftime("%Y-%m-%d")
                user_prompt = (
                    f"Anda adalah Security Assessment Engine. Susun laporan Deep Validation (Status Fetch Gagal) secara lengkap dan profesional dengan struktur berikut:\n\n"
                    f"# Laporan Assessment Keamanan\n\n"
                    f"**Target:** {vuln.endpoint}\n"
                    f"**Tanggal:** {today_str}\n"
                    f"**Tools:** Automated Security Engine\n"
                    f"**Jenis Assessment:** Deep Validation - {vuln.type}\n"
                    f"**ID Laporan:** SEC-{today_str}-001\n\n"
                    f"---\n\n"
                    f"## 1. RINGKASAN EKSEKUTIF\n\n"
                    f"- **Status Pengujian:** GAGAL (Koneksi Target Terkendala)\n"
                    f"- **Kerentanan Ditemukan:** BELUM DAPAT DIKONFIRMASI\n"
                    f"- **Tingkat Risiko:** {vuln.severity}\n"
                    f"- **Tingkat Keyakinan:** 0% (Data Runtime Tidak Tersedia)\n"
                    f"- **Jenis Kerentanan:** {vuln.type}\n\n"
                    f"**Kesimpulan Singkat:**\n"
                    f"Engine tidak berhasil menarik respon HTTP dari `{vuln.endpoint}` karena kendala jaringan atau proteksi target ({error_msg}). Laporan ini bersifat Inconclusive sampai verifikasi manual dilakukan.\n\n"
                    f"---\n\n"
                    f"## 2. DIAGNOSTIK KENDALA KONEKSI\n\n"
                    f"- **Error Code / Detail:** {error_msg}\n"
                    f"- **Scanner Evidence Awal:** {vuln.evidence}\n"
                    f"- **Kemungkinan Penyebab:**\n"
                    f"  1. Target server sedang offline / DNS error\n"
                    f"  2. WAF / Firewall memblokir IP scanner\n"
                    f"  3. Connection Timeout / SSL Handshake failure\n\n"
                    f"---\n\n"
                    f"## 3. PANDUAN VERIFIKASI MANUAL & POC\n\n"
                    f"Lakukan pengujian manual dari terminal Anda:\n"
                    f"```bash\n"
                    f"curl -vIk \"{vuln.endpoint}\"\n"
                    f"```\n\n"
                    f"**Contoh Template PoC ({vuln.type}):**\n"
                    f"[Berikan contoh template PoC atau curl command untuk validasi manual jenis celah ini]\n\n"
                    f"---\n\n"
                    f"## 4. REKOMENDASI PERBAIKAN & STATUS AKHIR\n\n"
                    f"### Rekomendasi Remediasi Standar\n"
                    f"[Berikan panduan perbaikan umum untuk kerentanan {vuln.type}]\n\n"
                    f"### Status Akhir (Final Verdict)\n"
                    f"- **Verdict:** INCONCLUSIVE\n"
                    f"- **Confidence:** 0%\n"
                    f"- **Catatan:** Jangan laporkan temuan ini ke tim triage sebelum bukti koneksi dan response berhasil didapatkan secara manual.\n\n"
                    f"JANGAN sebut nama SOP/framework internal apapun."
                )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    target_ai = "auto"
    response = llm_providers.call_llm(messages, target_ai=target_ai)
    
    if action_clean == "deep_validate":
        response["fetch_status"] = locals().get("fetch_status", "unknown")
        
    return response
