import React, { useState, useEffect } from 'react';
import { Trash2, History, X, Download } from 'lucide-react';
import logo from '../assets/logo.png';
import VulnDetailModal from '../components/VulnDetailModal';

const API_BASE = import.meta.env.VITE_API_URL || "/api";

const ReportsPage = () => {
    const [reports, setReports] = useState([]);
    const [selectedReport, setSelectedReport] = useState(null);
    const [showDetail, setShowDetail] = useState(null);

    const [selectedForDelete, setSelectedForDelete] = useState([]);

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

    const handleDeleteSelected = async () => {
        if (!window.confirm(`Menghapus ${selectedForDelete.length} laporan secara permanen. Lanjutkan?`)) return;
        const token = localStorage.getItem('corvus_token');
        await Promise.all(selectedForDelete.map(id => 
            fetch(`${API_BASE}/reports/${id}`, {
                method: 'DELETE',
                headers: { "Authorization": `Bearer ${token}` }
            })
        ));
        setSelectedForDelete([]);
        fetchReports();
    };

    return (
        <>
        <div className="py-20">
            <div className="flex items-center justify-between mb-12">
                <h2 className="text-5xl font-black text-white italic tracking-tighter uppercase">Security <span className="text-red-600 underline">History</span></h2>
                {!selectedReport && selectedForDelete.length > 0 && (
                    <button 
                        onClick={handleDeleteSelected}
                        className="flex items-center gap-2 bg-red-900/40 hover:bg-red-600 text-white px-6 py-3 rounded-2xl transition-all border border-red-600/50 shadow-xl shadow-red-900/20 animate-in fade-in zoom-in duration-300"
                    >
                        <Trash2 className="w-5 h-5" />
                        <span className="font-black text-xs uppercase tracking-widest">Delete ({selectedForDelete.length})</span>
                    </button>
                )}
            </div>

            {!selectedReport ? (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                    {reports.map((h, i) => (
                        <div key={i} className="corvus-card p-10 rounded-[48px] hover:border-red-600 transition-all shadow-2xl group relative">
                            <div className="absolute top-10 right-10 z-20">
                                <input 
                                    type="checkbox" 
                                    className="w-5 h-5 accent-red-600 cursor-pointer bg-black border-red-900"
                                    checked={selectedForDelete.includes(h.id)}
                                    onChange={(e) => {
                                        if (e.target.checked) setSelectedForDelete(prev => [...prev, h.id]);
                                        else setSelectedForDelete(prev => prev.filter(id => id !== h.id));
                                    }}
                                />
                            </div>
                            <div className="cursor-pointer" onClick={() => setSelectedReport(h)}>
                                <History className="w-10 h-10 text-red-600 opacity-20 mb-6 group-hover:opacity-100 transition-opacity" />
                                <h4 className="text-2xl font-black text-white italic uppercase truncate mb-6">{h.target}</h4>
                                <div className="flex gap-8">
                                    <div className="flex flex-col"><span className="text-[8px] font-black text-red-600 uppercase">Findings</span><span className="text-white font-black text-2xl">{h.findings?.length || 0}</span></div>
                                    <div className="flex flex-col"><span className="text-[8px] font-black text-red-600 uppercase">Date</span><span className="text-slate-500 font-bold text-xs">{new Date(h.created_at).toLocaleDateString()}</span></div>
                                </div>
                                <div className="mt-8 pt-6 border-t border-red-900/10 flex justify-end">
                                    <span className="text-[10px] font-black text-red-600 group-hover:translate-x-2 transition-transform italic uppercase">Open Report →</span>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="space-y-8 animate-in fade-in duration-500">
                    <button onClick={() => setSelectedReport(null)} className="text-[10px] font-black text-slate-500 hover:text-red-600 uppercase tracking-widest flex items-center gap-2 mb-6 transition-colors">
                        ← BACK TO HISTORY
                    </button>
                    <div className="corvus-card rounded-[48px] overflow-hidden shadow-2xl">
                        <div className="p-10 border-b border-red-900/10 flex justify-between items-center bg-black/20">
                            <div>
                                <h3 className="text-3xl font-black text-white italic uppercase">{selectedReport.target}</h3>
                                <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mt-1">Snapshot Audit: {new Date(selectedReport.created_at).toLocaleString()}</p>
                            </div>
                            <div className="flex gap-4">
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
                                                fetch(`${API_BASE}/reports`, {
                                                    headers: { "Authorization": `Bearer ${token}` }
                                                }).then(r => r.json()).then(d => {
                                                    if (Array.isArray(d)) setReports(d);
                                                });
                                            }
                                        }
                                    }}
                                    className="bg-slate-900 text-slate-500 p-3 rounded-2xl hover:bg-red-600 hover:text-white transition-all shadow-lg relative z-50 group cursor-pointer"
                                >
                                    <X className="w-5 h-5 group-active:scale-90 transition-transform" />
                                </button>
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
                                    className="bg-red-600 text-white p-3 rounded-2xl hover:bg-white hover:text-red-900 transition-all shadow-lg shadow-red-600/40 relative z-50 group cursor-pointer"
                                >
                                    <Download className="w-5 h-5 group-active:scale-90 transition-transform" />
                                </button>
                            </div>
                        </div>
                        <div className="overflow-x-auto">
                            <table className="w-full text-left">
                                <thead className="bg-black/40 text-red-900/60 text-[10px] font-black uppercase tracking-[0.2em] italic">
                                    <tr>
                                        <th className="px-10 py-6">Threat Type / ID</th>
                                        <th className="px-10 py-6">Severity</th>
                                        <th className="px-10 py-6">Endpoint</th>
                                        <th className="px-10 py-6 text-right">Action</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-red-900/5">
                                    {selectedReport.findings.map((res, i) => (
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
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}
        </div>
        <VulnDetailModal finding={showDetail} onClose={() => setShowDetail(null)} />
        </>
    );
};

export default ReportsPage;
