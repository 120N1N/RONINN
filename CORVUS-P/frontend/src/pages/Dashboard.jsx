import React, { useState, useEffect, useRef, useMemo } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Target, Search, Activity, FileText, CheckCircle2, Terminal, Copy, Check, ArrowDown, Brain, ShieldCheck, Filter, Trash2, Lock, AlertTriangle } from 'lucide-react';
import logo from '../assets/logo.png';
import VulnDetailModal from '../components/VulnDetailModal';
import ReconResults from '../components/ReconResults';
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

const Dashboard = ({ user }) => {
    const navigate = useNavigate();
    const token = localStorage.getItem('corvus_token');
    const isAuthenticated = Boolean(user && token);

    const [target, setTarget] = useState("");
    const [isScanning, setIsScanning] = useState(false);
    const [activeScan, setActiveScan] = useState(null);
    const [showDetail, setShowDetail] = useState(null);
    const [mode, setMode] = useState("normal");
    const [scanSubdomains, setScanSubdomains] = useState(true);
    const [scanError, setScanError] = useState(null);

    // Live logs & terminal states
    const [liveLogs, setLiveLogs] = useState([]);
    const [autoScroll, setAutoScroll] = useState(true);
    const [copiedLogs, setCopiedLogs] = useState(false);
    const [findingsFilter, setFindingsFilter] = useState('all'); // 'all' | 'tp' | 'fp'
    const logContainerRef = useRef(null);

    // Initial sync on mount: check localStorage or fetch active scan from backend
    useEffect(() => {
        const token = localStorage.getItem('corvus_token');
        if (!token) return;

        const checkScan = (scanId) => {
            fetch(`${API_BASE}/scan/${scanId}`, {
                headers: { "Authorization": `Bearer ${token}` }
            })
            .then(r => r.ok ? r.json() : null)
            .then(d => {
                if (d) {
                    setActiveScan(d);
                    if (d.target) setTarget(d.target);
                    if (d.logs && Array.isArray(d.logs)) {
                        setLiveLogs(d.logs);
                    }
                    if (d.status === "RUNNING" || d.status === "PENDING") {
                        setIsScanning(true);
                    } else {
                        setIsScanning(false);
                    }
                } else {
                    checkActiveOnServer();
                }
            })
            .catch(() => checkActiveOnServer());
        };

        const checkActiveOnServer = () => {
            fetch(`${API_BASE}/scans/active`, {
                headers: { "Authorization": `Bearer ${token}` }
            })
            .then(r => r.ok ? r.json() : null)
            .then(d => {
                if (d && (d.status === "RUNNING" || d.status === "PENDING")) {
                    setActiveScan(d);
                    setIsScanning(true);
                    if (d.target) setTarget(d.target);
                    if (d.logs && Array.isArray(d.logs)) {
                        setLiveLogs(d.logs);
                    }
                    localStorage.setItem('corvus_active_scan_id', d.id);
                }
            })
            .catch(() => {});
        };

        const savedScanId = localStorage.getItem('corvus_active_scan_id');
        if (savedScanId) {
            checkScan(savedScanId);
        } else {
            checkActiveOnServer();
        }
    }, []);

    // WebSocket real-time live log listener
    useEffect(() => {
        if (!activeScan?.id) return;

        const isHttps = window.location.protocol === 'https:';
        const wsProto = isHttps ? 'wss:' : 'ws:';
        let wsHost = window.location.host;
        let wsUrl;

        const token = localStorage.getItem('corvus_token') || '';
        const tokenQuery = token ? `?token=${encodeURIComponent(token)}` : '';

        if (API_BASE.startsWith('http')) {
            try {
                const u = new URL(API_BASE);
                const proto = u.protocol === 'https:' ? 'wss:' : 'ws:';
                wsUrl = `${proto}//${u.host}/api/ws/scans/${activeScan.id}/log${tokenQuery}`;
            } catch (e) {
                wsUrl = `${wsProto}//${wsHost}/api/ws/scans/${activeScan.id}/log${tokenQuery}`;
            }
        } else {
            wsUrl = `${wsProto}//${wsHost}/api/ws/scans/${activeScan.id}/log${tokenQuery}`;
        }

        let ws;
        const buffer = [];
        let flushTimer = null;

        const flushBuffer = () => {
            if (buffer.length > 0) {
                const incoming = [...buffer];
                buffer.length = 0;
                setLiveLogs(prev => {
                    const existingSet = new Set(prev);
                    const newItems = incoming.filter(item => !existingSet.has(item));
                    if (newItems.length === 0) return prev;
                    return [...prev, ...newItems];
                });
            }
            flushTimer = null;
        };

        try {
            ws = new WebSocket(wsUrl);
            ws.onmessage = (event) => {
                if (event.data) {
                    buffer.push(event.data);
                    if (!flushTimer) {
                        flushTimer = setTimeout(flushBuffer, 120);
                    }
                }
            };
        } catch (wsErr) {
            // WebSockets fallback to polling gracefully
        }

        return () => {
            if (flushTimer) clearTimeout(flushTimer);
            if (ws) ws.close();
        };
    }, [activeScan?.id]);

    // Synchronize liveLogs with activeScan.logs from polling (lightweight & debounced)
    useEffect(() => {
        if (Array.isArray(activeScan?.logs) && activeScan.logs.length > 0) {
            setLiveLogs(prev => {
                if (prev.length === 0) return activeScan.logs;
                if (prev.length >= activeScan.logs.length) return prev;
                const existingSet = new Set(prev);
                const newItems = activeScan.logs.filter(line => !existingSet.has(line));
                if (newItems.length === 0) return prev;
                return [...prev, ...newItems];
            });
        }
    }, [activeScan?.logs?.length]);

    // Auto-scroll inside terminal container only (throttled via requestAnimationFrame)
    useEffect(() => {
        if (autoScroll && logContainerRef.current) {
            requestAnimationFrame(() => {
                if (logContainerRef.current) {
                    logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
                }
            });
        }
    }, [liveLogs.length, autoScroll]);

    const handleScan = async (e) => {
        e.preventDefault();
        const currentToken = localStorage.getItem('corvus_token');
        if (!user || !currentToken) {
            setScanError("Akses ditolak: Silakan login terlebih dahulu untuk melakukan scanning.");
            navigate("/login");
            return;
        }

        setIsScanning(true);
        setLiveLogs([]);
        const token = currentToken;
        try {
            setScanError(null);
            const res = await fetch(`${API_BASE}/scan`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({ target, mode, include_subdomain: scanSubdomains })
            });
            
            if (res.ok) {
                const data = await res.json();
                setActiveScan(data);
                if (data && data.id) {
                    localStorage.setItem('corvus_active_scan_id', data.id);
                }
            } else {
                let errorMsg = "Scan failed to initiate. Please check login status or server health.";
                try {
                    const errorData = await res.json();
                    errorMsg = errorData.detail || errorData.error || errorMsg;
                    if (typeof errorMsg !== 'string') {
                        errorMsg = JSON.stringify(errorMsg);
                    }
                } catch (parseErr) {}
                setScanError(errorMsg);
                setIsScanning(false);
            }
        } catch (networkErr) {
            setScanError("Network error. Could not connect to the scanner API.");
            setIsScanning(false);
        }
    };

    const handleResetScan = () => {
        if (isScanning && !window.confirm("Scanning sedang berlangsung di latar belakang. Tetap ingin memulai audit baru?")) return;
        setActiveScan(null);
        setIsScanning(false);
        setTarget("");
        setLiveLogs([]);
        localStorage.removeItem('corvus_active_scan_id');
    };

    const handleCopyLogs = () => {
        if (!liveLogs || liveLogs.length === 0) return;
        navigator.clipboard.writeText(liveLogs.join('\n'));
        setCopiedLogs(true);
        setTimeout(() => setCopiedLogs(false), 2000);
    };

    const handleClearLogs = () => {
        setLiveLogs([]);
    };

    useEffect(() => {
        let interval;
        if (activeScan && (activeScan.status === "RUNNING" || activeScan.status === "PENDING")) {
            interval = setInterval(() => {
                const token = localStorage.getItem('corvus_token');
                fetch(`${API_BASE}/scan/${activeScan.id}`, {
                    headers: { "Authorization": `Bearer ${token}` }
                }).then(r => r.json()).then(d => {
                    if (d) {
                        setActiveScan(d);
                        if (d.status === 'COMPLETED' || d.status === 'FAILED') {
                            setIsScanning(false);
                        }
                    }
                }).catch(err => console.error("Polling error:", err));
            }, 2000);
        }
        return () => clearInterval(interval);
    }, [activeScan?.id, activeScan?.status]);

    // Auto-clear error after 5 seconds
    useEffect(() => {
        if (scanError) {
            const timer = setTimeout(() => setScanError(null), 5000);
            return () => clearTimeout(timer);
        }
    }, [scanError]);

    // Filter findings (memoized for 60fps responsiveness)
    const allFindings = useMemo(() => {
        return Array.isArray(activeScan?.findings) ? activeScan.findings : [];
    }, [activeScan?.findings]);

    const filteredFindings = useMemo(() => {
        return allFindings.filter(f => {
            if (findingsFilter === 'tp') {
                return isFindingTruePositive(f);
            }
            if (findingsFilter === 'fp') {
                return !isFindingTruePositive(f);
            }
            return true;
        });
    }, [allFindings, findingsFilter]);

    // Display last 200 log lines in DOM for ultra-smooth scrolling without layout thrashing
    const displayLogs = useMemo(() => {
        return liveLogs.slice(-200);
    }, [liveLogs]);

    const formatLogLine = (line) => {
        if (line.includes('[✓]') || line.includes('[ OK ]')) {
            return 'text-emerald-700 dark:text-emerald-400 font-bold';
        }
        if (line.includes('[!]') || line.includes('[ERROR]') || line.includes('ABORTED') || line.includes('FAILED')) {
            return 'text-red-600 dark:text-red-400 font-bold';
        }
        if (line.includes('[AI-Analyst]') || line.includes('[AI-Brain]') || line.includes('[ai-brain]')) {
            return 'text-purple-700 dark:text-purple-400 font-semibold';
        }
        if (line.includes('[VulnCore]')) {
            return 'text-amber-700 dark:text-orange-400 font-semibold';
        }
        if (line.includes('[recon]') || line.includes('[discovery') || line.includes('[katana]') || line.includes('[dalfox]') || line.includes('[nuclei]')) {
            return 'text-sky-700 dark:text-cyan-400 font-semibold';
        }
        if (line.startsWith('===') || line.startsWith('[*] Phase')) {
            return 'text-slate-900 dark:text-white font-black underline decoration-red-600/50';
        }
        return 'text-slate-700 dark:text-slate-300';
    };

    return (
        <>
        <div className="space-y-6 sm:space-y-8 animate-in fade-in duration-1000">
            <div className="grid grid-cols-1 lg:grid-cols-12 xl:grid-cols-12 2xl:grid-cols-12 gap-6 sm:gap-8">
                <div className="lg:col-span-7 xl:col-span-8 2xl:col-span-8 flex flex-col gap-6 sm:gap-8">
                    <section className="corvus-card p-5 sm:p-8 md:p-10 rounded-3xl md:rounded-[40px] shadow-2xl relative overflow-hidden group flex-shrink-0">
                        <div className="flex justify-between items-center mb-6 sm:mb-8">
                            <h2 className="text-xl sm:text-2xl font-black flex items-center gap-3 italic" style={{ color: 'var(--text-primary)' }}>
                                <Target className="w-5 h-5 sm:w-6 sm:h-6 text-red-600" />
                                INITIATE AUDIT CENTER
                            </h2>
                            {activeScan && (
                                <button
                                    type="button"
                                    onClick={handleResetScan}
                                    className="text-[10px] font-black uppercase tracking-widest text-slate-600 dark:text-slate-400 hover:text-red-600 border border-slate-300 dark:border-slate-800 hover:border-red-600 px-3 py-1.5 rounded-xl transition-all bg-slate-100 dark:bg-black/40 cursor-pointer"
                                >
                                    + New Audit
                                </button>
                            )}
                        </div>
                        
                        {scanError && (
                            <div className="mb-6 p-4 rounded-2xl bg-red-900/20 border border-red-600/30 flex items-center gap-3 animate-in fade-in zoom-in-95 duration-300">
                                <div className="w-2 h-full bg-red-600 rounded-full"></div>
                                <p className="text-xs sm:text-sm text-red-500 font-mono flex-1">{scanError}</p>
                                <button onClick={() => setScanError(null)} className="text-red-500/50 hover:text-red-500 font-black px-2 transition-colors">X</button>
                            </div>
                        )}

                        {!isAuthenticated && (
                            <div className="mb-6 p-4 rounded-2xl bg-amber-500/10 dark:bg-amber-950/30 border border-amber-500/30 dark:border-amber-600/30 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 animate-in fade-in duration-300">
                                <div className="flex items-center gap-3">
                                    <Lock className="w-5 h-5 text-amber-500 flex-shrink-0" />
                                    <div>
                                        <p className="text-xs font-black text-amber-700 dark:text-amber-300 uppercase tracking-wider">Unauthenticated Session</p>
                                        <p className="text-[11px] text-amber-600 dark:text-amber-400/80">Silakan login terlebih dahulu untuk memulai pemindaian kerentanan (audit).</p>
                                    </div>
                                </div>
                                <Link to="/login" className="px-4 py-2 bg-amber-600 hover:bg-amber-500 text-white dark:text-black font-black text-[10px] uppercase tracking-widest rounded-xl transition-all flex-shrink-0">
                                    Login to Scan
                                </Link>
                            </div>
                        )}
                        
                        <form onSubmit={handleScan} className="space-y-6 sm:space-y-8">
                            <div className="relative">
                                <input
                                    type="text"
                                    placeholder={!isAuthenticated ? "Silakan login terlebih dahulu untuk memasukkan target..." : "Enter target (e.g., identity.corvus.net or https://target.com)"}
                                    className="w-full bg-slate-50 dark:bg-black/60 border border-slate-300 dark:border-slate-800 rounded-2xl sm:rounded-3xl py-4 sm:py-6 px-6 sm:px-8 pl-12 sm:pl-16 text-sm sm:text-lg md:text-xl focus:outline-none focus:border-red-600 transition-all text-slate-900 dark:text-white placeholder:text-slate-400 dark:placeholder:text-slate-700 disabled:opacity-50"
                                    value={target}
                                    onChange={(e) => setTarget(e.target.value)}
                                    disabled={isScanning || !isAuthenticated}
                                />
                                <Search className="absolute left-4 sm:left-6 top-1/2 -translate-y-1/2 text-red-600 w-5 h-5 sm:w-7 sm:h-7" />
                            </div>

                            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 sm:gap-6">
                                <div className="bg-slate-100/80 dark:bg-black/40 p-4 sm:p-5 rounded-2xl border border-slate-200 dark:border-slate-800 flex items-center justify-between">
                                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest italic">Phase</span>
                                    <select 
                                        value={mode}
                                        onChange={(e) => setMode(e.target.value)}
                                        disabled={!isAuthenticated || isScanning}
                                        className="bg-transparent text-xs font-black text-red-600 focus:outline-none cursor-pointer uppercase font-sans disabled:opacity-50"
                                    >
                                        <option value="quick" className="bg-white dark:bg-black text-slate-900 dark:text-white">Quick</option>
                                        <option value="normal" className="bg-white dark:bg-black text-slate-900 dark:text-white">Normal</option>
                                        <option value="deep" className="bg-white dark:bg-black text-slate-900 dark:text-white">Deep</option>
                                    </select>
                                </div>
                                <div 
                                    onClick={() => isAuthenticated && !isScanning && setScanSubdomains(!scanSubdomains)}
                                    className={`bg-slate-100/80 dark:bg-black/40 p-4 sm:p-5 rounded-2xl border border-slate-200 dark:border-slate-800 flex items-center justify-between transition-colors ${!isAuthenticated || isScanning ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer group hover:bg-slate-200/50 dark:hover:bg-black/60'}`}
                                >
                                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest italic group-hover:text-slate-700 dark:group-hover:text-slate-400 transition-colors">Subdomains</span>
                                    <div className={`w-4 h-4 rounded flex items-center justify-center transition-colors ${scanSubdomains ? 'bg-red-600' : 'bg-slate-300 dark:bg-slate-800'}`}>
                                        {scanSubdomains && <CheckCircle2 className="w-3 h-3 text-white" />}
                                    </div>
                                </div>
                                <button
                                    type={isAuthenticated ? "submit" : "button"}
                                    onClick={!isAuthenticated ? () => navigate("/login") : undefined}
                                    disabled={isScanning || (isAuthenticated && !target)}
                                    className="bg-red-600 hover:bg-white hover:text-red-900 text-white font-black py-4 sm:py-5 px-6 sm:px-8 rounded-2xl transition-all shadow-xl shadow-red-600/20 active:scale-95 disabled:grayscale uppercase tracking-widest text-xs col-span-1 sm:col-span-2 md:col-span-1 cursor-pointer"
                                >
                                    {!isAuthenticated ? 'LOGIN TO SCAN' : (isScanning ? 'SYSTEM RUNNING...' : 'LAUNCH CORVUS')}
                                </button>
                            </div>
                        </form>
                    </section>

                    {/* LIVE TOOL EXECUTION LOG */}
                    <section className="corvus-card p-5 sm:p-7 rounded-3xl md:rounded-[40px] shadow-2xl flex-1 flex flex-col min-h-[360px] max-h-[490px] overflow-hidden">
                        {/* Polished Terminal Window Chrome & Header */}
                        <div className="flex flex-wrap justify-between items-center gap-3 pb-3 border-b border-slate-200/70 dark:border-slate-800/80 mb-3">
                            {/* Window Dots, Title & Badges */}
                            <div className="flex items-center gap-2.5 sm:gap-3 flex-wrap">
                                <div className="hidden sm:flex items-center gap-1.5 pr-1">
                                    <span className="w-2.5 h-2.5 rounded-full bg-red-500/80 border border-red-600/30"></span>
                                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500/80 border border-amber-600/30"></span>
                                    <span className="w-2.5 h-2.5 rounded-full bg-emerald-500/80 border border-emerald-600/30"></span>
                                </div>

                                <div className="flex items-center gap-2">
                                    <div className="p-1.5 rounded-lg bg-red-50 dark:bg-red-950/60 text-red-600 dark:text-red-400 border border-red-200/60 dark:border-red-900/40">
                                        <Terminal className="w-3.5 h-3.5" />
                                    </div>
                                    <h2 className="text-[11px] font-mono font-bold tracking-wider text-slate-800 dark:text-slate-200">
                                        LIVE TOOL EXECUTION LOG
                                    </h2>
                                </div>

                                {isScanning ? (
                                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800/60 text-[10px] font-mono font-bold text-emerald-700 dark:text-emerald-400">
                                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
                                        STREAMING
                                    </span>
                                ) : (
                                    <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[10px] font-mono font-medium text-slate-500 dark:text-slate-400">
                                        <span className="w-1.5 h-1.5 rounded-full bg-slate-400 dark:bg-slate-600"></span>
                                        IDLE
                                    </span>
                                )}

                                <span className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-slate-100 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-slate-600 dark:text-slate-400 font-semibold shadow-xs">
                                    {liveLogs.length} events
                                </span>
                            </div>

                            {/* Unified Segmented Control Toolbar */}
                            <div className="flex items-center gap-1 bg-slate-100/90 dark:bg-slate-900/90 p-1 rounded-xl border border-slate-200 dark:border-slate-800 shadow-xs">
                                <button 
                                    onClick={() => setAutoScroll(!autoScroll)}
                                    title="Toggle auto-scroll to latest log"
                                    className={`text-[10px] px-2.5 py-1 rounded-lg font-mono font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
                                        autoScroll 
                                            ? 'bg-white dark:bg-red-950/70 text-red-600 dark:text-red-400 shadow-xs border border-slate-200/80 dark:border-red-900/50' 
                                            : 'text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white'
                                    }`}
                                >
                                    <ArrowDown className={`w-3 h-3 ${autoScroll ? 'text-red-600 dark:text-red-400' : 'text-slate-400'}`} />
                                    <span>Scroll</span>
                                </button>

                                <div className="w-[1px] h-3.5 bg-slate-200 dark:bg-slate-800"></div>

                                <button 
                                    onClick={handleCopyLogs}
                                    disabled={liveLogs.length === 0}
                                    title="Copy logs to clipboard"
                                    className="text-[10px] px-2.5 py-1 rounded-lg font-mono font-bold text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white hover:bg-white dark:hover:bg-slate-800 transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                                >
                                    {copiedLogs ? <Check className="w-3 h-3 text-emerald-600 dark:text-emerald-400" /> : <Copy className="w-3 h-3 text-slate-400" />}
                                    <span>{copiedLogs ? 'Copied' : 'Copy'}</span>
                                </button>

                                <div className="w-[1px] h-3.5 bg-slate-200 dark:bg-slate-800"></div>

                                <button 
                                    onClick={handleClearLogs}
                                    disabled={liveLogs.length === 0}
                                    title="Clear display logs"
                                    className="text-[10px] px-2.5 py-1 rounded-lg font-mono font-bold text-slate-500 hover:text-red-600 dark:text-slate-400 dark:hover:text-red-400 hover:bg-white dark:hover:bg-slate-800 transition-all flex items-center gap-1 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                                >
                                    <Trash2 className="w-3 h-3" />
                                    <span>Clear</span>
                                </button>
                            </div>
                        </div>

                        {/* Terminal Body: Clean Slate-50 in Light, Stealth Dark in Dark Mode */}
                        <div 
                            ref={logContainerRef}
                            style={{ overscrollBehavior: 'contain' }}
                            className="bg-slate-50 dark:bg-[#070404] rounded-2xl sm:rounded-3xl p-4 sm:p-5 border border-slate-200/90 dark:border-red-950/40 flex-1 font-mono text-xs overflow-y-auto overflow-x-hidden relative shadow-inner space-y-1.5 scrollbar-thin scrollbar-thumb-slate-300 dark:scrollbar-thumb-slate-800 max-h-[360px] break-all"
                        >
                            <div className="leading-relaxed">
                                <span className="text-red-600 dark:text-red-500 font-bold">root@corvus</span>
                                <span className="text-slate-400 dark:text-slate-600">:~#</span> systemctl status corvus_engine
                            </div>
                            <div className="text-emerald-700 dark:text-green-500 font-medium leading-relaxed">
                                [ OK ] Corvus Vulnerability Scanning Engine standby &amp; operational.
                            </div>

                            {!isScanning && !activeScan && liveLogs.length === 0 && (
                                <div className="text-slate-400 dark:text-slate-500 mt-4 italic">
                                    _ waiting for target specification to launch live audit...
                                </div>
                            )}

                            {isScanning && liveLogs.length === 0 && (
                                <>
                                    <div className="text-slate-800 dark:text-slate-200">
                                        [*] Engaging target: <span className="text-red-600 dark:text-red-400 font-bold">{target || activeScan?.target}</span>
                                    </div>
                                    <div className="text-amber-700 dark:text-yellow-500">
                                        [-] Deploying phase: {activeScan?.current_step || "INITIALIZING"} ({activeScan?.progress || 0}%) ...
                                    </div>
                                </>
                            )}

                            {displayLogs.map((logLine, i) => (
                                <div key={i} className={`leading-relaxed hover:bg-slate-200/60 dark:hover:bg-white/[0.04] px-1.5 py-0.5 rounded transition-colors break-all ${formatLogLine(logLine)}`}>
                                    &gt; {logLine}
                                </div>
                            ))}

                            {!isScanning && activeScan && activeScan.status === 'COMPLETED' && liveLogs.length === 0 && (
                                <div className="text-emerald-700 dark:text-green-400 font-bold mt-2">
                                    [✓] Audit completed for {activeScan.target}. Total findings: {activeScan.findings?.length || 0}
                                </div>
                            )}

                            {!isScanning && activeScan && activeScan.status === 'FAILED' && liveLogs.length === 0 && (
                                <div className="text-red-600 dark:text-red-400 font-bold mt-2">
                                    [!] Audit stopped: {activeScan.current_step}
                                </div>
                            )}

                            {isScanning && (
                                <div className="text-red-600 dark:text-red-500 font-bold animate-pulse flex items-center gap-1.5 pt-1">
                                    <span className="w-2 h-2 rounded-full bg-red-600 animate-ping"></span>
                                    <span>_ stream active ({activeScan?.current_step || 'RUNNING'})</span>
                                </div>
                            )}
                        </div>
                    </section>
                </div>

                <div className="lg:col-span-5 xl:col-span-4 2xl:col-span-4">
                    <section className="corvus-card p-5 sm:p-8 md:p-10 rounded-3xl md:rounded-[40px] h-full flex flex-col justify-between">
                        <div>
                            <h2 className="text-xl font-black mb-8 flex items-center gap-3 italic" style={{ color: 'var(--text-primary)' }}>
                                <Activity className="w-6 h-6 text-red-600" /> ACTIVE STATUS
                            </h2>
                            <div className="space-y-8">
                                <div className="flex flex-col gap-3">
                                    <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-widest">
                                        <span className="text-slate-500">Execution Progress</span>
                                        <span className="text-red-500 font-bold">{activeScan?.progress || 0}%</span>
                                    </div>
                                    <div className="w-full bg-slate-200 dark:bg-slate-950 rounded-full h-2 border border-slate-300 dark:border-slate-900 overflow-hidden">
                                        <div className="bg-red-600 h-full transition-all duration-700 shadow-[0_0_15px_#dc2626]" style={{ width: `${activeScan?.progress || 0}%` }} />
                                    </div>
                                </div>
                                <div className="flex items-center gap-4 bg-slate-100/80 dark:bg-black/40 p-5 rounded-3xl border border-slate-200 dark:border-slate-800/50">
                                    <div className={`w-3 h-3 rounded-full ${isScanning ? 'bg-red-600 animate-pulse shadow-[0_0_10px_#dc2626]' : 'bg-emerald-500'}`} />
                                    <div className="flex flex-col">
                                        <span className="text-[9px] text-slate-500 font-black uppercase tracking-widest">Current Task</span>
                                        <span className="text-xs font-black italic uppercase" style={{ color: 'var(--text-primary)' }}>{activeScan?.current_step || "IDLE"}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="mt-10 pt-8 border-t border-slate-200 dark:border-slate-800/50 grid grid-cols-2 gap-4 text-center">
                            <div className="p-4 bg-red-50 dark:bg-red-600/10 rounded-2xl border border-red-200 dark:border-red-900/10">
                                <p className="text-2xl font-black text-red-600 tracking-tighter">{Array.isArray(activeScan?.findings) ? activeScan.findings.filter(f => (f.severity || "").toUpperCase() === 'CRITICAL')?.length : 0}</p>
                                <p className="text-[8px] text-slate-600 dark:text-slate-400 uppercase font-black">Critical</p>
                            </div>
                            <div className="p-4 bg-orange-50 dark:bg-orange-600/10 rounded-2xl border border-orange-200 dark:border-orange-900/10">
                                <p className="text-2xl font-black text-orange-600 tracking-tighter">{Array.isArray(activeScan?.findings) ? activeScan.findings.filter(f => (f.severity || "").toUpperCase() === 'HIGH')?.length : 0}</p>
                                <p className="text-[8px] text-slate-600 dark:text-slate-400 uppercase font-black">High</p>
                            </div>
                            <div className="p-4 bg-yellow-50 dark:bg-yellow-600/10 rounded-2xl border border-yellow-200 dark:border-yellow-900/10">
                                <p className="text-2xl font-black text-yellow-600 tracking-tighter">{Array.isArray(activeScan?.findings) ? activeScan.findings.filter(f => (f.severity || "").toUpperCase() === 'MEDIUM')?.length : 0}</p>
                                <p className="text-[8px] text-slate-600 dark:text-slate-400 uppercase font-black">Medium</p>
                            </div>
                            <div className="p-4 bg-blue-50 dark:bg-blue-600/10 rounded-2xl border border-blue-200 dark:border-blue-900/10">
                                <p className="text-2xl font-black text-blue-600 tracking-tighter">{Array.isArray(activeScan?.findings) ? activeScan.findings.filter(f => ['LOW', 'INFO', 'INFORMATIONAL'].includes((f.severity || "").toUpperCase()))?.length : 0}</p>
                                <p className="text-[8px] text-slate-600 dark:text-slate-400 uppercase font-black">Low / Info</p>
                            </div>
                        </div>
                    </section>
                </div>
            </div>

            <ReconResults activeScan={activeScan} />

            {/* AI-BRAIN SECURITY ANALYST SUMMARY CARD */}
            <AIBrainSummary 
                findings={allFindings} 
                activeFilter={findingsFilter} 
                onSelectFilter={setFindingsFilter} 
            />

            {/* VULNERABILITY ANALYSIS TABLE */}
            <section className="corvus-card rounded-[40px] sm:rounded-[48px] overflow-hidden shadow-2xl">
                <div className="p-6 sm:p-10 border-b border-slate-200 dark:border-red-900/10 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-slate-50/70 dark:bg-black/20">
                    <div className="flex items-center gap-4">
                        <FileText className="w-7 h-7 text-red-600" />
                        <div>
                            <h2 className="text-2xl font-black italic tracking-tighter" style={{ color: 'var(--text-primary)' }}>
                                VULNERABILITY ANALYSIS
                            </h2>
                            <p className="text-xs text-slate-500 font-bold uppercase tracking-wider">
                                {filteredFindings.length} issues displayed • Filter: {findingsFilter.toUpperCase()}
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs font-black text-slate-500 uppercase tracking-widest mr-1">Filter:</span>
                        <button
                            onClick={() => setFindingsFilter('all')}
                            className={`px-3.5 py-1.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all cursor-pointer ${findingsFilter === 'all' ? 'bg-red-600 text-white shadow-lg shadow-red-600/30' : 'bg-slate-100 dark:bg-black/60 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white border border-slate-300 dark:border-slate-800'}`}
                        >
                            All ({allFindings.length})
                        </button>
                        <button
                            onClick={() => setFindingsFilter('tp')}
                            className={`px-3.5 py-1.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all cursor-pointer ${findingsFilter === 'tp' ? 'bg-emerald-600 text-white shadow-lg shadow-emerald-600/30' : 'bg-slate-100 dark:bg-black/60 text-emerald-600 dark:text-emerald-400 hover:text-emerald-700 dark:hover:text-white border border-slate-300 dark:border-slate-800'}`}
                        >
                            ✓ True Positives ({allFindings.filter(isFindingTruePositive).length})
                        </button>
                        <button
                            onClick={() => setFindingsFilter('fp')}
                            className={`px-3.5 py-1.5 rounded-xl text-xs font-black uppercase tracking-wider transition-all cursor-pointer ${findingsFilter === 'fp' ? 'bg-red-700 text-white shadow-lg' : 'bg-slate-100 dark:bg-black/60 text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-white border border-slate-300 dark:border-slate-800'}`}
                        >
                            ✗ Filtered FP ({allFindings.filter(f => !isFindingTruePositive(f)).length})
                        </button>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-slate-100 dark:bg-black/40 text-slate-700 dark:text-red-900/60 text-xs font-black uppercase tracking-[0.15em] italic border-b border-slate-200 dark:border-transparent">
                            <tr>
                                <th className="px-6 sm:px-10 py-5">Threat Type / ID</th>
                                <th className="px-6 sm:px-10 py-5">Severity & AI Verdict</th>
                                <th className="px-6 sm:px-10 py-5">Endpoint / Vector</th>
                                <th className="px-6 sm:px-10 py-5 text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-red-900/5">
                            {!activeScan || filteredFindings.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="px-10 py-24 text-center opacity-60 font-black uppercase text-xs tracking-widest text-slate-500 dark:text-slate-400">
                                        {isScanning ? 'Pemindaian sedang berjalan... temuan akan muncul secara langsung saat terdeteksi' : 'Tidak ada temuan kerentanan untuk filter ini'}
                                    </td>
                                </tr>
                            ) : (
                                filteredFindings.map((res, i) => {
                                    const val = res.ai_brain_validation || res.ai_validation;
                                    const sevUpper = (res.severity || "INFO").toUpperCase();
                                    return (
                                        <tr key={i} className="hover:bg-red-500/5 transition-colors group">
                                            <td className="px-6 sm:px-10 py-6">
                                                <div className="flex items-center gap-4">
                                                    <div className="w-11 h-11 rounded-2xl bg-red-600/10 flex items-center justify-center border border-red-600/20 group-hover:scale-110 transition-all flex-shrink-0">
                                                        <img src={logo} alt="L" className="w-7 h-7 object-contain" />
                                                    </div>
                                                    <div>
                                                         <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                                                             <span className="text-[11px] bg-red-50 text-red-600 border border-red-200 dark:bg-white/10 dark:text-white dark:border-white/20 px-2 py-0.5 rounded-md font-bold">
                                                                 {res.owasp_code || "A00:2021"} — {res.owasp || res.category || "Vulnerability"}
                                                             </span>
                                                             <div className="text-xs font-mono font-bold text-slate-500 dark:text-slate-500">{res.id || `COR-${i}`}</div>
                                                         </div>
                                                         <div className="text-base font-black italic" style={{ color: 'var(--text-primary)' }}>{res.name || res.type || "Identified Vulnerability"}</div>
                                                     </div>
                                                </div>
                                            </td>
                                            <td className="px-6 sm:px-10 py-6">
                                                <div className="flex flex-col gap-2 items-start">
                                                    {/* Unified Severity & CVSS Score Badge */}
                                                    <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-xl text-[11px] font-black uppercase tracking-wider border shadow-xs ${
                                                        sevUpper === 'CRITICAL' ? 'bg-red-500/15 dark:bg-red-950/60 text-red-700 dark:text-red-400 border-red-300/80 dark:border-red-800/60' :
                                                        sevUpper === 'HIGH' ? 'bg-rose-500/15 dark:bg-rose-950/60 text-rose-700 dark:text-rose-400 border-rose-300/80 dark:border-rose-800/60' :
                                                        sevUpper === 'MEDIUM' ? 'bg-amber-500/15 dark:bg-amber-950/60 text-amber-800 dark:text-amber-400 border-amber-300/80 dark:border-amber-800/60' :
                                                        sevUpper === 'LOW' ? 'bg-yellow-500/15 dark:bg-yellow-950/60 text-yellow-800 dark:text-yellow-400 border-yellow-300/80 dark:border-yellow-800/60' :
                                                        'bg-sky-500/15 dark:bg-sky-950/60 text-sky-800 dark:text-sky-400 border-sky-300/80 dark:border-sky-800/60'
                                                    }`}>
                                                        <span className={`w-2 h-2 rounded-full ${
                                                            sevUpper === 'CRITICAL' ? 'bg-red-600 dark:bg-red-500 animate-pulse' :
                                                            sevUpper === 'HIGH' ? 'bg-rose-600 dark:bg-rose-500' :
                                                            sevUpper === 'MEDIUM' ? 'bg-amber-600 dark:bg-amber-500' :
                                                            sevUpper === 'LOW' ? 'bg-yellow-600 dark:bg-yellow-500' :
                                                            'bg-sky-600 dark:bg-sky-500'
                                                        }`}></span>
                                                        <span>{sevUpper === 'INFORMATIONAL' ? 'INFO' : sevUpper}</span>
                                                        <span className="text-[10px] font-mono font-bold opacity-80 pl-1.5 border-l border-current/25">
                                                            CVSS {getCvssScore(res)}
                                                        </span>
                                                    </span>

                                                    {/* Dual-Engine Validation Badge */}
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
                                                        } else if (val || res.rf_validation) {
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
                                                </div>
                                            </td>
                                            <td className="px-6 sm:px-10 py-6">
                                                <code className="text-xs bg-slate-100 dark:bg-black px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 text-red-600 dark:text-red-400 font-mono italic max-w-sm truncate block font-medium">
                                                    {res.location || res.endpoint || "N/A"}
                                                </code>
                                            </td>
                                            <td className="px-6 sm:px-10 py-6 text-right">
                                                <button 
                                                    onClick={() => setShowDetail(res)} 
                                                    className="text-xs font-black text-red-600 hover:text-red-800 dark:hover:text-white uppercase tracking-wider opacity-80 group-hover:opacity-100 transition-all cursor-pointer flex items-center gap-1.5 ml-auto"
                                                >
                                                    <span>View Details & AI Review</span>
                                                    <span>→</span>
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
        <VulnDetailModal finding={showDetail} onClose={() => setShowDetail(null)} />
        </>
    );
};

export default Dashboard;
