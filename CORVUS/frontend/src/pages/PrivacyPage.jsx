import React from 'react';

const PrivacyPage = () => (
    <div className="py-20 max-w-4xl animate-in fade-in duration-700">
        <h2 className="text-5xl font-black text-white italic tracking-tighter mb-10 uppercase">Privacy <span className="text-red-600 underline">Policy</span></h2>
        <div className="bg-slate-950/40 p-12 rounded-[50px] border border-red-900/20 text-slate-400 space-y-8 italic">
            <p className="text-sm font-bold leading-loose"><span className="corvus-matrix" data-text="Corvus">Corvus</span> beroperasi dalam lingkungan mandiri (standalone). Kami tidak membagikan atau mengirimkan data audit Anda ke server eksternal mana pun di luar infrastruktur lokal Anda.</p>
            <div>
                <h4 className="text-white font-black uppercase mb-2">Data Collection</h4>
                <p className="text-xs">Kami hanya menyimpan riwayat scan (target, tanggal, temuan) secara lokal di database internal Anda untuk kebutuhan pelaporan Anda sendiri.</p>
            </div>
            <div>
                <h4 className="text-white font-black uppercase mb-2">Security Measures</h4>
                <p className="text-xs">Semua data sensitif dilindungi dengan enkripsi level database dan kontrol akses JWT pada API Backend.</p>
            </div>
        </div>
    </div>
);

export default PrivacyPage;
