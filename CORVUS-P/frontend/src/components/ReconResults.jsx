import React from 'react';
import { Network } from 'lucide-react';

const ReconResults = ({ activeScan }) => {
    // Gunakan data asli dari backend, jika belum ada tampilkan field kosong
    const data = {
        tested_address: activeScan?.recon?.tested_address || "—",
        public_addresses: activeScan?.recon?.public_addresses || "—",
        whois: {
            source: activeScan?.recon?.whois?.source || "—",
            registrar: activeScan?.recon?.whois?.registrar || "—",
            created: activeScan?.recon?.whois?.created || "—",
            updated: activeScan?.recon?.whois?.updated || "—",
            expires: activeScan?.recon?.whois?.expires || "—",
            status: activeScan?.recon?.whois?.status || "—",
            nameservers: activeScan?.recon?.whois?.nameservers || "—"
        },
        ping: {
            protocol: activeScan?.recon?.ping?.protocol || "—",
            loss: activeScan?.recon?.ping?.loss || "—",
            stats: activeScan?.recon?.ping?.stats || "—",
            duration: activeScan?.recon?.ping?.duration || "—",
            raw: activeScan?.recon?.ping?.raw || "Waiting for ICMP sequence data..."
        },
        ports: {
            ptr: activeScan?.recon?.ports?.ptr || "—",
            profile: activeScan?.recon?.ports?.profile || "—",
            tested: activeScan?.recon?.ports?.tested || "—",
            duration: activeScan?.recon?.ports?.duration || "—",
            list: activeScan?.recon?.ports?.list || []
        }
    };

    const targetUrl = activeScan?.target || "—";

    // Komponen Row Header Merge
    const GroupHeader = ({ title }) => (
        <tr className="bg-slate-100 dark:bg-red-950/40 border-b border-slate-200 dark:border-red-900/30">
            <td colSpan="2" className="p-3 text-center text-red-600 dark:text-red-400 font-black uppercase text-[10px] tracking-[0.2em]">
                {title}
            </td>
        </tr>
    );

    // Komponen Row Biasa
    const KVRow = ({ label, value }) => (
        <tr className="border-b border-slate-200 dark:border-slate-800/60 hover:bg-slate-50 dark:hover:bg-red-500/5 transition-colors group">
            <td className="w-1/3 md:w-1/4 bg-slate-50/80 dark:bg-black/40 p-4 text-[10px] sm:text-xs font-black text-slate-700 dark:text-slate-400 tracking-wider align-top border-r border-slate-200 dark:border-slate-800/60 group-hover:text-red-600 transition-colors">
                {label}
            </td>
            <td className="w-2/3 md:w-3/4 p-4 text-xs sm:text-sm text-slate-900 dark:text-slate-200 font-medium whitespace-pre-wrap font-mono align-top">
                {value}
            </td>
        </tr>
    );

    return (
        <section className="corvus-card rounded-[40px] sm:rounded-[48px] overflow-hidden shadow-2xl">
            {/* Main Header */}
            <div className="p-6 sm:p-8 border-b border-slate-200 dark:border-red-900/20 bg-slate-50/80 dark:bg-black/40 flex items-center gap-3">
                <Network className="w-6 h-6 text-red-600" />
                <h2 className="text-xl font-black italic tracking-tighter uppercase" style={{ color: 'var(--text-primary)' }}>RECONNAISSANCE RESULTS</h2>
            </div>
            
            <div className="bg-transparent dark:bg-black/10 overflow-x-auto w-full">
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
                        <tr className="hover:bg-slate-50 dark:hover:bg-red-500/5 transition-colors border-b border-slate-200 dark:border-slate-800/60">
                            <td className="w-1/3 md:w-1/4 bg-slate-50/80 dark:bg-black/40 p-4 text-[10px] sm:text-xs font-black text-slate-700 dark:text-slate-400 tracking-wider align-top border-r border-slate-200 dark:border-slate-800/60">
                                Terminal Output (ICMP)
                            </td>
                            <td className="w-2/3 md:w-3/4 p-4 align-top">
                                <pre className="text-xs text-slate-800 dark:text-slate-300 font-mono whitespace-pre-wrap overflow-x-auto p-4 border border-slate-200 dark:border-slate-900 rounded-2xl bg-white dark:bg-[#090a0f] shadow-sm">
                                    {data.ping.raw}
                                </pre>
                            </td>
                        </tr>

                        <GroupHeader title="Port Scanner Results" />
                        <KVRow label="Profile" value={data.ports.profile} />
                        <KVRow label="Ports Tested" value={data.ports.tested} />
                        <KVRow label="Duration" value={data.ports.duration} />
                        
                        {/* Ports Matrix Special Row */}
                        <tr className="hover:bg-slate-50 dark:hover:bg-red-500/5 transition-colors border-b border-slate-200 dark:border-slate-800/60">
                            <td colSpan="2" className="p-0">
                                {data.ports.list.length === 0 ? (
                                    <div className="p-8 text-center text-slate-500 italic tracking-widest font-sans font-black text-[9px] uppercase">
                                        Awaiting Port Scan Data...
                                    </div>
                                ) : (
                                    <table className="w-full text-left bg-slate-50/60 dark:bg-black/20">
                                        <thead className="text-[9px] font-black uppercase text-slate-700 dark:text-slate-400 tracking-widest border-b border-slate-200 dark:border-slate-800 bg-slate-100 dark:bg-black/60">
                                            <tr>
                                                <th className="px-6 py-4">Port</th>
                                                <th className="px-6 py-4">Protocol</th>
                                                <th className="px-6 py-4">State</th>
                                                <th className="px-6 py-4">Service</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y divide-slate-200 dark:divide-slate-800/50 font-mono text-[10px] text-slate-900 dark:text-slate-300">
                                            {data.ports.list.map((p, idx) => (
                                                <tr key={idx} className="hover:bg-slate-100/70 dark:hover:bg-red-900/20 transition-colors">
                                                    <td className="px-6 py-4 font-bold text-red-600 dark:text-red-400">{p.port}</td>
                                                    <td className="px-6 py-4">{p.protocol}</td>
                                                    <td className="px-6 py-4"><span className="text-emerald-600 dark:text-green-500 font-bold">{p.state}</span></td>
                                                    <td className="px-6 py-4 text-slate-700 dark:text-slate-300">{p.service}</td>
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

export default React.memo(ReconResults);
