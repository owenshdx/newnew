
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
    await new Promise(r => setTimeout(r, 400)); 

    const basePrice = symbol === 'SPY' ? 500 : Math.random() * 200 + 50;
    const change = (Math.random() - 0.4) * 5;
    
    // Simulate Earnings Proximity with tiered penalties
    const earningsDays = Math.floor(Math.random() * 25);
    let earningsPenalty = 0;
    let earningsDesc = `Safe (${earningsDays}d)`;

    if (earningsDays <= 7) {
      earningsPenalty = 20;
      earningsDesc = `CRITICAL (${earningsDays}d) -20 Pnlty`;
    } else if (earningsDays <= 14) {
      earningsPenalty = 10;
      earningsDesc = `Approaching (${earningsDays}d) -10 Pnlty`;
    }
    
    // Base scores
    let callScore = Math.floor(Math.random() * 50 + 30);
    let putScore = Math.floor(Math.random() * 50 + 30);

    // Apply Penalty
    callScore = Math.max(0, callScore - earningsPenalty);
    putScore = Math.max(0, putScore - earningsPenalty);
    
    const rsiVal = Math.floor(Math.random() * 80 + 10);

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
        trend: Math.random() > 0.5 ? 'Above MA50 (+15c)' : 'Below MA50 (+15p)',
        rsiDesc: `${rsiVal} (${rsiVal < 35 ? 'Oversold +20c' : rsiVal > 65 ? 'Overbought +20p' : 'Neutral'})`,
        macdDesc: Math.random() > 0.5 ? 'Bullish Cross (+15c)' : 'Bearish Cross (+15p)',
        skewDesc: Math.random() > 0.6 ? 'Call Heavy (+15c)' : Math.random() > 0.3 ? 'Put Heavy (+15p)' : 'Balanced',
        ivDesc: Math.random() > 0.7 ? 'High Vol' : 'Normal Regime',
        earningsDesc: earningsDesc
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
        const oi = Math.random() * 3000 + 500;
        contracts.push({
          strike,
          type: type as 'CALL' | 'PUT',
          lastPrice: Math.random() * 10,
          change: (Math.random() - 0.5),
          volume: vol,
          openInterest: oi,
          impliedVolatility: Math.random() * 0.8,
          isUnusual: false 
        });
      });
    });

    const totalChainVol = contracts.reduce((acc, c) => acc + c.volume, 0);
    const avgVol = totalChainVol / contracts.length;

    return contracts.map(c => ({
      ...c,
      isUnusual: c.volume > (avgVol * 3) || (c.volume > c.openInterest * 1.5)
    })).sort((a, b) => b.volume - a.volume);
  }

  static isMarketOpen(): boolean {
    const now = new Date();
    const utcHour = now.getUTCHours();
    const utcMin = now.getUTCMinutes();
    const etHour = utcHour - 5;
    
    const day = now.getUTCDay();
    if (day === 0 || day === 6) return false;
    
    const totalMinutes = etHour * 60 + utcMin;
    return totalMinutes >= 570 && totalMinutes <= 960;
  }
}
