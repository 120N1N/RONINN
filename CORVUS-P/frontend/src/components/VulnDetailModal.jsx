import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { X } from 'lucide-react';
import logo from '../assets/logo.png';

const API_BASE = import.meta.env.VITE_API_URL || "/api";

const VulnDetailModal = ({ finding, onClose }) => {
    if (!finding) return null;
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

    useEffect(() => {
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

    const handleLlmAnalyze = async () => {
        if (!selectedKeyId) {
            setError("Please register and select an LLM API Key first in the API Keys menu.");
            return;
        }
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
                    key_id: parseInt(selectedKeyId),
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

    return (
        <div className="fixed inset-0 z-[1000] flex items-center justify-center p-6 bg-black/95 backdrop-blur-md overflow-y-auto animate-in fade-in duration-300">
            <div className="bg-[#0a0505] border border-red-900/30 w-full max-w-4xl rounded-[48px] shadow-2xl p-10 relative overflow-hidden my-8 max-h-[90vh] overflow-y-auto">
                <button onClick={onClose} className="absolute top-8 right-8 text-slate-500 hover:text-red-500 transition-colors"><X className="w-8 h-8" /></button>
                <div className="flex items-center gap-6 mb-10">
                    <div className="p-3 rounded-3xl border border-red-600/30 bg-red-950/20"><img src={logo} alt="L" className="w-14 h-14 object-contain" /></div>
                    <div>
                        <h3 className="text-3xl font-black text-white italic uppercase leading-none">{finding.name || finding.type}</h3>
                        <div className="flex items-center gap-3 mt-3">
                            <span className="bg-red-600 text-white text-[10px] px-3 py-1 rounded-md font-bold tracking-wider">{finding.owasp_code || "A00:2021"}</span>
                            <p className="text-xs font-black text-red-500 uppercase tracking-widest">{finding.category || "Vulnerability Finding"}</p>
                        </div>
                    </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-10 border-b border-red-900/10 pb-10 mb-10">
                    <div>
                        <h4 className="text-[10px] font-black text-slate-500 uppercase underline decoration-red-600 mb-4 tracking-widest italic">PoC Points</h4>
                        <ul className="space-y-3">
                            {(finding.points || ["Manual validation required", "No automated proof points available"]).map((p, i) => (
                                <li key={i} className="text-xs text-slate-400 font-bold italic">• {p}</li>
                            ))}
                        </ul>
                    </div>
                    <div>
                        <h4 className="text-[10px] font-black text-slate-500 uppercase underline decoration-red-600 mb-4 tracking-widest italic">Mitigation</h4>
                        <div className="bg-red-950/10 border border-red-900/20 p-6 rounded-3xl text-xs font-bold text-red-200/60 leading-relaxed italic">
                            {finding.remediation}
                        </div>
                        <div className="mt-6 flex justify-between items-center">
                            <span className="text-[9px] font-black text-slate-600 uppercase tracking-wider">CVSS Score</span>
                            <span className="text-3xl font-black text-red-600">{finding.cvss || "5.0"}</span>
                        </div>
                    </div>
                </div>

                {/* LLM Automated Cyber Security Analysis Drawer */}
                <div className="space-y-6">
                    {keys.length === 0 ? (
                        <div className="bg-red-950/10 border border-red-900/20 p-6 rounded-3xl text-center">
                            <p className="text-xs text-slate-400 font-bold italic">
                                Tambahkan API key di halaman{" "}
                                <span className="text-red-500 font-black">
                                    Administrator
                                </span>{" "}
                                untuk mengaktifkan analisis LLM.
                            </p>
                        </div>
                    ) : (
                        <>
                            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 bg-red-950/5 border border-red-900/15 p-6 rounded-3xl">
                                <div>
                                    <h4 className="text-xs font-black text-white italic uppercase tracking-wider flex items-center gap-2">
                                        LLM Cyber Security Assistant
                                    </h4>
                                    <p className="text-[9px] text-slate-500 font-bold italic uppercase mt-1">Get automated classification, explanation, or safe code remediations</p>
                                </div>
                                
                                <div className="flex flex-wrap items-center gap-3">
                                    {/* Key selection dropdown */}
                                    <select 
                                        value={selectedKeyId}
                                        onChange={(e) => setSelectedKeyId(e.target.value)}
                                        className="bg-black/60 border border-slate-800 rounded-xl py-2 px-3 text-[10px] font-black text-white focus:outline-none focus:border-red-600 uppercase"
                                    >
                                        {keys.map(k => (
                                            <option key={k.id} value={k.id}>{k.name || k.provider} ({k.provider.toUpperCase()})</option>
                                        ))}
                                    </select>

                                    {/* Action selection dropdown */}
                                    <select 
                                        value={action}
                                        onChange={(e) => setAction(e.target.value)}
                                        className="bg-black/60 border border-slate-800 rounded-xl py-2 px-3 text-[10px] font-black text-white focus:outline-none focus:border-red-600 uppercase"
                                    >
                                        <option value="analyze_all">ANALYZE & ASSIST (EXPLAIN, REMEDIATE, SUMMARIZE, TP/FP)</option>
                                        <option value="deep_validate">Deep Validate (Ambil Bukti HTML)</option>
                                    </select>

                                    <button
                                        onClick={handleLlmAnalyze}
                                        disabled={loading}
                                        className="bg-red-600 hover:bg-white hover:text-red-900 text-white font-black py-2 px-4 rounded-xl transition-all uppercase tracking-widest text-[9px] disabled:grayscale active:scale-95 cursor-pointer"
                                    >
                                        {loading ? "Analyzing..." : "Analyze Finding"}
                                    </button>
                                </div>
                            </div>
                            
                            {action === 'deep_validate' && (
                                <div className="text-[9px] font-black text-orange-500 italic mt-2 ml-4">
                                    ⚠️ Deep Validate akan mengirim permintaan HTTP GET ke endpoint target. Pastikan Anda memiliki izin.
                                </div>
                            )}

                            {error && (
                                <div className="bg-red-600/10 border border-red-600/20 p-4 rounded-2xl text-red-400 font-bold italic text-xs">
                                    {error}
                                </div>
                            )}

                            {result && (
                                <div className="space-y-4">
                                    {fetchStatus && (
                                        <div className="flex">
                                            {fetchStatus === 'success' ? (
                                                <span className="bg-green-600/20 border border-green-600/30 text-green-500 text-[10px] font-black uppercase tracking-wider px-4 py-2 rounded-xl">
                                                    ✅ HTML Berhasil Diambil (Maks 400 Karakter)
                                                </span>
                                            ) : (
                                                <span className="bg-yellow-600/20 border border-yellow-600/30 text-yellow-500 text-[10px] font-black uppercase tracking-wider px-4 py-2 rounded-xl">
                                                    ⚠️ Endpoint Tidak Merespons / Ditolak — Analisis Tetap Dilakukan
                                                </span>
                                            )}
                                        </div>
                                    )}
                                    <div className="bg-black/60 border border-slate-800/80 rounded-3xl p-6 relative group overflow-hidden">
                                        <span className="text-[8px] font-black text-red-600 uppercase tracking-widest block mb-4 italic">LLM Analysis response</span>
                                        <div className="text-xs text-slate-300 font-medium leading-relaxed italic whitespace-pre-wrap font-mono">
                                            {result}
                                        </div>
                                        <div className="mt-6 pt-4 border-t border-slate-850 text-[9px] text-slate-500 font-bold italic">
                                            ⚠️ Hasil ini bersifat asistif. Keputusan akhir tetap pada analis manusia.
                                        </div>
                                    </div>
                                    
                                    {/* Usefulness Survey */}
                                    <div className="bg-red-950/5 border border-red-900/10 p-5 rounded-2xl flex items-center justify-between">
                                        <span className="text-[10px] font-black text-white uppercase tracking-wider">Apakah analisis ini membantu?</span>
                                        {surveySubmitted ? (
                                            <span className="text-[10px] font-black text-green-500 italic uppercase">Terima kasih atas feedback Anda!</span>
                                        ) : (
                                            <div className="flex items-center gap-1">
                                                {[1, 2, 3, 4, 5].map((val) => (
                                                    <button
                                                        key={val}
                                                        onClick={() => handleSurveySubmit(val)}
                                                        className="w-7 h-7 bg-slate-900 border border-slate-800 hover:bg-red-600 hover:border-red-600 text-slate-400 hover:text-white rounded-lg text-xs font-black transition-all active:scale-90 cursor-pointer"
                                                    >
                                                        {val}
                                                    </button>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </>
                    )}
                </div>

            </div>
        </div>
    );
};

export default VulnDetailModal;
