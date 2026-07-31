import React, { useState, useEffect, useRef } from 'react';
import {
    Cpu, BarChart2, Play, CheckCircle2, AlertTriangle,
    Loader2, Database, Award, Activity, ToggleLeft, ToggleRight, Check
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || "/api";

export default function Models() {
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

    useEffect(() => {
        fetchDatasets();
        fetchModels();
    }, []);

    // Polling effect
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
                            // Set newly trained model as currently viewed/selected
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
                // Set default selection to the first model
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


    // Render features with clean CSS row progress bars
    const renderFeatureImportance = (importanceObj) => {
        if (!importanceObj) return null;
        // Sort importances descending
        const items = Object.entries(importanceObj).sort((a, b) => b[1] - a[1]);

        return (
            <div className="space-y-5">
                {items.map(([feat, val]) => (
                    <div key={feat} className="space-y-1.5">
                        <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-wider">
                            <span className="text-slate-400 font-bold italic">{feat.replace('_', ' ')}</span>
                            <span className="text-red-500 font-black font-mono italic">{(val * 100).toFixed(2)}%</span>
                        </div>
                        <div className="w-full bg-black/60 rounded-full h-2.5 overflow-hidden border border-slate-800/50">
                            <div
                                className="bg-gradient-to-r from-red-800 to-red-600 h-full rounded-full transition-all duration-1000"
                                style={{ width: `${val * 100}%` }}
                            />
                        </div>
                    </div>
                ))}
            </div>
        );
    };

    // Render interactive premium 2x2 confusion matrix heatmap
    const renderConfusionMatrix = (matrix) => {
        if (!matrix) return null;
        const { tn, fp, fn, tp } = matrix;
        const total = tn + fp + fn + tp;

        const getPercent = (val) => total > 0 ? ((val / total) * 100).toFixed(1) : 0;

        return (
            <div className="grid grid-cols-2 gap-4 max-w-sm mx-auto font-mono text-center">
                {/* True Negative */}
                <div className="bg-green-950/20 border border-green-800/20 p-6 rounded-3xl flex flex-col justify-center items-center shadow-lg relative group overflow-hidden">
                    <div className="absolute inset-0 bg-green-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <span className="text-[9px] font-black text-green-500 uppercase tracking-widest italic mb-2">True Negative (TN)</span>
                    <span className="text-3xl font-black text-white italic">{tn}</span>
                    <span className="text-[10px] text-green-400 font-bold mt-1">{getPercent(tn)}%</span>
                </div>
                {/* False Positive */}
                <div className="bg-red-950/20 border border-red-900/10 p-6 rounded-3xl flex flex-col justify-center items-center shadow-lg relative group overflow-hidden">
                    <div className="absolute inset-0 bg-red-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <span className="text-[9px] font-black text-red-500/60 uppercase tracking-widest italic mb-2">False Positive (FP)</span>
                    <span className="text-3xl font-black text-red-600 italic">{fp}</span>
                    <span className="text-[10px] text-red-400/50 font-bold mt-1">{getPercent(fp)}%</span>
                </div>
                {/* False Negative */}
                <div className="bg-red-950/20 border border-red-900/10 p-6 rounded-3xl flex flex-col justify-center items-center shadow-lg relative group overflow-hidden">
                    <div className="absolute inset-0 bg-red-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <span className="text-[9px] font-black text-red-500/60 uppercase tracking-widest italic mb-2">False Negative (FN)</span>
                    <span className="text-3xl font-black text-red-600 italic">{fn}</span>
                    <span className="text-[10px] text-red-400/50 font-bold mt-1">{getPercent(fn)}%</span>
                </div>
                {/* True Positive */}
                <div className="bg-green-950/20 border border-green-800/20 p-6 rounded-3xl flex flex-col justify-center items-center shadow-lg relative group overflow-hidden">
                    <div className="absolute inset-0 bg-green-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                    <span className="text-[9px] font-black text-green-500 uppercase tracking-widest italic mb-2">True Positive (TP)</span>
                    <span className="text-3xl font-black text-white italic">{tp}</span>
                    <span className="text-[10px] text-green-400 font-bold mt-1">{getPercent(tp)}%</span>
                </div>
            </div>
        );
    };

    return (
        <div className="py-20 animate-in fade-in duration-500 space-y-16">
            <div className="flex justify-between items-start mb-4">
                <div>
                    <h2 className="text-5xl font-black text-white italic tracking-tighter uppercase">Random Forest <span className="text-red-600 underline">Training</span></h2>
                    <p className="text-xs text-slate-500 font-bold italic mt-2 uppercase tracking-widest">Train security vulnerability classification models using Celery background processes</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                {/* Left Panel: Upload and Train Forms */}
                <div className="space-y-10 lg:col-span-1">

                    {/* Preprocess / Upload Section */}
                    <div className="corvus-card p-8 rounded-[40px] space-y-6">
                        <h3 className="text-lg font-black text-white italic uppercase tracking-tighter flex items-center gap-3">
                            <Database className="w-5 h-5 text-red-600" /> 1. Upload dataset
                        </h3>
                        <form onSubmit={handleUploadDataset} className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest italic block">Dataset Alias Name</label>
                                <input
                                    type="text"
                                    placeholder="e.g. SQLi Scanner Telemetry"
                                    value={datasetName}
                                    onChange={(e) => setDatasetName(e.target.value)}
                                    className="w-full bg-black/60 border border-slate-800 rounded-2xl py-3 px-4 text-xs focus:outline-none focus:border-red-600 text-white italic font-bold placeholder:text-slate-700"
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest italic block">Label Column in File</label>
                                <input
                                    type="text"
                                    placeholder="label"
                                    value={labelCol}
                                    onChange={(e) => setLabelCol(e.target.value)}
                                    className="w-full bg-black/60 border border-slate-800 rounded-2xl py-3 px-4 text-xs focus:outline-none focus:border-red-600 text-white font-mono"
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest italic block">Select Dataset File (CSV/JSON/Parquet)</label>
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    accept=".csv,.json,.parquet,.pq"
                                    className="w-full text-slate-400 file:bg-slate-900 file:border-slate-800 file:text-[10px] file:font-black file:uppercase file:tracking-widest file:px-4 file:py-2 file:rounded-xl file:text-slate-400 hover:file:text-white file:mr-4 file:cursor-pointer text-xs font-bold"
                                    required
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={uploading}
                                className="w-full bg-slate-900 hover:bg-slate-800 border border-slate-800 text-slate-400 hover:text-white font-black py-3 rounded-2xl transition-all flex items-center justify-center gap-2 text-[10px] uppercase tracking-widest active:scale-95"
                            >
                                {uploading ? (
                                    <>
                                        <Loader2 className="w-4 h-4 animate-spin text-red-500" />
                                        Preprocessing Data...
                                    </>
                                ) : (
                                    "Preprocess & Save Dataset"
                                )}
                            </button>
                        </form>
                    </div>

                    {/* Background RandomForest Training Config */}
                    <div className="corvus-card p-8 rounded-[40px] space-y-6">
                        <h3 className="text-lg font-black text-white italic uppercase tracking-tighter flex items-center gap-3">
                            <Cpu className="w-5 h-5 text-red-600" /> 2. Train classifier
                        </h3>
                        <form onSubmit={handleTrainModel} className="space-y-4">
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest italic block">Dataset</label>
                                {loadingDatasets ? (
                                    <div className="text-xs text-slate-600 italic">Querying preprocessed datasets...</div>
                                ) : datasets.length === 0 ? (
                                    <div className="text-xs text-red-500 font-bold italic">No datasets available. Upload one above.</div>
                                ) : (
                                    <select
                                        value={selectedDatasetId}
                                        onChange={(e) => setSelectedDatasetId(e.target.value)}
                                        className="w-full bg-black/60 border border-slate-800 rounded-2xl py-3.5 px-4 text-xs focus:outline-none focus:border-red-600 text-white uppercase font-black"
                                    >
                                        {datasets.map(d => (
                                            <option key={d.id} value={d.id} className="bg-black text-white">
                                                {d.name} ({d.rows} rows, {d.features} feats)
                                            </option>
                                        ))}
                                    </select>
                                )}
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest italic block">N Estimators (Trees)</label>
                                <input
                                    type="number"
                                    min="1"
                                    max="1000"
                                    value={nEstimators}
                                    onChange={(e) => setNEstimators(e.target.value)}
                                    className="w-full bg-black/60 border border-slate-800 rounded-2xl py-3 px-4 text-xs focus:outline-none focus:border-red-600 text-white font-mono"
                                    required
                                />
                            </div>
                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest italic block">Max Depth (Optional)</label>
                                <input
                                    type="number"
                                    placeholder="None"
                                    value={maxDepth}
                                    onChange={(e) => setMaxDepth(e.target.value)}
                                    className="w-full bg-black/60 border border-slate-800 rounded-2xl py-3 px-4 text-xs focus:outline-none focus:border-red-600 text-white font-mono"
                                />
                            </div>
                            <button
                                type="submit"
                                disabled={datasets.length === 0 || jobStatus === 'training'}
                                className="w-full bg-red-600 hover:bg-white hover:text-red-900 text-white font-black py-4 rounded-2xl transition-all shadow-xl shadow-red-600/20 active:scale-95 disabled:grayscale flex items-center justify-center gap-2 text-xs uppercase tracking-widest"
                            >
                                <Play className="w-4 h-4" /> Start Celery Training
                            </button>
                        </form>
                    </div>

                </div>

                {/* Right Panel: Polling Progress & Visualizations */}
                <div className="lg:col-span-2 space-y-8">
                    {/* Live job training progress */}
                    {jobStatus && (
                        <div className="corvus-card p-8 rounded-[40px] border border-red-950 shadow-xl space-y-6">
                            <div className="flex justify-between items-center">
                                <h4 className="text-sm font-black text-white italic uppercase tracking-widest flex items-center gap-2">
                                    {jobStatus === 'training' ? (
                                        <>
                                            <Loader2 className="w-4 h-4 animate-spin text-red-600" />
                                            Active Training Session
                                        </>
                                    ) : jobStatus === 'completed' ? (
                                        <>
                                            <CheckCircle2 className="w-4 h-4 text-green-500" />
                                            Training Task Concluded
                                        </>
                                    ) : (
                                        <>
                                            <AlertTriangle className="w-4 h-4 text-red-500" />
                                            Training Task Failed
                                        </>
                                    )}
                                </h4>
                                <span className="text-[10px] text-slate-500 font-mono">Job ID: {jobId}</span>
                            </div>

                            {jobStatus === 'training' && (
                                <div className="space-y-4">
                                    <div className="w-full bg-black rounded-full h-3 overflow-hidden border border-slate-800">
                                        <div
                                            className="bg-red-600 h-full rounded-full transition-all duration-500"
                                            style={{ width: `${jobProgress}%` }}
                                        />
                                    </div>
                                    <div className="text-[10px] text-slate-400 font-bold uppercase tracking-widest flex justify-between">
                                        <span>Model calculation on Celery...</span>
                                        <span>{jobProgress}%</span>
                                    </div>
                                </div>
                            )}

                            {jobStatus === 'failed' && (
                                <div className="bg-red-600/10 border border-red-600/20 p-4 rounded-2xl text-red-400 text-xs font-bold italic">
                                    Error: {jobError}
                                </div>
                            )}

                            {jobStatus === 'completed' && finishedModelMetrics && (
                                <div className="bg-green-600/10 border border-green-600/20 p-5 rounded-3xl text-green-400 font-bold italic text-xs flex justify-between items-center">
                                    <span>Model successfully compiled. View details in model list below.</span>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Active Model / Selected Model Visualization */}
                    <div className="corvus-card p-10 rounded-[50px] space-y-10">
                        {loadingModels ? (
                            <div className="py-24 text-center opacity-40 font-black uppercase text-[10px]">
                                <Loader2 className="w-6 h-6 animate-spin mx-auto mb-3 text-red-600" /> Loading models details...
                            </div>
                        ) : !selectedModel ? (
                            <div className="py-32 text-center opacity-30 font-black uppercase text-[10px]">
                                No trained models available. Trigger a training session on the left to generate model assets.
                            </div>
                        ) : (
                            <>
                                <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-6 border-b border-red-900/10 pb-8">
                                    <div>
                                        <div className="flex items-center gap-3">
                                            <h3 className="text-2xl font-black text-white italic tracking-tighter uppercase">{selectedModel.name}</h3>
                                        </div>
                                        <p className="text-[10px] text-slate-500 font-bold italic uppercase tracking-wider mt-1.5">
                                            Trained on {new Date(selectedModel.created_at).toLocaleString()} • ID: #{selectedModel.id}
                                        </p>
                                    </div>
                                </div>

                                {/* Metrics stats card blocks */}
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                                    {[
                                        { title: "Accuracy", value: `${(selectedModel.metrics.accuracy * 100).toFixed(1)}%`, desc: "Total correct predictions" },
                                        { title: "Precision", value: `${(selectedModel.metrics.precision * 100).toFixed(1)}%`, desc: "Positive predictive value" },
                                        { title: "Recall (TPR)", value: `${(selectedModel.metrics.recall * 100).toFixed(1)}%`, desc: "Sensitivity or hit rate" },
                                        { title: "F1 Score", value: `${(selectedModel.metrics.f1_score * 100).toFixed(1)}%`, desc: "Harmonic mean of precision/recall" }
                                    ].map((stat, i) => (
                                        <div key={i} className="bg-black/40 border border-slate-900 p-5 rounded-3xl flex flex-col relative overflow-hidden group">
                                            <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1 italic">{stat.title}</span>
                                            <span className="text-2xl font-black text-white italic tracking-tight">{stat.value}</span>
                                            <span className="text-[8px] text-slate-600 font-bold italic mt-2 leading-relaxed">{stat.desc}</span>
                                        </div>
                                    ))}
                                </div>

                                {/* Charts Area */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-10">
                                    {/* Confusion Matrix Heatmap container */}
                                    <div className="space-y-6">
                                        <h4 className="text-xs font-black text-white italic uppercase tracking-widest border-b border-slate-900 pb-3 flex items-center gap-2">
                                            <Activity className="w-4 h-4 text-red-600" /> Confusion Matrix Heatmap
                                        </h4>
                                        {renderConfusionMatrix(selectedModel.metrics.confusion_matrix)}
                                    </div>
                                    {/* Feature Importance Container */}
                                    <div className="space-y-6">
                                        <h4 className="text-xs font-black text-white italic uppercase tracking-widest border-b border-slate-900 pb-3 flex items-center gap-2">
                                            <BarChart2 className="w-4 h-4 text-red-600" /> Feature Importance Breakdown
                                        </h4>
                                        {renderFeatureImportance(selectedModel.metrics.feature_importance)}
                                    </div>
                                </div>
                            </>
                        )}
                    </div>
                </div>
            </div>

            {/* Models Inventory Table */}
            <div className="corvus-card rounded-[48px] overflow-hidden space-y-6">
                <div className="p-8 border-b border-red-900/10 bg-black/20 flex justify-between items-center">
                    <h3 className="text-lg font-black text-white italic uppercase tracking-tighter flex items-center gap-2">
                        <Award className="w-5 h-5 text-red-600" /> Trained Model Inventory
                    </h3>
                    <span className="text-[10px] text-slate-500 font-black uppercase tracking-widest italic">{modelsList.length} Models Recorded</span>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-black/30 text-red-900/60 text-[10px] font-black uppercase tracking-[0.2em] italic">
                            <tr>
                                <th className="px-10 py-6">Model ID / Name</th>
                                <th className="px-10 py-6">Hyper-params</th>
                                <th className="px-10 py-6">Accuracy</th>
                                <th className="px-10 py-6">Precision</th>

                                <th className="px-10 py-6 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-red-900/5 text-xs font-bold">
                            {loadingModels ? (
                                <tr>
                                    <td colSpan="6" className="px-10 py-16 text-center opacity-30 font-black uppercase text-[10px]">
                                        Retrieving inventory data...
                                    </td>
                                </tr>
                            ) : modelsList.length === 0 ? (
                                <tr>
                                    <td colSpan="6" className="px-10 py-20 text-center opacity-30 font-black uppercase text-[10px]">
                                        Inventory is empty.
                                    </td>
                                </tr>
                            ) : (
                                modelsList.map((m) => (
                                    <tr
                                        key={m.id}
                                        className={`hover:bg-red-600/5 transition-colors cursor-pointer ${selectedModel?.id === m.id ? 'bg-red-600/5' : ''}`}
                                        onClick={() => setSelectedModel(m)}
                                    >
                                        <td className="px-10 py-6 font-black text-white italic uppercase">{m.name}</td>
                                        <td className="px-10 py-6 text-slate-400 font-mono">
                                            Trees: {m.params.n_estimators || 100} | Depth: {m.params.max_depth || "None"}
                                        </td>
                                        <td className="px-10 py-6 text-red-500 font-mono italic">{(m.metrics.accuracy * 100).toFixed(1)}%</td>
                                        <td className="px-10 py-6 text-slate-300 font-mono">{(m.metrics.precision * 100).toFixed(1)}%</td>
                                        <td className="px-10 py-6 text-right" onClick={(e) => e.stopPropagation()}>
                                            <div className="flex justify-end gap-3">
                                                <button
                                                    onClick={() => setSelectedModel(m)}
                                                    className="bg-slate-900 hover:bg-red-600/10 text-slate-400 hover:text-white px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest border border-slate-800 transition-all"
                                                >
                                                    View Details
                                                </button>
                                                <button
                                                    onClick={() => handleDeleteModel(m.id)}
                                                    className="bg-slate-900 hover:bg-red-900/10 text-slate-500 hover:text-red-500 px-4 py-2 rounded-xl text-[9px] font-black uppercase tracking-widest border border-slate-800 transition-all"
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
            </div>
        </div>
    );
}
