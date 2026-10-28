import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Link } from 'react-router-dom';
import { X, Brain, Sparkles, ShieldCheck, Cpu } from 'lucide-react';
import logo from '../assets/logo.png';
import AIBrainValidationCard from './AIBrainValidationCard';

const API_BASE = import.meta.env.VITE_API_URL || "/api";

const VulnDetailModal = ({ finding, onClose }) => {
    const [keys, setKeys] = useState([]);
    const [selectedKeyId, setSelectedKeyId] = useState("");
    const [action, setAction] = useState("analyze_all");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState("");
    const [error, setError] = useState("");
    const [fetchStatus, setFetchStatus] = useState(null);
    
    // Usefulness Survey State
    const [rating, setRating] = useState(0);
    const [surveySubmitted, setSurveySubmitted] = useState(false);

    // Close on Escape key
    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'Escape' && finding) {
                onClose();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [finding, onClose]);

    useEffect(() => {
        if (!finding) return;
        const fetchKeys = async () => {
            try {
                const token = localStorage.getItem('corvus_token');
                if (!token) return;
                const res = await fetch(`${API_BASE}/llm/keys`, {
                    headers: { "Authorization": `Bearer ${token}` }
                });
                if (res.ok) {
                    const data = await res.json();
                    setKeys(data);
                    if (data.length > 0) setSelectedKeyId(data[0].id);
                }
            } catch (err) {
                console.error(err);
            }
        };
        fetchKeys();
        // Reset states
        setResult("");
        setError("");
        setFetchStatus(null);
        setRating(0);
        setSurveySubmitted(false);
    }, [finding]);

    if (!finding) return null;

    const handleLlmAnalyze = async () => {
        setLoading(true);
        setResult("");
        setError("");
        setFetchStatus(null);
        setRating(0);
        setSurveySubmitted(false);
        try {
            const token = localStorage.getItem('corvus_token');
            const res = await fetch(`${API_BASE}/llm/analyze`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    key_id: parseInt(selectedKeyId) || 1,
                    vulnerability: {
                        type: finding.name || finding.type || "Web Vulnerability",
                        severity: finding.severity || "5.0",
                        endpoint: finding.endpoint || finding.location || "target-domain.com",
                        evidence: finding.evidence || finding.remediation || "",
                        caido_request_verb: finding.caido_request_verb || "GET",
                        caido_param_count: parseInt(finding.caido_param_count || 0),
                        caido_auth_headers_present: parseInt(finding.caido_auth_headers_present || 0),
                        caido_content_type: finding.caido_content_type || "other",
                        caido_response_size_mean: parseFloat(finding.caido_response_size_mean || 1000.0),
                        caido_response_size_std: parseFloat(finding.caido_response_size_std || 100.0),
                        caido_status_codes_seen: finding.caido_status_codes_seen || [200],
                        caido_endpoint_depth: parseInt(finding.caido_endpoint_depth || 1)
                    },
                    action: action
                })
            });
            const data = await res.json();
            if (res.ok) {
                setResult(data.result);
                if (data.fetch_status) setFetchStatus(data.fetch_status);
            } else {
                setError(data.detail || "Analysis failed.");
            }
        } catch (err) {
            setError("Server connection failed.");
        } finally {
            setLoading(false);
        }
    };

    const handleSurveySubmit = async (val) => {
        setRating(val);
        try {
            const token = localStorage.getItem('corvus_token');
            const res = await fetch(`${API_BASE}/llm/evaluate`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    rating: val,
                    feedback: "UI Star Survey",
                    finding_id: finding.id || "finding",
                    action: action
                })
            });
            if (res.ok) {
                setSurveySubmitted(true);
            }
        } catch (err) {
            console.error("Survey submission failed", err);
        }
    };

    return createPortal(
        <div 
            className="fixed inset-0 z-[99999] flex items-center justify-center p-4 sm:p-6 bg-black/75 dark:bg-black/90 backdrop-blur-md overflow-y-auto"
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
                    maxWidth: '56rem',
                    maxHeight: 'min(90vh, 90dvh)',
                }}
                className="bg-white dark:bg-[#0a0505] border border-slate-200 dark:border-red-900/30 rounded-[36px] shadow-2xl p-6 sm:p-10 relative overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
            >
                    <button onClick={onClose} className="absolute top-8 right-8 text-slate-400 hover:text-red-500 transition-colors cursor-pointer"><X className="w-8 h-8" /></button>
                <div className="flex items-center gap-6 mb-10">
                    <div className="p-3 rounded-3xl border border-red-500/20 dark:border-red-600/30 bg-red-500/10 dark:bg-red-950/20"><img src={logo} alt="L" className="w-14 h-14 object-contain" /></div>
                    <div>
                        <h3 className="text-2xl sm:text-3xl font-black text-slate-900 dark:text-white italic uppercase leading-none">{finding.name || finding.type}</h3>
                        <div className="flex items-center gap-3 mt-3">
                            <span className="bg-red-600 text-white text-[10px] px-3 py-1 rounded-md font-bold tracking-wider">{finding.owasp_code || "A00:2021"}</span>
                            <p className="text-xs font-black text-red-600 dark:text-white uppercase tracking-widest">{finding.category || "Vulnerability Finding"}</p>
                        </div>
                    </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-10 border-b border-slate-200 dark:border-red-900/10 pb-10 mb-10">
                    <div>
                        <h4 className="text-[10px] font-black text-slate-500 uppercase underline decoration-red-600 mb-4 tracking-widest italic">PoC Points</h4>
                        <ul className="space-y-3">
                            {(Array.isArray(finding.points) ? finding.points : (typeof finding.points === 'string' && finding.points.trim() ? [finding.points] : ["Manual validation required", "No automated proof points available"])).map((p, i) => (
                                <li key={i} className="text-xs text-slate-700 dark:text-slate-400 font-bold italic">• {p}</li>
                            ))}
                        </ul>
                    </div>
                    <div>
                        <h4 className="text-[10px] font-black text-slate-500 uppercase underline decoration-red-600 mb-4 tracking-widest italic">Mitigation</h4>
                        <div className="bg-red-50 dark:bg-red-950/10 border border-red-200 dark:border-red-900/20 p-6 rounded-3xl text-xs font-bold text-slate-800 dark:text-red-200/60 leading-relaxed italic">
                            {finding.remediation}
                        </div>
                        <div className="mt-6 flex justify-between items-center">
                            <span className="text-[9px] font-black text-slate-500 uppercase tracking-wider">CVSS Score</span>
                            <span className="text-3xl font-black text-red-600">{finding.cvss || "5.0"}</span>
                        </div>
                    </div>
                </div>

                {/* Pre-computed AI-Brain Validation Card */}
                {(finding.ai_brain_validation || finding.ai_brain_status) && (
                    <div className="border-b border-slate-200 dark:border-red-900/10 pb-8 mb-8">
                        <AIBrainValidationCard finding={finding} />
                    </div>
                )}

                {/* Random Forest & Composite Confidence Score Card */}
                {finding.rf_validation && (
                    <div className="border-b border-slate-200 dark:border-red-900/10 pb-8 mb-8">
                        <div className="corvus-card p-6 rounded-3xl space-y-4">
                            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                                <div className="flex items-center gap-2.5">
                                    <div className="p-2.5 rounded-2xl bg-red-600/10 text-red-600 border border-red-600/20">
                                        <Cpu className="w-5 h-5" />
                                    </div>
                                    <div>
                                        <h4 className="text-xs font-black uppercase tracking-wider text-slate-900 dark:text-white">
                                            Random Forest Machine Learning Analysis
                                        </h4>
                                        <p className="text-[9px] text-slate-500 font-bold uppercase tracking-wider">
                                            Model: {finding.rf_validation.model_name || "Active Random Forest"}
                                        </p>
                                    </div>
                                </div>
                                <span className={`px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-wider border self-start sm:self-auto ${
                                    finding.rf_validation.predicted_class === 'Valid Finding'
                                        ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border-emerald-200 dark:border-emerald-500/30'
                                        : 'bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-400 border-rose-200 dark:border-rose-500/30'
                                }`}>
                                    {finding.rf_validation.predicted_class} ({finding.rf_validation.confidence_pct || finding.confidence_score}%)
                                </span>
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-center">
                                <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-slate-800">
                                    <div className="text-[9px] font-bold text-slate-500 uppercase">P_RF (Probabilitas RF)</div>
                                    <div className="text-base font-black text-slate-900 dark:text-white font-mono mt-1">{finding.rf_validation.p_rf_pct}%</div>
                                </div>
                                <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-slate-800">
                                    <div className="text-[9px] font-bold text-slate-500 uppercase">S_tool (Konsensus Tools)</div>
                                    <div className="text-base font-black text-slate-900 dark:text-white font-mono mt-1">{finding.rf_validation.s_tool}</div>
                                </div>
                                <div className="p-3.5 rounded-2xl bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-slate-800">
                                    <div className="text-[9px] font-bold text-slate-500 uppercase">V_DOM (Validasi DOM)</div>
                                    <div className="text-base font-black text-slate-900 dark:text-white font-mono mt-1">{finding.rf_validation.v_dom === 1 ? 'Confirmed (1)' : 'N/A (0)'}</div>
                                </div>
                            </div>
                            <div className="text-[10px] text-slate-500 font-mono italic">
                                Rumus Bab 4: CS = (0.50 × P_RF) + (0.30 × S_tool) + (0.20 × V_DOM) = <strong className="text-red-600 dark:text-red-400">{finding.rf_validation.confidence_pct || finding.confidence_score}%</strong>
                            </div>
                        </div>
                    </div>
                )}

                {/* LLM Automated Cyber Security Analysis Drawer */}
                <div className="space-y-6">
                    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-slate-50 dark:bg-red-950/10 border border-slate-200 dark:border-red-900/20 p-6 rounded-3xl">
                        <div>
                            <h4 className="text-xs font-black text-slate-900 dark:text-white italic uppercase tracking-wider flex items-center gap-2">
                                <Brain className="w-4 h-4 text-red-500" />
                                LLM Cyber Security Analyst
                                <span className="text-[8px] bg-red-100 dark:bg-red-950 text-red-600 dark:text-red-400 border border-red-200 dark:border-red-800/40 px-2 py-0.5 rounded-full font-bold">Server Dual-LLM</span>
                            </h4>
                            <p className="text-[9px] text-slate-500 font-bold italic uppercase mt-1">
                                Automated classification, proof-of-concept explanation, or deep agentic validation
                            </p>
                        </div>
                                
                                <div className="flex flex-wrap items-center gap-3">
                                    {/* Action selection dropdown */}
                                    <select 
                                        value={action}
                                        onChange={(e) => setAction(e.target.value)}
                                        className="bg-white dark:bg-black/60 border border-slate-300 dark:border-slate-800 rounded-xl py-2 px-3 text-[10px] font-black text-slate-900 dark:text-white focus:outline-none focus:border-red-600 uppercase"
                                    >
                                        <option value="analyze_all">ANALYZE & ASSIST (EXPLAIN, REMEDIATE, SUMMARIZE, TP/FP)</option>
                                        <option value="deep_validate">Deep Validate (Ambil Bukti HTML)</option>
                                    </select>

                                    <button
                                        onClick={handleLlmAnalyze}
                                        disabled={loading}
                                        className="bg-red-600 hover:bg-white hover:text-red-900 text-white font-black py-2 px-4 rounded-xl transition-all uppercase tracking-widest text-[9px] disabled:grayscale active:scale-95 cursor-pointer shadow-md shadow-red-600/20"
                                    >
                                        {loading ? "Analyzing..." : "Analyze Finding"}
                                    </button>
                                </div>
                            </div>
                            
                            {action === 'deep_validate' && (
                                <div className="text-[9px] font-black text-orange-600 dark:text-orange-500 italic mt-2 ml-4">
                                    ⚠️ Deep Validate akan mengirim permintaan HTTP GET ke endpoint target. Pastikan Anda memiliki izin.
                                </div>
                            )}

                            {error && (
                                <div className="bg-red-50 dark:bg-red-600/10 border border-red-200 dark:border-red-600/20 p-4 rounded-2xl text-red-600 dark:text-red-400 font-bold italic text-xs">
                                    {error}
                                </div>
                            )}

                            {result && (
                                <div className="space-y-4">
                                    {fetchStatus && (
                                        <div className="flex">
                                            {fetchStatus === 'success' ? (
                                                <span className="bg-emerald-50 dark:bg-green-600/20 border border-emerald-200 dark:border-green-600/30 text-emerald-700 dark:text-green-500 text-[10px] font-black uppercase tracking-wider px-4 py-2 rounded-xl">
                                                    ✅ HTML Berhasil Diambil (Maks 400 Karakter)
                                                </span>
                                            ) : (
                                                <span className="bg-amber-50 dark:bg-yellow-600/20 border border-amber-200 dark:border-yellow-600/30 text-amber-700 dark:text-yellow-500 text-[10px] font-black uppercase tracking-wider px-4 py-2 rounded-xl">
                                                    ⚠️ Endpoint Tidak Merespons / Ditolak — Analisis Tetap Dilakukan
                                                </span>
                                            )}
                                        </div>
                                    )}
                                    <div className="bg-slate-50 dark:bg-black/60 border border-slate-200 dark:border-slate-800/80 rounded-3xl p-6 relative group overflow-hidden">
                                        <span className="text-[8px] font-black text-red-600 uppercase tracking-widest block mb-4 italic">LLM Analysis response</span>
                                        <div className="text-xs text-slate-800 dark:text-slate-300 font-medium leading-relaxed italic whitespace-pre-wrap font-mono">
                                            {result}
                                        </div>
                                        <div className="mt-6 pt-4 border-t border-slate-200 dark:border-slate-850 text-[9px] text-slate-500 font-bold italic">
                                            ⚠️ Hasil ini bersifat asistif. Keputusan akhir tetap pada analis manusia.
                                        </div>
                                    </div>
                                    
                                    {/* Usefulness Survey */}
                                    <div className="bg-slate-50 dark:bg-red-950/5 border border-slate-200 dark:border-red-900/10 p-5 rounded-2xl flex items-center justify-between">
                                        <span className="text-[10px] font-black text-slate-800 dark:text-white uppercase tracking-wider">Apakah analisis ini membantu?</span>
                                        {surveySubmitted ? (
                                            <span className="text-[10px] font-black text-emerald-600 dark:text-green-500 italic uppercase">Terima kasih atas feedback Anda!</span>
                                        ) : (
                                            <div className="flex items-center gap-1">
                                                {[1, 2, 3, 4, 5].map((val) => (
                                                    <button
                                                        key={val}
                                                        onClick={() => handleSurveySubmit(val)}
                                                        className="w-7 h-7 bg-slate-100 dark:bg-slate-900 border border-slate-300 dark:border-slate-800 hover:bg-red-600 hover:border-red-600 text-slate-700 dark:text-slate-400 hover:text-white rounded-lg text-xs font-black transition-all active:scale-90 cursor-pointer"
                                                    >
                                                        {val}
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                </div>
            </div>
        </div>,
        document.body
    );
};

export default VulnDetailModal;
