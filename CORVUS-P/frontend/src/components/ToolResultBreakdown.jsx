import React, { useState } from 'react';
import { isFindingTruePositive, getFindingConfidenceScore } from '../utils/findingHelper';

const ToolResultBreakdown = ({ findings, caidoProfile }) => {
  // Kelompokkan temuan berdasarkan source tool
  const groupByTool = (findings) => {
    const grouped = {};
    findings.forEach(finding => {
      const tool = finding.source || 'unknown';
      if (!grouped[tool]) {
        grouped[tool] = [];
      }
      grouped[tool].push(finding);
    });
    return grouped;
  };

  const toolGroups = groupByTool(findings);

  // Konfigurasi tools
  const toolConfig = {
    subfinder: {
      name: 'Subfinder',
      icon: '🔍',
      color: '#3b82f6',
      description: 'Subdomain Discovery',
      category: 'Reconnaissance',
      riskLevel: 'Low',
    },
    nuclei: {
      name: 'Nuclei',
      icon: '🧬',
      color: '#8b5cf6',
      description: 'Template-Based Vulnerability Scanner',
      category: 'Vulnerability Scan',
      riskLevel: 'Medium',
    },
    dalfox: {
      name: 'Dalfox',
      icon: '🦊',
      color: '#f59e0b',
      description: 'XSS (Cross-Site Scripting) Scanner',
      category: 'Vulnerability Scan',
      riskLevel: 'Medium',
    },
    sqlmap: {
      name: 'SQLMap',
      icon: '💉',
      color: '#ef4444',
      description: 'SQL Injection Detection',
      category: 'Exploitation',
      riskLevel: 'High',
    },
    safe_checks: {
      name: 'Safe Checks',
      icon: '🛡️',
      color: '#10b981',
      description: 'Non-Destructive Security Checks',
      category: 'Configuration Audit',
      riskLevel: 'Low',
    },
    caido: {
      name: 'Caido CLI',
      icon: '📊',
      color: '#06b6d4',
      description: 'Traffic Intelligence Profiler',
      category: 'Traffic Analysis',
      riskLevel: 'Info',
    },
  };

  // Hitung statistik
  const getSeverityCount = (findings) => {
    const counts = { Critical: 0, High: 0, Medium: 0, Low: 0, Informational: 0 };
    findings.forEach(f => {
      const sev = f.severity || 'Informational';
      if (counts[sev] !== undefined) counts[sev]++;
    });
    return counts;
  };

  // Hitung AI-BRAIN & Random Forest validation stats
  const getAIValidationStats = (findings) => {
    const tp = findings.filter(isFindingTruePositive).length;
    const fp = findings.filter(f => !isFindingTruePositive(f)).length;
    return { total: findings.length, tp, fp };
  };

  return (
    <div className="tool-result-breakdown">
      <h2 className="section-title" style={{ marginTop: '2rem', marginBottom: '1rem', borderBottom: '1px solid #333', paddingBottom: '0.5rem' }}>🔬 Hasil Pemindaian Per Tools</h2>
      
      {/* Summary Cards */}
      <div className="tool-summary-grid">
        {Object.entries(toolGroups).map(([tool, toolFindings]) => {
          const config = toolConfig[tool] || {
            name: tool,
            icon: '🔧',
            color: '#6b7280',
            description: 'Unknown Tool',
            category: 'Other',
            riskLevel: 'Unknown',
          };
          const severityCounts = getSeverityCount(toolFindings);
          const aiStats = getAIValidationStats(toolFindings);
          const totalVulns = toolFindings.filter(f => f.type !== 'subdomain').length;
          const subdomains = toolFindings.filter(f => f.type === 'subdomain').length;

          return (
            <ToolSummaryCard
              key={tool}
              config={config}
              totalFindings={toolFindings.length}
              totalVulns={totalVulns}
              subdomains={subdomains}
              severityCounts={severityCounts}
              aiStats={aiStats}
              caidoProfile={tool === 'caido' ? caidoProfile : null}
            />
          );
        })}
      </div>

      {/* Detailed Breakdown Per Tool */}
      <div className="tool-detail-sections">
        {Object.entries(toolGroups).map(([tool, toolFindings]) => {
          const config = toolConfig[tool] || { name: tool, icon: '🔧', color: '#6b7280' };
          return (
            <ToolDetailSection
              key={tool}
              config={config}
              findings={toolFindings}
              caidoProfile={tool === 'caido' ? caidoProfile : null}
            />
          );
        })}
      </div>
    </div>
  );
};

// Sub-Komponen: Tool Summary Card
const ToolSummaryCard = ({ config, totalFindings, totalVulns, subdomains, severityCounts, aiStats, caidoProfile }) => {
  return (
    <div className="tool-summary-card" style={{ borderLeft: `4px solid ${config.color}` }}>
      <div className="tool-header">
        <span className="tool-icon">{config.icon}</span>
        <div>
          <h3 style={{ margin: 0 }}>{config.name}</h3>
          <span className="tool-category">{config.category}</span>
        </div>
        <span className={`risk-badge risk-${config.riskLevel?.toLowerCase()}`}>
          {config.riskLevel}
        </span>
      </div>
      
      <div className="tool-stats">
        {subdomains > 0 && (
          <div className="stat">
            <span className="stat-value">{subdomains}</span>
            <span className="stat-label">Subdomain</span>
          </div>
        )}
        <div className="stat">
          <span className="stat-value">{totalVulns}</span>
          <span className="stat-label">Kerentanan</span>
        </div>
        <div className="stat">
          <span className="stat-value">{totalFindings}</span>
          <span className="stat-label">Total Temuan</span>
        </div>
      </div>

      {/* Severity Mini Bar */}
      <div className="severity-mini-bar">
        {Object.entries(severityCounts).map(([sev, count]) => (
          count > 0 && (
            <div
              key={sev}
              className={`severity-segment severity-${sev.toLowerCase()}`}
              style={{ width: `${(count / (totalFindings || 1)) * 100}%` }}
              title={`${sev}: ${count}`}
            >
              {count}
            </div>
          )
        ))}
      </div>

      {/* AI-BRAIN Stats (jika ada) */}
      {aiStats.total > 0 && (
        <div className="ai-stats-mini">
          <span className="ai-badge">🧠 AI-BRAIN: {aiStats.total} tervalidasi</span>
          <span className="tp-badge">✅ {aiStats.tp} TP</span>
          <span className="fp-badge">❌ {aiStats.fp} FP</span>
        </div>
      )}

      {/* Caido Stats */}
      {caidoProfile && (
        <div className="caido-stats-mini">
          <span className="caido-badge">📊 {Object.keys(caidoProfile).length} endpoints diprofilkan</span>
        </div>
      )}
    </div>
  );
};

// Sub-Komponen: Tool Detail Section (Expandable)
const ToolDetailSection = ({ config, findings, caidoProfile }) => {
  const [isExpanded, setIsExpanded] = useState(false);

  const getSeverityBadge = (severity) => {
    const colors = {
      Critical: '#b71c1c',
      High: '#e53935',
      Medium: '#fb8c00',
      Low: '#fdd835',
      Informational: '#2196f3',
    };
    return (
      <span
        className="severity-badge"
        style={{ backgroundColor: colors[severity] || '#6b7280' }}
      >
        {severity}
      </span>
    );
  };

  const getOWASPBadge = (owasp) => {
    if (!owasp) return null;
    return <span className="owasp-badge">{owasp}</span>;
  };

  return (
    <div className="tool-detail-section" style={{ borderColor: config.color }}>
      <div
        className="tool-detail-header"
        onClick={() => setIsExpanded(!isExpanded)}
        style={{ backgroundColor: `${config.color}15` }}
      >
        <span className="tool-icon">{config.icon}</span>
        <h3 style={{ margin: 0 }}>{config.name}</h3>
        <span className="finding-count" style={{ marginLeft: '1rem', fontSize: '0.85rem', color: '#9ca3af' }}>{findings.length} temuan</span>
        <span className="expand-icon">{isExpanded ? '▲' : '▼'}</span>
      </div>

      {isExpanded && (
        <div className="tool-detail-content">
          {/* Tabel Temuan */}
          <table className="finding-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Jenis Kerentanan</th>
                <th>OWASP</th>
                <th>Severity</th>
                <th>Endpoint</th>
                <th>AI-BRAIN</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {findings.map((finding, index) => {
                const isTp = isFindingTruePositive(finding);
                const confScore = getFindingConfidenceScore(finding);
                return (
                <tr key={index} className={!isTp ? 'row-false-positive' : ''}>
                  <td>{index + 1}</td>
                  <td>
                    <strong>{finding.type || 'Unknown'}</strong>
                    {finding.description && (
                      <span className="finding-desc" style={{ display: 'block', fontSize: '0.75rem', color: '#9ca3af', marginTop: '0.2rem' }}>{finding.description}</span>
                    )}
                  </td>
                  <td>{getOWASPBadge(finding.owasp_code)}</td>
                  <td>{getSeverityBadge(finding.severity)}</td>
                  <td className="endpoint-cell">{finding.endpoint || 'N/A'}</td>
                  <td>
                    {isTp ? (
                      <span className="ai-badge-valid">✅ TP</span>
                    ) : (
                      <span className="ai-badge-invalid">❌ FP</span>
                    )}
                  </td>
                  <td>
                    <div className="confidence-bar">
                      <div
                        className="confidence-fill"
                        style={{ width: `${confScore}%` }}
                      />
                      <span>{confScore}%</span>
                    </div>
                  </td>
                </tr>
                );
              })}
            </tbody>
          </table>

          {/* Caido Traffic Details (khusus Caido) */}
          {caidoProfile && (
            <div className="caido-detail">
              <h4 style={{ color: '#06b6d4', marginBottom: '0.5rem' }}>📊 Traffic Profile (Caido CLI)</h4>
              <table className="caido-table">
                <thead>
                  <tr>
                    <th>Endpoint</th>
                    <th>Method</th>
                    <th>Params</th>
                    <th>Auth</th>
                    <th>Avg Size</th>
                    <th>Status Codes</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(caidoProfile).map(([endpoint, profile]) => (
                    <tr key={endpoint}>
                      <td className="endpoint-cell">{endpoint}</td>
                      <td>{profile.request_verb}</td>
                      <td>{profile.param_count}</td>
                      <td>{profile.auth_headers_present ? '✅' : '❌'}</td>
                      <td>{profile.response_size_mean} bytes</td>
                      <td>{profile.status_codes_seen?.join(', ')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ToolResultBreakdown;
