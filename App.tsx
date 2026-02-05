
import React, { useState, useEffect, useCallback } from 'react';
import { TickerSummary, PricePoint, OptionContract, Timeframe } from './types';
import { MarketDataService } from './services/marketDataService';
import Watchlist from './components/Watchlist';
import TechnicalChart from './components/TechnicalChart';
import OptionsAnalysis from './components/OptionsAnalysis';
import SignalEngine from './components/SignalEngine';

const DEFAULT_TICKERS = ['AAPL', 'TSLA', 'SPY', 'NFLX', 'AMZN', 'GOOGL', 'IWM'];

const App: React.FC = () => {
  const [watchlist, setWatchlist] = useState<string[]>(DEFAULT_TICKERS);
  const [selectedTicker, setSelectedTicker] = useState<string>('AAPL');
  const [summaries, setSummaries] = useState<Record<string, TickerSummary>>({});
  const [history, setHistory] = useState<PricePoint[]>([]);
  const [options, setOptions] = useState<OptionContract[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [showSetup, setShowSetup] = useState<boolean>(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    const hist = MarketDataService.generateHistory(selectedTicker, Timeframe.INTRADAY);
    const opts = MarketDataService.fetchOptionsChain(selectedTicker);
    const summary = await MarketDataService.fetchTickerSummary(selectedTicker);
    setHistory(hist);
    setOptions(opts);
    setSummaries(prev => ({ ...prev, [selectedTicker]: summary }));
    setLoading(false);
  }, [selectedTicker]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return (
    <div className="flex flex-col h-screen overflow-hidden text-slate-200">
      <header className="flex items-center justify-between px-6 py-3 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md z-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-white">O</div>
          <h1 className="text-xl font-bold tracking-tight">Optix <span className="text-slate-500 font-medium text-sm">PREVIEW</span></h1>
        </div>
        
        <div className="flex items-center gap-4">
          <button 
            onClick={() => setShowSetup(!showSetup)}
            className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-2"
          >
            <i className="fas fa-terminal"></i> RUN LOCAL (LIVE DATA)
          </button>
        </div>
      </header>

      {showSetup && (
        <div className="absolute inset-0 z-[100] bg-slate-950/90 backdrop-blur-sm flex items-center justify-center p-6">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-2xl w-full p-8 shadow-2xl">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">Local Terminal Setup</h2>
              <button onClick={() => setShowSetup(false)} className="text-slate-500 hover:text-white"><i className="fas fa-times text-xl"></i></button>
            </div>
            <p className="text-slate-400 mb-6 leading-relaxed">
              To fetch <strong>live near-real-time data</strong> using the Python <code>yfinance</code> library, you must run the local app.py script. The current web view is a high-fidelity visual simulation.
            </p>
            <div className="bg-black/50 rounded-lg p-5 mb-6 font-mono text-sm border border-slate-800">
              <p className="text-blue-400 mb-2"># 1. Install dependencies</p>
              <p className="text-slate-300 mb-4">pip install streamlit yfinance pandas plotly</p>
              <p className="text-blue-400 mb-2"># 2. Run the application</p>
              <p className="text-slate-300">streamlit run app.py</p>
            </div>
            <button 
              onClick={() => setShowSetup(false)}
              className="w-full bg-slate-800 hover:bg-slate-700 text-white font-bold py-3 rounded-xl transition-all"
            >
              GOT IT
            </button>
          </div>
        </div>
      )}

      <main className="flex flex-1 overflow-hidden p-4 gap-4 bg-slate-950">
        <div className="w-72 flex flex-col gap-4">
          <Watchlist tickers={watchlist} selected={selectedTicker} onSelect={setSelectedTicker} onAdd={()=>{}} onRemove={()=>{}} summaries={summaries} />
          <SignalEngine ticker={selectedTicker} summary={summaries[selectedTicker]} aiAnalysis="Select 'Run Local' for live AI analysis." />
        </div>

        <div className="flex-1 flex flex-col gap-4 overflow-hidden">
          <div className="flex-1 bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-slate-800">
              <h2 className="text-lg font-bold">{selectedTicker} <span className="text-xs text-slate-500 ml-2">(Simulation)</span></h2>
            </div>
            <div className="flex-1 p-4 relative">
              <TechnicalChart data={history} />
            </div>
          </div>
          <div className="h-1/3 bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden flex flex-col">
            <OptionsAnalysis contracts={options} />
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
