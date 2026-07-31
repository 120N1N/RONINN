import React, { useState, useEffect } from 'react';
import { Target, Search, Activity, FileText, CheckCircle2 } from 'lucide-react';
import logo from '../assets/logo.png';
import VulnDetailModal from '../components/VulnDetailModal';

const API_BASE = import.meta.env.VITE_API_URL || "/api";

const Dashboard = ({ user }) => {
    const [target, setTarget] = useState("");
    const [isScanning, setIsScanning] = useState(false);
    const [activeScan, setActiveScan] = useState(null);
    const [showDetail, setShowDetail] = useState(null);
    const [mode, setMode] = useState("normal");
    const [scanSubdomains, setScanSubdomains] = useState(true);

    const handleScan = async (e) => {
        e.preventDefault();
        setIsScanning(true);
        const token = localStorage.getItem('corvus_token');
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
        } else {
            alert("Scan failed to initiate. Please check login status.");
            setIsScanning(false);
        }
    };

    useEffect(() => {
        let interval;
        if (activeScan && (activeScan.status === "RUNNING" || activeScan.status === "PENDING")) {
            interval = setInterval(() => {
                const token = localStorage.getItem('corvus_token');
                fetch(`${API_BASE}/scan/${activeScan.id}`, {
                    headers: { "Authorization": `Bearer ${token}` }
                }).then(r => r.json()).then(d => {
                    setActiveScan(d);
                    if (d.status === 'COMPLETED' || d.status === 'FAILED') setIsScanning(false);
                });
            }, 2000);
        }
        return () => clearInterval(interval);
    }, [activeScan]);

    return (
        <>
        <div className="space-y-8 animate-in fade-in duration-1000">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                <div className="lg:col-span-8">
                    <section className="corvus-card p-10 rounded-[40px] shadow-2xl relative overflow-hidden group">
                        <h2 className="text-2xl font-black mb-8 flex items-center gap-3 text-white italic">
                            <Target className="w-6 h-6 text-red-600" />
                            INITIATE AUDIT CENTER
                        </h2>
                        <form onSubmit={handleScan} className="space-y-8">
                            <div className="relative">
                                <input
                                    type="text"
                                    placeholder="Enter target (e.g., identity.corvus.net)"
                                    className="w-full bg-black/60 border border-slate-800 rounded-3xl py-6 px-8 pl-16 text-xl focus:outline-none focus:border-red-600 transition-all text-white placeholder:text-slate-700"
                                    value={target}
                                    onChange={(e) => setTarget(e.target.value)}
                                    disabled={isScanning}
                                />
                                <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-red-600 w-7 h-7" />
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <div className="bg-black/40 p-5 rounded-2xl border border-slate-800 flex items-center justify-between">
                                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest italic">Phase</span>
                                    <select 
                                        value={mode}
                                        onChange={(e) => setMode(e.target.value)}
                                        className="bg-transparent text-xs font-black text-red-600 focus:outline-none cursor-pointer uppercase font-sans"
                                    >
                                        <option value="quick" className="bg-black text-white">Quick</option>
                                        <option value="normal" className="bg-black text-white">Normal</option>
                                        <option value="deep" className="bg-black text-white">Deep</option>
                                    </select>
                                </div>
                                <div 
                                    onClick={() => setScanSubdomains(!scanSubdomains)}
                                    className="bg-black/40 p-5 rounded-2xl border border-slate-800 flex items-center justify-between cursor-pointer group hover:bg-black/60 transition-colors"
                                >
                                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest italic group-hover:text-slate-400 transition-colors">Subdomains</span>
                                    <div className={`w-4 h-4 rounded flex items-center justify-center transition-colors ${scanSubdomains ? 'bg-red-600' : 'bg-slate-800'}`}>
                                        {scanSubdomains && <CheckCircle2 className="w-3 h-3 text-white" />}
                                    </div>
                                </div>
                                <button
                                    type="submit"
                                    disabled={isScanning || !target}
                                    className="bg-red-600 hover:bg-white hover:text-red-900 text-white font-black py-5 px-8 rounded-2xl transition-all shadow-xl shadow-red-600/20 active:scale-95 disabled:grayscale uppercase tracking-widest text-xs"
                                >
                                    {isScanning ? 'SYSTEM RUNNING...' : 'LAUNCH CORVUS'}
                                </button>
                            </div>
                        </form>
                    </section>
                </div>

                <div className="lg:col-span-4">
                    <section className="corvus-card p-10 rounded-[40px] h-full flex flex-col justify-between">
                        <div>
                            <h2 className="text-xl font-black mb-8 flex items-center gap-3 text-white italic">
                                <Activity className="w-6 h-6 text-red-600" /> ACTIVE STATUS
                            </h2>
                            <div className="space-y-8">
                                <div className="flex flex-col gap-3">
                                    <div className="flex justify-between items-center text-[10px] font-black uppercase tracking-widest">
                                        <span className="text-slate-500">Execution Progress</span>
                                        <span className="text-red-500">{activeScan?.progress || 0}%</span>
                                    </div>
                                    <div className="w-full bg-slate-950 rounded-full h-2 border border-slate-900 overflow-hidden">
                                        <div className="bg-red-600 h-full transition-all duration-700 shadow-[0_0_15px_#dc2626]" style={{ width: `${activeScan?.progress || 0}%` }} />
                                    </div>
                                </div>
                                <div className="flex items-center gap-4 bg-black/40 p-5 rounded-3xl border border-slate-800/50">
                                    <div className={`w-3 h-3 rounded-full ${isScanning ? 'bg-red-600 animate-pulse shadow-[0_0_10px_#dc2626]' : 'bg-green-500'}`} />
                                    <div className="flex flex-col">
                                        <span className="text-[9px] text-slate-600 font-black uppercase tracking-widest">Current Task</span>
                                        <span className="text-xs font-black text-white italic uppercase">{activeScan?.current_step || "IDLE"}</span>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div className="mt-10 pt-8 border-t border-slate-800/50 grid grid-cols-2 gap-4 text-center">
                            <div className="p-4 bg-red-600/10 rounded-2xl border border-red-900/10">
                                <p className="text-2xl font-black text-red-600 tracking-tighter">{activeScan?.findings?.filter(f => (f.severity || "").toUpperCase() === 'CRITICAL').length || 0}</p>
                                <p className="text-[8px] text-slate-600 uppercase font-black">Critical</p>
                            </div>
                            <div className="p-4 bg-orange-600/10 rounded-2xl border border-orange-900/10">
                                <p className="text-2xl font-black text-orange-600 tracking-tighter">{activeScan?.findings?.filter(f => (f.severity || "").toUpperCase() === 'HIGH').length || 0}</p>
                                <p className="text-[8px] text-slate-600 uppercase font-black">High</p>
                            </div>
                            <div className="p-4 bg-yellow-600/10 rounded-2xl border border-yellow-900/10">
                                <p className="text-2xl font-black text-yellow-600 tracking-tighter">{activeScan?.findings?.filter(f => (f.severity || "").toUpperCase() === 'MEDIUM').length || 0}</p>
                                <p className="text-[8px] text-slate-600 uppercase font-black">Medium</p>
                            </div>
                            <div className="p-4 bg-blue-600/10 rounded-2xl border border-blue-900/10">
                                <p className="text-2xl font-black text-blue-600 tracking-tighter">{activeScan?.findings?.filter(f => (f.severity || "").toUpperCase() === 'LOW').length || 0}</p>
                                <p className="text-[8px] text-slate-600 uppercase font-black">Low</p>
                            </div>
                        </div>
                    </section>
                </div>
            </div>

            <section className="corvus-card rounded-[48px] overflow-hidden shadow-2xl">
                <div className="p-10 border-b border-red-900/10 flex justify-between items-center bg-black/20">
                    <h2 className="text-2xl font-black flex items-center gap-4 text-white italic tracking-tighter">
                        <FileText className="w-7 h-7 text-red-600" /> VULNERABILITY ANALYSIS
                    </h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left">
                        <thead className="bg-black/40 text-red-900/60 text-[10px] font-black uppercase tracking-[0.2em] italic">
                            <tr>
                                <th className="px-10 py-6">Threat Type / ID</th>
                                <th className="px-10 py-6">Severity</th>
                                <th className="px-10 py-6">Endpoint / Vector</th>
                                <th className="px-10 py-6 text-right">Action</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-red-900/5">
                            {!activeScan || !activeScan.findings || activeScan.findings.length === 0 ? (
                                <tr><td colSpan="4" className="px-10 py-32 text-center opacity-30 animate-pulse font-black uppercase text-[10px]">No threats detected yet</td></tr>
                            ) : (
                                activeScan.findings.map((res, i) => (
                                    <tr key={i} className="hover:bg-red-600/5 transition-colors group">
                                        <td className="px-10 py-7">
                                            <div className="flex items-center gap-4">
                                                <div className="w-10 h-10 rounded-2xl bg-red-600/10 flex items-center justify-center border border-red-600/20 group-hover:scale-110 transition-all">
                                                    <img src={logo} alt="L" className="w-6 h-6 object-contain" />
                                                </div>
                                                <div>
                                                     <div className="flex items-center gap-2 mb-1">
                                                         <span className="text-[7px] bg-red-600/20 text-red-500 px-1.5 py-0.5 rounded border border-red-900/30 font-bold">
                                                             {res.owasp_code || "A00:2021"} — {res.owasp || res.category}
                                                         </span>
                                                         <div className="text-[8px] font-black text-slate-600">{res.id}</div>
                                                     </div>
                                                     <div className="text-sm font-black text-white italic">{res.name}</div>
                                                 </div>
                                            </div>
                                        </td>
                                        <td className="px-10 py-7">
                                            <span className={`px-4 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-tighter border ${
                                                    (res.severity || "INFO").toUpperCase() === 'CRITICAL' ? 'bg-[#b71c1c] text-white border-red-900 shadow-[0_0_10px_rgba(183,28,28,0.5)]' :
                                                    (res.severity || "INFO").toUpperCase() === 'HIGH' ? 'bg-[#e53935] text-white border-red-600' : 
                                                    (res.severity || "INFO").toUpperCase() === 'MEDIUM' ? 'bg-[#fb8c00] text-white border-orange-600' :
                                                    (res.severity || "INFO").toUpperCase() === 'LOW' ? 'bg-[#fdd835] text-black border-yellow-600' :
                                                    'bg-[#2196f3] text-white border-blue-600'
                                                }`}>{res.severity || "INFO"}</span>
                                        </td>
                                        <td className="px-10 py-7"><code className="text-[10px] bg-black px-4 py-2 rounded-xl border border-slate-800 text-red-400 font-mono italic">{res.location}</code></td>
                                        <td className="px-10 py-7 text-right">
                                            <button onClick={() => setShowDetail(res)} className="text-[10px] font-black text-red-600 hover:text-white uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-all">View Details →</button>
                                        </td>
                                    </tr>
                                ))
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
