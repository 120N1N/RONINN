import React from 'react';
import { Book, Lock } from 'lucide-react';

const DocsPage = () => (
    <div className="py-20 max-w-6xl mx-auto space-y-24 animate-in fade-in slide-in-from-bottom duration-1000">
        <header className="text-center space-y-6">
            <h2 className="text-6xl font-black italic tracking-tighter uppercase"><span className="corvus-matrix" data-text="CORVUS">CORVUS</span></h2>
            <p className="text-slate-500 font-bold tracking-[0.4em] uppercase text-xs">Automated Web Security Assessment Platform</p>
            <div className="flex justify-center gap-4 pt-4 flex-wrap">
                <span className="px-4 py-1 bg-red-600/10 border border-red-600/30 rounded-full text-[9px] font-black text-red-600 dark:text-red-500 uppercase tracking-widest">v2.1.0-RED</span>
                <span className="px-4 py-1 bg-emerald-600/10 border border-emerald-600/30 rounded-full text-[9px] font-black text-emerald-700 dark:text-green-500 uppercase tracking-widest">MIT LICENSE</span>
                <span className="px-4 py-1 bg-blue-600/10 border border-blue-600/30 rounded-full text-[9px] font-black text-blue-700 dark:text-blue-500 uppercase tracking-widest">DOCKER READY</span>
            </div>
        </header>

        <section className="corvus-card p-10 sm:p-16 rounded-[48px] sm:rounded-[60px] shadow-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-64 h-64 bg-red-600/5 blur-[100px] -z-10" />
            <h3 className="text-2xl font-black italic mb-8 flex items-center gap-4 uppercase tracking-tighter" style={{ color: 'var(--text-primary)' }}>
                <div className="bg-red-600 p-2 rounded-xl shadow-md shadow-red-600/30"><Book className="w-5 h-5 text-white" /></div> 
                Gambaran Umum
            </h3>
            <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed italic mb-12">
                Corvus adalah platform manajemen audit keamanan web otomatis yang dirancang untuk memberikan visibilitas mendalam terhadap postur risiko aset digital. Dibangun di atas fondasi modular, Corvus menggabungkan berbagai instrumen audit industri ke dalam satu orkestra cerdas untuk menghasilkan laporan kerentanan yang akurat, konsisten, dan dapat ditindaklanjuti.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
                {[
                    { t: "Inkonsistensi", s: "Idempotensi: Hasil reproduktif berbasis hashing." },
                    { t: "Destruktif", s: "Safe Probing: Audit aman tanpa eksploitasi." },
                    { t: "Overflow Data", s: "Deduplikasi: Pelaporan temuan redundan lintas scan." },
                    { t: "Silo Data", s: "Normalisasi: Satu format JSON standar untuk semua tool." }
                ].map((item, i) => (
                    <div key={i} className="bg-slate-50 dark:bg-black/40 p-8 rounded-3xl border border-slate-200 dark:border-slate-800/50 hover:border-red-600/40 transition-all shadow-sm">
                        <span className="text-[10px] font-black text-red-600 uppercase tracking-widest mb-3 block italic">{item.t}</span>
                        <p className="text-xs text-slate-900 dark:text-white font-bold">{item.s}</p>
                    </div>
                ))}
            </div>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-2 gap-10 sm:gap-12">
            <div className="corvus-card p-10 sm:p-12 rounded-[44px] sm:rounded-[50px] shadow-xl">
                <h3 className="text-xl font-black italic mb-6 uppercase tracking-wider" style={{ color: 'var(--text-primary)' }}>
                    Fase Audit Sistem
                </h3>
                <div className="space-y-6">
                    {[
                        { f: "01 Recon", d: "DNS Discovery & Tech Stack mapping." },
                        { f: "02 Enum", d: "Port scanning & service identification." },
                        { f: "03 Disc", d: "Sensitive file & directory enumeration." },
                        { f: "04 Vuln", d: "Template-based vulnerability scanning." },
                        { f: "05 Safe", d: "Security headers, CORS & rate limit audit." }
                    ].map((f, i) => (
                        <div key={i} className="flex gap-5 items-start">
                            <span className="text-2xl font-black text-red-600/30 italic tabular-nums font-mono">{f.f.split(' ')[0]}</span>
                            <div>
                                <span className="text-xs font-black text-slate-900 dark:text-white uppercase tracking-wider">{f.f.split(' ')[1]}</span>
                                <p className="text-[11px] text-slate-600 dark:text-slate-400 font-bold italic mt-0.5">{f.d}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="corvus-card p-10 sm:p-12 rounded-[44px] sm:rounded-[50px] shadow-xl">
                <h3 className="text-xl font-black italic mb-6 uppercase tracking-wider" style={{ color: 'var(--text-primary)' }}>
                    API Integration
                </h3>
                <div className="space-y-6 text-xs">
                    <p className="text-slate-600 dark:text-slate-400 italic">Interaksi pihak ketiga melalui Official REST API Endpoint (127.0.0.1:8000).</p>
                    <div className="space-y-4">
                        {/* POST /api/scan */}
                        <div className="bg-slate-50 dark:bg-black/50 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-3 shadow-sm">
                            <div className="flex items-center justify-between flex-wrap gap-2">
                                <div className="flex items-center gap-2.5">
                                    <span className="bg-blue-600/15 text-blue-700 dark:bg-blue-950 dark:text-blue-400 border border-blue-300 dark:border-blue-800 text-[10px] font-black px-2.5 py-1 rounded-lg uppercase tracking-wider font-mono">
                                        POST
                                    </span>
                                    <span className="font-mono font-bold text-xs text-slate-800 dark:text-slate-200">
                                        /api/scan
                                    </span>
                                </div>
                                <span className="text-slate-500 italic text-[10px] font-medium">Initiate audit</span>
                            </div>
                            <div className="bg-white dark:bg-black/80 rounded-xl p-3 border border-slate-200 dark:border-slate-800/80 font-mono text-[11px] overflow-x-auto">
                                <span className="text-slate-500">{"{"}</span>{" "}
                                <span className="text-purple-600 dark:text-purple-400 font-bold">"target"</span>
                                <span className="text-slate-500">:</span>{" "}
                                <span className="text-emerald-600 dark:text-emerald-400 font-bold">"domain.com"</span>
                                <span className="text-slate-500">,</span>{" "}
                                <span className="text-purple-600 dark:text-purple-400 font-bold">"mode"</span>
                                <span className="text-slate-500">:</span>{" "}
                                <span className="text-emerald-600 dark:text-emerald-400 font-bold">"normal"</span>{" "}
                                <span className="text-slate-500">{"}"}</span>
                            </div>
                        </div>

                        {/* GET /api/scan/id */}
                        <div className="bg-slate-50 dark:bg-black/50 p-5 rounded-2xl border border-slate-200 dark:border-slate-800 space-y-3 shadow-sm">
                            <div className="flex items-center justify-between flex-wrap gap-2">
                                <div className="flex items-center gap-2.5">
                                    <span className="bg-emerald-600/15 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400 border border-emerald-300 dark:border-emerald-800 text-[10px] font-black px-2.5 py-1 rounded-lg uppercase tracking-wider font-mono">
                                        GET
                                    </span>
                                    <span className="font-mono font-bold text-xs text-slate-800 dark:text-slate-200">
                                        /api/scan/:id
                                    </span>
                                </div>
                                <span className="text-slate-500 italic text-[10px] font-medium">Check progress</span>
                            </div>
                            <div className="bg-white dark:bg-black/80 rounded-xl p-3 border border-slate-200 dark:border-slate-800/80 font-mono text-[11px] overflow-x-auto">
                                <span className="text-purple-600 dark:text-purple-400 font-bold">status</span>
                                <span className="text-slate-500">:</span>{" "}
                                <span className="text-amber-600 dark:text-yellow-400 font-bold">"RUNNING"</span>
                                <span className="text-slate-500">,</span>{" "}
                                <span className="text-purple-600 dark:text-purple-400 font-bold">progress</span>
                                <span className="text-slate-500">:</span>{" "}
                                <span className="text-blue-600 dark:text-blue-400 font-bold">65</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </section>

        <section className="bg-slate-50 dark:bg-red-950/5 border border-slate-200 dark:border-red-900/20 p-10 sm:p-16 rounded-[48px] sm:rounded-[60px] text-center shadow-lg">
            <h3 className="text-xl font-black italic mb-6 flex items-center justify-center gap-4 uppercase tracking-tighter" style={{ color: 'var(--text-primary)' }}>
                <Lock className="w-5 h-5 text-red-600" /> Aturan Etika & Batasan
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {[
                    { t: "Otorisasi", d: "Izin tertulis wajib sebelum audit." },
                    { t: "No Exploit", d: "Pemetaan kerentanan tanpa merusak layanan." },
                    { t: "Blokir IP", d: "IP Privat (SSRF prevention) diblokir sistem." }
                ].map((e, i) => (
                    <div key={i}>
                        <h4 className="text-[10px] font-black text-red-600 uppercase mb-2 italic underline underline-offset-4 tracking-wider">{e.t}</h4>
                        <p className="text-[11px] text-slate-600 dark:text-slate-400 font-bold italic">{e.d}</p>
                    </div>
                ))}
            </div>
            <div className="mt-12 bg-white dark:bg-black/40 p-6 rounded-3xl border border-slate-200 dark:border-red-900/10 max-w-2xl mx-auto italic text-xs text-slate-700 dark:text-red-200/60 leading-relaxed shadow-sm">
                "Pengoperasian <span className="corvus-matrix" data-text="Corvus">Corvus</span> Red Edition diatur oleh hukum yang berlaku. CorvusNoct tidak bertanggung jawab atas segala penyalahgunaan infrastruktur yang melanggar hukum."
            </div>
        </section>

        <section className="corvus-card p-10 sm:p-16 rounded-[48px] sm:rounded-[60px] shadow-2xl relative overflow-hidden">
            <h3 className="text-2xl font-black italic mb-8 uppercase tracking-tighter" style={{ color: 'var(--text-primary)' }}>
                <span className="text-red-600">OWASP</span> Top 10 (2021) Mapping
            </h3>
            <p className="text-slate-600 dark:text-slate-400 text-sm leading-relaxed italic mb-8">
                Seluruh kerentanan yang terdeteksi oleh Corvus otomatis dipetakan ke standar keamanan internasional OWASP Top 10 versi terbaru untuk mempermudah pelaporan dan kepatuhan.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                    { code: "A01", name: "Broken Access Control", desc: "Akses tidak sah ke data/fitur" },
                    { code: "A02", name: "Cryptographic Failures", desc: "Data sensitif tidak terenkripsi" },
                    { code: "A03", name: "Injection", desc: "SQLi, XSS, Command Injection" },
                    { code: "A04", name: "Insecure Design", desc: "Cacat logika desain sistem" },
                    { code: "A05", name: "Security Misconfiguration", desc: "Salah konfigurasi keamanan" },
                    { code: "A06", name: "Vulnerable Components", desc: "Library kadaluarsa/rentan" },
                    { code: "A07", name: "Auth Failures", desc: "Kelemahan login & sesi" },
                    { code: "A08", name: "Data Integrity Failures", desc: "Integritas software rusak" },
                    { code: "A09", name: "Logging & Monitoring", desc: "Kurangnya audit trail" },
                    { code: "A10", name: "SSRF", desc: "Server-Side Request Forgery" }
                ].map((owasp, i) => (
                    <div key={i} className="flex gap-4 items-center bg-slate-50 dark:bg-black/40 p-4 rounded-2xl border border-slate-200 dark:border-slate-800/50 hover:border-red-600/30 transition-all shadow-sm">
                        <div className="bg-red-600 text-white font-black text-[11px] px-3 py-1.5 rounded-lg uppercase tracking-widest shrink-0">{owasp.code}:2021</div>
                        <div>
                            <div className="text-slate-900 dark:text-slate-200 text-xs font-bold uppercase tracking-wider">{owasp.name}</div>
                            <div className="text-slate-500 text-[10px] font-medium italic mt-0.5">{owasp.desc}</div>
                        </div>
                    </div>
                ))}
            </div>
        </section>
    </div>
);

export default DocsPage;
