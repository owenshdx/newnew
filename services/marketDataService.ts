
import { PricePoint, OptionContract, TickerSummary, Timeframe } from '../types';
import { calculateSMA, calculateRSI, calculateBollingerBands } from '../utils/indicators';

const MOCK_TICKERS = ['AAPL', 'TSLA', 'SPY', 'NFLX', 'AMZN', 'GOOGL', 'IWM'];

export class MarketDataService {
  private static useMock = false;

  static setMockMode(mode: boolean) {
    this.useMock = mode;
  }

  static isMockMode() {
    return this.useMock;
  }

  static async fetchTickerSummary(symbol: string): Promise<TickerSummary> {
    // In a real app, this would be an API call to a backend proxying yfinance.
    // Here we simulate the deterministic mock behavior or a "live" fetch.
    await new Promise(r => setTimeout(r, 400)); // Simulate latency

    const basePrice = symbol === 'SPY' ? 500 : Math.random() * 200 + 50;
    const change = (Math.random() - 0.4) * 5;
    const callScore = Math.floor(Math.random() * 100);
    const putScore = 100 - callScore;

    return {
      symbol,
      price: basePrice,
      change: change,
      changePercent: (change / basePrice) * 100,
      avgIv: Math.random() * 0.5 + 0.2,
      callScore,
      putScore,
      signalClass: callScore > 80 || putScore > 80 ? 'Strong' : callScore > 60 || putScore > 60 ? 'Moderate' : 'Weak',
      scoreBreakdown: {
        technical: Math.random() * 100,
        options: Math.random() * 100,
        volatility: Math.random() * 100,
      }
    };
  }

  static generateHistory(symbol: string, timeframe: Timeframe): PricePoint[] {
    const points: PricePoint[] = [];
    let price = symbol === 'SPY' ? 500 : 150;
    const count = timeframe === Timeframe.INTRADAY ? 60 : 100;
    const now = new Date();

    for (let i = 0; i < count; i++) {
      const time = new Date(now.getTime() - (count - i) * (timeframe === Timeframe.INTRADAY ? 60000 : 86400000));
      const open = price + (Math.random() - 0.5) * 2;
      const close = open + (Math.random() - 0.5) * 2;
      const high = Math.max(open, close) + Math.random();
      const low = Math.min(open, close) - Math.random();
      
      points.push({
        time: time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        open, high, low, close,
        volume: Math.random() * 1000000
      });
      price = close;
    }

    // Add indicators
    const smas = calculateSMA(points, 50);
    const rsis = calculateRSI(points, 14);
    const bbs = calculateBollingerBands(points, 20, 2);

    return points.map((p, idx) => ({
      ...p,
      ma50: smas[idx],
      rsi: rsis[idx],
      bbUpper: bbs.upper[idx],
      bbLower: bbs.lower[idx]
    }));
  }

  static fetchOptionsChain(symbol: string): OptionContract[] {
    const contracts: OptionContract[] = [];
    const basePrice = 150;
    const strikes = [basePrice - 10, basePrice - 5, basePrice, basePrice + 5, basePrice + 10];

    strikes.forEach(strike => {
      ['CALL', 'PUT'].forEach(type => {
        const vol = Math.random() * 5000;
        contracts.push({
          strike,
          type: type as 'CALL' | 'PUT',
          lastPrice: Math.random() * 10,
          change: (Math.random() - 0.5),
          volume: vol,
          openInterest: Math.random() * 10000,
          impliedVolatility: Math.random() * 0.8,
          isUnusual: vol > 4000
        });
      });
    });

    return contracts.sort((a, b) => b.volume - a.volume);
  }

  static isMarketOpen(): boolean {
    const now = new Date();
    // Simplified US Market Hours: 9:30 AM - 4:00 PM ET
    // We'll use local time as a proxy or UTC conversion
    const utcHour = now.getUTCHours();
    const utcMin = now.getUTCMinutes();
    const etHour = utcHour - 5; // Eastern Standard Time (no DST adjustment for simple logic)
    
    const day = now.getUTCDay();
    if (day === 0 || day === 6) return false; // Weekend
    
    const totalMinutes = etHour * 60 + utcMin;
    return totalMinutes >= 570 && totalMinutes <= 960; // 9:30 - 16:00
  }
}
