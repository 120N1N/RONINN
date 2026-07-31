import React from 'react';

const TermsPage = () => (
    <div className="py-20 max-w-4xl animate-in fade-in duration-700">
        <h2 className="text-5xl font-black text-white italic tracking-tighter mb-10 uppercase">Terms of <span className="text-red-600 underline">Service</span></h2>
        <div className="bg-red-950/10 p-12 rounded-[50px] border border-red-900/20 text-red-200/60 space-y-8 italic">
            <p className="text-sm font-bold leading-relaxed">PENGGUNAAN ALAT INI DIATUR OLEH HUKUM YANG BERLAKU DI WILAYAH ANDA. PENGGUNAAN <span className="corvus-matrix" data-text="CORVUS">CORVUS</span> UNTUK AKTIVITAS ILEGAL SANGAT DILARANG.</p>
            <ol className="list-decimal pl-6 space-y-4 text-xs font-bold">
                <li>Anda wajib memiliki izin eksplisit sebelum memindai infrastruktur apa pun.</li>
                <li>CorvusNoct tidak bertanggung jawab atas penyalahgunaan atau kerusakan yang diakibatkan oleh sistem ini.</li>
                <li>Segala hasil audit adalah rahasia pengguna dan tanggung jawab pengguna sepenuhnya.</li>
            </ol>
        </div>
    </div>
);

export default TermsPage;
