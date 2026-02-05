
import React, { useState, useMemo } from 'react';
import { OptionContract } from '../types';

interface OptionsProps {
  contracts: OptionContract[];
}

const OptionsAnalysis: React.FC<OptionsProps> = ({ contracts }) => {
  const [showUnusualOnly, setShowUnusualOnly] = useState(false);

  const filteredContracts = useMemo(() => {
    if (!showUnusualOnly) return contracts;
    return contracts.filter(c => c.isUnusual);
  }, [contracts, showUnusualOnly]);

  const calls = useMemo(() => filteredContracts.filter(c => c.type === 'CALL'), [filteredContracts]);
  const puts = useMemo(() => filteredContracts.filter(c => c.type === 'PUT'), [filteredContracts]);

  const TableHeader = () => (
    <div className="grid grid-cols-5 px-4 py-2 bg-slate-800/50 text-[10px] font-bold text-slate-500 uppercase tracking-wider sticky top-0 z-10">
      <span>Strike</span>
      <span>Price</span>
      <span>Vol</span>
      <span>OI</span>
      <span className="text-right">IV</span>
    </div>
  );

  const ContractRow = ({ c }: { c: OptionContract }) => (
    <div className={`grid grid-cols-5 px-4 py-2 border-b border-slate-800/30 text-[11px] items-center transition-colors hover:bg-slate-800/20 ${c.isUnusual ? 'bg-blue-600/5' : ''}`}>
      <span className="font-bold text-slate-300">{c.strike.toFixed(1)}</span>
      <span className="text-slate-400 font-mono">${c.lastPrice.toFixed(2)}</span>
      <span className={`font-mono ${c.isUnusual ? 'text-blue-400 font-bold' : 'text-slate-400'}`}>
        {c.volume > 1000 ? `${(c.volume / 1000).toFixed(1)}k` : c.volume.toFixed(0)}
      </span>
      <span className="text-slate-500 font-mono">
        {c.openInterest > 1000 ? `${(c.openInterest / 1000).toFixed(1)}k` : c.openInterest.toFixed(0)}
      </span>
      <span className="text-right text-slate-400 font-mono">{(c.impliedVolatility * 100).toFixed(1)}%</span>
    </div>
  );

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between p-4 border-b border-slate-800 shrink-0">
        <h2 className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">Options Activity</h2>
        <label className="flex items-center gap-2 cursor-pointer group">
          <input 
            type="checkbox" 
            checked={showUnusualOnly}
            onChange={(e) => setShowUnusualOnly(e.target.checked)}
            className="w-3 h-3 rounded bg-slate-800 border-slate-700 text-blue-600 focus:ring-0 focus:ring-offset-0"
          />
          <span className="text-[10px] font-bold text-slate-400 group-hover:text-slate-200 transition-colors uppercase tracking-tight">Unusual Vol Only</span>
        </label>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Calls Section */}
        <div className="flex-1 flex flex-col border-r border-slate-800">
          <div className="px-4 py-1.5 bg-green-500/10 border-b border-green-500/20">
            <span className="text-[9px] font-bold text-green-500 uppercase tracking-widest">Calls</span>
          </div>
          <TableHeader />
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {calls.length > 0 ? (
              calls.map((c, i) => <ContractRow key={`call-${i}`} c={c} />)
            ) : (
              <div className="p-8 text-center text-slate-600 text-[11px] italic">No matching call contracts</div>
            )}
          </div>
        </div>

        {/* Puts Section */}
        <div className="flex-1 flex flex-col">
          <div className="px-4 py-1.5 bg-red-500/10 border-b border-red-500/20">
            <span className="text-[9px] font-bold text-red-500 uppercase tracking-widest">Puts</span>
          </div>
          <TableHeader />
          <div className="flex-1 overflow-y-auto custom-scrollbar">
            {puts.length > 0 ? (
              puts.map((c, i) => <ContractRow key={`put-${i}`} c={c} />)
            ) : (
              <div className="p-8 text-center text-slate-600 text-[11px] italic">No matching put contracts</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OptionsAnalysis;
