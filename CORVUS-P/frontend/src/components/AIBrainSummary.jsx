import React from 'react';
import { Brain, CheckCircle2, AlertTriangle, ShieldCheck, Activity } from 'lucide-react';
import { isFindingTruePositive, getFindingConfidenceScore } from '../utils/findingHelper';

const AIBrainSummary = ({ findings = [], activeFilter = 'all', onSelectFilter }) => {
  const validatedFindings = findings.filter(f => f.ai_brain_validation || f.ai_validation || f.rf_validation);
  const validatedCount = validatedFindings.length;
  
  const tpCount = findings.filter(isFindingTruePositive).length;
  const fpCount = findings.filter(f => !isFindingTruePositive(f)).length;
  
  const avgConfidence = findings.length > 0
    ? findings.reduce((sum, f) => sum + (getFindingConfidenceScore(f) / 100), 0) / findings.length
    : 0;

  return (
    <div className="corvus-card p-6 sm:p-8 rounded-3xl md:rounded-[40px] shadow-2xl relative overflow-hidden group border border-slate-200 dark:border-red-900/30">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-red-600/10 border border-red-500/30 flex items-center justify-center text-red-500 shadow-lg shadow-red-950/30">
            <Brain className="w-5 h-5 text-red-500 animate-pulse" />
          </div>
          <div>
            <h3 className="text-lg sm:text-xl font-black italic tracking-tight flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              AI-BRAIN SECURITY ANALYST
            </h3>
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">
              Autonomous verification & False Positive elimination engine
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-[10px] font-bold text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-black/60 px-3 py-1.5 rounded-xl border border-slate-200 dark:border-red-900/30">
          <Activity className="w-3.5 h-3.5 text-red-500" />
          <span>Dual-LLM Engine Standby</span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div 
          onClick={() => onSelectFilter && onSelectFilter('all')}
          className={`p-4 rounded-2xl border transition-all cursor-pointer ${
            activeFilter === 'all' 
              ? 'bg-slate-100 dark:bg-slate-900/80 border-slate-400 dark:border-slate-600 shadow-lg' 
              : 'bg-slate-50/80 dark:bg-black/40 border-slate-200 dark:border-slate-900 hover:border-slate-300 dark:hover:border-slate-800'
          }`}
        >
          <div className="flex items-center justify-between text-slate-600 dark:text-slate-400 mb-1">
            <span className="text-[9px] font-black uppercase tracking-widest">Total Temuan</span>
          </div>
          <div className="text-2xl font-black tracking-tight" style={{ color: 'var(--text-primary)' }}>{findings.length}</div>
          <div className="text-[8px] text-slate-500 font-bold mt-1">
            {validatedCount} telah diverifikasi AI
          </div>
        </div>

        <div 
          onClick={() => onSelectFilter && onSelectFilter('tp')}
          className={`p-4 rounded-2xl border transition-all cursor-pointer ${
            activeFilter === 'tp' 
              ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-500 shadow-lg' 
              : 'bg-slate-50/80 dark:bg-black/40 border-slate-200 dark:border-slate-900 hover:border-emerald-500/50'
          }`}
        >
          <div className="flex items-center justify-between text-emerald-600 dark:text-emerald-400 mb-1">
            <span className="text-[9px] font-black uppercase tracking-widest flex items-center gap-1">
              <ShieldCheck className="w-3 h-3" /> True Positive
            </span>
          </div>
          <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400 tracking-tight">{tpCount}</div>
          <div className="text-[8px] text-emerald-600/80 dark:text-emerald-500/70 font-bold mt-1">
            Terverifikasi rentan nyata
          </div>
        </div>

        <div 
          onClick={() => onSelectFilter && onSelectFilter('fp')}
          className={`p-4 rounded-2xl border transition-all cursor-pointer ${
            activeFilter === 'fp' 
              ? 'bg-red-50 dark:bg-red-950/40 border-red-500 shadow-lg' 
              : 'bg-slate-50/80 dark:bg-black/40 border-slate-200 dark:border-slate-900 hover:border-red-500/50'
          }`}
        >
          <div className="flex items-center justify-between text-red-600 dark:text-red-400 mb-1">
            <span className="text-[9px] font-black uppercase tracking-widest flex items-center gap-1">
              <AlertTriangle className="w-3 h-3" /> False Positive
            </span>
          </div>
          <div className="text-2xl font-black text-red-600 dark:text-red-400 tracking-tight">{fpCount}</div>
          <div className="text-[8px] text-red-600/80 dark:text-red-500/70 font-bold mt-1">
            Noise terfilter & disaring
          </div>
        </div>

        <div className="p-4 rounded-2xl border border-slate-200 dark:border-red-950/40 bg-slate-50/80 dark:bg-black/40 hover:border-red-500/50 transition-all">
          <div className="flex items-center justify-between text-red-600 dark:text-red-400 mb-1">
            <span className="text-[9px] font-black uppercase tracking-widest flex items-center gap-1">
              <Brain className="w-3 h-3 text-red-500" /> Rata Confidence
            </span>
          </div>
          <div className="text-2xl font-black text-red-600 dark:text-red-400 tracking-tight">
            {validatedCount > 0 ? `${(avgConfidence * 100).toFixed(1)}%` : '—'}
          </div>
          <div className="text-[8px] text-red-500/80 font-bold mt-1">
            Skor konsensus reasoning
          </div>
        </div>
      </div>
    </div>
  );
};

export default React.memo(AIBrainSummary);
