/**
 * Shared helper for vulnerability validation classification across CORVUS.
 * Combines AI-Brain HunterFlowX analyst verdict and Random Forest ML confidence score.
 */

export const isFindingTruePositive = (f) => {
    if (!f || typeof f !== 'object') return false;

    // 1. Explicit AI Brain validation verdict
    const aiVal = f.ai_brain_validation || f.ai_validation;
    if (aiVal && typeof aiVal.is_valid === 'boolean') {
        if (aiVal.is_valid === true) return true;
    }
    if (f.ai_brain_valid === true) return true;

    // 2. Random Forest Machine Learning classification
    const rf = f.rf_validation;
    if (rf && rf.predicted_class === 'Valid Finding') return true;

    // 3. Composite Confidence Score threshold (>= 50% = Valid / True Positive)
    const cs = Number(f.confidence_score ?? rf?.confidence_pct ?? ((aiVal?.confidence_score ?? 0) * 100));
    if (!isNaN(cs) && cs >= 50.0) return true;

    return false;
};

export const getFindingConfidenceScore = (f) => {
    if (!f || typeof f !== 'object') return 0;
    const rf = f.rf_validation;
    const aiVal = f.ai_brain_validation || f.ai_validation;
    const cs = f.confidence_score ?? rf?.confidence_pct ?? (aiVal?.confidence_score ? Math.round(aiVal.confidence_score * 100) : null);
    if (cs !== null && !isNaN(Number(cs))) {
        return Math.round(Number(cs));
    }
    return isFindingTruePositive(f) ? 85 : 25;
};
