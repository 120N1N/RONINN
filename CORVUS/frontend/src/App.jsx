import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';

// Pages
import Dashboard from './pages/Dashboard';
import ReportsPage from './pages/ReportsPage';
import ApiKeys from './pages/ApiKeys';
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

const API_BASE = import.meta.env.VITE_API_URL || "/api";

// --- CSS ANIMATIONS ---
const styles = `
.corvus-card {
  background: #1a1a1a;
  border: 1px solid rgba(198, 40, 40, 0.15);
  backdrop-filter: blur(10px);
}
.corvus-card:hover {
  border-color: rgba(198, 40, 40, 0.4);
}
`;

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
        <Router>
            <style>{styles}</style>
            <div className="min-h-screen text-slate-300 px-8 py-10 selection:bg-red-600 selection:text-white relative overflow-hidden">
                <DisclaimerPopup />
                <Navbar user={user} onLogout={() => { localStorage.removeItem('corvus_token'); setUser(null); }} />
                <main className="max-w-7xl mx-auto min-h-[70vh] relative">
                    <Routes>
                        <Route path="/" element={<Dashboard user={user} />} />
                        <Route path="/reports" element={<ReportsPage />} />
                        <Route path="/api-keys" element={<ApiKeys />} />
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
                <footer className="max-w-7xl mx-auto mt-32 pt-10 border-t border-red-900/10 flex justify-between items-center text-[9px] font-black uppercase tracking-widest text-slate-600">
                    <div>© 2024 CORVUSNOCT • STANDALONE SYSTEM</div>
                    <div className="flex gap-10">
                        <Link to="/privacy" className="hover:text-red-500 transition-colors">Privacy</Link>
                        <Link to="/terms" className="hover:text-red-500 transition-colors">Terms</Link>
                    </div>
                </footer>
            </div>
        </Router>
    );
}

export default App;
