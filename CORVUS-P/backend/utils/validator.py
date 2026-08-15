# backend/utils/validator.py
import re
import socket
from backend.errors import ValidationError

def validate_target(target: str):
    """
    Validates target and blocks private IPs (Point #9, #26).
    """
    clean_target = target.lower().replace("https://", "").replace("http://", "").split("/")[0]
    
    try:
        ip = socket.gethostbyname(clean_target)
    except socket.gaierror:
        raise ValidationError(f"Could not resolve target: {target}")

    private_ips = [
        r"^127\.", r"^10\.", r"^172\.(1[6-9]|2[0-9]|3[0-1])\.", 
        r"^192\.168\.", r"^169\.254\.", r"^0\."
    ]
    
    for pattern in private_ips:
        if re.match(pattern, ip) or clean_target == "localhost":
            raise ValidationError(f"Restricted target: {target} (Internal/Private IP)")
            
    return clean_target
