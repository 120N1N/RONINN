# backend/core/risk.py
def calculate_risk(severity: str, confidence: float) -> float:
    """Basic risk scoring algorithm."""
    base_scores = {
        "CRITICAL": 10.0,
        "HIGH": 8.5,
        "MEDIUM": 6.0,
        "LOW": 3.0,
        "INFO": 0.0
    }
    score = base_scores.get(severity.upper(), 1.0)
    return round(score * confidence, 2)
