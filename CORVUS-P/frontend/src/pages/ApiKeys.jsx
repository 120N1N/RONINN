import React, { useState, useEffect } from 'react';
import { 
    Eye, EyeOff, Plus, MoreHorizontal, Search, Settings, 
    Info, Check, ChevronDown
} from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL || "/api";

const PROVIDERS_LIST = [
    "Anthropic", "Cohere", "DeepSeek", "Google", "Groq", "Ollama", "OpenAI", "OpenAI Compatible"
];

const PROVIDER_MODELS = {
    "OpenAI": [
        { name: "GPT-4o", tags: ["Explain", "Remediate"] },
        { name: "GPT-4.1", tags: ["Advanced reasoning"] },
        { name: "GPT-4.1 Mini", tags: ["Cheap analysis"] },
        { name: "o3", tags: ["Deep reasoning"] },
        { name: "o4-mini", tags: ["Fast TP/FP assist"] }
    ],
    "Anthropic": [
        { name: "Claude 3 Haiku", tags: ["Lightweight analysis"] },
        { name: "Claude 3 Sonnet", tags: ["Balanced reasoning"] },
        { name: "Claude 3 Opus", tags: ["Heavy contextual analysis"] },
        { name: "Claude 3.5 Sonnet", tags: ["TP/FP assist terbaik"] },
        { name: "Claude 4 Sonnet", tags: ["Advanced security reasoning"] },
        { name: "Claude 4 Opus", tags: ["Deep explain/remediation"] }
    ],
    "Google": [
        { name: "Gemini 3.5 Flash", tags: ["Stable", "Smart Agentic"] },
        { name: "Gemini 3.1 Pro", tags: ["Preview", "Complex Problem Solving"] },
        { name: "Gemini 3.1 Flash-Lite", tags: ["Stable", "Lightweight Edge"] },
        { name: "Gemini 2.5 Pro", tags: ["Stable", "Large Context"] },
        { name: "Gemini 2.5 Flash", tags: ["Stable", "Fast Responses"] }
    ],
    "Ollama": [
        { name: "Llama 3 8B", tags: ["Offline explain"] },
        { name: "Llama 3 70B", tags: ["Advanced offline reasoning"] },
        { name: "Mistral 7B", tags: ["Lightweight local mode"] },
        { name: "Mixtral", tags: ["Better local reasoning"] },
        { name: "Qwen2.5", tags: ["Multilingual local analysis"] },
        { name: "Gemma 2", tags: ["Efficient offline inference"] }
    ],
    "DeepSeek": [
        { name: "DeepSeek Chat", tags: ["General vulnerability analysis"] },
        { name: "DeepSeek R1", tags: ["Cheap TP/FP assist"] },
        { name: "DeepSeek Coder", tags: ["Payload & code analysis"] }
    ],
    "Groq": [
        { name: "llama3-8b-8192", tags: ["Super fast", "Free", "TP/FP Assist"] },
        { name: "llama3-70b-8192", tags: ["Super fast", "Free", "Deep Reasoning"] },
        { name: "mixtral-8x7b-32768", tags: ["Fast", "Free", "Large Context"] }
    ],
    "Cohere": [
        { name: "command-r", tags: ["Trial", "RAG & Security"] },
        { name: "command-r-plus", tags: ["Trial", "Advanced Reasoning"] }
    ],
    "River.ai": [
        { name: "Qwen/Qwen3.5-9B", tags: ["Default", "Fast Inference"] },
        { name: "Qwen/Qwen2.5-72B-Instruct", tags: ["High Accuracy", "Deep Reasoning"] },
        { name: "meta-llama/Llama-3.1-8B-Instruct", tags: ["Lightweight"] }
    ],
    "OpenAI Compatible": [
        { name: "Custom-LLM-1", tags: ["Local / Proxied endpoint"] },
        { name: "vLLM-Model", tags: ["High throughput"] },
        { name: "LM-Studio-Local", tags: ["Local inference"] }
    ]
};

export default function ApiKeys() {
    const [selectedProvider, setSelectedProvider] = useState("Ollama");
    
    // Form state
    const [name, setName] = useState("Ollama");
    const [currency, setCurrency] = useState("USD");
    const [isDefault, setIsDefault] = useState(false);
    const [endpoint, setEndpoint] = useState("");
    const [apiKey, setApiKey] = useState("");
    const [proxy, setProxy] = useState("");
    
    const [showKey, setShowKey] = useState(false);
    const [saving, setSaving] = useState(false);
    const [alertMessage, setAlertMessage] = useState(null);
    const [alertType, setAlertType] = useState("error");
    const [savedKeys, setSavedKeys] = useState({});
    const [savedModels, setSavedModels] = useState({});
    
    const [modelFilter, setModelFilter] = useState("");
    const [selectedModel, setSelectedModel] = useState("");
    const [customModels, setCustomModels] = useState(() => {
        const saved = localStorage.getItem('corvus_custom_models');
        return saved ? JSON.parse(saved) : {};
    });
    
    const fetchKeys = async () => {
        try {
            const token = localStorage.getItem('corvus_token');
            const res = await fetch(`${API_BASE}/llm/keys`, {
                headers: { "Authorization": `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                const keyMap = {};
                const modelMap = {};
                data.forEach(k => {
                    keyMap[k.provider.toLowerCase()] = k.masked_key;
                    modelMap[k.provider.toLowerCase()] = k.model;
                });
                setSavedKeys(keyMap);
                setSavedModels(modelMap);
                if (keyMap[selectedProvider.toLowerCase()]) {
                    setApiKey(keyMap[selectedProvider.toLowerCase()]);
                }
                if (modelMap[selectedProvider.toLowerCase()]) {
                    setSelectedModel(modelMap[selectedProvider.toLowerCase()]);
                }
            }
        } catch (e) {}
    };

    useEffect(() => {
        fetchKeys();
    }, []);

    // Handlers
    const handleProviderClick = (provider) => {
        setSelectedProvider(provider);
        setName(provider);
        setEndpoint("");
        setApiKey(savedKeys[provider.toLowerCase()] || "");
        setSelectedModel(savedModels[provider.toLowerCase()] || "");
        setModelFilter("");
    };

    const handleAddModel = () => {
        const newModel = window.prompt(`Enter new custom model name for ${selectedProvider}:`);
        if (!newModel) return;
        
        const updatedCustom = { ...customModels };
        if (!updatedCustom[selectedProvider]) {
            updatedCustom[selectedProvider] = [];
        }
        updatedCustom[selectedProvider].push({ name: newModel, tags: ["Custom"] });
        setCustomModels(updatedCustom);
        localStorage.setItem('corvus_custom_models', JSON.stringify(updatedCustom));
    };

    const handleSave = async (e) => {
        e.preventDefault();
        
        if (apiKey === savedKeys[selectedProvider.toLowerCase()] && selectedModel === savedModels[selectedProvider.toLowerCase()]) {
            setAlertType("error");
            setAlertMessage("No changes made. This API key and model are already saved and active.");
            return;
        }

        setSaving(true);
        setAlertMessage(null);
        try {
            const token = localStorage.getItem('corvus_token');
            const res = await fetch(`${API_BASE}/llm/keys`, {
                method: "POST",
                headers: { 
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    provider: selectedProvider.toLowerCase(),
                    name: name,
                    api_key: apiKey || "empty-key",
                    model: selectedModel || null
                })
            });
            if (res.ok) {
                setAlertType("success");
                setAlertMessage("Configuration saved & connected successfully!");
                fetchKeys();
            } else {
                const data = await res.json();
                setAlertType("error");
                setAlertMessage(`Error saving configuration: ${data.detail || JSON.stringify(data, null, 2)}`);
            }
        } catch (e) {
            setAlertType("error");
            setAlertMessage(`Server connection failed: ${e.message}`);
        } finally {
            setSaving(false);
        }
    };

    // Combine default and custom models
    const currentModels = [
        ...(PROVIDER_MODELS[selectedProvider] || [{ name: "default-model", tags: [] }]),
        ...(customModels[selectedProvider] || [])
    ];

    const filteredModels = currentModels.filter(m => 
        m.name.toLowerCase().includes(modelFilter.toLowerCase()) || 
        m.tags.some(t => t.toLowerCase().includes(modelFilter.toLowerCase()))
    );

    return (
        <div className="flex flex-col h-[85vh] bg-[#1c1c1e] rounded-xl border border-slate-800/50 shadow-2xl overflow-hidden mt-8 max-w-6xl mx-auto font-sans text-sm animate-in fade-in duration-500">
            {/* Header */}
            <div className="flex justify-between items-center px-6 py-4 border-b border-slate-800">
                <h2 className="text-xl font-medium text-slate-200">Providers</h2>
                <button className="text-slate-400 hover:text-slate-200 transition-colors">
                    <MoreHorizontal className="w-5 h-5" />
                </button>
            </div>

            {/* Main Content Area */}
            <div className="flex flex-1 overflow-hidden">
                {/* Left Sidebar - Providers List */}
                <div className="w-64 border-r border-slate-800 flex flex-col bg-[#1c1c1e]">
                    <div className="flex-1 overflow-y-auto py-2">
                        {PROVIDERS_LIST.map((prov) => (
                            <button
                                key={prov}
                                onClick={() => handleProviderClick(prov)}
                                className={`w-full text-left px-6 py-2.5 flex items-center transition-colors ${
                                    selectedProvider === prov 
                                        ? 'bg-[#2c2c2e] text-slate-200 font-medium' 
                                        : 'text-slate-400 hover:bg-[#2c2c2e]/50'
                                }`}
                            >
                                {prov}
                            </button>
                        ))}
                    </div>
                    {/* Add OpenAI Compatible Button */}
                    <div className="p-4 border-t border-slate-800">
                        <button className="flex items-center gap-2 text-slate-400 hover:text-slate-200 transition-colors w-full px-2 py-1.5 rounded-lg hover:bg-[#2c2c2e]/50">
                            <Plus className="w-4 h-4" />
                            <span>OpenAI Compatible</span>
                        </button>
                    </div>
                </div>

                {/* Right Panel - Settings Form */}
                <div className="flex-1 bg-[#151515] overflow-y-auto relative">
                    <div className="p-8 max-w-3xl">
                        
                        {alertMessage && (
                            <div className={`mb-6 p-4 rounded border flex items-start justify-between ${alertType === 'error' ? 'bg-red-500/10 border-red-500/50 text-red-400' : 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400'}`}>
                                <div className="flex-1 font-mono text-sm whitespace-pre-wrap select-all">
                                    {alertMessage}
                                </div>
                                <button onClick={() => setAlertMessage(null)} className="ml-4 text-slate-400 hover:text-white shrink-0 font-bold">
                                    ✕
                                </button>
                            </div>
                        )}

                        <form onSubmit={handleSave} className="space-y-6">
                            
                            {/* Name, Currency, Default Row */}
                            <div className="flex items-center gap-6">
                                <div className="flex-1 flex items-center gap-4">
                                    <label className="w-20 text-slate-400 flex items-center gap-1">
                                        Name <Info className="w-3.5 h-3.5 text-slate-500" />
                                    </label>
                                    <input 
                                        type="text" 
                                        value={name}
                                        onChange={(e) => setName(e.target.value)}
                                        className="flex-1 bg-[#1c1c1e] border border-slate-800 rounded px-3 py-1.5 text-slate-200 focus:outline-none focus:border-slate-600"
                                    />
                                </div>
                                <div className="flex items-center gap-4">
                                    <label className="text-slate-400">Currency</label>
                                    <div className="relative">
                                        <select 
                                            value={currency}
                                            onChange={(e) => setCurrency(e.target.value)}
                                            className="appearance-none bg-[#1c1c1e] border border-slate-800 rounded px-3 py-1.5 pr-8 text-slate-200 focus:outline-none focus:border-slate-600"
                                        >
                                            <option value="USD">USD</option>
                                            <option value="IDR">IDR</option>
                                            <option value="EUR">EUR</option>
                                        </select>
                                        <ChevronDown className="w-4 h-4 text-slate-500 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none" />
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <label className="text-slate-400">Default</label>
                                    {/* Toggle Switch */}
                                    <button 
                                        type="button"
                                        onClick={() => setIsDefault(!isDefault)}
                                        className={`w-10 h-5 rounded-full relative transition-colors ${isDefault ? 'bg-blue-500' : 'bg-slate-700'}`}
                                    >
                                        <span className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all ${isDefault ? 'left-[22px]' : 'left-0.5'}`} />
                                    </button>
                                </div>
                            </div>

                            {/* Endpoint Row */}
                            <div className="flex items-center gap-4">
                                <label className="w-20 text-slate-400">Endpoint</label>
                                <input 
                                    type="text" 
                                    value={endpoint}
                                    placeholder="http://127.0.0.1:8000"
                                    onChange={(e) => setEndpoint(e.target.value)}
                                    autoComplete="off"
                                    data-lpignore="true"
                                    data-form-type="other"
                                    className="flex-1 bg-[#1c1c1e] border border-slate-800 rounded px-3 py-1.5 text-slate-200 focus:outline-none focus:border-slate-600 placeholder:text-slate-600"
                                />
                            </div>

                            {/* API Key Row */}
                            <div className="flex items-center gap-4">
                                <label className="w-20 text-slate-400">API Key</label>
                                <div className="flex-1 relative">
                                    <input 
                                        type={showKey ? "text" : "password"} 
                                        value={apiKey}
                                        onChange={(e) => setApiKey(e.target.value)}
                                        autoComplete="new-password"
                                        data-lpignore="true"
                                        data-form-type="other"
                                        placeholder={savedKeys[selectedProvider.toLowerCase()] ? `Saved: ${savedKeys[selectedProvider.toLowerCase()]}` : "Most providers require an API key - don't forget to set yours here"}
                                        className="w-full bg-[#1c1c1e] border border-slate-800 rounded px-3 py-1.5 pr-10 text-slate-200 focus:outline-none focus:border-slate-600 placeholder:text-slate-600"
                                    />
                                    <button 
                                        type="button"
                                        onClick={() => setShowKey(!showKey)}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-300 transition-colors"
                                    >
                                        {showKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                                    </button>
                                </div>
                            </div>

                            {/* Proxy Row */}
                            <div className="flex items-center gap-4">
                                <label className="w-20 text-slate-400">Proxy</label>
                                <input 
                                    type="text" 
                                    value={proxy}
                                    onChange={(e) => setProxy(e.target.value)}
                                    placeholder="routes traffic via this server (leave blank if unsure)"
                                    className="flex-1 bg-[#1c1c1e] border border-slate-800 rounded px-3 py-1.5 text-slate-200 focus:outline-none focus:border-slate-600 placeholder:text-slate-600"
                                />
                            </div>
                            {/* Form Actions */}
                            <div className="flex justify-end pt-4">
                                <button 
                                    type="submit" 
                                    disabled={saving}
                                    className="bg-red-600 hover:bg-white hover:text-red-900 text-white font-black py-2.5 px-6 rounded-xl transition-all shadow-lg shadow-red-600/20 active:scale-95 disabled:grayscale uppercase tracking-widest text-[10px] flex items-center gap-2"
                                >
                                    {saving && <span className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />}
                                    Save Configuration
                                </button>
                            </div>
                        </form>

                        <div className="mt-12 pt-8 border-t border-slate-800/50">
                            {/* Models Filter & Add */}
                            <div className="flex items-center justify-between mb-6">
                                <div className="relative flex-1 max-w-sm">
                                    <input 
                                        type="text" 
                                        placeholder="Filter models" 
                                        value={modelFilter}
                                        onChange={(e) => setModelFilter(e.target.value)}
                                        className="w-full bg-transparent border-b border-slate-800 py-1.5 text-slate-300 focus:outline-none focus:border-slate-500 placeholder:text-slate-600 text-sm"
                                    />
                                </div>
                                <button 
                                    onClick={handleAddModel}
                                    type="button"
                                    className="flex items-center gap-1.5 text-slate-400 hover:text-slate-200 transition-colors px-3 py-1 rounded hover:bg-[#2c2c2e]/50 text-sm"
                                >
                                    <Plus className="w-4 h-4" />
                                    <span>Model</span>
                                </button>
                            </div>

                            {/* Models List */}
                            <div className="space-y-1">
                                {filteredModels.map((model, idx) => (
                                    <div 
                                        key={idx} 
                                        onClick={() => setSelectedModel(model.name)}
                                        className={`flex items-center justify-between py-3 group px-3 rounded -mx-3 transition-colors cursor-pointer ${selectedModel === model.name ? 'bg-red-900/20 border border-red-900/50' : 'hover:bg-[#1c1c1e]/50 border border-transparent'}`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`w-2 h-2 rounded-full border transition-colors ${selectedModel === model.name ? 'bg-red-500 border-red-400 shadow-[0_0_8px_#ef4444]' : 'border-slate-600 group-hover:border-slate-400'}`} />
                                            <span className={`font-medium ${selectedModel === model.name ? 'text-red-400' : 'text-slate-200'}`}>{model.name}</span>
                                            <Info className="w-4 h-4 text-slate-500 hover:text-slate-300 transition-colors" title="Select this model to save as active for this provider" />
                                        </div>
                                        <div className="flex gap-2">
                                            {model.tags.map(tag => (
                                                <span key={tag} className="flex items-center gap-1 px-2.5 py-0.5 rounded-md bg-[#2c2c2e] border border-slate-800 text-[11px] text-slate-400">
                                                    {tag === 'Custom' ? (
                                                        <div className="w-1.5 h-1.5 rounded-full bg-green-500" />
                                                    ) : tag === 'Tools' ? (
                                                        <div className="w-1.5 h-1.5 rounded-full bg-blue-500" />
                                                    ) : (
                                                        <div className="w-3 h-3 rounded-sm border border-slate-500" />
                                                    )}
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                                {filteredModels.length === 0 && (
                                    <div className="text-slate-500 text-center py-4 italic text-xs">No models match your filter.</div>
                                )}
                            </div>
                        </div>

                    </div>
                </div>
            </div>
            
            {/* Global save button overlay (optional, but requested layout typically autosaves or has save button) */}
            {saving && (
                <div className="absolute inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="text-white bg-[#1c1c1e] px-6 py-3 rounded shadow-lg border border-slate-800">Saving...</div>
                </div>
            )}
        </div>
    );
}
