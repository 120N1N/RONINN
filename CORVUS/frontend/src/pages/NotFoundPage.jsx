import React from 'react';
import { Link } from 'react-router-dom';

const NotFoundPage = () => (
    <div className="flex flex-col items-center justify-center min-h-[60vh] animate-in zoom-in duration-500 text-center">
        <h1 className="text-9xl font-black text-transparent bg-clip-text bg-gradient-to-br from-red-600 to-red-900 italic tracking-tighter mb-4 pr-4 drop-shadow-[0_0_30px_rgba(220,38,38,0.3)]">404</h1>
        <h2 className="text-2xl font-black text-white uppercase tracking-widest mb-6">Target Not Found</h2>
        <p className="text-slate-400 font-bold italic mb-10 max-w-md mx-auto text-sm">
            Entitas atau endpoint yang Anda cari tidak terdaftar dalam direktori Corvus. Pastikan URL sudah benar.
        </p>
        <Link to="/" className="bg-red-600 hover:bg-white hover:text-red-900 text-white font-black py-4 px-8 rounded-2xl transition-all uppercase text-[10px] tracking-widest shadow-xl shadow-red-600/20 active:scale-95">
            Kembali ke Dashboard
        </Link>
    </div>
);

export default NotFoundPage;
