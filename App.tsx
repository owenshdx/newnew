
import React, { useState, useEffect, useCallback } from 'react';
import { TickerSummary, PricePoint, OptionContract, Timeframe, SignalLog } from './types';
import { MarketDataService } from './services/marketDataService';
import { generateAisignal } from './services/geminiService';
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
  const [aiAnalysis, setAiAnalysis] = useState<string>('Loading market intelligence...');
  const [timeframe, setTimeframe] = useState<Timeframe>(Timeframe.INTRADAY);
  const [isMarketOpen, setIsMarketOpen] = useState<boolean>(MarketDataService.isMarketOpen());
  const [loading, setLoading] = useState<boolean>(true);
  const [isMock, setIsMock] = useState<boolean>(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch data for the selected ticker
      const hist = MarketDataService.generateHistory(selectedTicker, timeframe);
      const opts = MarketDataService.fetchOptionsChain(selectedTicker);
      const summary = await MarketDataService.fetchTickerSummary(selectedTicker);
      
      setHistory(hist);
      setOptions(opts);
      setSummaries(prev => ({ ...prev, [selectedTicker]: summary }));
      
      // Update all summaries in watchlist (limited simulation)
      for (const t of watchlist) {
        if (t !== selectedTicker) {
          const s = await MarketDataService.fetchTickerSummary(t);
          setSummaries(prev => ({ ...prev, [t]: s }));
        }
      }

      // AI Analysis
      const signal = await generateAisignal(selectedTicker, hist, opts);
      setAiAnalysis(signal);

      // Log signal locally if market is open
      if (isMarketOpen) {
        const log: SignalLog = {
          timestamp: new Date().toISOString(),
          symbol: selectedTicker,
          price: hist[hist.length - 1].close,
          callScore: summary.callScore,
          putScore: summary.putScore,
          signal
        };
        const existingLogs = JSON.parse(localStorage.getItem('optix_logs') || '[]');
        localStorage.setItem('optix_logs', JSON.stringify([log, ...existingLogs].slice(0, 50)));
      }

      setIsMock(MarketDataService.isMockMode());
    } catch (err) {
      console.error("Data fetch failed", err);
      setIsMock(true);
      MarketDataService.setMockMode(true);
    } finally {
      setLoading(false);
    }
  }, [selectedTicker, timeframe, watchlist, isMarketOpen]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => {
      setIsMarketOpen(MarketDataService.isMarketOpen());
      if (isMarketOpen) fetchData();
    }, 60000); // 1-minute refresh
    return () => clearInterval(interval);
  }, [fetchData, isMarketOpen]);

  const addTicker = (symbol: string) => {
    const s = symbol.toUpperCase();
    if (s && !watchlist.includes(s)) {
      setWatchlist([...watchlist, s]);
    }
  };

  const removeTicker = (symbol: string) => {
    setWatchlist(watchlist.filter(t => t !== symbol));
    if (selectedTicker === symbol) setSelectedTicker(watchlist[0] || '');
  };

  return (
    <div className="flex flex-col h-screen overflow-hidden text-slate-200">
      {/* Top Banner */}
      <header className="flex items-center justify-between px-6 py-3 border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center font-bold text-white">O</div>
          <h1 className="text-xl font-bold tracking-tight">Optix <span className="text-slate-500 font-medium text-sm">PRO</span></h1>
        </div>
        
        <div className="flex items-center gap-6">
          {isMock && (
            <div className="flex items-center gap-2 bg-yellow-500/10 text-yellow-500 px-3 py-1 rounded-full border border-yellow-500/20 text-xs font-semibold animate-pulse">
              <i className="fas fa-exclamation-triangle"></i>
              <span>MOCK DATA ACTIVE</span>
              <button 
                onClick={() => { MarketDataService.setMockMode(false); fetchData(); }}
                className="ml-2 hover:underline text-yellow-400"
              >
                Retry Live
              </button>
            </div>
          )}
          
          <div className="flex items-center gap-4 text-xs font-medium">
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${isMarketOpen ? 'bg-green-500' : 'bg-red-500'}`}></span>
              <span>MARKET {isMarketOpen ? 'OPEN' : 'CLOSED'}</span>
            </div>
            <div className="text-slate-400">
              {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} EST
            </div>
          </div>
        </div>
      </header>

      <main className="flex flex-1 overflow-hidden p-4 gap-4 bg-slate-950">
        {/* Left: Watchlist */}
        <div className="w-72 flex flex-col gap-4">
          <Watchlist 
            tickers={watchlist} 
            selected={selectedTicker}
            onSelect={setSelectedTicker}
            onAdd={addTicker}
            onRemove={removeTicker}
            summaries={summaries}
          />
          <SignalEngine 
            ticker={selectedTicker} 
            summary={summaries[selectedTicker]} 
            aiAnalysis={aiAnalysis}
          />
        </div>

        {/* Center: Chart & Options */}
        <div className="flex-1 flex flex-col gap-4 overflow-hidden">
          <div className="flex-1 bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden flex flex-col">
            <div className="flex items-center justify-between p-4 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <h2 className="text-lg font-bold">{selectedTicker}</h2>
                <span className={`text-sm ${summaries[selectedTicker]?.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                  ${summaries[selectedTicker]?.price.toFixed(2)} ({summaries[selectedTicker]?.changePercent.toFixed(2)}%)
                </span>
              </div>
              <div className="flex bg-slate-800 rounded-lg p-1 gap-1">
                <button 
                  onClick={() => setTimeframe(Timeframe.INTRADAY)}
                  className={`px-3 py-1 rounded text-xs transition-colors ${timeframe === Timeframe.INTRADAY ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-700'}`}
                >
                  Intraday
                </button>
                <button 
                  onClick={() => setTimeframe(Timeframe.DAILY)}
                  className={`px-3 py-1 rounded text-xs transition-colors ${timeframe === Timeframe.DAILY ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-700'}`}
                >
                  Daily
                </button>
              </div>
            </div>
            <div className="flex-1 p-4 relative">
              {loading ? (
                <div className="absolute inset-0 flex items-center justify-center bg-slate-900/80 z-10">
                  <div className="flex flex-col items-center gap-3">
                    <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                    <span className="text-sm font-medium">Syncing Terminal...</span>
                  </div>
                </div>
              ) : null}
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
