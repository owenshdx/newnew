
import React from 'react';
import { 
  ComposedChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Area, 
  Bar 
} from 'recharts';
import { PricePoint } from '../types';

interface ChartProps {
  data: PricePoint[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-slate-900/95 border border-slate-700 p-3 rounded-lg shadow-xl text-xs flex flex-col gap-1">
        <p className="font-bold text-slate-300 mb-1">{label}</p>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
          <span className="text-slate-500">Price:</span>
          <span className="font-mono text-white">${data.close.toFixed(2)}</span>
          <span className="text-slate-500">SMA 50:</span>
          <span className="font-mono text-blue-400">${data.ma50?.toFixed(2) || 'N/A'}</span>
          <span className="text-slate-500">RSI:</span>
          <span className="font-mono text-purple-400">{data.rsi?.toFixed(1) || 'N/A'}</span>
          <span className="text-slate-500">Vol:</span>
          <span className="font-mono text-slate-300">{(data.volume / 1000).toFixed(0)}k</span>
        </div>
      </div>
    );
  }
  return null;
};

const TechnicalChart: React.FC<ChartProps> = ({ data }) => {
  const minPrice = Math.min(...data.map(d => d.low)) * 0.995;
  const maxPrice = Math.max(...data.map(d => d.high)) * 1.005;

  return (
    <div className="w-full h-full min-h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={data}>
          <defs>
            <linearGradient id="colorPv" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.1}/>
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorRsi" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#a855f7" stopOpacity={0.1}/>
              <stop offset="95%" stopColor="#a855f7" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
          <XAxis 
            dataKey="time" 
            stroke="#475569" 
            fontSize={10} 
            tickLine={false} 
            axisLine={false}
          />
          <YAxis 
            domain={[minPrice, maxPrice]} 
            stroke="#475569" 
            fontSize={10} 
            tickLine={false} 
            axisLine={false} 
            orientation="right"
            tickFormatter={(val) => `$${val.toFixed(0)}`}
          />
          <Tooltip content={<CustomTooltip />} />
          
          {/* Bollinger Bands */}
          <Area 
            type="monotone" 
            dataKey="bbUpper" 
            stroke="none" 
            fill="#334155" 
            fillOpacity={0.1} 
          />
          <Line 
            type="monotone" 
            dataKey="bbUpper" 
            stroke="#334155" 
            strokeWidth={1} 
            dot={false} 
            strokeDasharray="5 5"
          />
          <Line 
            type="monotone" 
            dataKey="bbLower" 
            stroke="#334155" 
            strokeWidth={1} 
            dot={false} 
            strokeDasharray="5 5"
          />

          {/* Volume bars at bottom */}
          <Bar 
            dataKey="volume" 
            fill="#1e293b" 
            opacity={0.3} 
            yAxisId="vol" 
          />
          <YAxis yAxisId="vol" hide domain={[0, max => max * 5]} />

          {/* SMA 50 */}
          <Line 
            type="monotone" 
            dataKey="ma50" 
            stroke="#3b82f6" 
            strokeWidth={2} 
            dot={false} 
          />

          {/* Price Line (Simplified version of candlestick for SVG perf) */}
          <Area 
            type="monotone" 
            dataKey="close" 
            stroke="#3b82f6" 
            fillOpacity={1} 
            fill="url(#colorPv)" 
            strokeWidth={2}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TechnicalChart;
