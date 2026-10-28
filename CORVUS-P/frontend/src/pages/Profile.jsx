import React, { useState, useEffect, useRef } from 'react';
import { User, Mail, Shield, Camera, Key, Check, Loader2, Upload, Type, Sun, Moon, Sliders } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '../context/ThemeContext';

const API_BASE = import.meta.env.VITE_API_URL || "/api";

export default function Profile({ user, fetchMe }) {
    const navigate = useNavigate();
    const { 
        theme, 
        setTheme, 
        fontFamily, 
        setFontFamily, 
        fontSize, 
        setFontSize, 
        FONT_OPTIONS, 
        FONT_SIZE_OPTIONS 
    } = useTheme();
    const fileInputRef = useRef(null);
    const [loading, setLoading] = useState(false);
    const [photoLoading, setPhotoLoading] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    
    const [form, setForm] = useState({
        username: "",
        first_name: "",
        last_name: "",
        password: ""
    });

    useEffect(() => {
        if (!user) {
            navigate("/login");
            return;
        }
        setForm({
            username: user.username || "",
            first_name: user.first_name || "",
            last_name: user.last_name || "",
            password: ""
        });
    }, [user, navigate]);

    const handlePhotoUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setPhotoLoading(true);
        setError("");
        
        const formData = new FormData();
        formData.append("file", file);

        try {
            const token = localStorage.getItem('corvus_token');
            const res = await fetch(`${API_BASE}/auth/photo`, {
                method: "POST",
                headers: { "Authorization": `Bearer ${token}` },
                body: formData
            });
            const data = await res.json();
            
            if (res.ok) {
                // Refresh global user state to show new photo
                await fetchMe(token);
                setSuccess("Profile photo updated successfully!");
                setTimeout(() => setSuccess(""), 3000);
            } else {
                setError(data.detail || "Failed to upload photo.");
            }
        } catch (err) {
            setError("Server connection failed.");
        } finally {
            setPhotoLoading(false);
        }
    };

    const handleProfileUpdate = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        setSuccess("");
        
        const updateData = {
            username: form.username,
            first_name: form.first_name || null,
            last_name: form.last_name || null,
        };
        
        if (form.password) {
            updateData.password = form.password;
        }

        try {
            const token = localStorage.getItem('corvus_token');
            const res = await fetch(`${API_BASE}/auth/profile`, {
                method: "PUT",
                headers: { 
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}` 
                },
                body: JSON.stringify(updateData)
            });
            const data = await res.json();
            
            if (res.ok) {
                // Update token in case username changed
                localStorage.setItem('corvus_token', data.access_token);
                // Refresh global user state
                await fetchMe(data.access_token);
                setSuccess("Profile updated successfully!");
                setForm({ ...form, password: "" }); // clear password field
                setTimeout(() => setSuccess(""), 3000);
            } else {
                setError(data.detail || "Failed to update profile.");
            }
        } catch (err) {
            setError("Server connection failed.");
        } finally {
            setLoading(false);
        }
    };

    if (!user) return null;

    return (
        <div className="max-w-4xl mx-auto py-12 animate-in fade-in slide-in-from-bottom-8 duration-700">
            <h2 className="text-3xl font-black text-white italic mb-8 uppercase tracking-tighter flex items-center gap-4">
                <Shield className="w-8 h-8 text-red-500" /> IDENTITY HUB
            </h2>
            
            {error && (
                <div className="bg-red-600/10 border border-red-600/20 p-4 rounded-2xl text-red-400 font-bold italic text-xs mb-8">
                    {error}
                </div>
            )}
            
            {success && (
                <div className="bg-green-600/10 border border-green-600/20 p-4 rounded-2xl text-green-400 font-bold italic text-xs mb-8 flex items-center gap-2">
                    <Check className="w-4 h-4" /> {success}
                </div>
            )}

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                {/* Left Column - Avatar */}
                <div className="md:col-span-1">
                    <div className="bg-[#1c1c1e] border border-slate-800/50 rounded-3xl p-8 flex flex-col items-center text-center shadow-xl">
                        <div className="relative group mb-6">
                            <div className="w-40 h-40 rounded-full border-4 border-red-900/30 overflow-hidden bg-black/50 flex items-center justify-center">
                                {photoLoading ? (
                                    <Loader2 className="w-8 h-8 text-red-500 animate-spin" />
                                ) : user.photo_url ? (
                                    <img src={user.photo_url} alt="Profile" className="w-full h-full object-cover" />
                                ) : (
                                    <User className="w-16 h-16 text-slate-600" />
                                )}
                            </div>
                            
                            {/* Upload Overlay */}
                            <label className="absolute inset-0 bg-black/60 rounded-full flex flex-col items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity cursor-pointer backdrop-blur-sm">
                                <Camera className="w-8 h-8 text-white mb-2" />
                                <span className="text-[10px] font-black text-white uppercase tracking-widest">Change</span>
                                <input 
                                    type="file" 
                                    className="hidden" 
                                    accept="image/*"
                                    onChange={handlePhotoUpload}
                                    disabled={photoLoading}
                                />
                            </label>
                        </div>
                        
                        <h3 className="text-xl font-black text-white uppercase tracking-tight">{user.first_name || user.username}</h3>
                        <p className="text-red-500 text-[10px] font-bold tracking-widest uppercase mt-1 flex items-center justify-center gap-1">
                            <Shield className="w-3 h-3" /> {user.username === 'admin' ? 'Administrator' : 'Operative'}
                        </p>
                        
                        <div className="w-full h-px bg-slate-800/50 my-6" />
                        
                        <div className="flex items-center gap-3 text-slate-400 text-xs font-medium w-full">
                            <Mail className="w-4 h-4 text-slate-500" />
                            <span className="truncate">{user.email}</span>
                        </div>
                    </div>
                </div>

                {/* Right Column - Form */}
                <div className="md:col-span-2">
                    <div className="bg-[#1c1c1e] border border-slate-800/50 rounded-3xl p-8 shadow-xl">
                        <h3 className="text-lg font-black text-white italic mb-6 uppercase tracking-widest border-b border-slate-800 pb-4">Personal Data</h3>
                        
                        <form onSubmit={handleProfileUpdate} className="space-y-6">
                            <div className="grid grid-cols-2 gap-6">
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">First Name</label>
                                    <input 
                                        type="text" 
                                        value={form.first_name}
                                        onChange={(e) => setForm({ ...form, first_name: e.target.value })}
                                        className="w-full bg-black/40 border border-slate-800 rounded-xl p-3 text-sm text-white outline-none focus:border-red-600 transition-colors"
                                    />
                                </div>
                                <div className="space-y-2">
                                    <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Last Name</label>
                                    <input 
                                        type="text" 
                                        value={form.last_name}
                                        onChange={(e) => setForm({ ...form, last_name: e.target.value })}
                                        className="w-full bg-black/40 border border-slate-800 rounded-xl p-3 text-sm text-white outline-none focus:border-red-600 transition-colors"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Username</label>
                                <input 
                                    type="text" 
                                    value={form.username}
                                    onChange={(e) => setForm({ ...form, username: e.target.value })}
                                    required
                                    className="w-full bg-black/40 border border-slate-800 rounded-xl p-3 text-sm text-white outline-none focus:border-red-600 transition-colors"
                                />
                            </div>

                            <div className="w-full h-px bg-slate-800/50 my-8" />
                            
                            <h3 className="text-lg font-black text-white italic mb-6 uppercase tracking-widest flex items-center gap-2">
                                <Key className="w-5 h-5 text-red-500" /> Security
                            </h3>

                            <div className="space-y-2">
                                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">New Password</label>
                                <input 
                                    type="password" 
                                    placeholder="Leave blank to keep current password"
                                    value={form.password}
                                    onChange={(e) => setForm({ ...form, password: e.target.value })}
                                    className="w-full bg-black/40 border border-slate-800 rounded-xl p-3 text-sm text-white outline-none focus:border-red-600 transition-colors placeholder:text-slate-700"
                                    autoComplete="new-password"
                                />
                            </div>

                            <div className="pt-6">
                                <button 
                                    type="submit" 
                                    disabled={loading}
                                    className="bg-red-600 text-white font-black py-3 px-8 rounded-xl hover:bg-white hover:text-red-900 transition-all uppercase tracking-widest text-[10px] shadow-lg shadow-red-600/20 disabled:opacity-50 flex items-center justify-center gap-2"
                                >
                                    {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Upload className="w-4 h-4" />}
                                    {loading ? "Updating..." : "Update Profile"}
                                </button>
                            </div>
                        </form>
                    </div>

                    {/* Interface & Typography Settings Card */}
                    <div className="corvus-card rounded-3xl p-8 shadow-xl mt-8">
                        <div className="flex items-center justify-between border-b border-red-900/20 pb-4 mb-6">
                            <h3 className="text-lg font-black italic uppercase tracking-widest flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
                                <Sliders className="w-5 h-5 text-red-500" /> Interface & Typography Settings
                            </h3>
                            <span className="text-[9px] font-bold uppercase tracking-widest text-slate-500">Live Applied</span>
                        </div>

                        {/* Theme Style */}
                        <div className="mb-6">
                            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block mb-3">Theme Style</label>
                            <div className="grid grid-cols-2 gap-4">
                                <button
                                    type="button"
                                    onClick={() => setTheme('dark')}
                                    className={`flex items-center justify-between p-4 rounded-2xl border transition-all ${
                                        theme === 'dark'
                                            ? 'border-red-600 bg-red-600/10 shadow-[0_0_15px_rgba(220,38,38,0.2)]'
                                            : 'border-slate-800/80 bg-black/20 hover:border-slate-700'
                                    }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 rounded-xl bg-black/60 border border-red-900/40 text-red-400">
                                            <Moon className="w-4 h-4" />
                                        </div>
                                        <div className="text-left">
                                            <div className="text-xs font-black uppercase tracking-wider text-slate-200">Dark Mode</div>
                                            <div className="text-[9px] text-slate-500">Obsidian Cyber</div>
                                        </div>
                                    </div>
                                    {theme === 'dark' && <Check className="w-4 h-4 text-red-500" />}
                                </button>

                                <button
                                    type="button"
                                    onClick={() => setTheme('light')}
                                    className={`flex items-center justify-between p-4 rounded-2xl border transition-all ${
                                        theme === 'light'
                                            ? 'border-red-600 bg-red-600/10 shadow-[0_0_15px_rgba(220,38,38,0.2)]'
                                            : 'border-slate-800/80 bg-black/20 hover:border-slate-700'
                                    }`}
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 rounded-xl bg-yellow-500/10 border border-yellow-500/30 text-yellow-500">
                                            <Sun className="w-4 h-4" />
                                        </div>
                                        <div className="text-left">
                                            <div className="text-xs font-black uppercase tracking-wider text-slate-200">Light Mode</div>
                                            <div className="text-[9px] text-slate-500">Clean Slate</div>
                                        </div>
                                    </div>
                                    {theme === 'light' && <Check className="w-4 h-4 text-red-500" />}
                                </button>
                            </div>
                        </div>

                        {/* Font Family */}
                        <div className="mb-6">
                            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block mb-3 flex items-center gap-1.5">
                                <Type className="w-3.5 h-3.5 text-red-500" /> UI Font Family
                            </label>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                {FONT_OPTIONS.map((f) => (
                                    <button
                                        key={f.id}
                                        type="button"
                                        onClick={() => setFontFamily(f.id)}
                                        style={{ fontFamily: f.family }}
                                        className={`flex items-center justify-between p-3.5 rounded-xl border text-left transition-all ${
                                            fontFamily === f.id
                                                ? 'border-red-600 bg-red-600/10 text-red-400 font-bold'
                                                : 'border-slate-800/60 bg-black/20 hover:border-slate-700 text-slate-300'
                                        }`}
                                    >
                                        <span className="text-xs">{f.name}</span>
                                        {fontFamily === f.id && <Check className="w-3.5 h-3.5 text-red-500" />}
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Font Size */}
                        <div>
                            <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest block mb-3">UI Font Density / Scale</label>
                            <div className="grid grid-cols-3 gap-3">
                                {FONT_SIZE_OPTIONS.map((s) => (
                                    <button
                                        key={s.id}
                                        type="button"
                                        onClick={() => setFontSize(s.id)}
                                        className={`p-3 rounded-xl border text-center transition-all ${
                                            fontSize === s.id
                                                ? 'border-red-600 bg-red-600/10 text-red-400 font-bold'
                                                : 'border-slate-800/60 bg-black/20 hover:border-slate-700 text-slate-400'
                                        }`}
                                    >
                                        <div className="text-xs font-black uppercase tracking-wider">{s.name}</div>
                                        <div className="text-[10px] opacity-60 mt-0.5">{s.label}</div>
                                    </button>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
