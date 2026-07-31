import os
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

# Automatically resolve or generate dynamic encryption key
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    ENCRYPTION_KEY = Fernet.generate_key().decode()
    env_path = ".env"
    try:
        # Append dynamically generated key to .env for persistence across server cycles
        if os.path.exists(env_path):
            with open(env_path, "a") as f:
                f.write(f"\nENCRYPTION_KEY={ENCRYPTION_KEY}\n")
        else:
            with open(env_path, "w") as f:
                f.write(f"ENCRYPTION_KEY={ENCRYPTION_KEY}\n")
    except Exception:
        pass

# Force ensure key is set in environment so child processes read it too
os.environ["ENCRYPTION_KEY"] = ENCRYPTION_KEY
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def encrypt_api_key(key: str) -> str:
    """Encrypt plain text API key to Fernet encrypted cipher token"""
    if not key:
        return ""
    return cipher_suite.encrypt(key.encode()).decode()

def decrypt_api_key(encrypted: str) -> str:
    """Decrypt Fernet encrypted token back to plain text key"""
    if not encrypted:
        return ""
    return cipher_suite.decrypt(encrypted.encode()).decode()
