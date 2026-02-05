
import { GoogleGenAI, Type } from "@google/genai";
import { TickerSummary, PricePoint, OptionContract } from "../types";

const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

export async function generateAisignal(
  ticker: string,
  priceData: PricePoint[],
  options: OptionContract[]
): Promise<string> {
  const latestPrice = priceData[priceData.length - 1];
  const prompt = `
    Act as a pro options floor trader. Analyze ${ticker}:
    Price: $${latestPrice.close.toFixed(2)}
    Latest RSI: ${latestPrice.rsi?.toFixed(2) || 'N/A'}
    Technical: Price vs MA50 is ${latestPrice.close > (latestPrice.ma50 || 0) ? 'Above' : 'Below'}.
    Options Activity: ${options.filter(o => o.isUnusual).length} unusual contracts detected.
    
    Provide a concise (2-sentence) tactical trade recommendation (Call/Put/Neutral) with institutional-level reasoning.
  `;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-pro-preview',
      contents: prompt,
      config: {
        temperature: 0.6,
        maxOutputTokens: 150
      }
    });

    return response.text || "Unable to generate AI signal at this time.";
  } catch (error) {
    console.error("Gemini Error:", error);
    return "Market analysis temporarily unavailable. Check technicals manually.";
  }
}
