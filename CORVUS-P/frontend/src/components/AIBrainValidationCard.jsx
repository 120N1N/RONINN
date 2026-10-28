import React from 'react';
import { Brain, ShieldCheck, AlertTriangle, ArrowRight, Activity, Terminal } from 'lucide-react';

const AIBrainValidationCard = ({ finding }) => {
  const validation = finding?.ai_brain_validation || finding?.ai_validation;
  const caido = finding?.caido_profile;
  
  if (!validation && !finding?.ai_brain_status) return null;

  const isValid = validation?.is_valid ?? finding?.ai_brain_valid ?? true;
  const confidence = validation?.confidence_score ?? finding?.ai_brain_confidence ?? 0.85;
  const reasoning = validation?.reasoning || finding?.ai_brain_reasoning;
  const recommendation = validation?.recommendation;
  const adjustedSeverity = validation?.adjusted_severity;

  return (
    <div className="bg-white dark:bg-[#0c0808] border border-slate-200 dark:border-red-900/30 rounded-3xl p-6 sm:p-8 space-y-6 shadow-sm animate-in fade-in duration-300">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 border-b border-slate-200 dark:border-red-900/20 pb-5">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-2xl bg-red-500/10 border border-red-500/30 flex items-center justify-center text-red-500 shadow-md">
            <Brain className="w-5 h-5 text-red-500" />
          </div>
          <div>
            <h4 className="text-sm font-black text-slate-900 dark:text-white uppercase italic tracking-wider flex items-center gap-2">
              AI-Brain Security Verification
            </h4>
            <p className="text-[9px] text-slate-500 font-bold uppercase tracking-widest">
              Automated Triage & Validation Verdict
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {isValid ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-[10px] font-black uppercase tracking-wider bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/40">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> True Positive
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-xl text-[10px] font-black uppercase tracking-wider bg-red-50 dark:bg-red-950/50 text-red-700 dark:text-red-400 border border-red-200 dark:border-red-500/40">
              <AlertTriangle className="w-3.5 h-3.5 text-red-600 dark:text-red-400" /> False Positive
            </span>
          )}
          <span className="text-[10px] font-mono font-bold text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-900/50 px-2.5 py-1 rounded-xl">
            {(confidence * 100).toFixed(0)}% Conf
          </span>
        </div>
      </div>

      {adjustedSeverity && (
        <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-slate-50 dark:bg-black/40 border border-slate-200 dark:border-slate-900 text-xs font-bold">
          <span className="text-[9px] font-black uppercase tracking-wider text-slate-500">Tingkat Keparahan Disarankan:</span>
          <span className="text-orange-600 dark:text-orange-400 uppercase font-black">{finding.severity}</span>
          <ArrowRight className="w-3 h-3 text-slate-400 dark:text-slate-600" />
          <span className="text-red-600 dark:text-red-500 uppercase font-black">{adjustedSeverity}</span>
        </div>
      )}

      {caido && (
        <div className="p-4 rounded-2xl bg-cyan-50 dark:bg-cyan-950/10 border border-cyan-200 dark:border-cyan-800/30 space-y-3">
          <div className="flex items-center gap-2 text-cyan-800 dark:text-cyan-400 text-[10px] font-black uppercase tracking-wider">
            <Activity className="w-3.5 h-3.5" /> Konteks Traffic Runtime (Caido CLI Profiler)
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[10px] font-mono">
            <div className="bg-white dark:bg-black/40 p-2 rounded-xl border border-cyan-200 dark:border-cyan-950/40">
              <span className="text-slate-500 block text-[8px] uppercase font-sans">Method</span>
              <span className="text-slate-800 dark:text-white font-bold">{caido.request_verb || "GET"}</span>
            </div>
            <div className="bg-white dark:bg-black/40 p-2 rounded-xl border border-cyan-200 dark:border-cyan-950/40">
              <span className="text-slate-500 block text-[8px] uppercase font-sans">Param Count</span>
              <span className="text-slate-800 dark:text-white font-bold">{caido.param_count ?? 0}</span>
            </div>
            <div className="bg-white dark:bg-black/40 p-2 rounded-xl border border-cyan-200 dark:border-cyan-950/40">
              <span className="text-slate-500 block text-[8px] uppercase font-sans">Auth Headers</span>
              <span className="text-slate-800 dark:text-white font-bold">{caido.auth_headers_present ? "Ada" : "Nihil"}</span>
            </div>
            <div className="bg-white dark:bg-black/40 p-2 rounded-xl border border-cyan-200 dark:border-cyan-950/40">
              <span className="text-slate-500 block text-[8px] uppercase font-sans">Content-Type</span>
              <span className="text-slate-800 dark:text-white font-bold truncate block">{caido.content_type || "other"}</span>
            </div>
          </div>
        </div>
      )}

      {reasoning && (
        <div className="space-y-2">
          <h5 className="text-[10px] font-black uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Penalaran AI (Reasoning)
          </h5>
          <div className="text-xs text-slate-800 dark:text-slate-300 font-medium leading-relaxed italic bg-slate-50 dark:bg-black/40 p-4 rounded-2xl border border-slate-200 dark:border-slate-900 whitespace-pre-wrap">
            {reasoning}
          </div>
        </div>
      )}

      {recommendation && (
        <div className="space-y-2">
          <h5 className="text-[10px] font-black uppercase tracking-wider text-slate-500 dark:text-slate-400">
            Rekomendasi Remediasi Tambahan
          </h5>
          <div className="bg-slate-50 dark:bg-black/60 p-4 rounded-2xl border border-slate-200 dark:border-slate-900 font-mono text-xs text-slate-800 dark:text-slate-300 whitespace-pre-wrap">
            {recommendation}
          </div>
        </div>
      )}

      <div className="pt-2 text-[9px] text-amber-600 dark:text-amber-500/80 italic font-bold flex items-center gap-1.5">
        <span>⚠️</span> Hasil ini merupakan evaluasi otonom AI-Brain Security. Keputusan verifikasi akhir tetap berada pada analis manusia.
      </div>
    </div>
  );
};

export default AIBrainValidationCard;
