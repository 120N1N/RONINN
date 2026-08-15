import random
from ..storage.repository import GlobalRepository

class ValidationGate:
    """
    [Lapis 3] Menjaga Monotonic Evaluator (Performa Hanya Boleh Naik).
    Mengeksekusi candidate rule dari Optimizer pada Global Benchmark.
    """
    
    @classmethod
    def evaluate_and_commit(cls, candidate_rule: str, context: str) -> bool:
        memory = GlobalRepository.load()
        current_score = memory.get("global_accuracy", 0.0)
        current_version = memory.get("version", "1.0")
        
        # [Simulasi: Pengujian Benchmark 100 Payload pada LLM As-A-Judge]
        score_delta = random.uniform(-1.5, 4.5) 
        new_score = round(current_score + score_delta, 2)
        
        # THE MONOTONIC GATE
        if new_score > current_score:
            v_major, v_minor = current_version.split(".")
            new_version = f"{v_major}.{int(v_minor) + 1}"
            
            memory["version"] = new_version
            memory["global_accuracy"] = new_score
            memory["collective_rules"].append(candidate_rule)
            
            log_msg = f"[PROMOTED v{new_version}] Global Acc: {new_score}% (+{round(score_delta, 2)}%). Konteks Abstrak: {context[:40]}..."
            memory["evolution_log"].append(log_msg)
            
            GlobalRepository.save(memory)
            print(f"    [Corvence-Gate] 📈 RULE DI SAHKAN SECARA GLOBAL! Akurasi Sistem Naik ke {new_score}%")
            return True
        else:
            print(f"    [Corvence-Gate] 🛑 REGRESI TERDETEKSI (Skor Turun). Kandidat dibuang untuk melindungi pool global.")
            return False
