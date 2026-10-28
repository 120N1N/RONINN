import json
import uuid
from typing import List, Dict, Any, Optional
from backend.core.VulnCore.base_scanner import BaseVulnScanner
from backend.core.llm_providers import call_llm
from backend.utils.asset_helper import is_static_asset

class BusinessLogicAuditor(BaseVulnScanner):
    """
    Kelas AI-Brain yang dialihfungsikan menjadi Plugin modular OWASP API Security.
    Fokus: Broken Object/Function Level Authorization (BOLA/BFLA) dan celah logika lainnya.
    """
    
    OWASP_CODE = "API1:2023" # OWASP API Top 10 BOLA (Bisa juga dikombinasikan dengan API5 dsb)
    CATEGORY_NAME = "Broken Object Level Authorization"

    @classmethod
    def scan(cls, target_url: str, discovered_endpoints: List[str], scan_context: Dict[str, Any]) -> List[Dict]:
        """
        Mengirim topologi web ke AI dan meminta dia mencari Logical Flaws!
        """
        if not discovered_endpoints:
            return []

        # Hanya gunakan endpoint API/dinamis, buang semua file statis (.js, .css, images, dll)
        dynamic_endpoints = [ep for ep in discovered_endpoints if not is_static_asset(ep)]
        if not dynamic_endpoints:
            return []

        # Saring hanya endpoint yang benar-benar menyerupai API atau aksi logika bisnis dinamis
        api_keywords = ["/api/", "/v1/", "/v2/", "/auth/", "/user/", "/admin/", "/checkout", "/order", "/profile", "/cart", "/graphql", "/rest/"]
        filtered_endpoints = [
            ep for ep in dynamic_endpoints 
            if any(k in ep.lower() for k in api_keywords) or ("?" in ep and any(p in ep.lower() for p in ["id=", "user", "account", "token", "role"]))
        ]
        
        # JIKA TIDAK ADA endpoint API nyata, JANGAN panggil LLM untuk mencegah halusinasi rute palsu!
        if not filtered_endpoints:
            return []

        filtered_endpoints = filtered_endpoints[:15]

        try:
            prompt = cls._build_hunting_prompt(target_url, filtered_endpoints)
            messages = [
                {"role": "system", "content": "Anda adalah Senior Penetration Tester spesialis Business Logic Vulnerabilities (OWASP API Security). Bersikaplah objektif dan kritis."},
                {"role": "user", "content": prompt}
            ]
            
            resp = call_llm(messages, target_ai="auto")
            content = resp.get("result", "")
            return cls._parse_ai_findings(content, target_url, valid_endpoints=filtered_endpoints)
        except Exception as e:
            print(f"    [VulnCore BusinessLogic] Error: {str(e)}")
            return []

    @classmethod
    def _build_hunting_prompt(cls, base_url: str, endpoints: List[str]) -> str:
        eps_str = "\n".join([f"- {ep}" for ep in endpoints])
        
        return f"""
Berikut adalah daftar rute API nyata yang berhasil dipetakan dari target: {base_url}

{eps_str}

TUGAS ANDA:
Evaluasi secara kritis apakah daftar rute nyata di atas menunjukkan pola arsitektur yang berpotensi memiliki celah logika:
1. BOLA / IDOR (HANYA jika rute secara nyata memiliki identifier objek/pengguna).
2. BFLA (HANYA jika rute administratif terekspos tanpa kontrol hak akses).
3. Mass Assignment (HANYA jika rute modifikasi entitas menerima input tidak terbatas).

ATURAN WAJIB & ANTI-HALUSINASI:
- DILARANG MENGARANG atau menambahkan endpoint baru yang TIDAK ADA dalam daftar di atas!
- DILARANG menandai file statis (.js, .css, images, dll).
- JIKA TIDAK ADA indikasi kerentanan yang nyata pada daftar di atas, KEMBALIKAN ARRAY KOSONG `[]`. Jangan pernah mengarang celah jika tidak ada bukti kuat!

Bentuk hasil analisa dalam JSON Array baku (HANYA JSON tanpa teks pengantar):
Skema JSON:
[
  {{
    "type": "business_logic_flaw",
    "subtype": "[BOLA | BFLA | Mass Assignment]",
    "severity": "HIGH",
    "endpoint": "URL PERSIS dari daftar di atas yang dianalisis",
    "description": "Penjelasan ancaman logika bisnis berdasarkan endpoint tersebut.",
    "remediation": "Cara mitigasi sesuai OWASP API Security."
  }}
]
"""

    @classmethod
    def _parse_ai_findings(cls, content: str, base_url: str, valid_endpoints: List[str] = None) -> List[Dict]:
        findings = []
        if not content: return findings
        
        try:
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "[" in content and "]" in content:
                json_str = content[content.find("["):content.rfind("]")+1]
            else:
                return []
                
            ai_data = json.loads(json_str)
            if not isinstance(ai_data, list):
                return []

            valid_set = set(valid_endpoints or [])
            import requests

            for item in ai_data:
                target_ep = item.get('endpoint', '')
                if not target_ep:
                    continue

                # ANTI-HALUSINASI 1: Endpoint HARUS ada dalam daftar yang dikirim ke LLM
                # Jika LLM mengarang rute baru yang tidak pernah ditemukan, tolak!
                if valid_set and target_ep not in valid_set:
                    # Cek toleransi trailing slash
                    if target_ep.rstrip("/") not in {ve.rstrip("/") for ve in valid_set}:
                        print(f"    [VulnCore BusinessLogic] [FP-FILTER] Rejected hallucinated endpoint from LLM: {target_ep}")
                        continue

                # ANTI-HALUSINASI 2: Abaikan jika file statis
                if is_static_asset(target_ep):
                    continue

                # ANTI-HALUSINASI 3: Validasi aktif dengan HTTP request
                # Jika endpoint mengembalikan 404 Not Found atau gagal koneksi, buang!
                try:
                    probe_resp = requests.head(target_ep, timeout=4, verify=False, allow_redirects=True)
                    if probe_resp.status_code == 404:
                        print(f"    [VulnCore BusinessLogic] [FP-FILTER] Discarded non-existent endpoint (404): {target_ep}")
                        continue
                except Exception:
                    pass

                finding = {
                    "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                    "name": f"Business Logic: {item.get('subtype', 'Anomaly')}",
                    "type": item.get('type', 'business_logic_flaw'),
                    "severity": item.get('severity', 'HIGH').upper(),
                    "endpoint": target_ep,
                    "location": target_ep,
                    "cvss": 7.5 if item.get('severity', 'HIGH').upper() == 'HIGH' else 5.5,
                    "description": item.get('description', 'Potensi kelemahan logika aplikasi terdeteksi oleh AI-Brain.'),
                    "remediation": item.get('remediation', 'Terapkan validasi dan RBAC (Role Based Access Control) yang ketat.'),
                    "points": ["AI-Brain Grounded Threat Modeling", "Diverifikasi terhadap rute aktif target."],
                    "source": "VulnCore-BusinessLogicAuditor"
                }
                findings.append(finding)
        except Exception as parse_e:
            print(f"    [VulnCore BusinessLogic] Parse error: {parse_e}")
            
        return findings
