import React, { useState, useMemo, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { 
  X, 
  GitCompare, 
  ArrowRight, 
  CheckCircle2, 
  AlertTriangle, 
  ShieldAlert, 
  TrendingDown, 
  TrendingUp, 
  Minus, 
  Download, 
  Copy, 
  Check, 
  Shield, 
  Calendar, 
  Globe 
} from 'lucide-react';
import logo from '../assets/logo.png';
import VulnDetailModal from './VulnDetailModal';

export default function ReportComparisonModal({ reportA, reportB, onClose }) {
  const [filterTab, setFilterTab] = useState('all'); // 'all', 'new', 'resolved', 'persistent'
  const [detailFinding, setDetailFinding] = useState(null);
  const [copied, setCopied] = useState(false);

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Determine chronological order: Baseline (older) vs Target (newer)
  const [baseline, current] = useMemo(() => {
    if (!reportA || !reportB) return [reportA, reportB];
    const timeA = new Date(reportA.created_at).getTime();
    const timeB = new Date(reportB.created_at).getTime();
    return timeA <= timeB ? [reportA, reportB] : [reportB, reportA];
  }, [reportA, reportB]);

  // Helper to create unique finding fingerprint
  const getFingerprint = (f) => {
    if (!f) return '';
    const name = (f.name || f.type || '').trim().toLowerCase();
    const endpoint = (f.location || f.endpoint || '').trim().toLowerCase();
    const owasp = (f.owasp_code || f.owasp || '').trim().toLowerCase();
    return `${owasp}:::${endpoint}:::${name}`;
  };

  // Diff findings calculation
  const diff = useMemo(() => {
    const listA = Array.isArray(baseline?.findings) ? baseline.findings : [];
    const listB = Array.isArray(current?.findings) ? current.findings : [];

    const mapA = new Map();
    listA.forEach(f => mapA.set(getFingerprint(f), f));

    const mapB = new Map();
    listB.forEach(f => mapB.set(getFingerprint(f), f));

    // Persistent: in both A and B
    const persistent = [];
    // Resolved: in A, not in B
    const resolved = [];
    // New: in B, not in A
    const newFindings = [];

    listA.forEach(fA => {
      const fp = getFingerprint(fA);
      if (mapB.has(fp)) {
        persistent.push({ baseline: fA, current: mapB.get(fp), status: 'persistent' });
      } else {
        resolved.push({ baseline: fA, current: null, status: 'resolved' });
      }
    });

    listB.forEach(fB => {
      const fp = getFingerprint(fB);
      if (!mapA.has(fp)) {
        newFindings.push({ baseline: null, current: fB, status: 'new' });
      }
    });

    // Severity counts helper
    const countSeverity = (list) => {
      const counts = { CRITICAL: 0, HIGH: 0, MEDIUM: 0, LOW: 0, INFO: 0 };
      list.forEach(f => {
        const sev = (f.severity || 'INFO').toUpperCase();
        if (counts[sev] !== undefined) counts[sev]++;
        else counts.INFO++;
      });
      return counts;
    };

    const sevA = countSeverity(listA);
    const sevB = countSeverity(listB);

    return {
      listA,
      listB,
      persistent,
      resolved,
      newFindings,
      totalDelta: listB.length - listA.length,
      sevA,
      sevB,
    };
  }, [baseline, current]);

  if (!reportA || !reportB) return null;

  const filteredItems = useMemo(() => {
    if (filterTab === 'new') return diff.newFindings;
    if (filterTab === 'resolved') return diff.resolved;
    if (filterTab === 'persistent') return diff.persistent;
    return [...diff.newFindings, ...diff.resolved, ...diff.persistent];
  }, [filterTab, diff]);

  const handleCopyMarkdown = () => {
    const md = `### Corvus Audit Comparison Report
**Baseline Scan (A):** ${baseline.target} (${new Date(baseline.created_at).toLocaleString()})
**Current Scan (B):** ${current.target} (${new Date(current.created_at).toLocaleString()})

**Summary Delta:**
- Total Findings: ${diff.listA.length} → ${diff.listB.length} (${diff.totalDelta >= 0 ? '+' : ''}${diff.totalDelta})
- 🔴 New Vulnerabilities: ${diff.newFindings.length}
- 🟢 Resolved / Fixed: ${diff.resolved.length}
- 🟡 Persistent Unfixed: ${diff.persistent.length}

**Severity Comparison:**
- Critical: ${diff.sevA.CRITICAL} → ${diff.sevB.CRITICAL}
- High: ${diff.sevA.HIGH} → ${diff.sevB.HIGH}
- Medium: ${diff.sevA.MEDIUM} → ${diff.sevB.MEDIUM}
- Low/Info: ${diff.sevA.LOW + diff.sevA.INFO} → ${diff.sevB.LOW + diff.sevB.INFO}
`;
    navigator.clipboard.writeText(md);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  const handleExportJson = () => {
    const payload = {
      comparison_type: 'corvus_scan_diff',
      generated_at: new Date().toISOString(),
      baseline_scan: {
        id: baseline.id,
        target: baseline.target,
        created_at: baseline.created_at,
        total_findings: diff.listA.length,
      },
      current_scan: {
        id: current.id,
        target: current.target,
        created_at: current.created_at,
        total_findings: diff.listB.length,
      },
      delta: {
        total_delta: diff.totalDelta,
        new_count: diff.newFindings.length,
        resolved_count: diff.resolved.length,
        persistent_count: diff.persistent.length,
      },
      findings_diff: {
        new: diff.newFindings.map(i => i.current),
        resolved: diff.resolved.map(i => i.baseline),
        persistent: diff.persistent.map(i => i.current),
      }
    };
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `corvus_comparison_${baseline.id.slice(0, 6)}_vs_${current.id.slice(0, 6)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return createPortal(
    <div 
      className="fixed inset-0 z-[99999] flex items-center justify-center p-3 sm:p-6 bg-black/80 backdrop-blur-md overflow-y-auto"
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        width: '100vw',
        height: '100dvh',
      }}
      onClick={onClose}
    >
      <div 
        style={{
          margin: 'auto',
          width: '100%',
          maxWidth: '72rem',
          maxHeight: 'min(92vh, 92dvh)',
        }}
        className="relative flex flex-col rounded-[36px] corvus-card shadow-[0_25px_80px_rgba(0,0,0,0.8)] border border-red-900/40 overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header */}
        <div className="p-6 sm:p-8 border-b border-slate-200 dark:border-red-900/20 bg-slate-50/90 dark:bg-black/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 shrink-0">
          <div className="flex items-center gap-4">
            <div className="p-3 rounded-2xl bg-red-600/10 border border-red-600/30 text-red-500 shadow-lg shadow-red-600/10">
              <GitCompare className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[9px] font-black uppercase tracking-widest text-red-500 bg-red-600/10 px-2 py-0.5 rounded-full border border-red-900/30">
                  Audit Diff Engine
                </span>
                <span className="text-[10px] text-slate-500 font-mono">
                  {baseline.id.slice(0, 8)} ↔ {current.id.slice(0, 8)}
                </span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-black italic tracking-tight uppercase mt-0.5" style={{ color: 'var(--text-primary)' }}>
                Reports <span className="text-red-600 underline">Comparison</span>
              </h2>
            </div>
          </div>

          <div className="flex items-center gap-2 self-end sm:self-center">
            <button
              onClick={handleCopyMarkdown}
              className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-black/30 text-slate-700 dark:text-slate-300 hover:text-red-600 dark:hover:text-red-400 hover:border-red-500 transition-all flex items-center gap-1.5 text-xs font-black uppercase tracking-wider cursor-pointer shadow-sm"
              title="Copy Summary Markdown"
            >
              {copied ? <Check className="w-4 h-4 text-emerald-500" /> : <Copy className="w-4 h-4" />}
              <span className="hidden md:inline">{copied ? "Copied" : "Copy MD"}</span>
            </button>
            <button
              onClick={handleExportJson}
              className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-black/30 text-slate-700 dark:text-slate-300 hover:text-red-600 dark:hover:text-red-400 hover:border-red-500 transition-all flex items-center gap-1.5 text-xs font-black uppercase tracking-wider cursor-pointer shadow-sm"
              title="Export Diff JSON"
            >
              <Download className="w-4 h-4" />
              <span className="hidden md:inline">Export JSON</span>
            </button>
            <button
              onClick={onClose}
              className="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-black/30 text-slate-400 hover:text-red-500 hover:border-red-500 transition-all cursor-pointer shadow-sm"
              title="Close Comparison"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body (Scrollable) */}
        <div className="flex-1 overflow-y-auto p-6 sm:p-8 space-y-8">
          
          {/* Target comparison summary bar */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 relative">
            {/* Scan A (Baseline) */}
            <div className="p-5 rounded-2xl bg-slate-50/80 dark:bg-black/20 border border-slate-200 dark:border-slate-800/80 relative overflow-hidden">
              <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest flex items-center gap-1.5 mb-1.5">
                <Calendar className="w-3.5 h-3.5 text-slate-400" /> Baseline Scan (Earlier)
              </div>
              <div className="text-xl font-black italic uppercase truncate" style={{ color: 'var(--text-primary)' }}>
                {baseline.target}
              </div>
              <div className="flex items-center gap-4 mt-3 text-xs text-slate-500 dark:text-slate-400 font-mono">
                <span>{new Date(baseline.created_at).toLocaleString()}</span>
                <span className="text-red-600 font-bold">{diff.listA.length} Findings</span>
              </div>
            </div>

            {/* Scan B (Current / Retest) */}
            <div className="p-5 rounded-2xl bg-red-50/40 dark:bg-black/20 border border-red-200 dark:border-red-900/30 relative overflow-hidden">
              <div className="text-[9px] font-black text-red-600 dark:text-red-500 uppercase tracking-widest flex items-center gap-1.5 mb-1.5">
                <Calendar className="w-3.5 h-3.5 text-red-600 dark:text-red-500" /> Comparison Target (Latest)
              </div>
              <div className="text-xl font-black italic uppercase truncate" style={{ color: 'var(--text-primary)' }}>
                {current.target}
              </div>
              <div className="flex items-center gap-4 mt-3 text-xs text-slate-500 dark:text-slate-400 font-mono">
                <span>{new Date(current.created_at).toLocaleString()}</span>
                <span className="text-red-600 font-bold">{diff.listB.length} Findings</span>
              </div>
            </div>
          </div>

          {/* Key Executive Metrics Delta Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 sm:gap-4">
            {/* Total Delta */}
            <div className="p-4 sm:p-5 rounded-2xl bg-slate-50 dark:bg-black/30 border border-slate-200 dark:border-slate-800">
              <div className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">
                Net Finding Delta
              </div>
              <div className="flex items-baseline gap-2">
                <span className="text-2xl sm:text-3xl font-black" style={{ color: diff.totalDelta < 0 ? '#10b981' : diff.totalDelta > 0 ? '#ef4444' : 'var(--text-primary)' }}>
                  {diff.totalDelta > 0 ? `+${diff.totalDelta}` : diff.totalDelta}
                </span>
                {diff.totalDelta < 0 ? (
                  <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 flex items-center">
                    <TrendingDown className="w-3.5 h-3.5 mr-0.5" /> Improved
                  </span>
                ) : diff.totalDelta > 0 ? (
                  <span className="text-xs font-bold text-red-600 dark:text-red-400 flex items-center">
                    <TrendingUp className="w-3.5 h-3.5 mr-0.5" /> Increased
                  </span>
                ) : (
                  <span className="text-xs font-bold text-slate-500 flex items-center">
                    <Minus className="w-3.5 h-3.5 mr-0.5" /> Equal
                  </span>
                )}
              </div>
            </div>

            {/* Resolved */}
            <div className="p-4 sm:p-5 rounded-2xl bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-200 dark:border-emerald-500/30">
              <div className="text-[9px] font-black text-emerald-700 dark:text-emerald-400 uppercase tracking-widest mb-1 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Remediated / Fixed
              </div>
              <div className="text-2xl sm:text-3xl font-black text-emerald-700 dark:text-emerald-400">
                {diff.resolved.length}
              </div>
              <div className="text-[10px] text-emerald-600 dark:text-emerald-500/80 mt-1 font-bold">
                Closed since baseline
              </div>
            </div>

            {/* New Findings */}
            <div className="p-4 sm:p-5 rounded-2xl bg-red-50 dark:bg-red-950/20 border border-red-200 dark:border-red-500/30">
              <div className="text-[9px] font-black text-red-700 dark:text-red-400 uppercase tracking-widest mb-1 flex items-center gap-1">
                <ShieldAlert className="w-3 h-3" /> New Vulnerabilities
              </div>
              <div className="text-2xl sm:text-3xl font-black text-red-700 dark:text-red-400">
                {diff.newFindings.length}
              </div>
              <div className="text-[10px] text-red-600 dark:text-red-500/80 mt-1 font-bold">
                Newly introduced risks
              </div>
            </div>

            {/* Persistent */}
            <div className="p-4 sm:p-5 rounded-2xl bg-amber-50 dark:bg-yellow-950/20 border border-amber-200 dark:border-yellow-500/30">
              <div className="text-[9px] font-black text-amber-800 dark:text-yellow-400 uppercase tracking-widest mb-1 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> Persistent Unfixed
              </div>
              <div className="text-2xl sm:text-3xl font-black text-amber-800 dark:text-yellow-400">
                {diff.persistent.length}
              </div>
              <div className="text-[10px] text-amber-700 dark:text-yellow-500/80 mt-1 font-bold">
                Still active in both scans
              </div>
            </div>
          </div>

          {/* Severity Comparison Grid */}
          <div className="p-5 sm:p-6 rounded-3xl bg-slate-50/80 dark:bg-black/20 border border-slate-200 dark:border-slate-800">
            <h4 className="text-xs font-black uppercase tracking-wider text-red-600 dark:text-red-500 mb-4 flex items-center gap-2">
              <Shield className="w-4 h-4" /> Severity Breakdown Shift
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'CRITICAL', color: 'text-red-600 dark:text-red-500', countA: diff.sevA.CRITICAL, countB: diff.sevB.CRITICAL },
                { label: 'HIGH', color: 'text-orange-600 dark:text-orange-500', countA: diff.sevA.HIGH, countB: diff.sevB.HIGH },
                { label: 'MEDIUM', color: 'text-yellow-600 dark:text-yellow-400', countA: diff.sevA.MEDIUM, countB: diff.sevB.MEDIUM },
                { label: 'LOW / INFO', color: 'text-blue-600 dark:text-blue-400', countA: diff.sevA.LOW + diff.sevA.INFO, countB: diff.sevB.LOW + diff.sevB.INFO },
              ].map((sev, idx) => {
                const sDelta = sev.countB - sev.countA;
                return (
                  <div key={idx} className="p-3.5 rounded-2xl bg-white dark:bg-black/40 border border-slate-200 dark:border-slate-800/80 shadow-sm">
                    <div className={`text-[10px] font-black uppercase tracking-widest ${sev.color}`}>
                      {sev.label}
                    </div>
                    <div className="flex items-center justify-between mt-2 font-mono">
                      <div className="text-xs text-slate-500 dark:text-slate-400">
                        {sev.countA} <ArrowRight className="w-3 h-3 inline mx-1 text-slate-400 dark:text-slate-600" /> <span className="font-bold text-slate-900 dark:text-white">{sev.countB}</span>
                      </div>
                      <span className={`text-[10px] font-black px-1.5 py-0.5 rounded ${
                        sDelta < 0 ? 'bg-emerald-50 text-emerald-700 dark:bg-emerald-950/60 dark:text-emerald-400' : sDelta > 0 ? 'bg-red-50 text-red-700 dark:bg-red-950/60 dark:text-red-400' : 'text-slate-400'
                      }`}>
                        {sDelta > 0 ? `+${sDelta}` : sDelta}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Detailed Findings Diff Section with Tabs */}
          <div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-200 dark:border-red-900/20 pb-4 mb-4">
              <h4 className="text-sm font-black italic uppercase tracking-wider" style={{ color: 'var(--text-primary)' }}>
                Vulnerability <span className="text-red-600 underline">Delta Breakdown</span>
              </h4>

              {/* Tabs */}
              <div className="flex gap-2 overflow-x-auto pb-1">
                <button
                  onClick={() => setFilterTab('all')}
                  className={`px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all cursor-pointer ${
                    filterTab === 'all'
                      ? 'bg-red-600 text-white shadow-md'
                      : 'bg-slate-100 dark:bg-black/30 text-slate-600 dark:text-slate-400 hover:text-red-600 border border-slate-200 dark:border-slate-800'
                  }`}
                >
                  All ({diff.newFindings.length + diff.resolved.length + diff.persistent.length})
                </button>
                <button
                  onClick={() => setFilterTab('new')}
                  className={`px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-1 cursor-pointer ${
                    filterTab === 'new'
                      ? 'bg-red-600 text-white shadow-md'
                      : 'bg-red-50 dark:bg-black/30 text-red-700 dark:text-red-400 hover:text-red-600 border border-red-200 dark:border-red-900/30'
                  }`}
                >
                  <ShieldAlert className="w-3 h-3" /> New (+{diff.newFindings.length})
                </button>
                <button
                  onClick={() => setFilterTab('resolved')}
                  className={`px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-1 cursor-pointer ${
                    filterTab === 'resolved'
                      ? 'bg-emerald-600 text-white shadow-md'
                      : 'bg-emerald-50 dark:bg-black/30 text-emerald-700 dark:text-emerald-400 hover:text-emerald-600 border border-emerald-200 dark:border-emerald-900/30'
                  }`}
                >
                  <CheckCircle2 className="w-3 h-3" /> Fixed (-{diff.resolved.length})
                </button>
                <button
                  onClick={() => setFilterTab('persistent')}
                  className={`px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all flex items-center gap-1 cursor-pointer ${
                    filterTab === 'persistent'
                      ? 'bg-amber-600 text-white shadow-md'
                      : 'bg-amber-50 dark:bg-black/30 text-amber-800 dark:text-yellow-400 hover:text-amber-600 border border-amber-200 dark:border-yellow-900/30'
                  }`}
                >
                  <AlertTriangle className="w-3 h-3" /> Persistent ({diff.persistent.length})
                </button>
              </div>
            </div>

            {/* Finding Items List */}
            <div className="space-y-3">
              {filteredItems.length === 0 ? (
                <div className="p-12 text-center text-slate-500 font-bold uppercase tracking-wider text-xs bg-slate-50 dark:bg-black/20 rounded-2xl border border-slate-200 dark:border-slate-800/60">
                  No vulnerabilities in this category.
                </div>
              ) : (
                filteredItems.map((item, idx) => {
                  const targetFinding = item.current || item.baseline;
                  const isNew = item.status === 'new';
                  const isResolved = item.status === 'resolved';
                  const isPersistent = item.status === 'persistent';

                  return (
                    <div
                      key={idx}
                      className={`p-4 sm:p-5 rounded-2xl border transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 ${
                        isNew
                          ? 'border-red-200 dark:border-red-600/40 bg-red-50/50 dark:bg-red-950/10 hover:border-red-500'
                          : isResolved
                          ? 'border-emerald-200 dark:border-emerald-600/30 bg-emerald-50/50 dark:bg-emerald-950/10 hover:border-emerald-500'
                          : 'border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-black/20 hover:border-slate-400'
                      }`}
                    >
                      <div className="flex items-start sm:items-center gap-3 min-w-0">
                        {/* Status Badge Icon */}
                        <div className={`p-2.5 rounded-xl shrink-0 mt-0.5 sm:mt-0 ${
                          isNew
                            ? 'bg-red-50 text-red-600 border border-red-200 dark:bg-red-600/20 dark:text-red-400 dark:border-red-500/30'
                            : isResolved
                            ? 'bg-emerald-50 text-emerald-600 border border-emerald-200 dark:bg-emerald-600/20 dark:text-emerald-400 dark:border-emerald-500/30'
                            : 'bg-amber-50 text-amber-600 border border-amber-200 dark:bg-yellow-500/10 dark:text-yellow-400 dark:border-yellow-500/30'
                        }`}>
                          {isNew && <ShieldAlert className="w-4 h-4" />}
                          {isResolved && <CheckCircle2 className="w-4 h-4" />}
                          {isPersistent && <AlertTriangle className="w-4 h-4" />}
                        </div>

                        <div className="min-w-0">
                          <div className="flex flex-wrap items-center gap-2 mb-1">
                            <span className={`text-[8px] font-black px-2 py-0.5 rounded uppercase tracking-wider ${
                              isNew
                                ? 'bg-red-600 text-white'
                                : isResolved
                                ? 'bg-emerald-600 text-white'
                                : 'bg-amber-500/20 text-amber-800 dark:text-yellow-400 border border-amber-500/40'
                            }`}>
                              {isNew ? 'NEW IN SCAN B' : isResolved ? 'REMEDIATED / FIXED' : 'PERSISTENT UNRESOLVED'}
                            </span>
                            <span className="text-[8px] text-slate-500 font-mono">
                              {targetFinding.owasp_code || 'A00:2021'}
                            </span>
                          </div>

                          <div className="text-sm font-black italic uppercase truncate" style={{ color: 'var(--text-primary)' }}>
                            {targetFinding.name || targetFinding.type || 'Vulnerability'}
                          </div>

                          <div className="text-[10px] text-slate-500 dark:text-slate-400 font-mono mt-0.5 truncate flex items-center gap-1.5">
                            <Globe className="w-3 h-3 text-red-500 shrink-0" />
                            <span>{targetFinding.location || targetFinding.endpoint || 'N/A'}</span>
                          </div>
                        </div>
                      </div>

                      {/* Right Side: Severity & Action */}
                      <div className="flex items-center justify-between md:justify-end gap-3 shrink-0 pt-2 md:pt-0 border-t md:border-t-0 border-slate-200 dark:border-slate-800">
                        <span className={`px-3 py-1 rounded-xl text-[9px] font-black uppercase tracking-tighter border ${
                          (targetFinding.severity || 'INFO').toUpperCase() === 'CRITICAL' ? 'bg-[#b71c1c] text-white border-red-900 shadow-[0_0_10px_rgba(183,28,28,0.4)]' :
                          (targetFinding.severity || 'INFO').toUpperCase() === 'HIGH' ? 'bg-[#e53935] text-white border-red-600' :
                          (targetFinding.severity || 'INFO').toUpperCase() === 'MEDIUM' ? 'bg-[#fb8c00] text-white border-orange-600' :
                          (targetFinding.severity || 'INFO').toUpperCase() === 'LOW' ? 'bg-[#fdd835] text-black border-yellow-600' :
                          'bg-[#2196f3] text-white border-blue-600'
                        }`}>
                          {targetFinding.severity || 'INFO'}
                        </span>

                        <button
                          onClick={() => setDetailFinding(targetFinding)}
                          className="px-3 py-1.5 rounded-xl border border-red-200 dark:border-red-900/30 bg-red-50 dark:bg-red-600/10 hover:bg-red-600 text-red-600 dark:text-red-400 hover:text-white transition-all text-[9px] font-black uppercase tracking-wider cursor-pointer"
                        >
                          View Finding →
                        </button>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 sm:p-6 border-t border-slate-200 dark:border-red-900/20 bg-slate-50/90 dark:bg-black/30 flex justify-between items-center shrink-0">
          <div className="text-[9px] font-mono text-slate-500 uppercase tracking-widest hidden sm:block">
            CORVUS INTELLIGENT RETEST & REGRESSION COMPARATOR
          </div>
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-xl bg-red-600 text-white font-black text-xs uppercase tracking-widest hover:bg-white hover:text-red-900 transition-all shadow-lg shadow-red-600/20 ml-auto cursor-pointer"
          >
            Close Comparison
          </button>
        </div>
      </div>

    {/* Sub modal to inspect finding detail if clicked */}
    {detailFinding && (
      <VulnDetailModal finding={detailFinding} onClose={() => setDetailFinding(null)} />
    )}
  </div>,
  document.body
);
}
