
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
  const [isMock, setIsMock] = useState<boolean>(true); // Simulation defaults to mock

  const fetchData = useCallback(async (isRetry = false) => {
    setLoading(true);
    
    // Simulate a slight delay for the "live" attempt
    if (isRetry) {
      await new Promise(r => setTimeout(r, 1000));
    }

    try {
      const hist = MarketDataService.generateHistory(selectedTicker, Timeframe.INTRADAY);
      const opts = MarketDataService.fetchOptionsChain(selectedTicker);
      const summary = await MarketDataService.fetchTickerSummary(selectedTicker);
      
      setHistory(hist);
      setOptions(opts);
      setSummaries(prev => ({ ...prev, [selectedTicker]: summary }));
      
      // In simulation mode, we stay in mock but provide the toggle experience
      setIsMock(true); 
    } catch (error) {
      console.error("Data fetch error:", error);
      setIsMock(true);
    } finally {
      setLoading(false);
    }
  }, [selectedTicker]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleRetry = () => {
    fetchData(true);
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden text-slate-200">
      <header className="flex items-center justify-between px-6 py-3 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md z-50 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-white">O</div>
          <h1 className="text-xl font-bold tracking-tight">Optix <span className="text-slate-500 font-medium text-sm">PRO</span></h1>
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

      {/* Robust Fallback Banner */}
      {isMock && (
        <div className="bg-amber-600/90 backdrop-blur-sm border-b border-amber-500/50 px-6 py-2 flex items-center justify-between z-40 shrink-0">
          <div className="flex items-center gap-2 text-white">
            <i className="fas fa-exclamation-triangle text-amber-200"></i>
            <span className="text-xs font-bold uppercase tracking-wider">Mock Data Active</span>
            <span className="text-[10px] text-amber-100/80 font-medium hidden md:inline">— Live yfinance fetching requires local execution.</span>
          </div>
          <button 
            onClick={handleRetry}
            disabled={loading}
            className={`flex items-center gap-2 bg-white/10 hover:bg-white/20 text-white px-3 py-1 rounded border border-white/20 text-[10px] font-bold transition-all ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {loading ? <i className="fas fa-spinner fa-spin"></i> : <i className="fas fa-sync-alt"></i>}
            RETRY LIVE DATA
          </button>
        </div>
      )}

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
          <div className="flex-1 bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden flex flex-col relative">
            <div className="flex items-center justify-between p-4 border-b border-slate-800 shrink-0">
              <h2 className="text-lg font-bold">
                {selectedTicker} 
                <span className="text-[10px] text-slate-500 ml-3 uppercase tracking-widest font-bold">
                  {loading ? 'Updating...' : 'Intraday View'}
                </span>
              </h2>
              {isMock && <span className="text-[9px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded font-bold uppercase">Simulation Mode</span>}
            </div>
            <div className="flex-1 p-4 relative">
              {loading && !history.length ? (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-900/50 z-10">
                  <i className="fas fa-circle-notch fa-spin text-blue-500 text-2xl"></i>
                </div>
              ) : (
                <TechnicalChart data={history} />
              )}
            </div>
          </div>
          <div className="h-1/3 bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden flex flex-col shrink-0">
            <OptionsAnalysis contracts={options} />
          </div>
        </div>
      </main>
    </div>
  );
};

export default App;
