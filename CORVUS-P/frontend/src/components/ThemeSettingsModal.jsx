import React, { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, Sun, Moon, Type, Sparkles, Check } from 'lucide-react';
import { useTheme } from '../context/ThemeContext';

export default function ThemeSettingsModal({ isOpen, onClose }) {
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

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return createPortal(
    <div 
      className="fixed inset-0 z-[99999] flex items-center justify-center p-4 sm:p-6 bg-black/75 dark:bg-black/85 backdrop-blur-md overflow-y-auto"
      style={{
        position: 'fixed',
        inset: 0,
        width: '100%',
        height: '100%',
      }}
      onClick={onClose}
    >
      <div 
        style={{
          margin: 'auto',
          width: '100%',
          maxWidth: '32rem',
          maxHeight: 'min(90vh, 90dvh)',
        }}
        className="relative rounded-3xl p-6 sm:p-8 corvus-card shadow-[0_25px_70px_rgba(0,0,0,0.6)] border border-slate-200 dark:border-red-900/40 overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Background Ambient Glow */}
        <div className="absolute -top-24 -right-24 w-48 h-48 bg-red-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -left-24 w-48 h-48 bg-red-600/10 rounded-full blur-3xl pointer-events-none" />

        {/* Modal Header */}
        <div className="flex items-center justify-between pb-5 border-b border-red-900/20 mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-red-600/10 border border-red-600/30 text-red-500">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xl font-black italic tracking-tight uppercase" style={{ color: 'var(--text-primary)' }}>
                Interface <span className="text-red-600 underline">Settings</span>
              </h3>
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-500">
                Theme & Font Customization
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-slate-400 hover:text-red-500 hover:bg-red-500/10 transition-colors"
            title="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Setting Section 1: Appearance Mode */}
        <div className="space-y-6">
          <div>
            <label className="text-xs font-black uppercase tracking-wider block mb-3 text-red-600 dark:text-red-500">
              Theme Style
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setTheme('dark')}
                className={`flex items-center justify-between p-4 rounded-2xl border transition-all cursor-pointer ${
                  theme === 'dark'
                    ? 'border-red-600 bg-red-600/10 shadow-[0_0_20px_rgba(220,38,38,0.2)]'
                    : 'border-slate-200 dark:border-slate-800/80 bg-slate-50 dark:bg-slate-900/30 hover:border-slate-400'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-black/60 border border-red-900/40 text-red-400">
                    <Moon className="w-4 h-4" />
                  </div>
                  <div className="text-left">
                    <div className="text-xs font-black uppercase tracking-wider text-slate-900 dark:text-slate-200">Dark Mode</div>
                    <div className="text-[10px] text-slate-500">Obsidian Cyber</div>
                  </div>
                </div>
                {theme === 'dark' && <Check className="w-4 h-4 text-red-500" />}
              </button>

              <button
                type="button"
                onClick={() => setTheme('light')}
                className={`flex items-center justify-between p-4 rounded-2xl border transition-all cursor-pointer ${
                  theme === 'light'
                    ? 'border-red-600 bg-red-600/10 shadow-[0_0_20px_rgba(220,38,38,0.2)]'
                    : 'border-slate-200 dark:border-slate-800/80 bg-slate-50 dark:bg-slate-900/30 hover:border-slate-400'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="p-2 rounded-xl bg-yellow-500/10 border border-yellow-500/30 text-yellow-500">
                    <Sun className="w-4 h-4" />
                  </div>
                  <div className="text-left">
                    <div className="text-xs font-black uppercase tracking-wider text-slate-900 dark:text-slate-200">Light Mode</div>
                    <div className="text-[10px] text-slate-500">Clean Slate</div>
                  </div>
                </div>
                {theme === 'light' && <Check className="w-4 h-4 text-red-500" />}
              </button>
            </div>
          </div>

          {/* Setting Section 2: Font Family */}
          <div>
            <label className="text-xs font-black uppercase tracking-wider block mb-3 text-red-600 dark:text-red-500 flex items-center gap-2">
              <Type className="w-4 h-4" /> UI Font Family
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {FONT_OPTIONS.map((font) => (
                <button
                  key={font.id}
                  type="button"
                  onClick={() => setFontFamily(font.id)}
                  style={{ fontFamily: font.family }}
                  className={`flex items-center justify-between p-3.5 rounded-xl border text-left transition-all cursor-pointer ${
                    fontFamily === font.id
                      ? 'border-red-600 bg-red-600/10 shadow-[0_0_15px_rgba(220,38,38,0.15)] text-red-600 dark:text-red-400 font-bold'
                      : 'border-slate-200 dark:border-slate-800/60 bg-slate-50 dark:bg-black/20 hover:border-slate-400 text-slate-700 dark:text-slate-300'
                  }`}
                >
                  <span className="text-xs tracking-wide">{font.name}</span>
                  {fontFamily === font.id && <Check className="w-3.5 h-3.5 text-red-500 shrink-0" />}
                </button>
              ))}
            </div>
          </div>

          {/* Setting Section 3: Font Scale */}
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-xs font-black uppercase tracking-wider text-red-600 dark:text-red-500">
                Skala Tampilan UI (Scale / Density)
              </label>
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">
                Min 67% • Locked X
              </span>
            </div>
            <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
              {FONT_SIZE_OPTIONS.map((size) => (
                <button
                  key={size.id}
                  type="button"
                  onClick={() => setFontSize(size.id)}
                  className={`p-2.5 sm:p-3 rounded-xl border text-center transition-all cursor-pointer ${
                    fontSize === size.id
                      ? 'border-red-600 bg-red-600/10 text-red-600 dark:text-red-400 font-bold shadow-sm'
                      : 'border-slate-200 dark:border-slate-800/60 bg-slate-50 dark:bg-black/20 hover:border-slate-400 text-slate-700 dark:text-slate-400'
                  }`}
                >
                  <div className="text-xs font-black uppercase tracking-wider">{size.label}</div>
                  <div className="text-[9px] opacity-70 mt-0.5 truncate">{size.name.split(' ')[0]}</div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 pt-4 border-t border-slate-200 dark:border-red-900/20 flex justify-end">
          <button
            onClick={onClose}
            className="px-6 py-2.5 rounded-xl bg-red-600 text-white font-black text-xs uppercase tracking-widest hover:bg-white hover:text-red-900 transition-all shadow-lg shadow-red-600/20 cursor-pointer"
          >
            Apply & Close
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
