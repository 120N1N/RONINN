import React from 'react';

const AIBrainStatusBadge = ({ hasApiKey, aiBrainEnabled }) => {
  if (!hasApiKey) {
    return (
      <div className="badge badge-neutral" style={{ padding: '0.4rem 0.8rem', borderRadius: '4px', backgroundColor: '#374151', color: '#d1d5db', fontSize: '0.8rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem' }}>
        <span>⚪</span> AI-BRAIN: Tidak Aktif (API Key belum ditambahkan)
      </div>
    );
  }
  
  if (!aiBrainEnabled) {
    return (
      <div className="badge badge-warning" style={{ padding: '0.4rem 0.8rem', borderRadius: '4px', backgroundColor: '#f59e0b20', color: '#f59e0b', fontSize: '0.8rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', border: '1px solid #f59e0b' }}>
        <span>🟡</span> AI-BRAIN: Tidak Aktif (Nonaktifkan di Settings)
      </div>
    );
  }
  
  return (
    <div className="badge badge-success" style={{ padding: '0.4rem 0.8rem', borderRadius: '4px', backgroundColor: '#dc262620', color: '#ef4444', fontSize: '0.8rem', display: 'inline-flex', alignItems: 'center', gap: '0.5rem', border: '1px solid #dc2626', fontWeight: 'bold' }}>
      <span>🧠</span> AI-BRAIN: Aktif
    </div>
  );
};

export default AIBrainStatusBadge;
