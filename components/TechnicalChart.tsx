
import React, { useMemo } from 'react';
import { 
  ComposedChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Bar, 
  Cell,
  ReferenceLine
} from 'recharts';
import { PricePoint } from '../types';

interface ChartProps {
  data: PricePoint[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const isUp = data.close >= data.open;
    return (
      <div className="bg-slate-900/95 border border-slate-700 p-3 rounded-lg shadow-xl text-[10px] flex flex-col gap-1 backdrop-blur-md z-50 min-w-[140px]">
        <p className="font-black text-slate-500 mb-1 border-b border-slate-800 pb-1 uppercase tracking-tighter">{label}</p>
        <div className="grid grid-cols-2 gap-x-2 gap-y-1 mt-1">
          <span className="text-slate-500">O:</span>
          <span className="font-mono text-slate-200 text-right">${data.open.toFixed(2)}</span>
          <span className="text-slate-500">H:</span>
          <span className="font-mono text-slate-200 text-right">${data.high.toFixed(2)}</span>
          <span className="text-slate-500">L:</span>
          <span className="font-mono text-slate-200 text-right">${data.low.toFixed(2)}</span>
          <span className="text-slate-500">C:</span>
          <span className={`font-mono font-bold text-right ${isUp ? 'text-green-400' : 'text-red-400'}`}>${data.close.toFixed(2)}</span>
          
          <div className="col-span-2 border-t border-slate-800 my-1 pt-1"></div>
          
          <span className="text-slate-500">SMA 50:</span>
          <span className="font-mono text-amber-400 text-right">${data.ma50?.toFixed(2) || '--'}</span>
          <span className="text-slate-500">RSI (14):</span>
          <span className={`font-mono text-right ${data.rsi > 70 ? 'text-red-400' : data.rsi < 30 ? 'text-green-400' : 'text-blue-400'}`}>
            {data.rsi?.toFixed(1) || '--'}
          </span>
        </div>
      </div>
    );
  }
  return null;
};

const VolumeProfile: React.FC<{ data: PricePoint[], minPrice: number, maxPrice: number }> = ({ data, minPrice, maxPrice }) => {
  const bins = useMemo(() => {
    if (!data.length) return [];
    const numBins = 40;
    const binSize = (maxPrice - minPrice) / numBins;
    const profile = new Array(numBins).fill(0);
    
    data.forEach(p => {
      const idx = Math.min(numBins - 1, Math.max(0, Math.floor((p.close - minPrice) / binSize)));
      profile[idx] += p.volume;
    });

    const maxVol = Math.max(...profile);
    return profile.map((vol, i) => ({
      vol,
      width: (vol / maxVol) * 100,
      bottom: (i / numBins) * 100,
      height: 100 / numBins
    }));
  }, [data, minPrice, maxPrice]);

  return (
    <div className="absolute inset-0 pointer-events-none opacity-20 left-0 right-[45px]">
      {bins.map((bin, i) => (
        <div 
          key={i}
          style={{
            position: 'absolute',
            bottom: `${bin.bottom}%`,
            left: 0,
            height: `${bin.height}%`,
            width: `${bin.width * 0.4}%`, // Max width 40% of chart
            backgroundColor: '#3b82f6',
            borderBottom: '1px solid rgba(15, 23, 42, 0.2)',
            transition: 'width 0.3s ease'
          }}
        />
      ))}
    </div>
  );
};

const TechnicalChart: React.FC<ChartProps> = ({ data }) => {
  if (!data || data.length === 0) return null;

  const minPrice = useMemo(() => Math.min(...data.map(d => d.low)) * 0.999, [data]);
  const maxPrice = useMemo(() => Math.max(...data.map(d => d.high)) * 1.001, [data]);

  // Prepare data for candles: Recharts Bar can take [low, high] as dataKey
  const chartData = useMemo(() => data.map(d => ({
    ...d,
    candle: [d.open, d.close],
    wick: [d.low, d.high]
  })), [data]);

  return (
    <div className="w-full h-full flex flex-col gap-2">
      {/* Price + MA50 Pane */}
      <div className="flex-[3] w-full min-h-[250px] relative overflow-hidden">
        <div className="absolute top-2 left-4 z-10 flex gap-4 pointer-events-none">
           <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-amber-400"></div>
              <span className="text-[9px] font-black text-slate-500 uppercase">SMA 50</span>
           </div>
           <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-blue-500 opacity-50"></div>
              <span className="text-[9px] font-black text-slate-500 uppercase">Vol Profile</span>
           </div>
        </div>

        {/* Volume Profile Overlay */}
        <VolumeProfile data={data} minPrice={minPrice} maxPrice={maxPrice} />
        
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }} syncId="optix_sync">
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} opacity={0.3} />
            
            <XAxis 
              dataKey="time" 
              hide={true}
            />
            
            <YAxis 
              domain={[minPrice, maxPrice]} 
              stroke="#475569" 
              fontSize={9} 
              tickLine={false} 
              axisLine={false} 
              orientation="right"
              tickFormatter={(val) => `$${val.toFixed(1)}`}
              width={45}
            />
            
            <Tooltip 
              content={<CustomTooltip />} 
              cursor={{ stroke: '#334155', strokeWidth: 1 }} 
              isAnimationActive={false}
            />

            {/* Wick */}
            <Bar dataKey="wick" barSize={1} isAnimationActive={false}>
              {chartData.map((entry, index) => (
                <Cell key={`wick-${index}`} fill={entry.close >= entry.open ? '#22c55e' : '#ef4444'} opacity={0.6} />
              ))}
            </Bar>

            {/* Candle Body */}
            <Bar dataKey="candle" barSize={8} isAnimationActive={false}>
              {chartData.map((entry, index) => (
                <Cell key={`candle-${index}`} fill={entry.close >= entry.open ? '#22c55e' : '#ef4444'} />
              ))}
            </Bar>

            {/* MA50 Line - Bold and Distinct */}
            <Line
              type="monotone"
              dataKey="ma50"
              stroke="#fbbf24"
              strokeWidth={1.5}
              dot={false}
              isAnimationActive={false}
              strokeOpacity={0.9}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* RSI Pane */}
      <div className="flex-1 w-full min-h-[100px] border-t border-slate-800 pt-2">
        <div className="px-4 mb-1 flex justify-between items-center">
          <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest">RSI (14)</span>
          <div className="flex gap-2 text-[8px] font-bold">
            <span className="text-red-500/80">70 OB</span>
            <span className="text-green-500/80">30 OS</span>
          </div>
        </div>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 5, right: 10, left: 0, bottom: 10 }} syncId="optix_sync">
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} opacity={0.2} />
            <XAxis 
              dataKey="time" 
              stroke="#475569" 
              fontSize={8} 
              tickLine={false} 
              axisLine={false}
              minTickGap={40}
            />
            <YAxis 
              domain={[0, 100]} 
              stroke="#475569" 
              fontSize={8} 
              tickLine={false} 
              axisLine={false} 
              orientation="right"
              ticks={[30, 70]}
              width={45}
            />
            
            {/* RSI Threshold Lines */}
            <ReferenceLine y={70} stroke="#ef4444" strokeDasharray="3 3" opacity={0.3} />
            <ReferenceLine y={30} stroke="#22c55e" strokeDasharray="3 3" opacity={0.3} />

            <Line 
              type="monotone" 
              dataKey="rsi" 
              stroke="#3b82f6" 
              strokeWidth={1.5} 
              dot={false} 
              isAnimationActive={false}
            />
            
            <Tooltip 
              content={<div className="hidden" />} // Shared sync tooltip handled by top chart
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default TechnicalChart;
