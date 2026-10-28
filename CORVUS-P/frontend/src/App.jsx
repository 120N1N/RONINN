import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

// Pages
import Dashboard from './pages/Dashboard';
import ReportsPage from './pages/ReportsPage';

import Models from './pages/Models';
import Profile from './pages/Profile';
import DocsPage from './pages/DocsPage';
import PrivacyPage from './pages/PrivacyPage';
import TermsPage from './pages/TermsPage';
import LoginPage from './pages/LoginPage';
import NotFoundPage from './pages/NotFoundPage';

// Components
import Navbar from './components/Navbar';
import DisclaimerPopup from './components/DisclaimerPopup';
import { ThemeProvider } from './context/ThemeContext';

const API_BASE = import.meta.env.VITE_API_URL || "/api";

function App() {
    const [user, setUser] = useState(null);

    const fetchMe = async (token) => {
        try {
            const res = await fetch(`${API_BASE}/auth/me`, { 
                headers: { "Authorization": `Bearer ${token}` } 
            });
            if (res.ok) { 
                setUser(await res.json()); 
            } else { 
                localStorage.removeItem('corvus_token'); 
                setUser(null);
            }
        } catch (err) {
            console.error("Failed to fetch user:", err);
            localStorage.removeItem('corvus_token');
            setUser(null);
        }
    };

    useEffect(() => { 
        const token = localStorage.getItem('corvus_token'); 
        if (token) fetchMe(token); 
    }, []);

    return (
        <ThemeProvider>
            <Router>
                <div className="min-h-screen text-[var(--text-primary)] px-3 sm:px-5 md:px-8 py-4 sm:py-6 md:py-8 selection:bg-red-600 selection:text-white relative w-full max-w-full overflow-x-hidden transition-colors duration-300">
                    <DisclaimerPopup />
                <Navbar user={user} onLogout={() => { 
                    localStorage.removeItem('corvus_token'); 
                    localStorage.removeItem('corvus_active_scan_id'); 
                    setUser(null); 
                }} />
                <main className="max-w-[1800px] 2xl:max-w-[2000px] w-full min-w-0 mx-auto min-h-[70vh] relative">
                    <Routes>
                        <Route path="/" element={<Dashboard user={user} />} />
                        <Route path="/reports" element={<ReportsPage />} />

                        <Route path="/models" element={<Models />} />
                        <Route path="/profile" element={<Profile user={user} fetchMe={fetchMe} />} />
                        <Route path="/docs" element={<DocsPage />} />
                        <Route path="/privacy" element={<PrivacyPage />} />
                        <Route path="/terms" element={<TermsPage />} />
                        <Route path="/login" element={<LoginPage onLogin={() => {
                            const token = localStorage.getItem('corvus_token');
                            if (token) fetchMe(token);
                        }} />} />
                        <Route path="*" element={<NotFoundPage />} />
                    </Routes>
                </main>
                <footer className="max-w-[1800px] 2xl:max-w-[2000px] mx-auto mt-16 md:mt-32 pt-8 md:pt-10 border-t border-red-900/10 flex flex-col sm:flex-row justify-between items-center gap-4 text-[9px] font-black uppercase tracking-widest text-slate-600">
                    <div>@CORVUSNOCT</div>
                    <div className="flex gap-6 sm:gap-10">
                        <Link to="/privacy" className="hover:text-red-500 transition-colors">Privacy</Link>
                        <Link to="/terms" className="hover:text-red-500 transition-colors">Terms</Link>
                    </div>
                </footer>
            </div>
        </Router>
    </ThemeProvider>
    );
}

export default App;
