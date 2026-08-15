class RolloutRunner:
    """
    [Lapis Khusus Rollout Transisi]
    Menangkap dan merekam percakapan penuh AI (Trajectories) saat ia mencoba scan.
    Jika terjadi kegagalan/Refusal, RolloutRunner inilah yang menyerahkan lognya ke Reflection Critique.
    """
    
    @classmethod
    def capture_trajectory(cls, scan_id: str, raw_response: str, success: bool):
        # Merekam status eksekusi: BERHASIL atau GAGAL (Refusal)
        # Trajectories disimpan di memori sementara (RAM) sebelum dilempar ke Evaluator
        status = "SUCCESS" if success else "FAILED"
        print(f"    [Corvence-Rollout] 🖭 Merekam jejak taktis pemindaian {scan_id} (Status: {status})")
        
        # (TODO: Menyimpan ke file .jsonl untuk Dataset Training lokal)
        return {"scan_id": scan_id, "status": status, "trajectory_len": len(raw_response)}
