import React from 'react';
import { Link } from 'react-router-dom';
import { User, LogOut, LogIn } from 'lucide-react';
import logo from '../assets/logo.png';

const Navbar = ({ user, onLogout }) => (
    <nav className="flex items-center justify-between mb-12 border-b border-red-900/20 pb-6 max-w-7xl mx-auto sticky top-0 z-50 bg-[#0f0f0f]/80 backdrop-blur-md">
        <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-3 group">
                <div className="group-hover:scale-110 transition-transform">
                    <img src={logo} alt="Corvus Logo" className="w-12 h-12 object-cover rounded-2xl shadow-[0_0_20px_rgba(220,38,38,0.3)]" />
                </div>
                <div>
                    <h1 className="text-2xl font-black tracking-tight text-white italic">CORVUS</h1>
                    <p className="text-[8px] text-red-500 font-bold tracking-[0.3em] uppercase">Automated Testing</p>
                </div>
            </Link>
        </div>
        <div className="flex items-center gap-8">
            <div className="hidden md:flex gap-8 items-center">
                <Link to="/" className="text-[10px] font-black text-slate-400 hover:text-red-500 transition-colors uppercase tracking-widest">Dashboard</Link>
                <Link to="/reports" className="text-[10px] font-black text-slate-400 hover:text-red-500 transition-colors uppercase tracking-widest">Reports</Link>
                {user && (
                    <>
                        <Link to="/api-keys" className="text-[10px] font-black text-slate-400 hover:text-red-500 transition-colors uppercase tracking-widest flex items-center gap-1">API</Link>
                        {user.username === 'admin' && (
                            <Link to="/models" className="text-[10px] font-black text-slate-400 hover:text-red-500 transition-colors uppercase tracking-widest flex items-center gap-1">Models</Link>
                        )}
                    </>
                )}
                <Link to="/docs" className="text-[10px] font-black text-slate-400 hover:text-red-500 transition-colors uppercase tracking-widest">Docs</Link>
            </div>
            {user ? (
                <div className="flex items-center gap-4">
                    <Link to="/profile" className="flex items-center gap-2 bg-red-600/10 border border-red-900/30 px-5 py-2 rounded-xl text-[10px] font-black text-red-500 uppercase tracking-widest italic hover:bg-red-600/20 transition-colors">
                        {user.photo_url ? (
                            <img src={user.photo_url} alt="Profile" className="w-5 h-5 rounded-full object-cover border border-red-500/50" />
                        ) : (
                            <User className="w-3 h-3" />
                        )}
                        {user.first_name || user.username}
                    </Link>
                    <button onClick={onLogout} className="text-slate-600 hover:text-red-500 transition-colors"><LogOut className="w-5 h-5" /></button>
                </div>
            ) : (
                <Link to="/login" className="bg-red-600 text-white px-6 py-2.5 rounded-xl text-[10px] font-black hover:bg-white hover:text-red-900 transition-all uppercase tracking-widest flex items-center gap-2 shadow-lg shadow-red-600/20 underline-offset-4">
                    <LogIn className="w-4 h-4" /> SECURE LOGIN
                </Link>
            )}
        </div>
    </nav>
);

export default Navbar;
