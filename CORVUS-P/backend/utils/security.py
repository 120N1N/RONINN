import ipaddress
import socket
from urllib.parse import urlparse

class SecurityValidator:
    @staticmethod
    def validate_target(url: str, is_admin: bool = False) -> str:
        """
        Validates a URL to prevent Server-Side Request Forgery (SSRF) and Command Injection.
        Blocks requests to private, loopback, link-local, and multicast IPs, UNLESS the user is an admin.
        """
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"http://{url}"
            
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            
            if not hostname:
                raise ValueError("Invalid URL format.")
                
            # Basic Command Injection prevention on the URL level
            dangerous_chars = [';', '|', '&', '$', '>', '<', '`', '\\']
            if any(char in url for char in dangerous_chars):
                raise ValueError("Dangerous characters detected in URL.")

            # Resolve DNS to check the actual underlying IP
            try:
                ip_str = socket.gethostbyname(hostname)
            except socket.gaierror:
                raise ValueError(f"Could not resolve hostname: {hostname}")
                
            ip = ipaddress.ip_address(ip_str)
            
            # Block internal network pivoting (SSRF) unless admin
            if not is_admin and (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast):
                raise ValueError(f"SSRF Blocked: Target '{hostname}' resolves to a private or reserved IP address ({ip_str}). Scanning internal networks is strictly prohibited for standard users.")
                
            return url
            
        except ValueError as ve:
            raise ve
        except Exception as e:
            raise ValueError(f"Failed to validate target security: {str(e)}")
