
import React, { useState } from 'react';
import { TickerSummary } from '../types';

interface WatchlistProps {
  tickers: string[];
  selected: string;
  onSelect: (symbol: string) => void;
  onAdd: (symbol: string) => void;
  onRemove: (symbol: string) => void;
  summaries: Record<string, TickerSummary>;
}

const Watchlist: React.FC<WatchlistProps> = ({ tickers, selected, onSelect, onAdd, onRemove, summaries }) => {
  const [input, setInput] = useState('');

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl flex flex-col h-[500px]">
      <div className="p-4 border-b border-slate-800">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-3">Watchlist</h3>
        <div className="relative">
          <input 
            type="text" 
            placeholder="Add Ticker..." 
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                onAdd(input);
                setInput('');
              }
            }}
            className="w-full bg-slate-800 border border-slate-700 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
          <button 
            onClick={() => { onAdd(input); setInput(''); }}
            className="absolute right-2 top-1.5 text-slate-400 hover:text-white"
          >
            <i className="fas fa-plus"></i>
          </button>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {tickers.map(ticker => {
          const s = summaries[ticker];
          const isSelected = selected === ticker;
          return (
            <div 
              key={ticker}
              onClick={() => onSelect(ticker)}
              className={`group flex items-center justify-between px-4 py-3 cursor-pointer border-l-2 transition-all ${isSelected ? 'bg-blue-600/10 border-blue-500' : 'border-transparent hover:bg-slate-800/50'}`}
            >
              <div className="flex flex-col">
                <span className="text-sm font-bold">{ticker}</span>
                <span className="text-[10px] text-slate-500">
                  IV: {s ? (s.avgIv * 100).toFixed(1) : '--'}%
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <div className="text-sm font-medium">
                    {s ? `$${s.price.toFixed(2)}` : '--'}
                  </div>
                  <div className={`text-[10px] font-bold ${s && s.change >= 0 ? 'text-green-500' : 'text-red-500'}`}>
                    {s ? `${s.change >= 0 ? '+' : ''}${s.changePercent.toFixed(2)}%` : '--'}
                  </div>
                </div>
                <button 
                  onClick={(e) => { e.stopPropagation(); onRemove(ticker); }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-red-500 transition-opacity"
                >
                  <i className="fas fa-times text-xs"></i>
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Watchlist;
