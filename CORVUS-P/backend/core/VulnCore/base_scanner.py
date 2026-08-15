from typing import List, Dict, Any

class BaseVulnScanner:
    """
    Kelas Induk (Base Class) untuk semua modul kerentanan OWASP yang ada di dalam VulnCore.
    Semua modul baru harus memiliki turunan (inherit) dari kelas ini.
    """
    OWASP_CODE = "UNKNOWN"
    CATEGORY_NAME = "Uncategorized Vulnerability"
    
    @classmethod
    def scan(cls, target_url: str, discovered_endpoints: List[str], scan_context: Dict[str, Any]) -> List[Dict]:
        """
        Setiap modul (seperti Injection, BOLA, Security Misconfig) wajib 
        meng-override fungsi ini untuk mengembalikan daftar kerentanan yang ditemukan.
        
        Args:
            target_url: URL Utama (induk)
            discovered_endpoints: Rute hasil recon (crawling/discovery)
            scan_context: Data pelengkap (seperti mode scan, API Keys jika butuh AI, dll)
            
        Returns:
            List of Dictionary (Kumpulan JSON findings standar Corvus)
        """
        raise NotImplementedError("Modul belum diimplementasikan dengan antarmuka BaseVulnScanner.")
