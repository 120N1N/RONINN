import logging
import os
import joblib
import warnings
from backend.core.risk import calculate_risk

warnings.filterwarnings('ignore') # Mengabaikan warning Scikit-learn
logger = logging.getLogger("corvus.ml")

class MLEngine:
    @staticmethod
    def calculate_confidence_score(p_rf: float, s_tool: float, v_dom: int) -> float:
        """
        Phase 2: Real Confidence Score Engine
        Berdasarkan Bab 4: Confidence Score = (0.50 * P_RF) + (0.30 * S_tool) + (0.20 * V_DOM)
        
        Args:
            p_rf (float): Probabilitas RF (0.0 - 1.0)
            s_tool (float): Bobot konsensus Multi-tools (0.0 - 1.0)
            v_dom (int): Validasi Playwright DOM (0 atau 1)
        """
        score = (0.50 * p_rf) + (0.30 * s_tool) + (0.20 * v_dom)
        return round(score, 4)

    @staticmethod
    def load_active_model():
        """Memuat model Random Forest (.pkl) terbaru dari direktori models."""
        models_dir = "models"
        if not os.path.exists(models_dir):
            return None
        
        pkl_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
        if not pkl_files:
            return None
            
        # Mengambil model terakhir/terbaru
        latest_model = sorted(pkl_files)[-1]
        try:
            return joblib.load(os.path.join(models_dir, latest_model))
        except Exception as e:
            logger.error(f"Gagal memuat model RF {latest_model}: {e}")
            return None

def ml_risk_score(finding_data: dict) -> float:
    """
    Fungsi wrapper legacy agar sistem lama tidak error.
    Menerapkan sistem skor dinamis.
    """
    severity = finding_data.get("severity", "LOW")
    confidence = finding_data.get("confidence", 0.5)
    return calculate_risk(severity, confidence)
