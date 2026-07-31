import requests
import hashlib
import logging

logger = logging.getLogger("corvus.existence_checker")

class ExistenceChecker:
    _cached_404_hash = None
    _base_url = None

    @staticmethod
    def get_page_hash(url: str) -> str:
        """Mendapatkan hash dari konten halaman untuk deteksi Soft-404."""
        try:
            resp = requests.get(url, timeout=5, allow_redirects=True, verify=False)
            # Ambil body saja, abaikan whitespace untuk stabilitas hash
            content = "".join(resp.text[:2000].split())
            return hashlib.md5(content.encode()).hexdigest()
        except Exception as e:
            logger.error(f"Error getting page hash for {url}: {e}")
            return ""

    @classmethod
    def setup_base(cls, base_url: str):
        """Setup hash pembanding menggunakan path yang pasti tidak ada."""
        cls._base_url = base_url.rstrip('/')
        # Gunakan path random yang hampir pasti 404/Soft-404
        cls._cached_404_hash = cls.get_page_hash(f"{cls._base_url}/corvus_non_existent_path_{hashlib.md5(base_url.encode()).hexdigest()[:8]}")
        print(f"    [ExistenceChecker] Baseline 404 hash: {cls._cached_404_hash}")

    @classmethod
    def is_really_vulnerable(cls, finding: dict) -> bool:
        """
        Validasi apakah temuan benar-benar valid menggunakan perbandingan hash konten
        dan verifikasi signature yang lebih ketat.
        """
        v_type = finding.get("type", "")
        location = finding.get("location", "")
        
        if not location:
            return True

        # Setup baseline jika belum ada
        if not cls._cached_404_hash and cls._base_url:
            cls.setup_base(cls._base_url)

        try:
            # 1. Cek Hash Konten (Deteksi Soft-404)
            current_hash = cls.get_page_hash(location)
            if cls._cached_404_hash and current_hash == cls._cached_404_hash:
                return False # Konten sama dengan halaman error, fix FP

            # 2. Re-fetch untuk validasi konten spesifik
            resp = requests.get(location, timeout=7, verify=False)
            if resp.status_code != 200:
                return False
            
            content = resp.text.lower()
            
            # 3. Validasi Berbasis Signature (Ketat)
            if v_type == "information_disclosure":
                # Path spesifik harus punya konten spesifik
                if ".env" in location:
                    signatures = ["db_password", "app_key", "aws_access_key", "secret_key", "database_url", "app_env", "app_debug"]
                    return any(sig in content for sig in signatures)
                if ".git" in location:
                    return "ref:" in content or "master" in content or "main" in content
                if "phpinfo" in location:
                    return "php version" in content or "system info" in content or "php.ini" in content
                if "robots.txt" in location:
                    return "user-agent:" in content or "disallow:" in content
                
                # Umum
                signatures = ["root:x:", "password=", "secret_key", "api_key"]
                return any(sig in content for sig in signatures)

            if v_type == "exposed_admin_panel":
                # Harus ada form login nyata
                has_input = "<input" in content and ("type=\"password\"" in content or "type='password'" in content)
                admin_sigs = ["login", "password", "username", "admin", "dashboard", "masuk", "kata sandi"]
                return has_input and any(sig in content for sig in admin_sigs)

            # 4. Validasi Pasif (Header) - Biasanya jarang FP
            if v_type in ["clickjacking", "missing_security_headers", "cookie_security", "dangerous_http_methods"]:
                return True

            return True

        except Exception as e:
            logger.error(f"Validation error for {location}: {e}")
            return False
