
export interface PricePoint {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  ma50?: number;
  bbUpper?: number;
  bbLower?: number;
  rsi?: number;
  macd?: number;
  signal?: number;
}

export interface OptionContract {
  strike: number;
  type: 'CALL' | 'PUT';
  lastPrice: number;
  change: number;
  volume: number;
  openInterest: number;
  impliedVolatility: number;
  isUnusual: boolean;
}

export interface TickerSummary {
  symbol: string;
  price: number;
  change: number;
  changePercent: number;
  avgIv: number;
  callScore: number;
  putScore: number;
  signalClass: 'Strong' | 'Moderate' | 'Weak';
  scoreBreakdown: {
    technical: number;
    options: number;
    volatility: number;
    // Descriptive factors
    trend: string;
    rsiDesc: string;
    macdDesc: string;
    skewDesc: string;
    ivDesc: string;
  };
}

export interface SignalLog {
  timestamp: string;
  symbol: string;
  price: number;
  callScore: number;
  putScore: number;
  signal: string;
}

export enum Timeframe {
  INTRADAY = '1m',
  DAILY = '1d'
}
