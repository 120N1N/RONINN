import React from 'react';

const AIBrainRecommendation = ({ recommendation, onAccept, onModify }) => {
  if (!recommendation) return null;
  
  return (
    <div className="ai-brain-recommendation card pulse-border" style={{ backgroundColor: '#1a1a1a', border: '1px solid #8b5cf6', borderRadius: '8px', padding: '1.5rem', marginBottom: '1.5rem', boxShadow: '0 0 15px rgba(139, 92, 246, 0.1)' }}>
      <h3 style={{ margin: '0 0 1.5rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#e5e7eb' }}>
        🧠 Rekomendasi AI-BRAIN (HunterFlowX)
      </h3>
      
      <div className="recommendation-details" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <div className="tool-list">
          <h4 style={{ margin: '0 0 0.5rem 0', color: '#9ca3af' }}>Tools yang Direkomendasikan:</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {recommendation.recommended_tools?.map(tool => (
              <span key={tool} className="badge" style={{ backgroundColor: '#10b98120', color: '#10b981', padding: '0.25rem 0.75rem', borderRadius: '4px', fontSize: '0.85rem', fontWeight: '500' }}>{tool}</span>
            ))}
          </div>
        </div>
        
        <div className="tool-list">
          <h4 style={{ margin: '0 0 0.5rem 0', color: '#9ca3af' }}>Tools yang Dilewati:</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {recommendation.skip_tools?.map(tool => (
              <span key={tool} className="badge" style={{ backgroundColor: '#f59e0b20', color: '#f59e0b', padding: '0.25rem 0.75rem', borderRadius: '4px', fontSize: '0.85rem', fontWeight: '500' }}>{tool}</span>
            ))}
          </div>
        </div>
        
        <div className="reasoning" style={{ backgroundColor: '#2a2a2a', padding: '1rem', borderRadius: '6px' }}>
          <h4 style={{ margin: '0 0 0.5rem 0', color: '#e5e7eb' }}>Alasan:</h4>
          <p style={{ margin: 0, color: '#a3a3a3', fontSize: '0.9rem', lineHeight: '1.5' }}>{recommendation.reasoning}</p>
        </div>
        
        <div className="risk-level" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <h4 style={{ margin: 0, color: '#9ca3af' }}>Tingkat Risiko:</h4>
          <span className={`badge`} style={{ 
            backgroundColor: recommendation.risk_level?.toLowerCase() === 'high' ? '#ef444420' : recommendation.risk_level?.toLowerCase() === 'medium' ? '#f59e0b20' : '#10b98120', 
            color: recommendation.risk_level?.toLowerCase() === 'high' ? '#ef4444' : recommendation.risk_level?.toLowerCase() === 'medium' ? '#f59e0b' : '#10b981', 
            padding: '0.25rem 0.75rem', borderRadius: '4px', fontSize: '0.85rem', fontWeight: 'bold', textTransform: 'uppercase' 
          }}>
            {recommendation.risk_level}
          </span>
        </div>
      </div>
      
      <div className="actions" style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem', paddingTop: '1.5rem', borderTop: '1px solid #333' }}>
        <button onClick={onAccept} className="btn" style={{ backgroundColor: '#8b5cf6', color: 'white', padding: '0.5rem 1rem', borderRadius: '4px', border: 'none', cursor: 'pointer', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          ✅ Gunakan Rekomendasi Ini
        </button>
        <button onClick={onModify} className="btn" style={{ backgroundColor: '#374151', color: 'white', padding: '0.5rem 1rem', borderRadius: '4px', border: 'none', cursor: 'pointer', fontWeight: '500', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          ✏️ Modifikasi Manual
        </button>
      </div>
    </div>
  );
};

export default AIBrainRecommendation;
