import json
from pathlib import Path

class GlobalRepository:
    """
    Pengelola Penyimpanan Global Memory Pool (Cross-User Intelligence).
    Semua User (A, B, C) akan membaca & menyumbang ke file master ini.
    """
    GLOBAL_MEMORY_FILE = Path("AI-BRAIN/corvence/storage/global_corvence_memory.json")
    
    @classmethod
    def load(cls) -> dict:
        if not cls.GLOBAL_MEMORY_FILE.exists():
            return {
                "version": "1.0",
                "global_accuracy": 88.0, 
                "collective_rules": [
                    "General: Jika confidence score dibawah 0.70, tetapkan 'MANUAL_REVIEW_REQUIRED' (False Positive Prevention)."
                ],
                "evolution_log": []
            }
        with open(cls.GLOBAL_MEMORY_FILE, 'r') as f:
            return json.load(f)

    @classmethod
    def save(cls, data: dict):
        cls.GLOBAL_MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(cls.GLOBAL_MEMORY_FILE, 'w') as f:
            json.dump(data, f, indent=4)
