
import React from 'react';
import { 
  AreaChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Area, 
  YAxis as YAxisHidden
} from 'recharts';
import { PricePoint } from '../types';

interface ChartProps {
  data: PricePoint[];
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-slate-900/95 border border-slate-700 p-3 rounded-lg shadow-xl text-xs flex flex-col gap-1 backdrop-blur-md">
        <p className="font-bold text-slate-400 mb-1 border-b border-slate-800 pb-1">{label}</p>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1 mt-1">
          <span className="text-slate-500">Price:</span>
          <span className="font-mono text-white font-bold">${data.close.toFixed(2)}</span>
          <span className="text-slate-500">SMA 50:</span>
          <span className="font-mono text-blue-400">${data.ma50?.toFixed(2) || 'N/A'}</span>
          <span className="text-slate-500">RSI:</span>
          <span className={`font-mono ${data.rsi > 70 ? 'text-red-400' : data.rsi < 30 ? 'text-green-400' : 'text-purple-400'}`}>
            {data.rsi?.toFixed(1) || 'N/A'}
          </span>
        </div>
      </div>
    );
  }
  return null;
};

const TechnicalChart: React.FC<ChartProps> = ({ data }) => {
  const prices = data.map(d => d.close);
  const minPrice = Math.min(...prices) * 0.998;
  const maxPrice = Math.max(...prices) * 1.002;

  return (
    <div className="w-full h-full min-h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id="priceGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
            </linearGradient>
          </defs>
          
          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} opacity={0.4} />
          
          <XAxis 
            dataKey="time" 
            stroke="#475569" 
            fontSize={9} 
            tickLine={false} 
            axisLine={false}
            minTickGap={30}
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
          
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: '#334155', strokeWidth: 1 }} />
          
          {/* Subtle Background SMA 50 */}
          <Area
            type="monotone"
            dataKey="ma50"
            stroke="#1d4ed8"
            strokeWidth={1}
            fill="none"
            dot={false}
            opacity={0.5}
          />

          {/* Main Price Area */}
          <Area 
            type="monotone" 
            dataKey="close" 
            stroke="#3b82f6" 
            strokeWidth={2.5}
            fill="url(#priceGradient)" 
            animationDuration={1000}
            activeDot={{ r: 4, stroke: '#1e293b', strokeWidth: 2, fill: '#3b82f6' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
};

export default TechnicalChart;
