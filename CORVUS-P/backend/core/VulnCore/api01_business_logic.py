import json
import uuid
from typing import List, Dict, Any, Optional
from backend.core.VulnCore.base_scanner import BaseVulnScanner
from backend.core.llm_providers import call_llm

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

        # Hanya ambil 20 endpoint terpenting untuk analisis efisiensi token
        important_keywords = ["api", "user", "admin", "checkout", "order", "profile", "cart", "pay", "auth", "secret"]
        filtered_endpoints = []
        for ep in discovered_endpoints:
            if any(k in ep.lower() for k in important_keywords):
                filtered_endpoints.append(ep)
        
        # Jika tidak ada yg menarik, ambil 10 endpoint pertama
        if not filtered_endpoints:
            filtered_endpoints = discovered_endpoints[:10]
        else:
            filtered_endpoints = filtered_endpoints[:20]

        try:
            decrypted_key = None
            prompt = cls._build_hunting_prompt(target_url, filtered_endpoints)
            messages = [
                {"role": "system", "content": "Anda adalah Senior Penetration Tester spesialis Business Logic Vulnerabilities (OWASP API Security)."},
                {"role": "user", "content": prompt}
            ]
            
            resp = call_llm(messages, target_ai="gemini")
            
            content = resp.get("result", "")
            return cls._parse_ai_findings(content, target_url)
        except Exception as e:
            print(f"    [VulnCore BusinessLogic] Error: {str(e)}")
            return []

    @classmethod
    def _build_hunting_prompt(cls, base_url: str, endpoints: List[str]) -> str:
        eps_str = "\n".join([f"- {ep}" for ep in endpoints])
        
        return f"""
Berikut adalah daftar endpoint/Rute API yang berhasil dipetakan dari target: {base_url}

{eps_str}

TUGAS ANDA:
Sebagai Hacker Top Tier, analisis daftar endpoint di atas. Temukan 1 hingga 3 titik yang paling rentan terhadap:
1. BOLA / IDOR (Broken Object Level Authorization - misal: mengakses ID pesanan orang lain).
2. BFLA (Broken Function Level Authorization - misal: endpoint admin yang terekspos).
3. Mass Assignment (misal: mengirim parameter `is_admin=true` pada endpoint update profile).

Bentuk hasil analisa dalam JSON Array baku, HANYA JSON tanpa teks lain!
Skema JSON:
[
  {{
    "type": "business_logic_flaw",
    "subtype": "[BOLA | BFLA | Mass Assignment]",
    "severity": "HIGH",
    "endpoint": "URL rute yang rentan",
    "description": "Jelaskan dengan skenario peretasan bagaimana celah ini berpotensi dieksploitasi menurut teori logika bisnis.",
    "remediation": "Cara memperbaikinya berdasarkan best practices OWASP."
  }}
]
"""

    @classmethod
    def _parse_ai_findings(cls, content: str, base_url: str) -> List[Dict]:
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
            for item in ai_data:
                finding = {
                    "id": f"COR-{uuid.uuid4().hex[:6].upper()}",
                    "name": f"Business Logic: {item.get('subtype', 'Anomaly')}",
                    "type": item.get('type', 'business_logic_flaw'),
                    "severity": item.get('severity', 'HIGH').upper(),
                    "endpoint": item.get('endpoint', base_url),
                    "location": item.get('endpoint', base_url),
                    "cvss": 7.5 if item.get('severity', 'HIGH').upper() == 'HIGH' else 5.5,
                    "description": item.get('description', 'Potensi kelemahan logika aplikasi terdeteksi oleh AI-Brain.'),
                    "remediation": item.get('remediation', 'Terapkan validasi dan RBAC (Role Based Access Control) yang ketat.'),
                    "points": ["AI-Brain Simulated Threat Modeling", "Potensi kerentanan pada alur proses bisnis."],
                    "source": "VulnCore-BusinessLogicAuditor"
                }
                findings.append(finding)
        except Exception:
            pass
            
        return findings
