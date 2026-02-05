
import React from 'react';
import { TickerSummary } from '../types';

interface SignalProps {
  ticker: string;
  summary?: TickerSummary;
  aiAnalysis: string;
}

const SignalEngine: React.FC<SignalProps> = ({ ticker, summary, aiAnalysis }) => {
  if (!summary) return null;

  const bias = summary.callScore > summary.putScore ? 'BULLISH' : 'BEARISH';
  const biasColor = bias === 'BULLISH' ? 'text-green-400' : 'text-red-400';

  return (
    <div className="flex flex-col gap-4">
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500">Signal Engine</h3>
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${summary.signalClass === 'Strong' ? 'bg-blue-600 text-white' : 'bg-slate-800 text-slate-400'}`}>
            {summary.signalClass}
          </span>
        </div>

        <div className="flex justify-around items-end h-24 gap-4 mb-4">
          <div className="flex flex-col items-center flex-1">
            <div 
              className="w-full bg-green-500/20 rounded-t-md relative transition-all duration-700"
              style={{ height: `${summary.callScore}%` }}
            >
              <div className="absolute top-[-20px] left-1/2 -translate-x-1/2 text-[10px] font-bold text-green-500">{summary.callScore}</div>
            </div>
            <span className="text-[10px] mt-2 font-bold text-slate-500">CALL</span>
          </div>
          <div className="flex flex-col items-center flex-1">
            <div 
              className="w-full bg-red-500/20 rounded-t-md relative transition-all duration-700"
              style={{ height: `${summary.putScore}%` }}
            >
              <div className="absolute top-[-20px] left-1/2 -translate-x-1/2 text-[10px] font-bold text-red-500">{summary.putScore}</div>
            </div>
            <span className="text-[10px] mt-2 font-bold text-slate-500">PUT</span>
          </div>
        </div>

        <div className="space-y-3 mb-4">
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Technical Trend</span>
            <span className="font-mono text-slate-200">{summary.scoreBreakdown.technical.toFixed(0)}</span>
          </div>
          <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500" style={{ width: `${summary.scoreBreakdown.technical}%` }}></div>
          </div>
          <div className="flex justify-between text-xs">
            <span className="text-slate-400">Options Skew</span>
            <span className="font-mono text-slate-200">{summary.scoreBreakdown.options.toFixed(0)}</span>
          </div>
          <div className="w-full h-1 bg-slate-800 rounded-full overflow-hidden">
            <div className="h-full bg-purple-500" style={{ width: `${summary.scoreBreakdown.options}%` }}></div>
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800">
          <div className="text-[10px] font-bold text-blue-500 mb-2 flex items-center gap-1">
            <i className="fas fa-robot"></i> AI ANALYSIS
          </div>
          <p className="text-xs leading-relaxed text-slate-300 italic">
            &quot;{aiAnalysis}&quot;
          </p>
        </div>
      </div>
    </div>
  );
};

export default SignalEngine;
