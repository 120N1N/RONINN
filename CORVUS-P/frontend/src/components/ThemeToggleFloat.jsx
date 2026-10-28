import React from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export default function ThemeToggleFloat() {
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="fixed bottom-6 right-6 z-40 animate-in fade-in slide-in-from-bottom-4 duration-300">
      <button
        onClick={toggleTheme}
        className={`group flex items-center gap-2.5 px-4 py-2.5 rounded-full border shadow-2xl backdrop-blur-xl transition-all duration-300 hover:scale-105 active:scale-95 ${
          theme === 'dark'
            ? 'bg-black/85 border-red-900/60 text-slate-200 hover:border-yellow-400/80 shadow-[0_0_25px_rgba(220,38,38,0.25)]'
            : 'bg-white/95 border-slate-300 text-slate-800 hover:border-red-600 shadow-[0_10px_25px_rgba(0,0,0,0.15)]'
        }`}
        title={theme === 'dark' ? "Klik untuk ganti ke Light Mode" : "Klik untuk ganti ke Dark Mode"}
      >
        <div className={`p-1.5 rounded-full transition-transform group-hover:rotate-45 ${
          theme === 'dark' ? 'bg-yellow-400/20 text-yellow-400' : 'bg-indigo-600/10 text-indigo-600'
        }`}>
          {theme === 'dark' ? (
            <Sun className="w-4 h-4" />
          ) : (
            <Moon className="w-4 h-4" />
          )}
        </div>
        <div className="flex flex-col text-left">
          <span className="text-[10px] font-black uppercase tracking-wider">
            {theme === 'dark' ? 'Light Mode' : 'Dark Mode'}
          </span>
          <span className="text-[8px] font-bold opacity-60 uppercase tracking-widest">
            {theme === 'dark' ? 'Switch theme' : 'Switch theme'}
          </span>
        </div>
      </button>
    </div>
  );
}
