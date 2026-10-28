import React, { useState, useEffect, useRef } from 'react';
import {
    Cpu, BarChart2, Play, CheckCircle2, AlertTriangle,
    Loader2, Database, Award, Activity, Sparkles, ShieldCheck,
    ShieldAlert, Filter, Search, ChevronLeft, ChevronRight,
    RefreshCw, Layers, HelpCircle
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || "/api";

export default function Models() {
    // ==========================================
    // 1. CONFIDENCE SCORE ANALYSIS STATE
    // ==========================================
    const [scanReports, setScanReports] = useState([]);
    const [loadingScanReports, setLoadingScanReports] = useState(true);
    const [selectedScanId, setSelectedScanId] = useState("all");
    const [confidenceAnalysisResult, setConfidenceAnalysisResult] = useState(null);
    const [analyzingConfidence, setAnalyzingConfidence] = useState(false);
    const [confidenceError, setConfidenceError] = useState("");

    // Table Filter & Pagination
    const [findingSearch, setFindingSearch] = useState("");
    const [findingFilterSeverity, setFindingFilterSeverity] = useState("all");
    const [findingFilterConfidence, setFindingFilterConfidence] = useState("all");
    const [currentPage, setCurrentPage] = useState(1);
    const itemsPerPage = 10;

    // ==========================================
    // 2. RANDOM FOREST TRAINING STATE
    // ==========================================
    const [datasets, setDatasets] = useState([]);
    const [modelsList, setModelsList] = useState([]);
    const [loadingDatasets, setLoadingDatasets] = useState(true);
    const [loadingModels, setLoadingModels] = useState(true);

    // Training Form State
    const [selectedDatasetId, setSelectedDatasetId] = useState("");
    const [nEstimators, setNEstimators] = useState(100);
    const [maxDepth, setMaxDepth] = useState("");

    // Upload Dataset Form State
    const [uploading, setUploading] = useState(false);
    const [datasetName, setDatasetName] = useState("");
    const [labelCol, setLabelCol] = useState("label");
    const fileInputRef = useRef(null);

    // Active Job State (Polling)
    const [jobId, setJobId] = useState(null);
    const [jobProgress, setJobProgress] = useState(0);
    const [jobStatus, setJobStatus] = useState(null); // 'training', 'completed', 'failed'
    const [jobError, setJobError] = useState("");
    const [finishedModelMetrics, setFinishedModelMetrics] = useState(null);

    // Selected Model Details for Visualization
    const [selectedModel, setSelectedModel] = useState(null);

    // Reference for Scrolling down to Training
    const trainingSectionRef = useRef(null);

    // ==========================================
    // INITIALIZATION & CACHING
    // ==========================================
    useEffect(() => {
        fetchScanReports();
        fetchDatasets();
        fetchModels();

        // Restore cached Confidence Analysis if available
        try {
            const cachedAnalysis = localStorage.getItem("corvus_confidence_analysis_result");
            const cachedScanId = localStorage.getItem("corvus_confidence_selected_scan");
            if (cachedAnalysis) {
                setConfidenceAnalysisResult(JSON.parse(cachedAnalysis));
            }
            if (cachedScanId) {
                setSelectedScanId(cachedScanId);
            }
        } catch (e) {
            console.error("Failed to load cached confidence analysis:", e);
        }
    }, []);

    // Polling effect for RF Training
    useEffect(() => {
        let interval;
        if (jobId && jobStatus === 'training') {
            interval = setInterval(async () => {
                try {
                    const token = localStorage.getItem('corvus_token');
                    const res = await fetch(`${API_BASE}/train/status/${jobId}`, {
                        headers: { "Authorization": `Bearer ${token}` }
                    });
                    if (res.ok) {
                        const data = await res.json();
                        if (data.status === 'completed') {
                            setJobStatus('completed');
                            setJobProgress(100);
                            setFinishedModelMetrics(data.metrics);
                            fetchModels();
                            if (data.model_id) {
                                fetchModelDetails(data.model_id);
                            }
                            clearInterval(interval);
                        } else if (data.status === 'failed') {
                            setJobStatus('failed');
                            setJobError(data.error || "Training failed on server.");
                            clearInterval(interval);
                        } else {
                            setJobProgress(data.progress || 50);
                        }
                    }
                } catch (err) {
                    console.error("Error polling job status:", err);
                }
            }, 2500);
        }
        return () => clearInterval(interval);
    }, [jobId, jobStatus]);

    // ==========================================
    // DATA FETCHING
    // ==========================================
    const fetchScanReports = async () => {
        setLoadingScanReports(true);
        try {
            const token = localStorage.getItem('corvus_token');
            const res = await fetch(`${API_BASE}/train/scan-reports`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setScanReports(data.scans || []);
            }
        } catch (err) {
            console.error("Error fetching scan reports:", err);
        } finally {
            setLoadingScanReports(false);
        }
    };

    const fetchDatasets = async () => {
        setLoadingDatasets(true);
        try {
            const token = localStorage.getItem('corvus_token');
            const res = await fetch(`${API_BASE}/preprocess/datasets`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setDatasets(data);
                if (data.length > 0) setSelectedDatasetId(data[0].id);
            }
        } catch (err) {
            console.error("Error fetching datasets:", err);
        } finally {
            setLoadingDatasets(false);
        }
    };

    const fetchModels = async () => {
        setLoadingModels(true);
        try {
            const token = localStorage.getItem('corvus_token');
            const res = await fetch(`${API_BASE}/train/models`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setModelsList(data);
                if (data.length > 0 && !selectedModel) {
                    setSelectedModel(data[0]);
                }
            }
        } catch (err) {
            console.error("Error fetching models:", err);
        } finally {
            setLoadingModels(false);
        }
    };

    const fetchModelDetails = async (id) => {
        try {
            const token = localStorage.getItem('corvus_token');
            const res = await fetch(`${API_BASE}/train/models`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                const matched = data.find(m => m.id === id);
                if (matched) setSelectedModel(matched);
            }
        } catch (err) {
            console.error(err);
        }
    };

    // ==========================================
    // CONFIDENCE SCORE CALCULATION
    // ==========================================
    const handleCalculateConfidence = async () => {
        setAnalyzingConfidence(true);
        setConfidenceError("");
        setCurrentPage(1);

        try {
            const token = localStorage.getItem('corvus_token');
            const res = await fetch(`${API_BASE}/train/confidence-analysis`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    scan_id: selectedScanId === "all" ? null : selectedScanId,
                    high_threshold: 80.0,
                    medium_threshold: 50.0
                })
            });

            const data = await res.json();
            if (res.ok) {
                setConfidenceAnalysisResult(data);
                try {
                    localStorage.setItem("corvus_confidence_analysis_result", JSON.stringify(data));
                    localStorage.setItem("corvus_confidence_selected_scan", selectedScanId);
                } catch (e) {
                    console.error("Failed caching confidence analysis:", e);
                }
            } else {
                setConfidenceError(data.detail || "Terjadi kesalahan saat menghitung Confidence Score.");
            }
        } catch (err) {
            console.error("Error in confidence analysis:", err);
            setConfidenceError("Gagal terhubung ke endpoint backend. Pastikan server aktif.");
        } finally {
            setAnalyzingConfidence(false);
        }
    };

    // ==========================================
    // TRAINING HANDLERS
    // ==========================================
    const handleUploadDataset = async (e) => {
        e.preventDefault();
        const file = fileInputRef.current?.files[0];
        if (!file) return;

        setUploading(true);
        const formData = new FormData();
        formData.append("file", file);
        formData.append("label_col", labelCol);
        if (datasetName) formData.append("dataset_name", datasetName);

        try {
            const token = localStorage.getItem('corvus_token');
            const res = await fetch(`${API_BASE}/preprocess/upload`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` },
                body: formData
            });
            if (res.ok) {
                alert("Dataset uploaded and preprocessed successfully!");
                setDatasetName("");
                if (fileInputRef.current) fileInputRef.current.value = "";
                fetchDatasets();
            } else {
                const errData = await res.json();
                alert(`Upload failed: ${errData.detail || "Error occurred."}`);
            }
        } catch (err) {
            alert("Error connecting to upload endpoint.");
        } finally {
            setUploading(false);
        }
    };

    const handleTrainModel = async (e) => {
        e.preventDefault();
        if (!selectedDatasetId) return;

        setJobStatus('training');
        setJobProgress(10);
        setJobError("");
        setFinishedModelMetrics(null);

        try {
            const token = localStorage.getItem('corvus_token');
            const res = await fetch(`${API_BASE}/train`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    dataset_id: parseInt(selectedDatasetId),
                    params: {
                        n_estimators: parseInt(nEstimators),
                        max_depth: maxDepth ? parseInt(maxDepth) : null
                    }
                })
            });

            const data = await res.json();
            if (res.ok) {
                setJobId(data.job_id);
            } else {
                setJobStatus('failed');
                setJobError(data.detail || "Could not launch training job.");
            }
        } catch (err) {
            setJobStatus('failed');
            setJobError("Server connection lost.");
        }
    };

    const handleDeleteModel = async (id) => {
        if (!confirm("Are you sure you want to remove this model from database?")) return;
        try {
            const token = localStorage.getItem('corvus_token');
            const res = await fetch(`${API_BASE}/train/models/${id}`, {
                method: "DELETE",
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                fetchModels();
                if (selectedModel?.id === id) setSelectedModel(null);
            }
        } catch (e) {
            console.error(e);
        }
    };

    // ==========================================
    // UI HELPERS
    // ==========================================
    const formatDate = (dateString) => {
        if (!dateString) return "-";
        try {
            const d = new Date(dateString);
            return d.toLocaleDateString('id-ID', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            });
        } catch {
            return dateString;
        }
    };

    const getSeverityBadge = (sev) => {
        const s = (sev || "").toUpperCase();
        if (s.includes("CRITICAL")) {
            return <span className="px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">Critical</span>;
        }
        if (s.includes("HIGH")) {
            return <span className="px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20">High</span>;
        }
        if (s.includes("MEDIUM")) {
            return <span className="px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">Medium</span>;
        }
        if (s.includes("LOW")) {
            return <span className="px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">Low</span>;
        }
        return <span className="px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider bg-slate-500/10 text-slate-600 dark:text-slate-400 border border-slate-500/20">Info</span>;
    };

    const renderConfidenceScore = (score, level) => {
        let badgeStyle = "text-rose-600 dark:text-rose-400 bg-rose-500/10 border-rose-500/20";
        let barColor = "bg-rose-500";
        if (score >= 80) {
            badgeStyle = "text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20";
            barColor = "bg-emerald-500";
        } else if (score >= 50) {
            badgeStyle = "text-amber-600 dark:text-amber-400 bg-amber-500/10 border-amber-500/20";
            barColor = "bg-amber-500";
        }

        return (
            <div className="flex flex-col gap-1 min-w-[100px] max-w-[130px] ml-auto">
                <div className="flex items-center justify-between gap-1 text-[10px] font-mono">
                    <span className={`px-1.5 py-0.2 rounded font-bold border ${badgeStyle}`}>
                        {score.toFixed(1)}%
                    </span>
                    <span className="text-[8px] font-bold text-slate-500 uppercase">
                        {level}
                    </span>
                </div>
                <div className="w-full bg-slate-100 dark:bg-black/60 rounded-full h-1 overflow-hidden border border-slate-200 dark:border-slate-800">
                    <div
                        className={`h-full rounded-full transition-all duration-300 ${barColor}`}
                        style={{ width: `${Math.min(100, Math.max(0, score))}%` }}
                    />
                </div>
            </div>
        );
    };

    const renderPredictionBadge = (pred) => {
        const isVal = pred === "Valid Finding";
        return (
            <span className={`px-2 py-0.5 rounded-md text-[9px] font-bold uppercase tracking-wider border inline-flex items-center gap-1 ${
                isVal
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20"
                    : "bg-slate-500/10 text-slate-600 dark:text-slate-400 border-slate-500/20"
            }`}>
                {isVal ? <ShieldCheck className="w-3 h-3 text-emerald-500 shrink-0" /> : <ShieldAlert className="w-3 h-3 text-slate-400 shrink-0" />}
                <span>{pred}</span>
            </span>
        );
    };

    const renderFeatureImportance = (importanceObj) => {
        if (!importanceObj) return null;
        const items = Object.entries(importanceObj).sort((a, b) => b[1] - a[1]);

        return (
            <div className="space-y-4">
                {items.map(([feat, val]) => (
                    <div key={feat} className="space-y-1">
                        <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-wider">
                            <span className="text-slate-600 dark:text-slate-400">{feat.replace(/_/g, ' ')}</span>
                            <span className="text-red-600 dark:text-red-500 font-mono">{(val * 100).toFixed(2)}%</span>
                        </div>
                        <div className="w-full bg-slate-100 dark:bg-black/60 rounded-full h-2 overflow-hidden border border-slate-200 dark:border-slate-800">
                            <div
                                className="bg-red-600 h-full rounded-full transition-all duration-700"
                                style={{ width: `${val * 100}%` }}
                            />
                        </div>
                    </div>
                ))}
            </div>
        );
    };

    const renderConfusionMatrix = (matrix) => {
        if (!matrix) return null;
        const { tn, fp, fn, tp } = matrix;
        const total = tn + fp + fn + tp;
        const getPercent = (val) => total > 0 ? ((val / total) * 100).toFixed(1) : 0;

        return (
            <div className="grid grid-cols-2 gap-3 max-w-xs mx-auto font-mono text-center">
                <div className="bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-slate-800 p-4 rounded-2xl flex flex-col justify-center items-center">
                    <span className="text-[8px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider mb-1">True Neg (TN)</span>
                    <span className="text-2xl font-black text-slate-900 dark:text-white">{tn}</span>
                    <span className="text-[9px] text-slate-500 mt-0.5">{getPercent(tn)}%</span>
                </div>
                <div className="bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-slate-800 p-4 rounded-2xl flex flex-col justify-center items-center">
                    <span className="text-[8px] font-bold text-red-600 dark:text-red-400 uppercase tracking-wider mb-1">False Pos (FP)</span>
                    <span className="text-2xl font-black text-red-600">{fp}</span>
                    <span className="text-[9px] text-slate-500 mt-0.5">{getPercent(fp)}%</span>
                </div>
                <div className="bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-slate-800 p-4 rounded-2xl flex flex-col justify-center items-center">
                    <span className="text-[8px] font-bold text-red-600 dark:text-red-400 uppercase tracking-wider mb-1">False Neg (FN)</span>
                    <span className="text-2xl font-black text-red-600">{fn}</span>
                    <span className="text-[9px] text-slate-500 mt-0.5">{getPercent(fn)}%</span>
                </div>
                <div className="bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-slate-800 p-4 rounded-2xl flex flex-col justify-center items-center">
                    <span className="text-[8px] font-bold text-emerald-600 dark:text-emerald-400 uppercase tracking-wider mb-1">True Pos (TP)</span>
                    <span className="text-2xl font-black text-slate-900 dark:text-white">{tp}</span>
                    <span className="text-[9px] text-slate-500 mt-0.5">{getPercent(tp)}%</span>
                </div>
            </div>
        );
    };

    // Filtered Findings Calculation
    const allFindings = confidenceAnalysisResult?.findings || [];
    const filteredFindings = allFindings.filter(item => {
        if (findingSearch) {
            const query = findingSearch.toLowerCase();
            const matchesName = (item.name || "").toLowerCase().includes(query);
            const matchesTarget = (item.target || "").toLowerCase().includes(query);
            const matchesEndpoint = (item.endpoint || "").toLowerCase().includes(query);
            const matchesSource = (item.source || "").toLowerCase().includes(query);
            const matchesId = (item.id || "").toLowerCase().includes(query);
            if (!matchesName && !matchesTarget && !matchesEndpoint && !matchesSource && !matchesId) {
                return false;
            }
        }
        if (findingFilterSeverity !== "all") {
            if ((item.severity || "").toLowerCase() !== findingFilterSeverity.toLowerCase()) {
                return false;
            }
        }
        if (findingFilterConfidence !== "all") {
            if (item.confidence_level !== findingFilterConfidence) {
                return false;
            }
        }
        return true;
    });

    const totalPages = Math.max(1, Math.ceil(filteredFindings.length / itemsPerPage));
    const paginatedFindings = filteredFindings.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

    return (
        <div className="py-6 sm:py-10 space-y-12 sm:space-y-16 w-full max-w-full min-w-0 overflow-hidden animate-in fade-in duration-300">

            {/* ========================================================================= */}
            {/* 1. CONFIDENCE SCORE ANALYSIS SECTION (TEPAT DI ATAS RANDOM FOREST)         */}
            {/* ========================================================================= */}
            <section className="space-y-6">
                {/* Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 dark:border-slate-800 pb-5">
                    <div>
                        <div className="flex items-center gap-2 mb-1.5">
                            <span className="px-2.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider bg-red-600/10 text-red-600 border border-red-600/20 inline-flex items-center gap-1">
                                <Sparkles className="w-3 h-3 text-red-600" />
                                Model Inference & False Positive Screening
                            </span>
                        </div>
                        <h2 className="text-3xl sm:text-4xl font-black uppercase tracking-tight text-slate-900 dark:text-white">
                            Confidence Score <span className="text-red-600">Analysis</span>
                        </h2>
                        <p className="text-xs text-slate-500 font-medium mt-1 max-w-3xl">
                            Analisis probabilitas Random Forest (<code className="text-red-500 font-mono text-[10px]">predict_proba</code>) dari temuan Scan History Report untuk verifikasi kepastian temuan dan penyaringan False Positive.
                        </p>
                    </div>

                    <button
                        onClick={fetchScanReports}
                        disabled={loadingScanReports}
                        className="self-start sm:self-center bg-slate-100 hover:bg-slate-200 dark:bg-slate-900 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300 px-3.5 py-2 rounded-xl text-[10px] font-bold uppercase tracking-wider border border-slate-200 dark:border-slate-800 transition-all flex items-center gap-1.5 shrink-0 cursor-pointer"
                        title="Perbarui daftar scan report"
                    >
                        <RefreshCw className={`w-3.5 h-3.5 ${loadingScanReports ? 'animate-spin text-red-600' : ''}`} />
                        Refresh Scan
                    </button>
                </div>

                {/* Scan Report Selector & Action Button Toolbar */}
                <div className="corvus-card p-5 sm:p-6 rounded-3xl space-y-4">
                    <div className="flex flex-col md:flex-row md:items-end gap-3 sm:gap-4">
                        <div className="flex-1 min-w-0 space-y-1.5">
                            <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1.5">
                                <Layers className="w-3.5 h-3.5 text-red-600" />
                                Sumber Data: Scan History Report
                            </label>
                            {loadingScanReports ? (
                                <div className="text-xs text-slate-500 italic py-2">Memuat riwayat scan...</div>
                            ) : (
                                <select
                                    value={selectedScanId}
                                    onChange={(e) => setSelectedScanId(e.target.value)}
                                    className="w-full bg-slate-50 dark:bg-black/60 border border-slate-200 dark:border-slate-800 rounded-xl py-2.5 px-3.5 text-xs text-slate-900 dark:text-white font-medium focus:outline-none focus:border-red-600"
                                >
                                    <option value="all" className="bg-white dark:bg-black text-slate-900 dark:text-white font-bold">
                                        📊 Seluruh Scan History (Komprehensif — {scanReports.length} Scan Reports)
                                    </option>
                                    {scanReports.map(s => (
                                        <option key={s.id} value={s.id} className="bg-white dark:bg-black text-slate-900 dark:text-white">
                                            {s.target} • {formatDate(s.created_at)} • ({s.findings_count} Temuan)
                                        </option>
                                    ))}
                                </select>
                            )}
                        </div>

                        <button
                            onClick={handleCalculateConfidence}
                            disabled={analyzingConfidence}
                            className="bg-red-600 hover:bg-red-700 text-white font-bold py-2.5 px-6 rounded-xl transition-all shadow-md shadow-red-600/20 active:scale-95 disabled:grayscale flex items-center justify-center gap-2 text-xs uppercase tracking-wider shrink-0 cursor-pointer"
                        >
                            {analyzingConfidence ? (
                                <>
                                    <Loader2 className="w-4 h-4 animate-spin text-white" />
                                    Menghitung...
                                </>
                            ) : (
                                <>
                                    <Sparkles className="w-4 h-4" />
                                    Calculate Confidence Score
                                </>
                            )}
                        </button>
                    </div>

                    {/* Error Banner with Guidance */}
                    {confidenceError && (
                        <div className="bg-red-50 dark:bg-red-600/10 border border-red-200 dark:border-red-600/20 p-4 rounded-2xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-red-600 dark:text-red-400 text-xs font-semibold">
                            <div className="flex items-center gap-2">
                                <AlertTriangle className="w-4 h-4 shrink-0 text-red-600" />
                                <span>{confidenceError}</span>
                            </div>
                            {confidenceError.toLowerCase().includes("belum dilatih") && (
                                <button
                                    onClick={() => trainingSectionRef.current?.scrollIntoView({ behavior: 'smooth' })}
                                    className="bg-red-600 text-white hover:bg-white hover:text-red-900 px-3.5 py-1.5 rounded-lg text-[10px] font-bold uppercase tracking-wider transition-all shrink-0 cursor-pointer"
                                >
                                    Latih Model Di Bawah ↓
                                </button>
                            )}
                        </div>
                    )}
                </div>

                {/* Analysis Results */}
                {confidenceAnalysisResult ? (
                    <div className="space-y-6">
                        {/* Summary Cards */}
                        <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-3 sm:gap-4 w-full min-w-0">
                            {/* Card 1: Total Temuan */}
                            <div className="corvus-card p-4 rounded-2xl flex flex-col justify-between">
                                <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">
                                    Total Temuan
                                </span>
                                <span className="text-2xl font-black text-slate-900 dark:text-white mt-1">
                                    {confidenceAnalysisResult.total_findings}
                                </span>
                                <span className="text-[8px] text-slate-500 mt-1">
                                    Temuan Scan History
                                </span>
                            </div>

                            {/* Card 2: Average Confidence Score */}
                            <div className="corvus-card p-4 rounded-2xl flex flex-col justify-between">
                                <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">
                                    Rata-Rata Confidence
                                </span>
                                <span className="text-2xl font-black text-red-600 font-mono mt-1">
                                    {confidenceAnalysisResult.avg_confidence}%
                                </span>
                                <div className="w-full bg-slate-200 dark:bg-black/60 rounded-full h-1 overflow-hidden mt-1.5">
                                    <div
                                        className="h-full bg-red-600 rounded-full transition-all duration-300"
                                        style={{ width: `${confidenceAnalysisResult.avg_confidence}%` }}
                                    />
                                </div>
                            </div>

                            {/* Card 3: High Confidence */}
                            <div className="corvus-card p-4 rounded-2xl flex flex-col justify-between">
                                <div className="flex items-center justify-between">
                                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">
                                        High (≥80%)
                                    </span>
                                    <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
                                </div>
                                <span className="text-2xl font-black text-emerald-600 dark:text-emerald-400 font-mono mt-1">
                                    {confidenceAnalysisResult.high_confidence_count}
                                </span>
                                <span className="text-[8px] text-emerald-600 dark:text-emerald-400 font-medium mt-1">
                                    Keyakinan valid tinggi
                                </span>
                            </div>

                            {/* Card 4: Medium Confidence */}
                            <div className="corvus-card p-4 rounded-2xl flex flex-col justify-between">
                                <div className="flex items-center justify-between">
                                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">
                                        Medium (50-79%)
                                    </span>
                                    <span className="w-2 h-2 rounded-full bg-amber-500"></span>
                                </div>
                                <span className="text-2xl font-black text-amber-600 dark:text-amber-400 font-mono mt-1">
                                    {confidenceAnalysisResult.medium_confidence_count}
                                </span>
                                <span className="text-[8px] text-amber-600 dark:text-amber-400 font-medium mt-1">
                                    Verifikasi manual
                                </span>
                            </div>

                            {/* Card 5: Low Confidence */}
                            <div className="corvus-card p-4 rounded-2xl flex flex-col justify-between col-span-2 md:col-span-1">
                                <div className="flex items-center justify-between">
                                    <span className="text-[9px] font-bold text-slate-500 uppercase tracking-wider">
                                        Low (&lt;50%)
                                    </span>
                                    <span className="w-2 h-2 rounded-full bg-rose-500"></span>
                                </div>
                                <span className="text-2xl font-black text-rose-600 dark:text-rose-400 font-mono mt-1">
                                    {confidenceAnalysisResult.low_confidence_count}
                                </span>
                                <span className="text-[8px] text-rose-600 dark:text-rose-400 font-medium mt-1">
                                    Kandidat False Positive
                                </span>
                            </div>
                        </div>

                        {/* Model & Interpretation Info Pill */}
                        <div className="corvus-card p-4 rounded-2xl flex flex-col md:flex-row justify-between items-start md:items-center gap-2 text-xs">
                            <div className="flex flex-wrap items-center gap-2 text-[10px]">
                                <span className="font-bold text-slate-500 uppercase">Model:</span>
                                <span className="px-2 py-0.5 rounded bg-slate-100 dark:bg-black/60 font-mono font-bold text-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-800">
                                    {confidenceAnalysisResult.model_info?.name || "Random Forest"}
                                </span>
                                <span className="text-slate-400">•</span>
                                <span className="font-bold text-slate-500 uppercase">Waktu:</span>
                                <span className="text-slate-700 dark:text-slate-300 font-mono">
                                    {formatDate(confidenceAnalysisResult.analyzed_at)}
                                </span>
                            </div>

                            <div className="text-[10px] text-slate-500 font-medium flex items-center gap-1.5">
                                <HelpCircle className="w-3.5 h-3.5 text-red-600 shrink-0" />
                                <span>Confidence Score membedakan validitas dari severity; temuan low confidence tidak dihapus otomatis.</span>
                            </div>
                        </div>

                        {/* Findings Analysis Table */}
                        <div className="corvus-card rounded-3xl overflow-hidden border border-slate-200 dark:border-slate-800 w-full max-w-full min-w-0">
                            {/* Search & Filters Toolbar */}
                            <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50/70 dark:bg-black/20 flex flex-col sm:flex-row justify-between items-stretch sm:items-center gap-3">
                                <div className="relative flex-1 max-w-sm">
                                    <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
                                    <input
                                        type="text"
                                        placeholder="Cari temuan, target, endpoint, scanner..."
                                        value={findingSearch}
                                        onChange={(e) => { setFindingSearch(e.target.value); setCurrentPage(1); }}
                                        className="w-full bg-white dark:bg-black/60 border border-slate-200 dark:border-slate-800 rounded-xl py-1.5 pl-8 pr-3 text-xs text-slate-900 dark:text-white placeholder:text-slate-400 focus:outline-none focus:border-red-600 font-medium"
                                    />
                                </div>

                                <div className="flex flex-wrap items-center gap-2">
                                    <div className="flex items-center gap-1.5">
                                        <Filter className="w-3 h-3 text-slate-400" />
                                        <span className="text-[10px] font-bold text-slate-500 uppercase">Confidence:</span>
                                        <select
                                            value={findingFilterConfidence}
                                            onChange={(e) => { setFindingFilterConfidence(e.target.value); setCurrentPage(1); }}
                                            className="bg-white dark:bg-black/60 border border-slate-200 dark:border-slate-800 rounded-lg py-1 px-2 text-xs text-slate-900 dark:text-white font-medium"
                                        >
                                            <option value="all">Semua</option>
                                            <option value="HIGH">High (≥80%)</option>
                                            <option value="MEDIUM">Medium (50-79%)</option>
                                            <option value="LOW">Low (&lt;50%)</option>
                                        </select>
                                    </div>

                                    <div className="flex items-center gap-1.5">
                                        <span className="text-[10px] font-bold text-slate-500 uppercase">Severity:</span>
                                        <select
                                            value={findingFilterSeverity}
                                            onChange={(e) => { setFindingFilterSeverity(e.target.value); setCurrentPage(1); }}
                                            className="bg-white dark:bg-black/60 border border-slate-200 dark:border-slate-800 rounded-lg py-1 px-2 text-xs text-slate-900 dark:text-white font-medium"
                                        >
                                            <option value="all">Semua</option>
                                            <option value="critical">Critical</option>
                                            <option value="high">High</option>
                                            <option value="medium">Medium</option>
                                            <option value="low">Low</option>
                                            <option value="informational">Info</option>
                                        </select>
                                    </div>
                                </div>
                            </div>

                            {/* Table with controlled overflow */}
                            <div className="overflow-x-auto w-full max-w-full">
                                <table className="w-full text-left border-collapse min-w-[650px] sm:min-w-[720px]">
                                    <thead className="bg-slate-100/80 dark:bg-black/40 text-slate-600 dark:text-slate-400 text-[10px] font-bold uppercase tracking-wider border-b border-slate-200 dark:border-slate-800">
                                        <tr>
                                            <th className="px-4 py-3">Nama Temuan</th>
                                            <th className="px-4 py-3">Target / Endpoint</th>
                                            <th className="px-3 py-3">Scanner</th>
                                            <th className="px-3 py-3">Severity</th>
                                            <th className="px-3 py-3">Prediksi RF</th>
                                            <th className="px-4 py-3 text-right">Confidence Score</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-xs">
                                        {paginatedFindings.length === 0 ? (
                                            <tr>
                                                <td colSpan="6" className="px-4 py-10 text-center opacity-40 font-bold uppercase text-[10px]">
                                                    Tidak ada temuan yang cocok dengan filter.
                                                </td>
                                            </tr>
                                        ) : (
                                            paginatedFindings.map((f, idx) => (
                                                <tr key={idx} className="hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">
                                                    {/* Finding Name */}
                                                    <td className="px-4 py-3 font-semibold text-slate-900 dark:text-white max-w-[220px]">
                                                        <div className="truncate" title={f.name}>{f.name}</div>
                                                        <div className="flex items-center gap-1.5 mt-0.5 text-[9px] font-mono text-slate-400">
                                                            <span>{f.id}</span>
                                                            {f.owasp_code && <span>• {f.owasp_code}</span>}
                                                        </div>
                                                    </td>

                                                    {/* Target & Endpoint */}
                                                    <td className="px-4 py-3 max-w-[220px]">
                                                        <div className="font-semibold text-slate-800 dark:text-slate-200 truncate" title={f.target}>
                                                            {f.target}
                                                        </div>
                                                        <div className="text-[10px] text-slate-400 font-mono truncate" title={f.endpoint}>
                                                            {f.endpoint}
                                                        </div>
                                                    </td>

                                                    {/* Scanner */}
                                                    <td className="px-3 py-3 whitespace-nowrap">
                                                        <span className="px-2 py-0.5 rounded text-[9px] font-mono bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-800">
                                                            {f.source}
                                                        </span>
                                                    </td>

                                                    {/* Severity */}
                                                    <td className="px-3 py-3 whitespace-nowrap">
                                                        {getSeverityBadge(f.severity)}
                                                    </td>

                                                    {/* Predicted Class */}
                                                    <td className="px-3 py-3 whitespace-nowrap">
                                                        {renderPredictionBadge(f.predicted_class)}
                                                    </td>

                                                    {/* Confidence Score */}
                                                    <td className="px-4 py-3 text-right whitespace-nowrap">
                                                        {renderConfidenceScore(f.confidence_score, f.confidence_level)}
                                                    </td>
                                                </tr>
                                            ))
                                        )}
                                    </tbody>
                                </table>
                            </div>

                            {/* Pagination */}
                            {filteredFindings.length > itemsPerPage && (
                                <div className="p-3 border-t border-slate-200 dark:border-slate-800 flex items-center justify-between text-xs">
                                    <span className="text-[10px] font-medium text-slate-500">
                                        Menampilkan {(currentPage - 1) * itemsPerPage + 1} - {Math.min(currentPage * itemsPerPage, filteredFindings.length)} dari {filteredFindings.length}
                                    </span>
                                    <div className="flex items-center gap-1.5">
                                        <button
                                            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                            disabled={currentPage === 1}
                                            className="p-1 rounded-lg border border-slate-200 dark:border-slate-800 disabled:opacity-30 hover:bg-slate-100 dark:hover:bg-slate-900 cursor-pointer"
                                        >
                                            <ChevronLeft className="w-3.5 h-3.5" />
                                        </button>
                                        <span className="text-[10px] font-mono font-bold px-2">
                                            {currentPage} / {totalPages}
                                        </span>
                                        <button
                                            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                            disabled={currentPage === totalPages}
                                            className="p-1 rounded-lg border border-slate-200 dark:border-slate-800 disabled:opacity-30 hover:bg-slate-100 dark:hover:bg-slate-900 cursor-pointer"
                                        >
                                            <ChevronRight className="w-3.5 h-3.5" />
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                ) : (
                    /* Empty State */
                    <div className="corvus-card p-12 rounded-3xl text-center space-y-3 border border-dashed border-slate-300 dark:border-slate-800">
                        <div className="w-12 h-12 rounded-2xl bg-red-600/10 text-red-600 flex items-center justify-center mx-auto">
                            <Activity className="w-6 h-6" />
                        </div>
                        <h4 className="text-sm font-bold uppercase text-slate-800 dark:text-slate-200">
                            Belum Ada Hasil Analisis Confidence Score
                        </h4>
                        <p className="text-xs text-slate-500 max-w-sm mx-auto">
                            Pilih Scan History Report pada dropdown di atas dan klik <strong>Calculate Confidence Score</strong> untuk memulai inferensi probabilitas model.
                        </p>
                    </div>
                )}
            </section>

            {/* ========================================================================= */}
            {/* 2. RANDOM FOREST TRAINING SECTION                                         */}
            {/* ========================================================================= */}
            <section ref={trainingSectionRef} className="space-y-8 border-t border-slate-200 dark:border-slate-800 pt-10">
                <div className="border-b border-slate-200 dark:border-slate-800 pb-5">
                    <div className="flex items-center gap-2 mb-1.5">
                        <span className="px-2.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider bg-red-600/10 text-red-600 border border-red-600/20 inline-flex items-center gap-1">
                            <Cpu className="w-3 h-3 text-red-600" />
                            Machine Learning Pipeline
                        </span>
                    </div>
                    <h2 className="text-3xl sm:text-4xl font-black uppercase tracking-tight text-slate-900 dark:text-white">
                        Random Forest <span className="text-red-600">Training</span>
                    </h2>
                    <p className="text-xs text-slate-500 font-medium mt-1">
                        Train security vulnerability classification models using Celery background processes.
                    </p>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 lg:gap-8 w-full min-w-0">
                    {/* Left Panel: Upload and Train Forms */}
                    <div className="space-y-6 sm:space-y-8 lg:col-span-1 min-w-0">

                        {/* 1. Upload Dataset Form */}
                        <div className="corvus-card p-6 rounded-3xl space-y-5">
                            <h3 className="text-base font-black uppercase tracking-tight flex items-center gap-2 text-slate-900 dark:text-white">
                                <Database className="w-4 h-4 text-red-600" /> 1. Upload dataset
                            </h3>
                            <form onSubmit={handleUploadDataset} className="space-y-3.5">
                                <div className="space-y-1">
                                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Dataset Alias Name</label>
                                    <input
                                        type="text"
                                        placeholder="e.g. SQLi Scanner Telemetry"
                                        value={datasetName}
                                        onChange={(e) => setDatasetName(e.target.value)}
                                        className="w-full bg-slate-50 dark:bg-black/60 border border-slate-200 dark:border-slate-800 rounded-xl py-2 px-3 text-xs text-slate-900 dark:text-white font-medium focus:outline-none focus:border-red-600"
                                    />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Label Column in File</label>
                                    <input
                                        type="text"
                                        placeholder="label"
                                        value={labelCol}
                                        onChange={(e) => setLabelCol(e.target.value)}
                                        className="w-full bg-slate-50 dark:bg-black/60 border border-slate-200 dark:border-slate-800 rounded-xl py-2 px-3 text-xs text-slate-900 dark:text-white font-mono focus:outline-none focus:border-red-600"
                                        required
                                    />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Select File (CSV/JSON/Parquet)</label>
                                    <input
                                        type="file"
                                        ref={fileInputRef}
                                        accept=".csv,.json,.parquet,.pq"
                                        className="w-full text-slate-600 dark:text-slate-400 file:bg-slate-100 dark:file:bg-slate-900 file:border-slate-200 dark:file:border-slate-800 file:text-[9px] file:font-bold file:uppercase file:px-3 file:py-1.5 file:rounded-lg file:mr-3 file:cursor-pointer text-xs"
                                        required
                                    />
                                </div>
                                <button
                                    type="submit"
                                    disabled={uploading}
                                    className="w-full bg-slate-100 hover:bg-slate-200 dark:bg-slate-900 dark:hover:bg-slate-800 border border-slate-300 dark:border-slate-800 text-slate-700 dark:text-slate-300 font-bold py-2.5 rounded-xl transition-all flex items-center justify-center gap-2 text-[10px] uppercase tracking-wider cursor-pointer"
                                >
                                    {uploading ? (
                                        <>
                                            <Loader2 className="w-3.5 h-3.5 animate-spin text-red-500" />
                                            Preprocessing...
                                        </>
                                    ) : (
                                        "Preprocess & Save Dataset"
                                    )}
                                </button>
                            </form>
                        </div>

                        {/* 2. Train Classifier Form */}
                        <div className="corvus-card p-6 rounded-3xl space-y-5">
                            <h3 className="text-base font-black uppercase tracking-tight flex items-center gap-2 text-slate-900 dark:text-white">
                                <Cpu className="w-4 h-4 text-red-600" /> 2. Train classifier
                            </h3>
                            <form onSubmit={handleTrainModel} className="space-y-3.5">
                                <div className="space-y-1">
                                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Dataset</label>
                                    {loadingDatasets ? (
                                        <div className="text-xs text-slate-500 italic">Memuat dataset...</div>
                                    ) : datasets.length === 0 ? (
                                        <div className="text-xs text-red-500 font-bold">No datasets available. Upload above.</div>
                                    ) : (
                                        <select
                                            value={selectedDatasetId}
                                            onChange={(e) => setSelectedDatasetId(e.target.value)}
                                            className="w-full bg-slate-50 dark:bg-black/60 border border-slate-200 dark:border-slate-800 rounded-xl py-2 px-3 text-xs text-slate-900 dark:text-white font-medium focus:outline-none focus:border-red-600"
                                        >
                                            {datasets.map(d => (
                                                <option key={d.id} value={d.id} className="bg-white dark:bg-black text-slate-900 dark:text-white">
                                                    {d.name} ({d.rows} rows, {d.features} feats)
                                                </option>
                                            ))}
                                        </select>
                                    )}
                                </div>
                                <div className="space-y-1">
                                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">N Estimators (Trees)</label>
                                    <input
                                        type="number"
                                        min="1"
                                        max="1000"
                                        value={nEstimators}
                                        onChange={(e) => setNEstimators(e.target.value)}
                                        className="w-full bg-slate-50 dark:bg-black/60 border border-slate-200 dark:border-slate-800 rounded-xl py-2 px-3 text-xs text-slate-900 dark:text-white font-mono focus:outline-none focus:border-red-600"
                                        required
                                    />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Max Depth (Optional)</label>
                                    <input
                                        type="number"
                                        placeholder="None"
                                        value={maxDepth}
                                        onChange={(e) => setMaxDepth(e.target.value)}
                                        className="w-full bg-slate-50 dark:bg-black/60 border border-slate-200 dark:border-slate-800 rounded-xl py-2 px-3 text-xs text-slate-900 dark:text-white font-mono focus:outline-none focus:border-red-600"
                                    />
                                </div>
                                <button
                                    type="submit"
                                    disabled={datasets.length === 0 || jobStatus === 'training'}
                                    className="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-2.5 rounded-xl transition-all shadow-md shadow-red-600/20 active:scale-95 disabled:grayscale flex items-center justify-center gap-2 text-xs uppercase tracking-wider cursor-pointer"
                                >
                                    <Play className="w-3.5 h-3.5" /> Start Celery Training
                                </button>
                            </form>
                        </div>

                    </div>

                    {/* Right Panel: Polling Progress & Visualizations */}
                    <div className="lg:col-span-2 space-y-6 min-w-0">
                        {/* Live job training progress */}
                        {jobStatus && (
                            <div className="corvus-card p-6 rounded-3xl border border-slate-200 dark:border-red-950 space-y-4">
                                <div className="flex justify-between items-center">
                                    <h4 className="text-xs font-bold uppercase tracking-wider flex items-center gap-2 text-slate-900 dark:text-white">
                                        {jobStatus === 'training' ? (
                                            <>
                                                <Loader2 className="w-3.5 h-3.5 animate-spin text-red-600" />
                                                Active Training Session
                                            </>
                                        ) : jobStatus === 'completed' ? (
                                            <>
                                                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-green-500" />
                                                Training Task Concluded
                                            </>
                                        ) : (
                                            <>
                                                <AlertTriangle className="w-3.5 h-3.5 text-red-600" />
                                                Training Task Failed
                                            </>
                                        )}
                                    </h4>
                                    <span className="text-[10px] text-slate-500 font-mono">Job ID: {jobId}</span>
                                </div>

                                {jobStatus === 'training' && (
                                    <div className="space-y-2">
                                        <div className="w-full bg-slate-100 dark:bg-black rounded-full h-2 overflow-hidden border border-slate-200 dark:border-slate-800">
                                            <div
                                                className="bg-red-600 h-full rounded-full transition-all duration-300"
                                                style={{ width: `${jobProgress}%` }}
                                            />
                                        </div>
                                        <div className="text-[9px] text-slate-500 font-bold uppercase tracking-wider flex justify-between">
                                            <span>Calculating on Celery...</span>
                                            <span>{jobProgress}%</span>
                                        </div>
                                    </div>
                                )}

                                {jobStatus === 'failed' && (
                                    <div className="bg-red-50 dark:bg-red-600/10 border border-red-200 dark:border-red-600/20 p-3 rounded-xl text-red-600 dark:text-red-400 text-xs font-medium">
                                        Error: {jobError}
                                    </div>
                                )}

                                {jobStatus === 'completed' && finishedModelMetrics && (
                                    <div className="bg-emerald-50 dark:bg-green-600/10 border border-emerald-200 dark:border-green-600/20 p-3 rounded-xl text-emerald-700 dark:text-green-400 font-medium text-xs">
                                        Model successfully compiled and saved.
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Active Model / Selected Model Visualization */}
                        <div className="corvus-card p-6 sm:p-8 rounded-3xl space-y-6">
                            {loadingModels ? (
                                <div className="py-16 text-center opacity-40 font-bold uppercase text-xs">
                                    <Loader2 className="w-5 h-5 animate-spin mx-auto mb-2 text-red-600" /> Loading model details...
                                </div>
                            ) : !selectedModel ? (
                                <div className="py-20 text-center opacity-30 font-bold uppercase text-xs">
                                    No trained models available. Trigger a training session on the left.
                                </div>
                            ) : (
                                <>
                                    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 border-b border-slate-200 dark:border-slate-800 pb-4">
                                        <div>
                                            <h3 className="text-xl font-black uppercase tracking-tight text-slate-900 dark:text-white">
                                                {selectedModel.name}
                                            </h3>
                                            <p className="text-[10px] text-slate-500 font-mono mt-0.5">
                                                Trained {new Date(selectedModel.created_at).toLocaleString()} • ID: #{selectedModel.id}
                                            </p>
                                        </div>
                                    </div>

                                    {/* Metrics stats card blocks */}
                                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                        {[
                                            { title: "Accuracy", value: `${(selectedModel.metrics.accuracy * 100).toFixed(1)}%` },
                                            { title: "Precision", value: `${(selectedModel.metrics.precision * 100).toFixed(1)}%` },
                                            { title: "Recall (TPR)", value: `${(selectedModel.metrics.recall * 100).toFixed(1)}%` },
                                            { title: "F1 Score", value: `${(selectedModel.metrics.f1_score * 100).toFixed(1)}%` }
                                        ].map((stat, i) => (
                                            <div key={i} className="bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-slate-800 p-3.5 rounded-2xl flex flex-col">
                                                <span className="text-[8px] font-bold text-slate-500 uppercase tracking-wider">{stat.title}</span>
                                                <span className="text-xl font-black text-slate-900 dark:text-white mt-1">
                                                    {stat.value}
                                                </span>
                                            </div>
                                        ))}
                                    </div>

                                    {/* Charts Area */}
                                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
                                        {/* Confusion Matrix */}
                                        <div className="space-y-3">
                                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                                                <Activity className="w-3.5 h-3.5 text-red-600" /> Confusion Matrix
                                            </h4>
                                            {renderConfusionMatrix(selectedModel.metrics.confusion_matrix)}
                                        </div>
                                        {/* Feature Importance */}
                                        <div className="space-y-3">
                                            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                                                <BarChart2 className="w-3.5 h-3.5 text-red-600" /> Feature Importance
                                            </h4>
                                            {renderFeatureImportance(selectedModel.metrics.feature_importance)}
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </section>

            {/* ========================================================================= */}
            {/* 3. TRAINED MODEL INVENTORY TABLE                                          */}
            {/* ========================================================================= */}
            <section className="corvus-card rounded-3xl overflow-hidden border border-slate-200 dark:border-slate-800 w-full max-w-full min-w-0">
                <div className="p-5 border-b border-slate-200 dark:border-slate-800 bg-slate-50/80 dark:bg-black/20 flex justify-between items-center">
                    <h3 className="text-sm font-black uppercase tracking-wider flex items-center gap-2 text-slate-900 dark:text-white">
                        <Award className="w-4 h-4 text-red-600" /> Trained Model Inventory
                    </h3>
                    <span className="text-[10px] text-slate-500 font-bold uppercase">{modelsList.length} Models Recorded</span>
                </div>
                <div className="overflow-x-auto w-full max-w-full">
                    <table className="w-full text-left border-collapse min-w-[650px]">
                        <thead className="bg-slate-100/80 dark:bg-black/40 text-slate-600 dark:text-slate-400 text-[10px] font-bold uppercase tracking-wider border-b border-slate-200 dark:border-slate-800">
                            <tr>
                                <th className="px-5 py-3">Model Name</th>
                                <th className="px-5 py-3">Hyper-params</th>
                                <th className="px-5 py-3">Accuracy</th>
                                <th className="px-5 py-3">Precision</th>
                                <th className="px-5 py-3 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-100 dark:divide-slate-800/60 text-xs font-medium">
                            {loadingModels ? (
                                <tr>
                                    <td colSpan="5" className="px-5 py-10 text-center opacity-40 font-bold uppercase text-[10px]">
                                        Retrieving inventory data...
                                    </td>
                                </tr>
                            ) : modelsList.length === 0 ? (
                                <tr>
                                    <td colSpan="5" className="px-5 py-12 text-center opacity-30 font-bold uppercase text-[10px]">
                                        Inventory is empty.
                                    </td>
                                </tr>
                            ) : (
                                modelsList.map((m) => (
                                    <tr
                                        key={m.id}
                                        className={`hover:bg-slate-50 dark:hover:bg-white/5 transition-colors cursor-pointer ${selectedModel?.id === m.id ? 'bg-red-50/60 dark:bg-red-600/10' : ''}`}
                                        onClick={() => setSelectedModel(m)}
                                    >
                                        <td className="px-5 py-3 font-bold text-slate-900 dark:text-white">
                                            {m.name}
                                        </td>
                                        <td className="px-5 py-3 text-slate-500 font-mono text-[11px]">
                                            Trees: {m.params?.n_estimators || 100} | Depth: {m.params?.max_depth || "None"}
                                        </td>
                                        <td className="px-5 py-3 text-red-600 font-mono font-bold">
                                            {(m.metrics?.accuracy * 100 || 0).toFixed(1)}%
                                        </td>
                                        <td className="px-5 py-3 text-slate-700 dark:text-slate-300 font-mono">
                                            {(m.metrics?.precision * 100 || 0).toFixed(1)}%
                                        </td>
                                        <td className="px-5 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                                            <div className="flex justify-end gap-2">
                                                <button
                                                    onClick={() => setSelectedModel(m)}
                                                    className="bg-slate-100 hover:bg-slate-200 dark:bg-slate-900 dark:hover:bg-red-600/10 text-slate-700 dark:text-slate-300 px-3 py-1 rounded-lg text-[9px] font-bold uppercase tracking-wider border border-slate-300 dark:border-slate-800 transition-all cursor-pointer"
                                                >
                                                    View
                                                </button>
                                                <button
                                                    onClick={() => handleDeleteModel(m.id)}
                                                    className="bg-slate-100 hover:bg-red-50 dark:bg-slate-900 dark:hover:bg-red-900/20 text-red-600 px-3 py-1 rounded-lg text-[9px] font-bold uppercase tracking-wider border border-slate-300 dark:border-slate-800 transition-all cursor-pointer"
                                                >
                                                    Delete
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </section>

        </div>
    );
}
