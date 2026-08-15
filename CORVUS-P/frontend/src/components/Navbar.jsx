import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { User, LogOut, LogIn, Menu, X, Shield, Key, Cpu, FileText, LayoutDashboard } from 'lucide-react';
import logo from '../assets/logo.png';

const Navbar = ({ user, onLogout }) => {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const toggleMobileMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen);
    const closeMobileMenu = () => setIsMobileMenuOpen(false);

    return (
        <nav className="mb-8 md:mb-12 border-b border-red-900/20 pb-4 md:pb-6 max-w-[1800px] mx-auto sticky top-0 z-50 bg-[#0f0f0f]/90 backdrop-blur-md px-2 sm:px-4">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Link to="/" onClick={closeMobileMenu} className="flex items-center gap-3 group">
                        <div className="group-hover:scale-110 transition-transform">
                            <img src={logo} alt="Corvus Logo" className="w-10 h-10 sm:w-12 sm:h-12 object-cover rounded-2xl shadow-[0_0_20px_rgba(220,38,38,0.3)]" />
                        </div>
                        <div>
                            <h1 className="text-xl sm:text-2xl font-black tracking-tight text-white italic">CORVUS</h1>
                            <p className="text-[7px] sm:text-[8px] text-red-500 font-bold tracking-[0.3em] uppercase">Automated Testing</p>
                        </div>
                    </Link>
                </div>

                {/* Desktop & Tablet Navigation (768px+) */}
                <div className="hidden md:flex items-center gap-6 lg:gap-8">
                    <div className="flex gap-6 lg:gap-8 items-center">
                        <Link to="/" className="text-[10px] font-black text-slate-400 hover:text-red-500 transition-colors uppercase tracking-widest">Dashboard</Link>
                        <Link to="/reports" className="text-[10px] font-black text-slate-400 hover:text-red-500 transition-colors uppercase tracking-widest">Reports</Link>
                        {user && (
                            <>

                                {user.username === 'admin' && (
                                    <Link to="/models" className="text-[10px] font-black text-slate-400 hover:text-red-500 transition-colors uppercase tracking-widest">Models</Link>
                                )}
                            </>
                        )}
                        <Link to="/docs" className="text-[10px] font-black text-slate-400 hover:text-red-500 transition-colors uppercase tracking-widest">Docs</Link>
                    </div>

                    {user ? (
                        <div className="flex items-center gap-3 lg:gap-4">
                            <Link to="/profile" className="flex items-center gap-2 bg-red-600/10 border border-red-900/30 px-4 lg:px-5 py-2 rounded-xl text-[10px] font-black text-red-500 uppercase tracking-widest italic hover:bg-red-600/20 transition-colors">
                                {user.photo_url ? (
                                    <img src={user.photo_url} alt="Profile" className="w-5 h-5 rounded-full object-cover border border-red-500/50" />
                                ) : (
                                    <User className="w-3 h-3" />
                                )}
                                {user.first_name || user.username}
                            </Link>
                            <button onClick={onLogout} title="Logout" className="text-slate-500 hover:text-red-500 transition-colors p-2"><LogOut className="w-5 h-5" /></button>
                        </div>
                    ) : (
                        <Link to="/login" className="bg-red-600 text-white px-5 py-2.5 rounded-xl text-[10px] font-black hover:bg-white hover:text-red-900 transition-all uppercase tracking-widest flex items-center gap-2 shadow-lg shadow-red-600/20">
                            <LogIn className="w-4 h-4" /> SECURE LOGIN
                        </Link>
                    )}
                </div>

                {/* Mobile Hamburger Toggle (< 768px) */}
                <div className="flex md:hidden items-center gap-3">
                    {user && (
                        <Link to="/profile" onClick={closeMobileMenu} className="flex items-center gap-1.5 bg-red-600/10 border border-red-900/30 px-3 py-1.5 rounded-xl text-[9px] font-black text-red-500 uppercase tracking-widest">
                            <User className="w-3 h-3" />
                            {user.username}
                        </Link>
                    )}
                    <button 
                        onClick={toggleMobileMenu}
                        className="p-2 rounded-xl bg-red-950/40 border border-red-900/30 text-slate-200 hover:text-red-500 focus:outline-none transition-colors"
                        aria-label="Toggle Navigation Menu"
                    >
                        {isMobileMenuOpen ? <X className="w-6 h-6 text-red-500" /> : <Menu className="w-6 h-6 text-slate-200" />}
                    </button>
                </div>
            </div>

            {/* Mobile Hamburger Drawer Menu (< 768px) */}
            {isMobileMenuOpen && (
                <div className="md:hidden mt-4 pt-4 border-t border-red-900/30 flex flex-col gap-3 animate-in slide-in-from-top-4 duration-200">
                    <Link to="/" onClick={closeMobileMenu} className="flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs font-black text-slate-200 hover:text-red-400 hover:bg-red-950/20 transition-all uppercase tracking-widest">
                        <LayoutDashboard className="w-4 h-4 text-red-500" /> Dashboard
                    </Link>
                    <Link to="/reports" onClick={closeMobileMenu} className="flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs font-black text-slate-200 hover:text-red-400 hover:bg-red-950/20 transition-all uppercase tracking-widest">
                        <FileText className="w-4 h-4 text-red-500" /> Audit Reports
                    </Link>
                    {user && (
                        <>
                            {user.username === 'admin' && (
                                <Link to="/models" onClick={closeMobileMenu} className="flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs font-black text-slate-200 hover:text-red-400 hover:bg-red-950/20 transition-all uppercase tracking-widest">
                                    <Cpu className="w-4 h-4 text-red-500" /> ML Models
                                </Link>
                            )}
                            <Link to="/profile" onClick={closeMobileMenu} className="flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs font-black text-slate-200 hover:text-red-400 hover:bg-red-950/20 transition-all uppercase tracking-widest">
                                <User className="w-4 h-4 text-red-500" /> User Profile
                            </Link>
                        </>
                    )}
                    <Link to="/docs" onClick={closeMobileMenu} className="flex items-center gap-3 px-4 py-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs font-black text-slate-200 hover:text-red-400 hover:bg-red-950/20 transition-all uppercase tracking-widest">
                        <Shield className="w-4 h-4 text-red-500" /> Documentation
                    </Link>

                    {user ? (
                        <button 
                            onClick={() => { onLogout(); closeMobileMenu(); }} 
                            className="w-full flex items-center justify-center gap-2 mt-2 px-4 py-3 rounded-xl bg-red-950/40 border border-red-800/40 text-xs font-black text-red-400 hover:bg-red-600 hover:text-white transition-all uppercase tracking-widest"
                        >
                            <LogOut className="w-4 h-4" /> Logout ({user.username})
                        </button>
                    ) : (
                        <Link to="/login" onClick={closeMobileMenu} className="w-full flex items-center justify-center gap-2 mt-2 px-4 py-3 rounded-xl bg-red-600 text-white text-xs font-black hover:bg-white hover:text-red-900 transition-all uppercase tracking-widest shadow-lg shadow-red-600/20">
                            <LogIn className="w-4 h-4" /> SECURE LOGIN
                        </Link>
                    )}
                </div>
            )}
        </nav>
    );
};

export default Navbar;
