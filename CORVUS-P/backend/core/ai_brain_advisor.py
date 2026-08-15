import json
from typing import List, Dict, Optional
from .ai_brain import AIBrainLoader

class AIBrainAdvisor:
    """
    AI-BRAIN sebagai pre-scan advisor.
    Merekomendasikan tools & parameter berdasarkan workflow HunterFlowX.
    """
    
    @classmethod
    def get_available_tools(cls) -> List[Dict]:
        """
        Mengembalikan daftar tools yang tersedia di Corvus.
        """
        return [
            {
                "name": "subfinder",
                "description": "Subdomain discovery tool. Finds subdomains for a given domain.",
                "category": "recon",
                "risk_level": "low",
                "common_params": ["-d", "-o", "-silent"]
            },
            {
                "name": "nuclei",
                "description": "Template-based vulnerability scanner. Detects CVEs, misconfigurations, and OWASP Top 10.",
                "category": "vuln_scan",
                "risk_level": "medium",
                "common_params": ["-u", "-t", "-severity", "-tags"]
            },
            {
                "name": "dalfox",
                "description": "XSS scanner. Finds reflected, stored, and DOM-based XSS.",
                "category": "vuln_scan",
                "risk_level": "medium",
                "common_params": ["-u", "--skip-bav", "--custom-payload"]
            },
            {
                "name": "sqlmap",
                "description": "SQL Injection detection and exploitation tool. HIGH RISK.",
                "category": "exploit",
                "risk_level": "high",
                "common_params": ["-u", "--batch", "--level", "--risk"]
            },
            {
                "name": "safe_checks",
                "description": "Non-destructive security header and configuration checks (CORS, CSP, HSTS, cookies).",
                "category": "vuln_scan",
                "risk_level": "low",
                "common_params": []
            }
        ]
    
    @classmethod
    def build_advisor_prompt(cls, target: str, scan_mode: str, target_info: Optional[Dict] = None) -> str:
        """
        Membangun prompt untuk meminta rekomendasi tools.
        """
        workflow_context = AIBrainLoader.load_workflow(target_info)
        agents = AIBrainLoader.load_agents()
        available_tools = cls.get_available_tools()
        
        prompt = f"{agents}\n\n## Alur Kerja HunterFlowX\n{workflow_context}\n\n"
        prompt += f"## Tools yang Tersedia di Corvus\n{json.dumps(available_tools, indent=2)}\n\n"
        prompt += "## Instruksi\n"
        prompt += "Anda adalah security analyst yang mengikuti SOP HunterFlowX.\n"
        prompt += "Berdasarkan target berikut, berikan rekomendasi:\n\n"
        prompt += "1. **recommended_tools**: Tools mana yang harus dijalankan\n"
        prompt += "2. **skip_tools**: Tools mana yang sebaiknya dilewati\n"
        prompt += "3. **tool_params**: Parameter spesifik untuk setiap tool\n"
        prompt += "4. **reasoning**: Alasan di balik rekomendasi\n"
        prompt += "5. **risk_level**: Tingkat risiko keseluruhan (low/medium/high)\n\n"
        prompt += f"Target: {target}\n"
        prompt += f"Mode Scan: {scan_mode}\n"
        prompt += f"Informasi Tambahan: {json.dumps(target_info) if target_info else 'Tidak ada'}\n\n"
        prompt += "Format respons HARUS JSON.\n"
        return prompt
