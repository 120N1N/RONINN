import React from 'react';

const AIBrainValidationCard = ({ finding }) => {
  const validation = finding.ai_brain_validation || finding.ai_validation;
  const caido = finding.caido_profile;
  
  if (!validation) return null;
  
  return (
    <div className="ai-brain-validation card p-4 mb-4" style={{ backgroundColor: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: '8px' }}>
      <h3 style={{ borderBottom: '1px solid #333', paddingBottom: '0.5rem', marginBottom: '1rem' }}>🧠 Validasi AI-BRAIN (HunterFlowX)</h3>
      
      {/* Status Validasi */}
      <div className={`validation-status ${validation.is_valid ? 'valid' : 'invalid'}`} style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1rem' }}>
        {validation.is_valid ? (
          <span className="badge" style={{ backgroundColor: '#10b98120', color: '#10b981', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>✅ True Positive</span>
        ) : (
          <span className="badge" style={{ backgroundColor: '#ef444420', color: '#ef4444', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>❌ False Positive</span>
        )}
        <span className="confidence" style={{ fontSize: '0.9rem', color: '#a3a3a3' }}>
          Confidence: {(validation.confidence_score * 100).toFixed(1)}%
        </span>
      </div>
      
      {/* Severity Adjustment */}
      {validation.adjusted_severity && (
        <div className="severity-adjustment" style={{ marginBottom: '1rem', fontSize: '0.9rem' }}>
          <span className="original-severity">
            Original: <strong style={{ color: '#fb8c00' }}>{finding.severity}</strong>
          </span>
          <span className="arrow" style={{ margin: '0 0.5rem' }}>→</span>
          <span className="adjusted-severity">
            Disarankan: <strong style={{ color: '#ef4444' }}>{validation.adjusted_severity.toUpperCase()}</strong>
          </span>
        </div>
      )}
      
      {/* Traffic Context (Caido) */}
      {caido && (
        <div className="caido-context" style={{ marginBottom: '1rem', padding: '1rem', backgroundColor: '#06b6d415', borderRadius: '4px' }}>
          <h4 style={{ margin: '0 0 0.5rem 0', color: '#06b6d4' }}>📊 Konteks Traffic (Caido CLI)</h4>
          <table className="caido-table" style={{ width: '100%', fontSize: '0.8rem', textAlign: 'left' }}>
            <tbody>
              <tr><td style={{ padding: '0.2rem 0' }}>Method</td><td>{caido.request_verb}</td></tr>
              <tr><td style={{ padding: '0.2rem 0' }}>Parameters</td><td>{caido.param_count}</td></tr>
              <tr><td style={{ padding: '0.2rem 0' }}>Auth Headers</td><td>{caido.auth_headers_present ? '✅' : '❌'}</td></tr>
              <tr><td style={{ padding: '0.2rem 0' }}>Content-Type</td><td>{caido.content_type}</td></tr>
              <tr><td style={{ padding: '0.2rem 0' }}>Avg Response Size</td><td>{caido.response_size_mean} bytes</td></tr>
              <tr><td style={{ padding: '0.2rem 0' }}>Response Variability</td><td>±{caido.response_size_std} bytes</td></tr>
              <tr><td style={{ padding: '0.2rem 0' }}>Status Codes</td><td>{caido.status_codes_seen?.join(', ')}</td></tr>
              <tr><td style={{ padding: '0.2rem 0' }}>Endpoint Depth</td><td>{caido.endpoint_depth}</td></tr>
            </tbody>
          </table>
        </div>
      )}
      
      {/* Reasoning */}
      <div className="reasoning" style={{ marginBottom: '1rem' }}>
        <h4 style={{ margin: '0 0 0.25rem 0', color: '#e5e7eb' }}>📝 Alasan (Reasoning)</h4>
        <p style={{ margin: '0', color: '#a3a3a3', fontSize: '0.9rem', lineHeight: '1.5' }}>{validation.reasoning}</p>
      </div>
      
      {/* Recommendation */}
      <div className="recommendation" style={{ marginBottom: '1rem' }}>
        <h4 style={{ margin: '0 0 0.25rem 0', color: '#e5e7eb' }}>🛡️ Rekomendasi Mitigasi</h4>
        <pre style={{ margin: '0', padding: '0.75rem', backgroundColor: '#111', borderRadius: '4px', color: '#a3a3a3', fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}>
          {validation.recommendation}
        </pre>
      </div>
      
      {/* Human-in-the-Loop Disclaimer */}
      <div className="disclaimer" style={{ fontSize: '0.8rem', color: '#f59e0b', fontStyle: 'italic', marginTop: '1rem', paddingTop: '1rem', borderTop: '1px solid #333' }}>
        ⚠️ Hasil ini bersifat asistif. Keputusan akhir tetap pada analis manusia.
      </div>
    </div>
  );
};

export default AIBrainValidationCard;
