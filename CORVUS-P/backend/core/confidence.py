import os
import joblib
import logging
import math
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from backend.db import models

logger = logging.getLogger("corvus.confidence")

def get_active_rf_model(db: Optional[Session] = None) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
    """
    Retrieves the active Random Forest model from the database or filesystem.
    Returns (model_object, metadata_dict).
    """
    model_obj = None
    meta = {}

    # 1. Check database for active or latest model record
    if db is not None:
        try:
            # Check for explicitly marked active model first
            db_model = db.query(models.TrainedModel).filter(models.TrainedModel.is_active == True).first()
            if not db_model:
                # Fallback to latest trained model
                db_model = db.query(models.TrainedModel).order_by(models.TrainedModel.created_at.desc()).first()
            
            if db_model and db_model.model_path and os.path.exists(db_model.model_path):
                model_obj = joblib.load(db_model.model_path)
                meta = {
                    "id": db_model.id,
                    "name": db_model.name,
                    "model_path": db_model.model_path,
                    "created_at": db_model.created_at.isoformat() if db_model.created_at else None,
                    "source": "database",
                    "metrics": db_model.metrics
                }
                return model_obj, meta
        except Exception as e:
            logger.warning(f"Could not load model from database record: {e}")

    # 2. Filesystem fallback: scan models/ directory
    models_dir = "models"
    if os.path.exists(models_dir):
        pkl_files = [f for f in os.listdir(models_dir) if f.endswith('.pkl')]
        if pkl_files:
            latest_file = sorted(pkl_files)[-1]
            full_path = os.path.join(models_dir, latest_file)
            try:
                model_obj = joblib.load(full_path)
                meta = {
                    "id": None,
                    "name": f"Random Forest ({latest_file})",
                    "model_path": full_path,
                    "created_at": datetime.fromtimestamp(os.path.getmtime(full_path)).isoformat(),
                    "source": "filesystem",
                    "metrics": None
                }
                return model_obj, meta
            except Exception as e:
                logger.error(f"Failed loading model from disk {full_path}: {e}")

    return None, None


def _calculate_entropy(data_str: str) -> float:
    if not data_str:
        return 0.0
    s = str(data_str)
    prob = [float(s.count(c)) / len(s) for c in dict.fromkeys(list(s))]
    return -sum(p * math.log(p, 2) for p in prob)


def extract_finding_features(finding: Dict[str, Any], feature_names: List[str]) -> Dict[str, float]:
    """
    Dynamically maps vulnerability finding fields to the exact features required by the Random Forest model.
    """
    row = {}
    for feat in feature_names:
        feat_lower = feat.lower()

        # Severity Score
        if feat_lower in ['severity_score', 'severity', 'cvss']:
            cvss = finding.get('cvss')
            if cvss is not None:
                try:
                    row[feat] = float(cvss)
                    continue
                except (ValueError, TypeError):
                    pass
            sev = str(finding.get('severity', '')).upper()
            if 'CRITICAL' in sev:
                row[feat] = 9.0
            elif 'HIGH' in sev:
                row[feat] = 7.5
            elif 'MEDIUM' in sev:
                row[feat] = 5.5
            elif 'LOW' in sev:
                row[feat] = 3.0
            else:
                row[feat] = 1.0

        # Scanner Tool Source
        elif feat_lower in ['tool_source', 'source', 'tool', 'scanner']:
            src = str(finding.get('source', '')).strip().lower()
            row[feat] = float(abs(hash(src)) % 100) if src else 0.0

        # OWASP Category
        elif feat_lower in ['owasp_category', 'category', 'owasp_code']:
            cat = str(finding.get('owasp_code') or finding.get('category', '')).strip().lower()
            row[feat] = float(abs(hash(cat)) % 100) if cat else 0.0

        # Endpoint Depth
        elif feat_lower == 'endpoint_depth':
            ep = str(finding.get('endpoint') or finding.get('location') or '')
            parts = [p for p in ep.split('?')[0].split('/') if p and not p.startswith('http') and not p.endswith(':')]
            row[feat] = float(len(parts))

        # Has Payload / Evidence Flag
        elif feat_lower == 'has_payload':
            has_p = 1.0 if (finding.get('payload') or finding.get('evidence')) else 0.0
            row[feat] = has_p

        # Response Length
        elif feat_lower in ['response_length', 'response_size']:
            resp_size = finding.get('caido_response_size_mean')
            if resp_size is not None:
                try:
                    row[feat] = float(resp_size)
                    continue
                except (ValueError, TypeError):
                    pass
            evidence_str = str(finding.get('evidence', '') or finding.get('description', ''))
            row[feat] = float(len(evidence_str)) if evidence_str else 1000.0

        # Caido Request Verb
        elif feat_lower == 'caido_request_verb':
            verb = str(finding.get('caido_request_verb', 'GET')).upper()
            verb_map = {'GET': 1.0, 'POST': 2.0, 'PUT': 3.0, 'DELETE': 4.0, 'PATCH': 5.0, 'OPTIONS': 6.0, 'HEAD': 7.0}
            row[feat] = verb_map.get(verb, 1.0)

        # Caido Parameter Count
        elif feat_lower == 'caido_param_count':
            val = finding.get('caido_param_count', 0)
            try:
                row[feat] = float(val)
            except (ValueError, TypeError):
                row[feat] = 0.0

        # Caido Auth Headers
        elif feat_lower == 'caido_auth_headers_present':
            val = finding.get('caido_auth_headers_present', 0)
            try:
                row[feat] = float(val)
            except (ValueError, TypeError):
                row[feat] = 0.0

        # Caido Content Type
        elif feat_lower == 'caido_content_type':
            ct = str(finding.get('caido_content_type', '')).strip().lower()
            row[feat] = float(abs(hash(ct)) % 100) if ct else 0.0

        # Caido Response Size Mean
        elif feat_lower == 'caido_response_size_mean':
            val = finding.get('caido_response_size_mean', 1000.0)
            try:
                row[feat] = float(val)
            except (ValueError, TypeError):
                row[feat] = 1000.0

        # Caido Response Size Std
        elif feat_lower == 'caido_response_size_std':
            val = finding.get('caido_response_size_std', 0.0)
            try:
                row[feat] = float(val)
            except (ValueError, TypeError):
                row[feat] = 0.0

        # Caido Status Codes Seen
        elif feat_lower == 'caido_status_codes_seen':
            sc = finding.get('caido_status_codes_seen', 200)
            if isinstance(sc, list) and len(sc) > 0:
                try:
                    row[feat] = float(sc[0])
                except (ValueError, TypeError):
                    row[feat] = 200.0
            else:
                try:
                    row[feat] = float(sc)
                except (ValueError, TypeError):
                    row[feat] = 200.0

        # Caido Endpoint Depth
        elif feat_lower == 'caido_endpoint_depth':
            val = finding.get('caido_endpoint_depth', 1)
            try:
                row[feat] = float(val)
            except (ValueError, TypeError):
                row[feat] = 1.0

        # Heuristic 1: Entropy Payload
        elif feat_lower == 'entropy_payload':
            text = str(finding.get('payload') or finding.get('evidence', ''))
            row[feat] = _calculate_entropy(text)

        # Heuristic 2: Length Ratio
        elif feat_lower == 'length_ratio':
            resp_size = float(finding.get('caido_response_size_mean', 1000.0) or 1000.0)
            row[feat] = resp_size / 1000.0

        # Heuristic 3: Status Code Shift
        elif feat_lower == 'status_code_shift':
            sc = finding.get('caido_status_codes_seen', 200)
            code_str = str(sc[0] if isinstance(sc, list) and sc else sc)
            row[feat] = 1.0 if code_str in ['500', '403', '401', '406', '502'] else 0.0

        # Heuristic 4: DOM Reflection Flag
        elif feat_lower == 'dom_reflection_flag':
            payload = str(finding.get('payload', '') or '').strip()
            resp = str(finding.get('evidence', '') or '').strip()
            row[feat] = 1.0 if (len(payload) > 2 and payload in resp) else 0.0

        # Heuristic 5: Response Time Delta
        elif feat_lower == 'response_time_delta':
            row[feat] = 0.0

        # Heuristic 6: Pattern Regex Severity
        elif feat_lower == 'pattern_regex_severity':
            desc = str(finding.get('description', '') or finding.get('evidence', '')).lower()
            matches = sum(1 for kw in ['syntax error', 'sql syntax', 'mysql', 'warning', 'database', 'fatal'] if kw in desc)
            row[feat] = float(matches)

        # Heuristic 7: Multi Tool Consensus
        elif feat_lower == 'multi_tool_consensus':
            src = str(finding.get('source', ''))
            count = len(src.split(',')) if ',' in src else (2 if '/' in src else 1)
            row[feat] = float(count)

        # Generic Fallback
        else:
            val = finding.get(feat)
            if val is not None:
                try:
                    row[feat] = float(val)
                except (ValueError, TypeError):
                    row[feat] = float(abs(hash(str(val))) % 100)
            else:
                row[feat] = 0.0

    return row


def analyze_findings(
    raw_findings: List[Dict[str, Any]],
    model: Any,
    model_meta: Dict[str, Any],
    high_threshold: float = 80.0,
    medium_threshold: float = 50.0
) -> Dict[str, Any]:
    """
    Computes Confidence Scores for a list of findings using the loaded Random Forest model.
    """
    if not raw_findings:
        return {
            "total_findings": 0,
            "avg_confidence": 0.0,
            "high_confidence_count": 0,
            "medium_confidence_count": 0,
            "low_confidence_count": 0,
            "thresholds": {"high": high_threshold, "medium": medium_threshold},
            "model_info": model_meta,
            "analyzed_at": datetime.utcnow().isoformat(),
            "findings": []
        }

    # Extract model feature columns in exact required order
    feature_names = list(getattr(model, 'feature_names_in_', []))
    if not feature_names:
        # Fallback if model was trained without feature_names_in_
        feature_names = [
            'severity_score', 'tool_source', 'owasp_category', 'endpoint_depth',
            'has_payload', 'response_length', 'caido_request_verb', 'caido_param_count',
            'caido_auth_headers_present', 'caido_content_type', 'caido_response_size_mean',
            'caido_response_size_std', 'caido_status_codes_seen', 'caido_endpoint_depth'
        ]

    rows = [extract_finding_features(f, feature_names) for f in raw_findings]
    feature_df = pd.DataFrame(rows, columns=feature_names)

    # Predict Probabilities
    try:
        probs = model.predict_proba(feature_df)
        preds = model.predict(feature_df)
    except Exception as e:
        logger.error(f"Error predicting probabilities with Random Forest model: {e}")
        raise ValueError(f"Random Forest inference failed: {str(e)}")

    has_class_1 = (probs.shape[1] > 1)
    analyzed_results = []
    confidence_values = []

    for idx, f in enumerate(raw_findings):
        # Probability of class 1 (valid vulnerability)
        if has_class_1:
            p_val = float(probs[idx][1])
        else:
            p_val = float(probs[idx][0])

        conf_pct = round(p_val * 100.0, 1)
        confidence_values.append(conf_pct)

        # Categorization based on configurable thresholds
        if conf_pct >= high_threshold:
            conf_level = "HIGH"
        elif conf_pct >= medium_threshold:
            conf_level = "MEDIUM"
        else:
            conf_level = "LOW"

        pred_raw = preds[idx]
        pred_label = "Valid Finding" if pred_raw == 1 or conf_pct >= 50.0 else "False Positive"

        analyzed_results.append({
            "id": f.get("id") or f"FIND-{idx+1:04d}",
            "name": f.get("name") or f.get("type") or "Vulnerability Finding",
            "target": f.get("_target") or f.get("target") or "Unknown Target",
            "scan_id": f.get("_scan_id") or f.get("scan_id"),
            "endpoint": f.get("endpoint") or f.get("location") or "N/A",
            "source": f.get("source") or "Automated Scanner",
            "severity": (f.get("severity") or "Low").capitalize(),
            "predicted_class": pred_label,
            "confidence_score": conf_pct,
            "confidence_level": conf_level,
            "cvss": f.get("cvss"),
            "owasp_code": f.get("owasp_code") or f.get("category")
        })

    avg_conf = round(float(np.mean(confidence_values)), 1) if confidence_values else 0.0
    high_count = sum(1 for s in confidence_values if s >= high_threshold)
    med_count = sum(1 for s in confidence_values if medium_threshold <= s < high_threshold)
    low_count = sum(1 for s in confidence_values if s < medium_threshold)

    return {
        "total_findings": len(analyzed_results),
        "avg_confidence": avg_conf,
        "high_confidence_count": high_count,
        "medium_confidence_count": med_count,
        "low_confidence_count": low_count,
        "thresholds": {"high": high_threshold, "medium": medium_threshold},
        "model_info": model_meta,
        "analyzed_at": datetime.utcnow().isoformat(),
        "findings": analyzed_results
    }
