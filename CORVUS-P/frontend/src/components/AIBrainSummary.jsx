import React from 'react';

const AIBrainSummary = ({ findings }) => {
  const validatedCount = findings.filter(f => f.ai_brain_validation || f.ai_validation).length;
  const tpCount = findings.filter(f => {
      const val = f.ai_brain_validation || f.ai_validation;
      return val?.is_valid;
  }).length;
  const fpCount = findings.filter(f => {
      const val = f.ai_brain_validation || f.ai_validation;
      return val && !val.is_valid;
  }).length;
  
  const avgConfidence = findings
    .filter(f => f.ai_brain_validation || f.ai_validation)
    .reduce((sum, f) => {
        const val = f.ai_brain_validation || f.ai_validation;
        return sum + (val.confidence_score || 0);
    }, 0) / (validatedCount || 1);
  
  return (
    <div className="ai-brain-summary card" style={{ backgroundColor: '#1a1a1a', border: '1px solid #8b5cf6', borderRadius: '8px', padding: '1.5rem', marginBottom: '2rem' }}>
      <h3 style={{ margin: '0 0 1rem 0', color: '#e5e7eb', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        🧠 Ringkasan Validasi AI-BRAIN (HunterFlowX)
      </h3>
      <div className="stats-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem' }}>
        <div className="stat" style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#2a2a2a', borderRadius: '8px' }}>
          <span className="stat-value" style={{ fontSize: '1.75rem', fontWeight: 'bold', display: 'block', color: '#e5e7eb' }}>{validatedCount}</span>
          <span className="stat-label" style={{ fontSize: '0.8rem', color: '#9ca3af' }}>Temuan Tervalidasi</span>
        </div>
        <div className="stat" style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#10b98115', borderRadius: '8px' }}>
          <span className="stat-value text-success" style={{ fontSize: '1.75rem', fontWeight: 'bold', display: 'block', color: '#10b981' }}>{tpCount}</span>
          <span className="stat-label" style={{ fontSize: '0.8rem', color: '#10b981' }}>True Positive</span>
        </div>
        <div className="stat" style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#ef444415', borderRadius: '8px' }}>
          <span className="stat-value text-error" style={{ fontSize: '1.75rem', fontWeight: 'bold', display: 'block', color: '#ef4444' }}>{fpCount}</span>
          <span className="stat-label" style={{ fontSize: '0.8rem', color: '#ef4444' }}>False Positive Terdeteksi</span>
        </div>
        <div className="stat" style={{ textAlign: 'center', padding: '1rem', backgroundColor: '#8b5cf615', borderRadius: '8px' }}>
          <span className="stat-value" style={{ fontSize: '1.75rem', fontWeight: 'bold', display: 'block', color: '#8b5cf6' }}>{(avgConfidence * 100).toFixed(1)}%</span>
          <span className="stat-label" style={{ fontSize: '0.8rem', color: '#8b5cf6' }}>Rata-rata Confidence</span>
        </div>
      </div>
    </div>
  );
};

export default AIBrainSummary;
