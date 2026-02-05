
import React from 'react';
import { OptionContract } from '../types';

interface OptionsProps {
  contracts: OptionContract[];
}

const OptionsAnalysis: React.FC<OptionsProps> = ({ contracts }) => {
  return (
    <div className="flex flex-col h-full overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-800 bg-slate-800/20 flex items-center justify-between">
        <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500">Options Flow</h3>
        <div className="flex gap-4">
          <div className="flex items-center gap-1">
            <span className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse"></span>
            <span className="text-[10px] font-medium text-slate-400">Unusual Volume</span>
          </div>
        </div>
      </div>
      
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        <table className="w-full text-left border-collapse">
          <thead className="sticky top-0 bg-slate-900 border-b border-slate-800 z-10">
            <tr>
              <th className="px-4 py-2 text-[10px] font-bold text-slate-500 uppercase">Strike</th>
              <th className="px-4 py-2 text-[10px] font-bold text-slate-500 uppercase">Type</th>
              <th className="px-4 py-2 text-[10px] font-bold text-slate-500 uppercase">Price</th>
              <th className="px-4 py-2 text-[10px] font-bold text-slate-500 uppercase">Vol</th>
              <th className="px-4 py-2 text-[10px] font-bold text-slate-500 uppercase">OI</th>
              <th className="px-4 py-2 text-[10px] font-bold text-slate-500 uppercase text-right">IV</th>
            </tr>
          </thead>
          <tbody className="text-xs">
            {contracts.map((contract, i) => (
              <tr 
                key={`${contract.strike}-${contract.type}-${i}`} 
                className={`border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors ${contract.isUnusual ? 'bg-yellow-500/5' : ''}`}
              >
                <td className="px-4 py-2.5 font-bold">${contract.strike.toFixed(1)}</td>
                <td className="px-4 py-2.5">
                  <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${contract.type === 'CALL' ? 'bg-green-500/10 text-green-500' : 'bg-red-500/10 text-red-500'}`}>
                    {contract.type}
                  </span>
                </td>
                <td className="px-4 py-2.5 font-mono">${contract.lastPrice.toFixed(2)}</td>
                <td className={`px-4 py-2.5 font-mono ${contract.isUnusual ? 'text-yellow-400 font-bold' : ''}`}>
                  {contract.volume.toLocaleString()}
                </td>
                <td className="px-4 py-2.5 font-mono text-slate-400">{contract.openInterest.toLocaleString()}</td>
                <td className="px-4 py-2.5 font-mono text-right text-blue-400">{(contract.impliedVolatility * 100).toFixed(1)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default OptionsAnalysis;
