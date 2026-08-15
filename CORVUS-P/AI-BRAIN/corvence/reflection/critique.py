import re

class PrivacyStripper:
    """
    [Lapis 1] Menganonimkan data target (domain, IP, API Key) 
    agar Memory Global tidak membocorkan rahasia pengguna A ke pengguna B.
    """
    
    @classmethod
    def strip(cls, failed_context: str) -> str:
        # Hapus Pola URL / Domain
        url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        cleaned = re.sub(url_pattern, '[REDACTED_URL]', failed_context)
        
        # Hapus IP Address
        ip_pattern = re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b')
        cleaned = re.sub(ip_pattern, '[REDACTED_IP]', cleaned)
        
        # Hapus Bearer/Token
        token_pattern = re.compile(r'Bearer\s+[A-Za-z0-9\-\._~\+/]+=*')
        cleaned = re.sub(token_pattern, 'Bearer [REDACTED_TOKEN]', cleaned)
        
        return cleaned

class ReflectionCritique:
    """
    Menganalisis alasan mengapa AI gagal (Refusal) tanpa membocorkan data target.
    """
    @classmethod
    def analyze_failure(cls, raw_failed_context: str) -> str:
        # Bersihkan data spesifik user (Collective Intelligence Privacy)
        safe_context = PrivacyStripper.strip(raw_failed_context)
        
        # [TODO: Implementasi LLM prompt untuk mencari 'akar masalah' kegagalan]
        return safe_context
