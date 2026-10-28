import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { User, LogOut, LogIn, Menu, X, Shield, Key, Cpu, FileText, LayoutDashboard, Settings } from 'lucide-react';
import logo from '../assets/logo.png';
import { useTheme } from '../context/ThemeContext';
import ThemeSettingsModal from './ThemeSettingsModal';

const Navbar = ({ user, onLogout }) => {
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
    const [isThemeModalOpen, setIsThemeModalOpen] = useState(false);
    const { theme, toggleTheme } = useTheme();

    const toggleMobileMenu = () => setIsMobileMenuOpen(!isMobileMenuOpen);
    const closeMobileMenu = () => setIsMobileMenuOpen(false);

    return (
        <>
        <nav className="mb-6 md:mb-10 border-b border-slate-200 dark:border-red-900/20 pb-4 md:pb-6 max-w-[1800px] w-full min-w-0 mx-auto relative z-30 transition-colors">
            <div className="flex items-center justify-between gap-2 sm:gap-4 w-full min-w-0">
                <div className="flex items-center gap-2 sm:gap-3 shrink-0">
                    <Link to="/" onClick={closeMobileMenu} className="flex items-center gap-2 sm:gap-3 group">
                        <div className="group-hover:scale-110 transition-transform">
                            <img src={logo} alt="Corvus Logo" className="w-9 h-9 sm:w-11 sm:h-11 object-cover rounded-2xl shadow-[0_0_20px_rgba(220,38,38,0.3)]" />
                        </div>
                        <div>
                            <h1 className="text-lg sm:text-xl font-black tracking-tight italic" style={{ color: 'var(--text-primary)' }}>CORVUS</h1>
                            <p className="nav-scalable-sub text-red-600 font-bold tracking-[0.2em] uppercase text-[8px] sm:text-[9px]">Automated Testing</p>
                        </div>
                    </Link>
                </div>

                {/* Desktop & Tablet Navigation */}
                <div className="hidden md:flex items-center gap-2 lg:gap-3.5 xl:gap-6 shrink-0">
                    <div className="flex gap-2 lg:gap-3.5 xl:gap-6 items-center text-[11px] lg:text-xs xl:text-sm">
                        <Link to="/" className="nav-scalable-text font-black text-slate-600 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-500 transition-colors uppercase tracking-widest">Dashboard</Link>
                        <Link to="/reports" className="nav-scalable-text font-black text-slate-600 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-500 transition-colors uppercase tracking-widest">Reports</Link>
                        <button
                            type="button"
                            onClick={toggleTheme}
                            className="nav-scalable-text font-black text-slate-600 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-500 transition-colors uppercase tracking-widest cursor-pointer bg-transparent border-0 p-0 focus:outline-none"
                            title={theme === 'dark' ? "Switch to Light Mode" : "Switch to Dark Mode"}
                        >
                            {theme === 'dark' ? 'LIGHT' : 'DARK'}
                        </button>

                        {user && (
                            <>
                                {user.username === 'admin' && (
                                    <Link to="/models" className="nav-scalable-text font-black text-slate-600 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-500 transition-colors uppercase tracking-widest">Models</Link>
                                )}
                            </>
                        )}
                        <Link to="/docs" className="nav-scalable-text font-black text-slate-600 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-500 transition-colors uppercase tracking-widest">Docs</Link>
                    </div>

                    {/* Interface & Theme Settings Modal Button */}
                    <div className="flex items-center pl-1.5 xl:pl-2 border-l border-slate-200 dark:border-red-900/20">
                        <button
                            type="button"
                            onClick={() => setIsThemeModalOpen(true)}
                            title="Interface Settings"
                            className="px-2.5 py-1.5 rounded-xl text-slate-600 dark:text-slate-400 hover:text-red-600 dark:hover:text-red-500 hover:bg-red-500/10 transition-all border border-slate-200 dark:border-slate-800/60 hover:border-red-600/40 flex items-center gap-1.5 cursor-pointer nav-scalable-button font-black uppercase tracking-widest text-[10px] xl:text-xs"
                        >
                            <Settings className="w-3.5 h-3.5" />
                            <span>SETTING</span>
                        </button>
                    </div>

                    {user ? (
                        <div className="flex items-center gap-1.5 lg:gap-3">
                            <Link to="/profile" className="flex items-center gap-1.5 bg-red-600/10 border border-red-900/30 px-2.5 lg:px-4 py-1.5 rounded-xl nav-scalable-button font-black text-red-500 uppercase tracking-widest italic hover:bg-red-600/20 transition-colors text-[10px] xl:text-xs">
                                {user.photo_url ? (
                                    <img src={user.photo_url} alt="Profile" className="w-4 h-4 rounded-full object-cover border border-red-500/50" />
                                ) : (
                                    <User className="w-3 h-3" />
                                )}
                                {user.first_name || user.username}
                            </Link>
                            <button onClick={onLogout} title="Logout" className="text-slate-500 hover:text-red-500 transition-colors p-1.5 cursor-pointer"><LogOut className="w-4 h-4" /></button>
                        </div>
                    ) : (
                        <Link to="/login" className="bg-red-600 text-white px-4 py-2 rounded-xl text-xs font-black hover:bg-white hover:text-red-900 transition-all uppercase tracking-widest flex items-center gap-2 shadow-lg shadow-red-600/20">
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

                    <button
                        onClick={() => { toggleTheme(); closeMobileMenu(); }}
                        className="text-left px-4 py-3 rounded-xl bg-slate-900/60 border border-slate-800 text-xs font-black text-slate-200 hover:text-red-400 hover:bg-red-950/20 transition-all uppercase tracking-widest cursor-pointer flex justify-between items-center"
                    >
                        <span>MODE: {theme === 'dark' ? 'LIGHT' : 'DARK'}</span>
                        <span className="text-[9px] text-slate-500 font-mono">TOGGLE</span>
                    </button>

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

                    <div className="pt-2 border-t border-red-900/20">
                        <button
                            onClick={() => { setIsThemeModalOpen(true); closeMobileMenu(); }}
                            className="w-full flex items-center justify-center gap-2 px-3 py-2.5 rounded-xl bg-slate-900/60 border border-slate-800 text-xs font-black text-slate-300 hover:text-red-400 uppercase tracking-widest"
                        >
                            <Settings className="w-4 h-4 text-red-500" />
                            <span>SETTING</span>
                        </button>
                    </div>

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
        <ThemeSettingsModal isOpen={isThemeModalOpen} onClose={() => setIsThemeModalOpen(false)} />
        </>
    );
};

export default Navbar;
