
import React, { useState } from 'react';
import { TickerSummary } from '../types';

interface SignalProps {
  ticker: string;
  summary?: TickerSummary;
  aiAnalysis: string;
}

type BadgeStyle = 'default' | 'gold' | 'fire' | 'emerald';

const FactorRow: React.FC<{ 
  label: string; 
  value: string; 
  sentiment?: 'bullish' | 'bearish' | 'neutral' | 'warning';
  extra?: React.ReactNode;
}> = ({ label, value, sentiment, extra }) => {
  const getSentimentClasses = (s?: string) => {
    switch(s) {
      case 'bullish': return 'bg-green-500/15 text-green-400 border-green-500/30';
      case 'bearish': return 'bg-red-500/15 text-red-400 border-red-500/30';
      case 'warning': return 'bg-amber-500/15 text-amber-400 border-amber-500/30';
      default: return 'bg-slate-800/50 text-slate-400 border-slate-700/50';
    }
  };

  return (
    <div className="flex justify-between items-center py-[10px] border-b border-slate-800/40 last:border-0">
      <span className="text-[11px] font-medium text-slate-400">{label}</span>
      <div className="flex items-center gap-[10px]">
        {extra}
        <span className={`text-[10px] font-bold px-[10px] py-[2px] rounded uppercase tracking-tight border ${getSentimentClasses(sentiment)}`}>
          {value}
        </span>
      </div>
    </div>
  );
};

const EnhancedMiniCalendar: React.FC<{ days: string }> = ({ days }) => {
  const dayNum = parseInt(days);
  const isImminent = !isNaN(dayNum) && dayNum <= 7;
  const isApproaching = !isNaN(dayNum) && dayNum <= 14;

  return (
    <div className={`relative flex flex-col items-center justify-center w-9 h-10 rounded-md border overflow-hidden transition-all duration-500 shadow-lg 
      ${isImminent ? 'border-orange-500/50 shadow-orange-950/40 animate-pulse' : 'border-slate-700 shadow-black/40'} 
      ${isApproaching ? 'bg-slate-900' : 'bg-slate-950'}`}>
      
      {/* Calendar Top Rings Decor */}
      <div className="absolute top-[2px] left-1/2 -translate-x-1/2 flex gap-1 z-10">
        <div className="w-[2px] h-[4px] bg-slate-600 rounded-full"></div>
        <div className="w-[2px] h-[4px] bg-slate-600 rounded-full"></div>
      </div>

      <div className={`w-full text-[6px] font-black text-white text-center py-[2px] uppercase tracking-tighter border-b
        ${isImminent ? 'bg-orange-600 border-orange-400/30' : 'bg-red-600 border-red-400/30'}`}>
        {isImminent ? 'ALERT' : 'EST'}
      </div>

      <div className="flex-1 flex flex-col items-center justify-center leading-none">
        <span className={`text-[12px] font-black tracking-tighter ${isImminent ? 'text-orange-400' : 'text-slate-100'}`}>
          {isImminent || isApproaching ? `T-${days}` : days}
        </span>
        <span className="text-[5px] font-bold text-slate-500 uppercase tracking-widest mt-[1px]">DAYS</span>
      </div>

      {/* Glossy Overlay */}
      <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-white/10 pointer-events-none"></div>
    </div>
  );
};

const SignalEngine: React.FC<SignalProps> = ({ ticker, summary, aiAnalysis }) => {
  const [strongBadgeStyle, setStrongBadgeStyle] = useState<BadgeStyle>('default');
  const [isConfiguring, setIsConfiguring] = useState(false);

  if (!summary) return null;

  const getSentiment = (val: string): 'bullish' | 'bearish' | 'neutral' | 'warning' => {
    const lower = val.toLowerCase();
    if (lower.includes('pnlty') || lower.includes('penalty') || lower.includes('critical') || lower.includes('approaching')) return 'warning';
    if (lower.includes('bullish') || lower.includes('above') || lower.includes('oversold') || lower.includes('call heavy') || (lower.includes('low iv'))) return 'bullish';
    if (lower.includes('bearish') || lower.includes('below') || lower.includes('overbought') || lower.includes('put heavy') || (lower.includes('high iv'))) return 'bearish';
    return 'neutral';
  };

  const getBadgeClasses = (style: BadgeStyle, isStrong: boolean) => {
    if (!isStrong) return 'bg-slate-800 text-slate-400 border border-slate-700';
    switch(style) {
      case 'gold': return 'bg-amber-500 text-slate-900 shadow-lg shadow-amber-900/40';
      case 'fire': return 'bg-orange-600 text-white shadow-lg shadow-orange-900/40';
      case 'emerald': return 'bg-emerald-600 text-white shadow-lg shadow-emerald-900/40';
      default: return 'bg-blue-600 text-white shadow-lg shadow-blue-900/40';
    }
  };

  const getBadgeIcon = (style: BadgeStyle) => {
    switch(style) {
      case 'gold': return 'fa-star';
      case 'fire': return 'fa-fire';
      case 'emerald': return 'fa-check-double';
      default: return 'fa-bolt';
    }
  };

  const daysMatch = summary.scoreBreakdown.earningsDesc.match(/\((\d+)d\)/);
  const daysVal = daysMatch ? daysMatch[1] : "?";

  return (
    <div className="flex flex-col gap-4">
      <div className="bg-slate-900/40 border border-slate-800 rounded-xl p-5 relative backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <div className="flex flex-col">
            <h3 className="text-[10px] font-bold uppercase tracking-wider text-slate-500">Signal Engine</h3>
            <span className="text-[9px] text-slate-600 font-medium">Weighted Analysis</span>
          </div>
          
          <div className="flex items-center gap-2">
             {summary.signalClass === 'Strong' && (
               <button 
                onClick={() => setIsConfiguring(!isConfiguring)}
                className="p-1 text-slate-600 hover:text-slate-400 transition-colors"
               >
                 <i className="fas fa-cog text-[10px]"></i>
               </button>
             )}
            <span className={`text-[10px] font-extrabold px-[10px] py-[2px] rounded-full flex items-center gap-[6px] transition-all duration-300 ${getBadgeClasses(strongBadgeStyle, summary.signalClass === 'Strong')}`}>
              {summary.signalClass === 'Strong' && <i className={`fas ${getBadgeIcon(strongBadgeStyle)} text-[9px]`}></i>}
              {summary.signalClass.toUpperCase()}
            </span>
          </div>
        </div>

        {isConfiguring && summary.signalClass === 'Strong' && (
          <div className="absolute top-12 right-5 z-20 bg-slate-800 border border-slate-700 rounded-lg shadow-2xl p-2 flex flex-col gap-1 w-32">
            <div className="text-[8px] font-bold text-slate-500 uppercase px-1 mb-1">Badge Theme</div>
            {(['default', 'gold', 'fire', 'emerald'] as BadgeStyle[]).map((style) => (
              <button
                key={style}
                onClick={() => { setStrongBadgeStyle(style); setIsConfiguring(false); }}
                className={`flex items-center gap-2 px-2 py-[6px] rounded text-[10px] font-medium transition-colors ${strongBadgeStyle === style ? 'bg-slate-700 text-white' : 'text-slate-400 hover:bg-slate-750 hover:text-slate-200'}`}
              >
                <div className={`w-2 h-2 rounded-full ${getBadgeClasses(style, true).split(' ')[0]}`}></div>
                <span className="capitalize">{style}</span>
              </button>
            ))}
          </div>
        )}

        <div className="flex justify-around items-end h-20 gap-4 mb-8 pt-4">
          <div className="flex flex-col items-center flex-1 h-full">
            <div 
              className="w-full bg-green-500/10 rounded-t-md relative transition-all duration-700 ease-out" 
              style={{ height: `${summary.callScore}%` }}
            >
              <div className="absolute inset-x-0 top-0 h-[2px] bg-green-500"></div>
              <div className="absolute top-[-20px] left-1/2 -translate-x-1/2 text-[10px] font-black text-green-500">{summary.callScore}%</div>
            </div>
            <span className="text-[9px] mt-2 font-bold text-slate-500 tracking-tighter">CALL BIAS</span>
          </div>
          <div className="flex flex-col items-center flex-1 h-full">
            <div 
              className="w-full bg-red-500/10 rounded-t-md relative transition-all duration-700 ease-out" 
              style={{ height: `${summary.putScore}%` }}
            >
              <div className="absolute inset-x-0 top-0 h-[2px] bg-red-500"></div>
              <div className="absolute top-[-20px] left-1/2 -translate-x-1/2 text-[10px] font-black text-red-500">{summary.putScore}%</div>
            </div>
            <span className="text-[9px] mt-2 font-bold text-slate-500 tracking-tighter">PUT BIAS</span>
          </div>
        </div>

        <div className="mb-6 border-t border-slate-800/50 pt-4">
          <div className="text-[9px] font-black text-slate-600 tracking-widest uppercase mb-3">Factor Observation</div>
          <div className="flex flex-col">
            <FactorRow label="Trend (MA50)" value={summary.scoreBreakdown.trend} sentiment={getSentiment(summary.scoreBreakdown.trend)} />
            <FactorRow label="RSI Strategy" value={summary.scoreBreakdown.rsiDesc} sentiment={getSentiment(summary.scoreBreakdown.rsiDesc)} />
            <FactorRow label="MACD Momentum" value={summary.scoreBreakdown.macdDesc} sentiment={getSentiment(summary.scoreBreakdown.macdDesc)} />
            <FactorRow label="Option Flow" value={summary.scoreBreakdown.skewDesc} sentiment={getSentiment(summary.scoreBreakdown.skewDesc)} />
            <FactorRow 
              label="Earnings Prox" 
              value={summary.scoreBreakdown.earningsDesc} 
              sentiment={getSentiment(summary.scoreBreakdown.earningsDesc)} 
              extra={<EnhancedMiniCalendar days={daysVal} />}
            />
            <FactorRow label="IV Regime" value={summary.scoreBreakdown.ivDesc} sentiment={getSentiment(summary.scoreBreakdown.ivDesc)} />
          </div>
        </div>

        <div className="pt-4 border-t border-slate-800">
          <div className="text-[10px] font-black text-blue-500 mb-2 flex items-center gap-[6px] uppercase tracking-wider">
            <i className="fas fa-brain"></i> Cognitive Layer
          </div>
          <p className="text-[11px] leading-relaxed text-slate-400 italic font-medium">"{aiAnalysis}"</p>
        </div>
      </div>
    </div>
  );
};

export default SignalEngine;
