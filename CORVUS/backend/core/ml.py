# backend/core/ml.py
from .risk import calculate_risk

def ml_risk_score(finding_data: dict) -> float:
    """
    ML-ready scoring engine. 
    Can be expanded with real models.
    """
    severity = finding_data.get("severity", "LOW")
    confidence = finding_data.get("confidence", 0.5)
    
    # Heuristic adjustment based on specific indicators
    bonus = 0.0
    if "api_key" in str(finding_data).lower():
        bonus += 1.0
        
    return min(10.0, calculate_risk(severity, confidence) + bonus)
