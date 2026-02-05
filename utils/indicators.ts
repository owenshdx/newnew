
import { PricePoint } from '../types';

export const calculateSMA = (data: PricePoint[], period: number): number[] => {
  const smas: number[] = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      smas.push(NaN);
      continue;
    }
    const slice = data.slice(i - period + 1, i + 1);
    const sum = slice.reduce((acc, curr) => acc + curr.close, 0);
    smas.push(sum / period);
  }
  return smas;
};

export const calculateRSI = (data: PricePoint[], period: number = 14): number[] => {
  const rsis: number[] = [];
  let gains = 0;
  let losses = 0;

  for (let i = 1; i < data.length; i++) {
    const diff = data[i].close - data[i - 1].close;
    if (diff >= 0) gains += diff;
    else losses -= diff;

    if (i < period) {
      rsis.push(NaN);
      continue;
    }

    if (i === period) {
      const avgGain = gains / period;
      const avgLoss = losses / period;
      const rs = avgGain / avgLoss;
      rsis.push(100 - (100 / (1 + rs)));
    } else {
      // Smoothed calculation
      const prevRsi = rsis[i - 1];
      const avgGain = (gains / period); // Simplified for mock
      const avgLoss = (losses / period);
      const rs = avgGain / avgLoss;
      rsis.push(100 - (100 / (1 + rs)));
    }
  }
  return [NaN, ...rsis];
};

export const calculateBollingerBands = (data: PricePoint[], period: number = 20, stdDev: number = 2) => {
  const upper: number[] = [];
  const lower: number[] = [];
  
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      upper.push(NaN);
      lower.push(NaN);
      continue;
    }
    const slice = data.slice(i - period + 1, i + 1);
    const mean = slice.reduce((acc, curr) => acc + curr.close, 0) / period;
    const variance = slice.reduce((acc, curr) => acc + Math.pow(curr.close - mean, 2), 0) / period;
    const sd = Math.sqrt(variance);
    upper.push(mean + (stdDev * sd));
    lower.push(mean - (stdDev * sd));
  }
  return { upper, lower };
};
