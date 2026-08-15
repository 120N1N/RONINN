import React from 'react';
import { Network } from 'lucide-react';

const ReconResults = ({ activeScan }) => {
    // Gunakan data asli dari backend, jika belum ada tampilkan field kosong
    const data = activeScan?.recon || {
        tested_address: "—",
        public_addresses: "—",
        whois: {
            source: "—",
            registrar: "—",
            created: "—",
            updated: "—",
            expires: "—",
            status: "—",
            nameservers: "—"
        },
        ping: {
            protocol: "—",
            loss: "—",
            stats: "—",
            duration: "—",
            raw: "Waiting for ICMP sequence data..."
        },
        ports: {
            ptr: "—",
            profile: "—",
            tested: "—",
            duration: "—",
            list: []
        }
    };

    const targetUrl = activeScan?.target || "—";

    // Komponen Row Header Merge
    const GroupHeader = ({ title }) => (
        <tr className="bg-red-900/20 border-b border-red-900/30">
            <td colSpan="2" className="p-3 text-center text-red-500 font-black uppercase text-[10px] tracking-[0.2em]">
                {title}
            </td>
        </tr>
    );

    // Komponen Row Biasa
    const KVRow = ({ label, value }) => (
        <tr className="border-b border-red-900/10 hover:bg-red-600/5 transition-colors group">
            <td className="w-1/3 md:w-1/4 bg-black/40 p-4 text-[10px] sm:text-xs font-black text-slate-400 tracking-wider align-top border-r border-red-900/10 group-hover:text-slate-300">
                {label}
            </td>
            <td className="w-2/3 md:w-3/4 p-4 text-xs sm:text-sm text-slate-300 font-medium whitespace-pre-wrap font-mono align-top">
                {value}
            </td>
        </tr>
    );

    return (
        <section className="corvus-card rounded-[48px] overflow-hidden shadow-2xl animate-in slide-in-from-bottom-5 duration-700">
            {/* Main Header */}
            <div className="p-8 border-b border-red-900/20 bg-black/40 flex items-center gap-3">
                <Network className="w-6 h-6 text-red-600" />
                <h2 className="text-xl font-black text-white italic tracking-tighter uppercase">RECONNAISSANCE RESULTS</h2>
            </div>
            
            <div className="bg-black/10">
                <table className="w-full text-left border-collapse">
                    <tbody>
                        
                        <GroupHeader title="IP Mapping" />
                        <KVRow label="Target" value={targetUrl} />
                        <KVRow label="Tested Address" value={data.tested_address} />
                        <KVRow label="Public Addresses" value={data.public_addresses} />
                        
                        <GroupHeader title="Domain & Registrar (WHOIS)" />
                        <KVRow label="Primary Source" value={data.whois.source} />
                        <KVRow label="Registrar / Org" value={data.whois.registrar} />
                        <KVRow label="Created" value={data.whois.created} />
                        <KVRow label="Updated" value={data.whois.updated} />
                        <KVRow label="Expires" value={data.whois.expires} />
                        <KVRow label="Statuses" value={data.whois.status} />
                        <KVRow label="Name Servers" value={data.whois.nameservers} />

                        <GroupHeader title="Ping & Availability Profiling" />
                        <KVRow label="Protocol" value={data.ping.protocol} />
                        <KVRow label="Packet Loss" value={data.ping.loss} />
                        <KVRow label="Min/Avg/Max Ping" value={data.ping.stats} />
                        <KVRow label="Total Duration" value={data.ping.duration} />
                        
                        {/* Ping Output Special Row */}
                        <tr className="hover:bg-red-600/5 transition-colors">
                            <td className="w-1/3 md:w-1/4 bg-black/40 p-4 text-[10px] sm:text-xs font-black text-slate-400 tracking-wider align-top border-r border-red-900/10">
                                Terminal Output (ICMP)
                            </td>
                            <td className="w-2/3 md:w-3/4 p-4 align-top">
                                <pre className="text-[9px] text-slate-500 font-mono whitespace-pre-wrap overflow-x-auto p-4 border border-slate-900 rounded-2xl bg-[#050505] shadow-inner">
                                    {data.ping.raw}
                                </pre>
                            </td>
                        </tr>

                        <GroupHeader title="Port Scanner Results" />
                        <KVRow label="Profile" value={data.ports.profile} />
                        <KVRow label="Ports Tested" value={data.ports.tested} />
                        <KVRow label="Duration" value={data.ports.duration} />
                        
                        {/* Ports Matrix Special Row */}
                        <tr className="hover:bg-red-600/5 transition-colors border-b border-red-900/10">
                            <td colSpan="2" className="p-0">
                                {data.ports.list.length === 0 ? (
                                    <div className="p-8 text-center text-slate-600 italic tracking-widest font-sans font-black text-[9px] uppercase">
                                        Awaiting Port Scan Data...
                                    </div>
                                ) : (
                                    <table className="w-full text-left bg-black/20">
                                        <thead className="text-[9px] font-black uppercase text-slate-500 tracking-widest border-b border-slate-800 bg-black/40">
                                            <tr>
                                                <th className="px-6 py-4">Port</th>
                                                <th className="px-6 py-4">Protocol</th>
                                                <th className="px-6 py-4">State</th>
                                                <th className="px-6 py-4">Service</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-800/50 font-mono text-[10px] text-slate-300">
                                            {data.ports.list.map((p, idx) => (
                                                <tr key={idx} className="hover:bg-red-900/20 transition-colors">
                                                    <td className="px-6 py-4 font-bold text-red-400">{p.port}</td>
                                                    <td className="px-6 py-4">{p.protocol}</td>
                                                    <td className="px-6 py-4"><span className="text-green-500">{p.state}</span></td>
                                                    <td className="px-6 py-4">{p.service}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                )}
                            </td>
                        </tr>

                    </tbody>
                </table>
            </div>
        </section>
    );
};

export default ReconResults;
