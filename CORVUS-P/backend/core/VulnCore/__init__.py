import os
import importlib
import inspect
from typing import List, Dict, Any
from backend.core.VulnCore.base_scanner import BaseVulnScanner

class VulnManager:
    """
    Sistem Pengelola Plugin Terpusat (Plugin Manager).
    Secara dinamis mendeteksi semua file Python berformat `aXX_*.py` di folder ini,
    lalu memuat kelas yang mewarisi BaseVulnScanner secara otomatis!
    """
    
    @classmethod
    def run_all_modules(cls, target_url: str, discovered_endpoints: List[str], scan_context: Dict[str, Any]) -> List[Dict]:
        all_findings = []
        
        current_dir = os.path.dirname(__file__)
        
        # Load semua file secara dinamis
        for filename in os.listdir(current_dir):
            if filename.endswith(".py") and filename != "__init__.py" and filename != "base_scanner.py":
                module_name = filename[:-3]
                
                # Import module
                module = importlib.import_module(f"backend.core.VulnCore.{module_name}")
                
                # Cari kelas yang meng-inherit dari BaseVulnScanner
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseVulnScanner) and obj is not BaseVulnScanner:
                        try:
                            # Eksekusi Module!!
                            print(f"    [VulnCore] Menjalankan modul OWASP: {obj.OWASP_CODE} ({obj.CATEGORY_NAME})")
                            findings = obj.scan(target_url, discovered_endpoints, scan_context)
                            
                            # Standardisasi data sebelum disatukan
                            for f in findings:
                                f["owasp_code"] = obj.OWASP_CODE
                                f["category"] = obj.CATEGORY_NAME
                                f["source"] = f"VulnCore-Module-{obj.OWASP_CODE}"
                                
                            all_findings.extend(findings)
                        except Exception as e:
                            print(f"    [VulnCore] Gagal menjalankan modul {obj.OWASP_CODE}: {str(e)}")
                            
        return all_findings
