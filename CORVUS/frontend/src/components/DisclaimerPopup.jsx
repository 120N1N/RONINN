import React, { useState, useEffect } from 'react';
import logo from '../assets/logo.png';

const DisclaimerPopup = () => {
    const [show, setShow] = useState(false);
    useEffect(() => {
        const agreed = localStorage.getItem('corvus_agreed');
        if (!agreed) setShow(true);
    }, []);

    const handleAgree = () => {
        localStorage.setItem('corvus_agreed', 'true');
        setShow(false);
    };

    if (!show) return null;

    return (
        <div className="fixed inset-0 z-[999] flex items-center justify-center p-6 bg-black/90 backdrop-blur-xl animate-in fade-in duration-700">
            <div className="corvus-card w-full max-w-2xl rounded-[40px] shadow-[0_0_50px_rgba(220,38,38,0.2)] overflow-hidden">
                <div className="p-10 text-center">
                    <div className="flex justify-center mb-6">
                        <div className="animate-pulse">
                            <img src={logo} alt="Corvus Logo" className="w-24 h-24 object-contain shadow-[0_0_30px_rgba(220,38,38,0.3)] rounded-3xl" />
                        </div>
                    </div>
                    <h2 className="text-4xl font-black text-white tracking-tighter mb-4 italic uppercase">Identity <span className="text-red-600 underline">Authorized</span></h2>
                    <div className="bg-red-950/20 border border-red-900/30 p-8 rounded-3xl text-red-200/80 font-medium leading-relaxed italic mb-8 text-sm">
                        "Dengan menekan tombol setuju, Anda memahami bahwa Corvus adalah alat audit keamanan tingkat lanjut. CorvusNoct tidak bertanggung jawab atas segala kerusakan atau tuntutan hukum akibat penggunaan yang tidak sah terhadap infrastruktur target."
                    </div>
                    <button
                        onClick={handleAgree}
                        className="w-full bg-red-600 hover:bg-white hover:text-red-900 text-white font-black py-5 rounded-2xl transition-all shadow-xl shadow-red-600/20 active:scale-95 text-lg uppercase tracking-widest"
                    >
                        I AGREE & INITIALIZE
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DisclaimerPopup;
