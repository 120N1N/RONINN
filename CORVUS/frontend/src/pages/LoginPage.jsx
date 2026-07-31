import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { EyeOff, Eye } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || "/api";

const LoginPage = ({ onLogin }) => {
    const [isReg, setIsReg] = useState(false);
    const [form, setForm] = useState({ username: '', password: '', email: '', first_name: '', last_name: '' });
    const [showPassword, setShowPassword] = useState(false);
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const handleSubmit = async (e) => {
        e.preventDefault();
        setError("");
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE}${isReg ? '/auth/register' : '/auth/login'}`, { 
                method: "POST", 
                headers: { "Content-Type": "application/json" }, 
                body: JSON.stringify(isReg ? form : { username: form.username, password: form.password }) 
            });
            const data = await res.json();
            if (res.ok) { 
                if (!isReg) { 
                    localStorage.setItem('corvus_token', data.access_token); 
                    onLogin(); 
                    navigate("/"); 
                } else { 
                    setIsReg(false); 
                    setError("");
                    alert("Registration successful! Please login.");
                } 
            } else {
                setError(data.detail || "Invalid username or password.");
            }
        } catch (err) {
            setError("Connection failed. Ensure the FastAPI backend is running.");
        } finally {
            setLoading(false);
        }
    };
    return (
        <div className="max-w-md mx-auto py-32 animate-in zoom-in duration-500">
            <div className="corvus-card p-12 rounded-[50px] shadow-2xl">
                <h2 className="text-3xl font-black text-white italic mb-10 uppercase tracking-tighter">{isReg ? 'New Identity' : 'SECURE ENTRY'}</h2>
                
                {error && (
                    <div className="bg-red-600/10 border border-red-600/20 p-4 rounded-2xl text-red-400 font-bold italic text-xs mb-6">
                        {error}
                    </div>
                )}
                
                <form onSubmit={handleSubmit} className="space-y-6">
                    {isReg && (
                        <div className="flex gap-4">
                            <input type="text" placeholder="FIRST NAME" className="w-1/2 bg-black/60 border border-slate-800 rounded-2xl p-4 text-xs font-bold text-white outline-none focus:border-red-600" onChange={(e) => setForm({ ...form, first_name: e.target.value })} required />
                            <input type="text" placeholder="LAST NAME" className="w-1/2 bg-black/60 border border-slate-800 rounded-2xl p-4 text-xs font-bold text-white outline-none focus:border-red-600" onChange={(e) => setForm({ ...form, last_name: e.target.value })} />
                        </div>
                    )}
                    {isReg && <input type="email" placeholder="EMAIL" className="w-full bg-black/60 border border-slate-800 rounded-2xl p-4 text-xs font-bold text-white outline-none focus:border-red-600" onChange={(e) => setForm({ ...form, email: e.target.value })} required />}
                    <input type="text" placeholder="USERNAME" className="w-full bg-black/60 border border-slate-800 rounded-2xl p-4 text-xs font-bold text-white outline-none focus:border-red-600" onChange={(e) => setForm({ ...form, username: e.target.value })} required />
                    <div className="relative">
                        <input 
                            type={showPassword ? "text" : "password"} 
                            placeholder="PASSWORD" 
                            className="w-full bg-black/60 border border-slate-800 rounded-2xl p-4 pr-12 text-xs font-bold text-white outline-none focus:border-red-600" 
                            onChange={(e) => setForm({ ...form, password: e.target.value })} 
                            required
                        />
                        <button 
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white transition-colors"
                        >
                            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                        </button>
                    </div>
                    <button 
                        type="submit" 
                        disabled={loading}
                        className="w-full bg-red-600 text-white font-black py-4 rounded-2xl hover:bg-white hover:text-red-900 transition-all uppercase text-[10px] tracking-widest disabled:opacity-50"
                    >
                        {loading ? "Authorizing..." : "Authorize"}
                    </button>
                </form>
                <button onClick={() => { setIsReg(!isReg); setError(""); }} className="w-full mt-6 text-[9px] font-black text-slate-600 uppercase tracking-widest hover:text-red-600">{isReg ? "LOGIN" : "REGISTER"}</button>
            </div>
        </div>
    );
};

export default LoginPage;
