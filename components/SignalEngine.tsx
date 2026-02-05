
import React, { useState } from 'react';
import { TickerSummary } from '../types';

interface SignalProps {
  ticker: string;
  summary?: TickerSummary;
  aiAnalysis: string;
}

type BadgeStyle = 'default' | 'gold' | 'fire' | 'emerald';

const FactorRow: React.FC<{ label: string; value: string; sentiment?: 'bullish' | 'bearish' | 'neutral' | 'warning' }> = ({ label, value, sentiment }) => {
  const sentimentClasses = {
    bullish: 'bg-green-500/10 text-green-500',
    bearish: 'bg-red-500/10 text-red-500',
    neutral: 'bg-slate-800 text-slate-400',
    warning: 'bg-amber-500/10 text-amber-500'
  };

  return (
    <div className="flex justify-between items-center py-2 border-b border-slate-800/50 last:border-0">
      <span className="text-[11px] text-slate-400">{label}</span>
      <div className="flex items-center gap-2">
        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded uppercase tracking-tight ${sentiment ? sentimentClasses[sentiment] : 'text-slate-200'}`}>
          {value}
        </span>
      </div>
    </div>
  );
};

const SignalEngine: React.FC<SignalProps> = ({ ticker, summary, aiAnalysis }) => {
  const [strongBadgeStyle, setStrongBadgeStyle] = useState<BadgeStyle>('default');
  const [isConfiguring, setIsConfiguring] = useState(false);

  if (!summary) return null;

  const getSentiment = (val: string): 'bullish' | 'bearish' | 'neutral' | 'warning' => {
    const lower = val.toLowerCase();
    if (lower.includes('pnlty') || lower.includes('penalty') || lower.includes('critical')) return 'warning';
    if (lower.includes('bullish') || lower.includes('above') || lower.includes('oversold') || lower.includes('call')) return 'bullish';
    if (lower.includes('bearish') || lower.includes('below') || lower.includes('overbought') || lower.includes('put')) return 'bearish';
    return 'neutral';
  };

  const badgeThemes = {
    default: {
      className: 'bg-blue-600 text-white shadow-lg shadow-blue-900/40',
      icon: 'fa-bolt'
    },
    gold: {
      className: 'bg-amber-500 text-slate-900 shadow-lg shadow-amber-900/40',
      icon: 'fa-star'
    },
    fire: {
      className: 'bg-orange-600 text-white shadow-lg shadow-orange-900/40',
      icon: 'fa-fire'
    },
    emerald: {
      className: 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/40',
      icon: 'fa-check-double'
    }
  };

  const theme = badgeThemes[strongBadgeStyle];

  return (
    <div className="flex flex-col gap-4">
      <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5 relative">
        <div className="flex items-center justify-between mb-4">
          <div className="flex flex-col">
            <h3 className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Signal Engine</h3>
            <span className="text-[9px] text-slate-600">Weighted Multi-Factor Analysis</span>
          </div>
          
          <div className="flex items-center gap-2">
             {summary.signalClass === 'Strong' && (
               <button 
                onClick={() => setIsConfiguring(!isConfiguring)}
                className="p-1 text-slate-600 hover:text-slate-400 transition-colors"
                title="Customize Strong Badge"
               >
                 <i className="fas fa-cog text-[10px]"></i>
               </button>
             )}
            
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1.5 transition-all duration-300 ${summary.signalClass === 'Strong' ? theme.className : 'bg-slate-800 text-slate-400'}`}>
              {summary.signalClass === 'Strong' && <i className={`fas ${theme.icon} text-[9px]`}></i>}
              {summary.signalClass.toUpperCase()}
            </span>
          </div>
        </div>

        {/* Customization Dropdown */}
        {isConfiguring && summary.signalClass === 'Strong' && (
          <div className="absolute top-12 right-5 z-20 bg-slate-800 border border-slate-700 rounded-lg shadow-2xl p-2 flex flex-col gap-1 w-32 animate-in fade-in slide-in-from-top-2 duration-200">
            <div className="text-[8px] font-bold text-slate-500 uppercase px-1 mb-1">Badge Theme</div>
            {(Object.keys(badgeThemes) as BadgeStyle[]).map((style) => (
              <button
                key={style}
                onClick={() => {
                  setStrongBadgeStyle(style);
                  setIsConfiguring(false);
                }}
                className={`flex items-center gap-2 px-2 py-1.5 rounded text-[10px] font-medium transition-colors ${strongBadgeStyle === style ? 'bg-slate-700 text-white' : 'text-slate-400 hover:bg-slate-750 hover:text-slate-200'}`}
              >
                <div className={`w-2 h-2 rounded-full ${badgeThemes[style].className.split(' ')[0]}`}></div>
                <span className="capitalize">{style}</span>
              </button>
            ))}
          </div>
        )}

        <div className="flex justify-around items-end h-20 gap-4 mb-6 pt-2">
          <div className="flex flex-col items-center flex-1">
            <div 
              className="w-full bg-green-500/10 rounded-t-md relative transition-all duration-700 overflow-hidden"
              style={{ height: `${summary.callScore}%` }}
            >
              <div className="absolute inset-x-0 top-0 h-0.5 bg-green-500 shadow-[0_0_10px_rgba(34,197,94,0.5)]"></div>
              <div className="absolute inset-0 bg-gradient-to-t from-green-500/5 to-transparent"></div>
              <div className="absolute top-[-18px] left-1/2 -translate-x-1/2 text-[10px] font-bold text-green-500">{summary.callScore}%</div>
            </div>
            <span className="text-[9px] mt-2 font-bold text-slate-500">CALL BIAS</span>
          </div>
          <div className="flex flex-col items-center flex-1">
            <div 
              className="w-full bg-red-500/10 rounded-t-md relative transition-all duration-700 overflow-hidden"
              style={{ height: `${summary.putScore}%` }}
            >
              <div className="absolute inset-x-0 top-0 h-0.5 bg-red-500 shadow-[0_0_10px_rgba(239,68,68,0.5)]"></div>
              <div className="absolute inset-0 bg-gradient-to-t from-red-500/5 to-transparent"></div>
              <div className="absolute top-[-18px] left-1/2 -translate-x-1/2 text-[10px] font-bold text-red-500">{summary.putScore}%</div>
            </div>
            <span className="text-[9px] mt-2 font-bold text-slate-500">PUT BIAS</span>
          </div>
        </div>

        <div className="mb-6">
          <div className="flex justify-between items-center mb-2">
            <div className="text-[9px] font-bold text-slate-600 tracking-widest uppercase">Factor Observation</div>
            <div className="text-[9px] font-bold text-slate-600 tracking-widest uppercase">Score Imp.</div>
          </div>
          <div className="flex flex-col">
            <FactorRow 
              label="Price vs MA50" 
              value={summary.scoreBreakdown.trend} 
              sentiment={getSentiment(summary.scoreBreakdown.trend)}
            />
            <FactorRow 
              label="RSI Trend" 
              value={summary.scoreBreakdown.rsiDesc} 
              sentiment={getSentiment(summary.scoreBreakdown.rsiDesc)}
            />
            <FactorRow 
              label="MACD Momentum" 
              value={summary.scoreBreakdown.macdDesc} 
              sentiment={getSentiment(summary.scoreBreakdown.macdDesc)}
            />
            <FactorRow 
              label="Options Skew" 
              value={summary.scoreBreakdown.skewDesc} 
              sentiment={getSentiment(summary.scoreBreakdown.skewDesc)}
            />
            <FactorRow 
              label="Earnings Prox" 
              value={summary.scoreBreakdown.earningsDesc} 
              sentiment={getSentiment(summary.scoreBreakdown.earningsDesc)}
            />
            <FactorRow 
              label="IV Regime" 
              value={summary.scoreBreakdown.ivDesc} 
              sentiment="neutral"
            />
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800">
          <div className="text-[10px] font-bold text-blue-500 mb-2 flex items-center gap-1">
            <i className="fas fa-microchip"></i> AI INTELLIGENCE
          </div>
          <p className="text-[11px] leading-relaxed text-slate-400 italic">
            &quot;{aiAnalysis}&quot;
          </p>
        </div>
      </div>
    </div>
  );
};

export default SignalEngine;
