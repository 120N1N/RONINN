import React, { useState, useEffect } from 'react';
import { 
    CheckCircle2,
    AlertTriangle,
    Trash2, 
    History, 
    X, 
    Download, 
    FileText, 
    Activity, 
    GitCompare, 
    CheckSquare, 
    Square, 
    Calendar,
    Globe,
    Layers,
    ArrowRight,
    Brain,
    ShieldCheck,
    Cpu
} from 'lucide-react';
import { Link } from 'react-router-dom';
import logo from '../assets/logo.png';
import VulnDetailModal from '../components/VulnDetailModal';
import ReportComparisonModal from '../components/ReportComparisonModal';
import AIBrainSummary from '../components/AIBrainSummary';
import { isFindingTruePositive, getFindingConfidenceScore } from '../utils/findingHelper';

const API_BASE = import.meta.env.VITE_API_URL || "/api";

const getCvssScore = (finding) => {
    if (finding.cvss !== undefined && finding.cvss !== null && finding.cvss !== "") {
        const n = parseFloat(finding.cvss);
        if (!isNaN(n)) return n.toFixed(1);
    }
    if (finding.risk_score !== undefined && finding.risk_score !== null && finding.risk_score !== "") {
        const n = parseFloat(finding.risk_score);
        if (!isNaN(n)) return n.toFixed(1);
    }
    const sev = (finding.severity || "INFO").toUpperCase();
    const map = { 'CRITICAL': '9.5', 'HIGH': '7.5', 'MEDIUM': '5.5', 'LOW': '3.0', 'INFO': '1.0', 'INFORMATIONAL': '1.0' };
    return map[sev] || '3.0';
};

const ReportsPage = () => {
    const [reports, setReports] = useState([]);
    const [selectedReport, setSelectedReport] = useState(null);
    const [showDetail, setShowDetail] = useState(null);
    const [selectedReports, setSelectedReports] = useState([]);
    const [selectionMode, setSelectionMode] = useState(null); // null | 'compare' | 'delete'
    const [comparisonPair, setComparisonPair] = useState(null);
    const [showPickerForCompare, setShowPickerForCompare] = useState(false);
    const [findingsFilter, setFindingsFilter] = useState('all');

    const normalizeTarget = (url = '') => (url || '').trim().toLowerCase().replace(/\/+$/, '');

    const firstSelectedReport = (selectionMode === 'compare' && selectedReports.length > 0)
        ? reports.find(r => r.id === selectedReports[0])
        : null;
    const selectedTargetNormalized = firstSelectedReport ? normalizeTarget(firstSelectedReport.target) : null;

    const fetchReports = () => {
        const token = localStorage.getItem('corvus_token');
        fetch(`${API_BASE}/reports`, {
            headers: { "Authorization": `Bearer ${token}` }
        }).then(r => r.json()).then(d => {
            if (Array.isArray(d)) setReports(d);
            else setReports([]);
        }).catch(() => setReports([])); 
    };

    useEffect(() => { 
        fetchReports();
    }, []);

    // Polling interval if any scan is currently RUNNING or PENDING
    useEffect(() => {
        const hasActive = reports.some(r => r.status === 'RUNNING' || r.status === 'PENDING');
        let interval;
        if (hasActive) {
            interval = setInterval(() => {
                fetchReports();
            }, 3000);
        }
        return () => clearInterval(interval);
    }, [reports]);

    const toggleSelectReport = (id) => {
        setSelectedReports(prev => 
            prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
        );
    };

    const handleCardClick = (h) => {
        if (selectionMode === 'delete') {
            toggleSelectReport(h.id);
        } else if (selectionMode === 'compare') {
            const isSelected = selectedReports.includes(h.id);
            if (isSelected) {
                toggleSelectReport(h.id);
            } else {
                if (selectedReports.length === 0) {
                    toggleSelectReport(h.id);
                } else if (selectedReports.length === 1) {
                    if (normalizeTarget(h.target) === selectedTargetNormalized) {
                        toggleSelectReport(h.id);
                    } else {
                        alert(`Target harus sama dengan laporan pertama (${firstSelectedReport?.target}).`);
                    }
                }
            }
        } else {
            setSelectedReport(h);
        }
    };

    const handleDeleteSelected = async () => {
        if (selectedReports.length === 0) return;
        if (!window.confirm(`Menghapus ${selectedReports.length} laporan secara permanen. Lanjutkan?`)) return;
        const token = localStorage.getItem('corvus_token');
        await Promise.all(selectedReports.map(id => 
            fetch(`${API_BASE}/reports/${id}`, {
                method: 'DELETE',
                headers: { "Authorization": `Bearer ${token}` }
            })
        ));
        setSelectedReports([]);
        setSelectionMode(null);
        fetchReports();
    };

    const handleCompareSelected = () => {
        if (selectedReports.length !== 2) return;
        const rA = reports.find(r => r.id === selectedReports[0]);
        const rB = reports.find(r => r.id === selectedReports[1]);
        if (rA && rB) {
            if (normalizeTarget(rA.target) !== normalizeTarget(rB.target)) {
                alert("Komparasi hanya dapat dilakukan pada target yang sama.");
                return;
            }
            setComparisonPair([rA, rB]);
            setSelectionMode(null);
            setSelectedReports([]);
        }
    };

    const handleQuickCompare = (e, report) => {
        e.stopPropagation();
        const sameTargetReports = reports.filter(r => r.id !== report.id && normalizeTarget(r.target) === normalizeTarget(report.target));
        if (sameTargetReports.length > 0) {
            setComparisonPair([sameTargetReports[0], report]);
        } else {
            alert(`Belum ada riwayat scan lain untuk target ${report.target} untuk dibandingkan.`);
        }
    };

    return (
        <>
        <div className="py-12 sm:py-20">
            {/* Header & Batch Action Bar */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-10 sm:mb-12 gap-4">
                <div>
                    <h2 className="text-4xl sm:text-5xl font-black italic tracking-tighter uppercase" style={{ color: 'var(--text-primary)' }}>
                        Security <span className="text-red-600 underline">History</span>
                    </h2>
                    <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500 mt-1">
                        Historical audit scans & vulnerability regression tracker
                    </p>
                </div>

                {!selectedReport && (
                    <div className="flex items-center gap-3 flex-wrap">
                        {selectionMode === null ? (
                            <>
                                <button 
                                    onClick={() => {
                                        setSelectionMode('compare');
                                        setSelectedReports([]);
                                    }}
                                    disabled={reports.length < 2}
                                    className="flex items-center gap-2 bg-slate-100 hover:bg-slate-200 dark:bg-black/50 dark:hover:bg-red-950/40 text-slate-700 dark:text-slate-200 hover:text-red-600 dark:hover:text-red-400 px-4 sm:px-5 py-2.5 rounded-2xl transition-all border border-slate-300 dark:border-red-900/30 font-black text-xs uppercase tracking-widest cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
                                    title="Bandingkan 2 laporan dengan target yang sama"
                                >
                                    <GitCompare className="w-4 h-4 text-red-500" />
                                    <span>Compare</span>
                                </button>

                                <button 
                                    onClick={() => {
                                        setSelectionMode('delete');
                                        setSelectedReports([]);
                                    }}
                                    disabled={reports.length === 0}
                                    className="flex items-center gap-2 bg-slate-100 hover:bg-slate-200 dark:bg-black/50 dark:hover:bg-red-950/40 text-slate-700 dark:text-slate-200 hover:text-red-600 dark:hover:text-red-400 px-4 sm:px-5 py-2.5 rounded-2xl transition-all border border-slate-300 dark:border-red-900/30 font-black text-xs uppercase tracking-widest cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed shadow-sm"
                                    title="Pilih laporan untuk dihapus"
                                >
                                    <Trash2 className="w-4 h-4 text-red-500" />
                                    <span>Delete</span>
                                </button>
                            </>
                        ) : selectionMode === 'compare' ? (
                            <div className="flex items-center gap-3 flex-wrap animate-in fade-in duration-200">
                                <span className="text-[10px] font-bold text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-black/40 border border-slate-200 dark:border-slate-800 px-3.5 py-2 rounded-xl flex items-center gap-1.5 shadow-sm">
                                    <GitCompare className="w-3.5 h-3.5 text-red-500" />
                                    {selectedReports.length === 0 && "Pilih laporan pertama"}
                                    {selectedReports.length === 1 && `Pilih 1 lagi (Target: ${firstSelectedReport?.target})`}
                                    {selectedReports.length === 2 && "2 Laporan siap dibandingkan"}
                                </span>

                                {selectedReports.length === 2 && (
                                    <button 
                                        onClick={handleCompareSelected}
                                        className="flex items-center gap-2 bg-red-600 hover:bg-white hover:text-red-900 text-white px-5 py-2 rounded-xl transition-all shadow-xl shadow-red-600/30 font-black text-xs uppercase tracking-widest cursor-pointer"
                                    >
                                        <GitCompare className="w-4 h-4" />
                                        <span>Bandingkan (2)</span>
                                    </button>
                                )}

                                <button 
                                    onClick={() => {
                                        setSelectionMode(null);
                                        setSelectedReports([]);
                                    }}
                                    className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-200 hover:bg-slate-300 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-black uppercase tracking-wider transition-all cursor-pointer"
                                >
                                    <X className="w-4 h-4" />
                                    <span>Batal</span>
                                </button>
                            </div>
                        ) : (
                            <div className="flex items-center gap-3 flex-wrap animate-in fade-in duration-200">
                                <button
                                    onClick={() => {
                                        if (selectedReports.length === reports.length) {
                                            setSelectedReports([]);
                                        } else {
                                            setSelectedReports(reports.map(r => r.id));
                                        }
                                    }}
                                    className="px-3.5 py-2 rounded-xl bg-slate-100 dark:bg-black/40 border border-slate-300 dark:border-slate-800 text-[10px] font-bold text-slate-700 dark:text-slate-300 hover:border-red-500 uppercase cursor-pointer"
                                >
                                    {selectedReports.length === reports.length ? "Batal Semua" : "Pilih Semua"}
                                </button>

                                {selectedReports.length > 0 && (
                                    <button 
                                        onClick={handleDeleteSelected}
                                        className="flex items-center gap-2 bg-red-600 hover:bg-red-700 text-white px-5 py-2 rounded-xl transition-all shadow-lg text-xs font-black uppercase tracking-widest cursor-pointer"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                        <span>Hapus ({selectedReports.length})</span>
                                    </button>
                                )}

                                <button 
                                    onClick={() => {
                                        setSelectionMode(null);
                                        setSelectedReports([]);
                                    }}
                                    className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-slate-200 hover:bg-slate-300 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-700 dark:text-slate-300 text-xs font-black uppercase tracking-wider transition-all cursor-pointer"
                                >
                                    <X className="w-4 h-4" />
                                    <span>Selesai</span>
                                </button>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Reports Grid View */}
            {!selectedReport ? (
                reports.length === 0 ? (
                    <div className="corvus-card p-16 rounded-[40px] text-center border border-slate-200 dark:border-red-900/20">
                        <History className="w-16 h-16 text-red-600/30 mx-auto mb-4" />
                        <h3 className="text-xl font-black italic uppercase" style={{ color: 'var(--text-primary)' }}>
                            Belum Ada Riwayat Audit
                        </h3>
                        <p className="text-xs text-slate-500 mt-2 max-w-md mx-auto">
                            Mulai pemindaian pertama Anda di Dashboard untuk melihat catatan keamanan dan melakukan analisis komparasi.
                        </p>
                        <Link to="/" className="inline-block mt-6 px-6 py-2.5 rounded-xl bg-red-600 text-white font-black text-xs uppercase tracking-widest hover:bg-white hover:text-red-900 transition-all shadow-lg">
                            Ke Dashboard →
                        </Link>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                        {reports.map((h, i) => {
                            const isRunning = h.status === 'RUNNING' || h.status === 'PENDING';
                            const isSelected = selectedReports.includes(h.id);
                            const isTargetMatch = !selectedTargetNormalized || normalizeTarget(h.target) === selectedTargetNormalized;
                            const isCardDisabled = selectionMode === 'compare' && selectedReports.length === 1 && !isSelected && !isTargetMatch;

                            return (
                                <div 
                                    key={i} 
                                    onClick={() => handleCardClick(h)}
                                    className={`corvus-card p-8 sm:p-10 rounded-[44px] transition-all shadow-xl hover:shadow-2xl group relative cursor-pointer ${
                                        isSelected ? 'ring-2 ring-red-600 border-red-600 shadow-[0_0_30px_rgba(220,38,38,0.25)]' : ''
                                    } ${isCardDisabled ? 'opacity-40 grayscale pointer-events-none' : ''}`}
                                >
                                    {/* Checkbox for Select / Compare / Delete - ONLY shown when selectionMode is active */}
                                    {selectionMode && (
                                        <div className="absolute top-8 right-8 z-20">
                                            <button
                                                type="button"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleCardClick(h);
                                                }}
                                                disabled={isCardDisabled}
                                                title={isSelected ? "Batal Pilih" : "Pilih"}
                                                className="p-1 rounded-lg text-slate-400 hover:text-red-500 transition-colors cursor-pointer"
                                            >
                                                {isSelected ? (
                                                    <CheckSquare className="w-6 h-6 text-red-500" />
                                                ) : (
                                                    <Square className="w-6 h-6 text-slate-400 dark:text-slate-600 hover:text-red-500" />
                                                )}
                                            </button>
                                        </div>
                                    )}

                                    <div>
                                        <div className="flex items-center justify-between mb-6 pr-8">
                                            <div className="flex items-center gap-2">
                                                <History className="w-9 h-9 text-red-600 opacity-30 group-hover:opacity-100 transition-opacity" />
                                                {isCardDisabled && (
                                                    <span className="px-2 py-0.5 rounded-md text-[8px] font-black uppercase tracking-wider bg-slate-200 dark:bg-slate-800 text-slate-500">
                                                        Target Berbeda
                                                    </span>
                                                )}
                                            </div>
                                            {isRunning ? (
                                                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-wider bg-amber-50 text-amber-700 border border-amber-200 dark:bg-yellow-500/10 dark:text-yellow-400 dark:border-yellow-500/30 animate-pulse">
                                                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500 dark:bg-yellow-400 animate-ping"></span>
                                                    {h.status} ({h.progress || 0}%)
                                                </span>
                                            ) : h.status === 'FAILED' ? (
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider bg-red-50 text-red-700 border border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-600/30">
                                                    FAILED
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-600/30">
                                                    COMPLETED
                                                </span>
                                            )}
                                        </div>

                                        <h4 className="text-xl sm:text-2xl font-black italic uppercase truncate mb-5" style={{ color: 'var(--text-primary)' }}>
                                            {h.target}
                                        </h4>

                                        <div className="flex gap-8 mb-4">
                                            <div className="flex flex-col">
                                                <span className="text-[8px] font-black text-red-600 uppercase tracking-wider">Findings</span>
                                                <span className="font-black text-2xl" style={{ color: 'var(--text-primary)' }}>
                                                    {h.findings?.length || 0}
                                                </span>
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-[8px] font-black text-red-600 uppercase tracking-wider">Date</span>
                                                <span className="text-slate-500 font-bold text-xs mt-1">
                                                    {new Date(h.created_at).toLocaleDateString()}
                                                </span>
                                            </div>
                                        </div>

                                        {/* AI-BRAIN Analyst Snapshot */}
                                        {(() => {
                                            const fList = h.findings || [];
                                            const tp = fList.filter(isFindingTruePositive).length;
                                            const fp = fList.filter(f => !isFindingTruePositive(f)).length;
                                            const valCount = fList.filter(f => f.ai_brain_validation || f.ai_validation || f.rf_validation).length;
                                            return (
                                                <div className="flex items-center gap-2 mb-5 px-3 py-1.5 rounded-xl bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-red-950/40 text-[10px] font-bold">
                                                    <Brain className="w-3.5 h-3.5 text-red-500 flex-shrink-0" />
                                                    <span className="text-slate-600 dark:text-slate-400 font-black uppercase text-[8px] tracking-wider">AI-Brain:</span>
                                                    <span className="text-emerald-600 dark:text-emerald-400 font-black">{tp} TP</span>
                                                    <span className="text-slate-400">•</span>
                                                    <span className="text-red-500 font-black">{fp} FP</span>
                                                    {valCount > 0 && (
                                                        <span className="text-[9px] text-slate-500 ml-auto font-mono">
                                                            {Math.round((valCount / Math.max(fList.length, 1)) * 100)}% verified
                                                        </span>
                                                    )}
                                                </div>
                                            );
                                        })()}

                                        <div className="pt-5 border-t border-slate-200 dark:border-red-900/10 flex justify-between items-center">
                                            {/* Quick Compare Trigger (Only in default view) */}
                                            {selectionMode === null && reports.length > 1 ? (
                                                <button
                                                    onClick={(e) => handleQuickCompare(e, h)}
                                                    className="text-[9px] font-black text-slate-500 hover:text-red-600 dark:hover:text-red-500 flex items-center gap-1 uppercase tracking-wider transition-colors cursor-pointer"
                                                    title="Quick Compare with another scan"
                                                >
                                                    <GitCompare className="w-3.5 h-3.5" /> Compare
                                                </button>
                                            ) : <div />}

                                            <span className="text-[10px] font-black text-red-600 group-hover:translate-x-1.5 transition-transform italic uppercase ml-auto">
                                                {selectionMode ? (isSelected ? 'Terpilih ✓' : 'Klik untuk Pilih') : 'Open Report →'}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )
            ) : (
                /* Single Report Detail View */
                <div className="space-y-8 animate-in fade-in duration-300">
                    <button 
                        onClick={() => setSelectedReport(null)} 
                        className="text-[10px] font-black text-slate-500 hover:text-red-600 uppercase tracking-widest flex items-center gap-2 mb-6 transition-colors"
                    >
                        ← BACK TO HISTORY
                    </button>

                    {(selectedReport.status === 'RUNNING' || selectedReport.status === 'PENDING') && (
                        <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-3xl p-5 mb-8 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-yellow-400 animate-pulse">
                            <div className="flex items-center gap-3">
                                <Activity className="w-6 h-6 animate-spin text-yellow-400 flex-shrink-0" />
                                <div>
                                    <p className="text-xs sm:text-sm font-black uppercase tracking-wider">Pemindaian Masih Berlangsung ({selectedReport.progress || 0}%)</p>
                                    <p className="text-[10px] text-slate-400 font-mono mt-0.5">Task: {selectedReport.current_step || "EXECUTING"}</p>
                                </div>
                            </div>
                            <Link
                                to="/"
                                onClick={() => localStorage.setItem('corvus_active_scan_id', selectedReport.id)}
                                className="bg-yellow-500 hover:bg-yellow-400 text-black font-black text-[10px] uppercase tracking-widest px-5 py-2.5 rounded-xl transition-all shadow-lg flex-shrink-0"
                            >
                                Buka Terminal Live di Dashboard →
                            </Link>
                        </div>
                    )}

                    {/* AI-BRAIN SECURITY ANALYST SUMMARY CARD */}
                    <div className="mb-8">
                        <AIBrainSummary 
                            findings={selectedReport.findings || []}
                            activeFilter={findingsFilter}
                            onSelectFilter={setFindingsFilter}
                        />
                    </div>

                    {/* AI-BRAIN EXECUTIVE SUMMARY / VERDICT IF AVAILABLE */}
                    {(selectedReport.ai_summary?.executive_summary || (selectedReport.tool_outputs?.ai_brain_summary)?.executive_summary) && (
                        <div className="corvus-card p-6 sm:p-8 rounded-3xl md:rounded-[36px] mb-8 border border-red-500/30 bg-gradient-to-br from-red-950/20 via-black/40 to-black/60 shadow-xl relative overflow-hidden">
                            <div className="flex items-center gap-3 mb-3">
                                <div className="w-8 h-8 rounded-xl bg-red-600/20 border border-red-500/40 flex items-center justify-center text-red-500">
                                    <Brain className="w-4 h-4 text-red-500 animate-pulse" />
                                </div>
                                <div>
                                    <h4 className="text-sm sm:text-base font-black italic uppercase tracking-wider text-red-600 dark:text-red-400">
                                        Executive Security Analyst Verdict
                                    </h4>
                                    <p className="text-[9px] text-slate-500 font-bold uppercase tracking-widest">
                                        Autonomous Intelligence Assessment
                                    </p>
                                </div>
                            </div>
                            <p className="text-xs sm:text-sm text-slate-700 dark:text-slate-300 leading-relaxed font-medium pl-1">
                                {selectedReport.ai_summary?.executive_summary || selectedReport.tool_outputs?.ai_brain_summary?.executive_summary}
                            </p>
                        </div>
                    )}

                    <div className="corvus-card rounded-[40px] sm:rounded-[48px] overflow-hidden shadow-2xl">
                        <div className="p-6 sm:p-10 border-b border-slate-200 dark:border-red-900/10 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-50/80 dark:bg-black/20">
                            <div>
                                <div className="flex items-center gap-3">
                                    <h3 className="text-2xl sm:text-3xl font-black italic uppercase" style={{ color: 'var(--text-primary)' }}>
                                        {selectedReport.target}
                                    </h3>
                                    <span className={`px-2.5 py-0.5 rounded-full text-[9px] font-black uppercase tracking-wider border ${
                                        selectedReport.status === 'RUNNING' || selectedReport.status === 'PENDING'
                                            ? 'bg-amber-50 text-amber-700 border-amber-200 dark:bg-yellow-500/20 dark:text-yellow-400 dark:border-yellow-500/30'
                                            : selectedReport.status === 'FAILED'
                                            ? 'bg-red-50 text-red-700 border-red-200 dark:bg-red-900/30 dark:text-red-400 dark:border-red-600/30'
                                            : 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-green-900/30 dark:text-green-400 dark:border-green-600/30'
                                    }`}>
                                        {selectedReport.status}
                                    </span>
                                </div>
                                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mt-1">
                                    Snapshot Audit: {new Date(selectedReport.created_at).toLocaleString()}
                                </p>
                            </div>

                            <div className="flex items-center gap-2 sm:gap-3 flex-wrap">
                                {/* Compare with Another Scan */}
                                {reports.length > 1 && (
                                    <button
                                        onClick={() => setShowPickerForCompare(true)}
                                        title="Compare with another audit scan"
                                        className="bg-white dark:bg-black/40 border border-slate-200 dark:border-slate-800 text-slate-700 dark:text-slate-300 p-3 rounded-2xl hover:bg-red-600 hover:text-white hover:border-red-600 transition-all shadow-md flex items-center gap-1.5 cursor-pointer"
                                    >
                                        <GitCompare className="w-4 h-4" />
                                        <span className="text-[10px] font-black uppercase tracking-wider pr-1">Compare</span>
                                    </button>
                                )}

                                {/* PDF Download */}
                                <button 
                                    onClick={async () => {
                                        try {
                                            const token = localStorage.getItem('corvus_token');
                                            const res = await fetch(`${API_BASE}/reports/${selectedReport.id}/pdf`, {
                                                headers: { "Authorization": `Bearer ${token}` }
                                            });
                                            if (!res.ok) throw new Error("Gagal mengunduh PDF");
                                            const blob = await res.blob();
                                            const url = window.URL.createObjectURL(blob);
                                            const link = document.createElement('a');
                                            link.href = url;
                                            link.setAttribute('download', `Corvus_Report_${selectedReport.target}_${selectedReport.id.slice(0,8)}.pdf`);
                                            document.body.appendChild(link);
                                            link.click();
                                            document.body.removeChild(link);
                                            window.URL.revokeObjectURL(url);
                                        } catch (e) {
                                            alert("Gagal mengunduh PDF: " + e.message);
                                        }
                                    }}
                                    title="Download Audit PDF Report"
                                    className="bg-blue-600 text-white p-3 rounded-2xl hover:bg-blue-700 transition-all shadow-lg shadow-blue-600/30 cursor-pointer flex items-center gap-1.5"
                                >
                                    <FileText className="w-4 h-4" />
                                    <span className="text-[10px] font-black uppercase tracking-wider pr-1">PDF</span>
                                </button>

                                {/* JSON Download */}
                                <button 
                                    onClick={() => {
                                        const reportData = JSON.stringify(selectedReport, null, 4);
                                        const blob = new Blob([reportData], { type: 'application/json' });
                                        const url = window.URL.createObjectURL(blob);
                                        const link = document.createElement('a');
                                        link.href = url;
                                        link.setAttribute('download', `corvus_${selectedReport.target}_${selectedReport.id.slice(0,8)}.json`);
                                        document.body.appendChild(link);
                                        link.click();
                                        document.body.removeChild(link);
                                        window.URL.revokeObjectURL(url);
                                    }}
                                    title="Download JSON Report"
                                    className="bg-red-600 text-white p-3 rounded-2xl hover:bg-red-700 transition-all shadow-lg shadow-red-600/30 cursor-pointer flex items-center gap-1.5"
                                >
                                    <Download className="w-4 h-4" />
                                    <span className="text-[10px] font-black uppercase tracking-wider pr-1">JSON</span>
                                </button>

                                {/* Delete */}
                                <button 
                                    onClick={async () => {
                                        if (window.confirm("Are you sure you want to delete this report?")) {
                                            const token = localStorage.getItem('corvus_token');
                                            const res = await fetch(`${API_BASE}/reports/${selectedReport.id}`, { 
                                                method: "DELETE",
                                                headers: { "Authorization": `Bearer ${token}` }
                                            });
                                            if (res.ok) {
                                                setSelectedReport(null);
                                                fetchReports();
                                            }
                                        }
                                    }}
                                    className="bg-white dark:bg-black/40 border border-slate-200 dark:border-slate-800 text-slate-500 hover:bg-red-600 hover:text-white hover:border-red-600 p-3 rounded-2xl transition-all shadow-md cursor-pointer"
                                    title="Delete Report"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>
                        </div>

                        {/* Interactive Filter Toolbar for Findings */}
                        {(() => {
                            const rawList = Array.isArray(selectedReport.findings) ? selectedReport.findings : [];
                            const tpNum = rawList.filter(isFindingTruePositive).length;
                            const fpNum = rawList.filter(f => !isFindingTruePositive(f)).length;
                            return (
                                <div className="flex items-center gap-2 px-6 sm:px-10 py-3.5 bg-slate-50/60 dark:bg-black/40 border-b border-slate-200 dark:border-red-900/10 flex-wrap">
                                    <span className="text-[10px] font-black uppercase tracking-wider text-slate-500 mr-1">Tampilkan:</span>
                                    <button
                                        onClick={() => setFindingsFilter('all')}
                                        className={`px-3 py-1 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all cursor-pointer ${
                                            findingsFilter === 'all'
                                                ? 'bg-red-600 text-white shadow-md'
                                                : 'bg-slate-200/80 dark:bg-slate-900 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                                        }`}
                                    >
                                        Semua ({rawList.length})
                                    </button>
                                    <button
                                        onClick={() => setFindingsFilter('tp')}
                                        className={`px-3 py-1 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all cursor-pointer flex items-center gap-1.5 ${
                                            findingsFilter === 'tp'
                                                ? 'bg-emerald-600 text-white shadow-md'
                                                : 'bg-slate-200/80 dark:bg-slate-900 text-emerald-600 dark:text-emerald-400 hover:bg-emerald-950/40'
                                        }`}
                                    >
                                        <ShieldCheck className="w-3 h-3" /> True Positive ({tpNum})
                                    </button>
                                    <button
                                        onClick={() => setFindingsFilter('fp')}
                                        className={`px-3 py-1 rounded-xl text-[10px] font-black uppercase tracking-wider transition-all cursor-pointer flex items-center gap-1.5 ${
                                            findingsFilter === 'fp'
                                                ? 'bg-red-600 text-white shadow-md'
                                                : 'bg-slate-200/80 dark:bg-slate-900 text-red-600 dark:text-red-400 hover:bg-red-950/40'
                                        }`}
                                    >
                                        <AlertTriangle className="w-3 h-3" /> False Positive ({fpNum})
                                    </button>
                                </div>
                            );
                        })()}

                        {/* Findings Table */}
                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead className="bg-slate-100/90 dark:bg-black/40 text-slate-700 dark:text-red-500/80 text-[10px] font-black uppercase tracking-[0.2em] border-b border-slate-200 dark:border-red-900/20">
                                    <tr>
                                        <th className="px-6 sm:px-10 py-5">Threat Type / ID</th>
                                        <th className="px-6 sm:px-10 py-5">Severity</th>
                                        <th className="px-6 sm:px-10 py-5">Endpoint</th>
                                        <th className="px-6 sm:px-10 py-5 text-right">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-200 dark:divide-red-900/10">
                                    {(() => {
                                        const rawList = Array.isArray(selectedReport.findings) ? selectedReport.findings : [];
                                        const filtered = rawList.filter(f => {
                                            if (findingsFilter === 'tp') return isFindingTruePositive(f);
                                            if (findingsFilter === 'fp') return !isFindingTruePositive(f);
                                            return true;
                                        });

                                        if (rawList.length === 0) {
                                            return (
                                                <tr>
                                                    <td colSpan="4" className="px-10 py-24 text-center opacity-50 font-black uppercase text-xs tracking-widest text-slate-500">
                                                        {selectedReport.status === 'RUNNING' || selectedReport.status === 'PENDING'
                                                            ? 'Audit sedang berlangsung di background engine...'
                                                            : 'Tidak ada temuan kerentanan tercatat.'}
                                                    </td>
                                                </tr>
                                            );
                                        }

                                        if (filtered.length === 0) {
                                            return (
                                                <tr>
                                                    <td colSpan="4" className="px-10 py-16 text-center opacity-60 font-black uppercase text-xs tracking-widest text-slate-500">
                                                        Tidak ada temuan dengan status {findingsFilter === 'tp' ? 'True Positive' : 'False Positive'}.
                                                    </td>
                                                </tr>
                                            );
                                        }

                                        return filtered.map((res, i) => (
                                        <tr key={i} className="hover:bg-slate-50 dark:hover:bg-red-600/5 transition-colors group">
                                            <td className="px-6 sm:px-10 py-6">
                                                <div className="flex items-center gap-4">
                                                    <div className="w-10 h-10 rounded-2xl bg-red-50 dark:bg-red-600/10 flex items-center justify-center border border-red-200 dark:border-red-600/20 group-hover:scale-110 transition-all">
                                                        <img src={logo} alt="L" className="w-6 h-6 object-contain" />
                                                    </div>
                                                    <div>
                                                         <div className="flex items-center gap-2 mb-1">
                                                             <span className="text-[7px] bg-red-50 text-red-600 border border-red-200 dark:bg-white/10 dark:text-white dark:border-white/20 px-1.5 py-0.5 rounded font-bold">
                                                                 {res.owasp_code || "A00:2021"} — {res.owasp || res.category || "Vulnerability"}
                                                             </span>
                                                             <div className="text-[8px] font-mono font-bold text-slate-400 dark:text-slate-500">{res.id || `COR-${i}`}</div>
                                                         </div>
                                                         <div className="text-sm font-black italic uppercase" style={{ color: 'var(--text-primary)' }}>
                                                            {res.name || res.type || "Identified Vulnerability"}
                                                         </div>
                                                     </div>
                                                </div>
                                            </td>
                                            <td className="px-6 sm:px-10 py-6">
                                                <div className="flex flex-col gap-1 items-start">
                                                    {/* Unified Severity & CVSS Score Badge */}
                                                    <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-xl text-[11px] font-black uppercase tracking-wider border shadow-xs ${
                                                        (res.severity || "INFO").toUpperCase() === 'CRITICAL' ? 'bg-red-500/15 dark:bg-red-950/60 text-red-700 dark:text-red-400 border-red-300/80 dark:border-red-800/60' :
                                                        (res.severity || "INFO").toUpperCase() === 'HIGH' ? 'bg-rose-500/15 dark:bg-rose-950/60 text-rose-700 dark:text-rose-400 border-rose-300/80 dark:border-rose-800/60' :
                                                        (res.severity || "INFO").toUpperCase() === 'MEDIUM' ? 'bg-amber-500/15 dark:bg-amber-950/60 text-amber-800 dark:text-amber-400 border-amber-300/80 dark:border-amber-800/60' :
                                                        (res.severity || "INFO").toUpperCase() === 'LOW' ? 'bg-yellow-500/15 dark:bg-yellow-950/60 text-yellow-800 dark:text-yellow-400 border-yellow-300/80 dark:border-yellow-800/60' :
                                                        'bg-sky-500/15 dark:bg-sky-950/60 text-sky-800 dark:text-sky-400 border-sky-300/80 dark:border-sky-800/60'
                                                    }`}>
                                                        <span className={`w-2 h-2 rounded-full ${
                                                            (res.severity || "INFO").toUpperCase() === 'CRITICAL' ? 'bg-red-600 dark:bg-red-500 animate-pulse' :
                                                            (res.severity || "INFO").toUpperCase() === 'HIGH' ? 'bg-rose-600 dark:bg-rose-500' :
                                                            (res.severity || "INFO").toUpperCase() === 'MEDIUM' ? 'bg-amber-600 dark:bg-amber-500' :
                                                            (res.severity || "INFO").toUpperCase() === 'LOW' ? 'bg-yellow-600 dark:bg-yellow-500' :
                                                            'bg-sky-600 dark:bg-sky-500'
                                                        }`}></span>
                                                        <span>{(res.severity || "INFO").toUpperCase() === 'INFORMATIONAL' ? 'INFO' : (res.severity || "INFO").toUpperCase()}</span>
                                                        <span className="text-[10px] font-mono font-bold opacity-80 pl-1.5 border-l border-current/25">
                                                            CVSS {getCvssScore(res)}
                                                        </span>
                                                    </span>

                                                    {/* Validation Verdict Badge (Dual-Engine AI-Brain + Random Forest) */}
                                                    {(() => {
                                                        const isTp = isFindingTruePositive(res);
                                                        const confScore = getFindingConfidenceScore(res);
                                                        if (isTp) {
                                                            return (
                                                                <span className="inline-flex items-center gap-1.5 text-[10px] font-bold text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-500/30 px-2.5 py-1 rounded-lg">
                                                                    <CheckCircle2 className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                                                                    <span>True Positive ({confScore}%)</span>
                                                                </span>
                                                            );
                                                        } else if (res.ai_brain_validation || res.rf_validation) {
                                                            return (
                                                                <span className="inline-flex items-center gap-1.5 text-[10px] font-bold text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/30 px-2.5 py-1 rounded-lg">
                                                                    <AlertTriangle className="w-3 h-3 text-red-600 dark:text-red-400" />
                                                                    <span>False Positive ({confScore}%)</span>
                                                                </span>
                                                            );
                                                        } else {
                                                            return (
                                                                <span className="inline-flex items-center gap-1.5 text-[10px] font-medium text-slate-500 dark:text-slate-400 bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 px-2.5 py-1 rounded-lg">
                                                                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-600"></span>
                                                                    <span>Analysis Standby</span>
                                                                </span>
                                                            );
                                                        }
                                                    })()}

                                                    {/* Random Forest Machine Learning Confidence Score */}
                                                    {res.rf_validation ? (
                                                        <span 
                                                            className={`inline-flex items-center gap-1.5 text-[10px] font-bold px-2.5 py-1 rounded-lg border ${
                                                                res.rf_validation.predicted_class === 'Valid Finding'
                                                                    ? 'text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-500/30'
                                                                    : 'text-rose-700 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-500/30'
                                                            }`}
                                                            title={`Random Forest: ${res.rf_validation.model_name || 'Active RF'} | P_RF: ${res.rf_validation.p_rf_pct}% | S_tool: ${res.rf_validation.s_tool} | CS: ${res.rf_validation.confidence_pct}%`}
                                                        >
                                                            <Cpu className="w-3 h-3 text-red-600" />
                                                            <span>RF: {res.rf_validation.predicted_class === 'Valid Finding' ? 'Valid' : 'FP'} ({res.rf_validation.confidence_pct || res.confidence_score}%)</span>
                                                        </span>
                                                    ) : res.confidence_score ? (
                                                        <span 
                                                            className="inline-flex items-center gap-1.5 text-[10px] font-bold px-2.5 py-1 rounded-lg border text-slate-700 dark:text-slate-300 bg-slate-100 dark:bg-slate-900 border-slate-200 dark:border-slate-800"
                                                            title="Composite Confidence Score"
                                                        >
                                                            <Cpu className="w-3 h-3 text-red-600" />
                                                            <span>RF Score: {res.confidence_score}%</span>
                                                        </span>
                                                    ) : null}
                                                </div>
                                            </td>
                                            <td className="px-6 sm:px-10 py-6">
                                                <code className="text-[10px] bg-slate-100 dark:bg-black/70 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 text-red-600 dark:text-red-400 font-mono italic">
                                                    {res.location || res.endpoint || "N/A"}
                                                </code>
                                            </td>
                                            <td className="px-6 sm:px-10 py-6 text-right">
                                                <button onClick={() => setShowDetail(res)} className="text-[10px] font-black text-red-600 hover:text-red-700 dark:hover:text-white uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-all cursor-pointer">
                                                    View Details →
                                                </button>
                                            </td>
                                        </tr>
                                    ));
                                })()}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}
        </div>

        {/* Modal for Selecting Second Report to Compare */}
        {showPickerForCompare && (
            <div 
                className="fixed inset-0 z-[99999] flex items-center justify-center p-4 bg-black/75 dark:bg-black/85 backdrop-blur-md overflow-y-auto"
                style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    width: '100vw',
                    height: '100dvh',
                }}
                onClick={() => setShowPickerForCompare(false)}
            >
                <div 
                    style={{
                        margin: 'auto',
                        width: '100%',
                        maxWidth: '32rem',
                        maxHeight: 'min(90vh, 90dvh)',
                    }}
                    className="corvus-card rounded-3xl p-6 sm:p-8 shadow-2xl border border-slate-200 dark:border-red-900/40 overflow-y-auto"
                    onClick={(e) => e.stopPropagation()}
                >
                    <div className="flex items-center justify-between pb-4 border-b border-slate-200 dark:border-red-900/20 mb-6">
                        <div className="flex items-center gap-3">
                            <div className="p-2 rounded-xl bg-red-600/10 text-red-500">
                                <GitCompare className="w-5 h-5" />
                            </div>
                            <div>
                                <h4 className="text-lg font-black italic uppercase" style={{ color: 'var(--text-primary)' }}>
                                    Select Report to Compare
                                </h4>
                                <p className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">
                                    Current Baseline: {selectedReport?.target}
                                </p>
                            </div>
                        </div>
                        <button onClick={() => setShowPickerForCompare(false)} className="text-slate-400 hover:text-red-500 cursor-pointer">
                            <X className="w-5 h-5" />
                        </button>
                    </div>

                    <div className="max-h-72 overflow-y-auto space-y-2 pr-1">
                        {(() => {
                            const candidateReports = reports.filter(r => r.id !== selectedReport?.id && normalizeTarget(r.target) === normalizeTarget(selectedReport?.target));
                            if (candidateReports.length === 0) {
                                return (
                                    <div className="p-8 text-center bg-slate-50 dark:bg-black/20 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-2">
                                        <p className="text-xs font-bold text-slate-700 dark:text-slate-300">
                                            Tidak ada riwayat scan lain untuk target ini.
                                        </p>
                                        <p className="text-[10px] text-slate-500 max-w-xs mx-auto">
                                            Lakukan pemindaian ulang pada target yang sama ({selectedReport?.target}) di Dashboard untuk menghasilkan data perbandingan delta.
                                        </p>
                                    </div>
                                );
                            }
                            return candidateReports.map((r) => (
                                <button
                                    key={r.id}
                                    onClick={() => {
                                        setShowPickerForCompare(false);
                                        setComparisonPair([selectedReport, r]);
                                    }}
                                    className="w-full p-4 rounded-2xl bg-slate-50 dark:bg-black/30 border border-slate-200 dark:border-slate-800 hover:border-red-500 text-left transition-all flex items-center justify-between group cursor-pointer"
                                >
                                    <div>
                                        <div className="text-xs font-black italic uppercase group-hover:text-red-600 dark:group-hover:text-red-400 transition-colors" style={{ color: 'var(--text-primary)' }}>
                                            {r.target}
                                        </div>
                                        <div className="text-[9px] text-slate-500 font-mono mt-0.5">
                                            {new Date(r.created_at).toLocaleString()} • {r.findings?.length || 0} findings
                                        </div>
                                    </div>
                                    <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-red-500 group-hover:translate-x-1 transition-all" />
                                </button>
                            ));
                        })()}
                    </div>

                    <div className="mt-6 pt-4 border-t border-slate-200 dark:border-red-900/20 flex justify-end">
                        <button
                            onClick={() => setShowPickerForCompare(false)}
                            className="px-5 py-2 rounded-xl bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 text-xs font-black uppercase tracking-wider hover:bg-slate-200 dark:hover:bg-slate-700 border border-slate-200 dark:border-transparent transition-all cursor-pointer"
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            </div>
        )}

        {/* Modal for Finding Detail */}
        <VulnDetailModal finding={showDetail} onClose={() => setShowDetail(null)} />

        {/* Modal for Report Comparison */}
        {comparisonPair && (
            <ReportComparisonModal 
                reportA={comparisonPair[0]} 
                reportB={comparisonPair[1]} 
                onClose={() => setComparisonPair(null)} 
            />
        )}
        </>
    );
};

export default ReportsPage;
