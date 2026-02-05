
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import pytz
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Optix: Professional Options Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Professional Dark Theme
st.markdown("""
    <style>
    .main { background-color: #0d1117; color: #c9d1d9; }
    .stMetric { background-color: #161b22; border: 1px solid #30363d; padding: 15px; border-radius: 8px; }
    div[data-testid="stExpander"] { border: 1px solid #30363d; background-color: #0d1117; }
    .signal-badge { font-weight: bold; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; }
    .strong-call { background-color: #238636; color: white; }
    .strong-put { background-color: #da3633; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=60)
def get_history_data(symbol, period="5d", interval="1m"):
    """Fetches real-time intraday price data from Yahoo Finance."""
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            # Fallback to daily if intraday is unavailable (e.g. historical gaps)
            df = ticker.history(period="1mo", interval="1d")
        return df
    except Exception as e:
        return None

@st.cache_data(ttl=300)
def get_options_data(symbol):
    """Fetches the nearest expiry options chain data."""
    try:
        ticker = yf.Ticker(symbol)
        if not ticker.options:
            return None
        
        # Get the nearest expiration date
        expiry = ticker.options[0]
        chain = ticker.option_chain(expiry)
        
        # Convert to serializable dict of dataframes
        return {
            'calls': chain.calls,
            'puts': chain.puts,
            'expiry': expiry
        }
    except Exception as e:
        return None

def calculate_technical_indicators(df):
    """Computes technical markers for the signal engine."""
    if df is None or df.empty:
        return df
        
    # 50-period Moving Average
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    
    # RSI (14)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # Bollinger Bands (20, 2)
    df['BB_Mid'] = df['Close'].rolling(window=20).mean()
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Mid'] + (df['BB_Std'] * 2)
    df['BB_Lower'] = df['BB_Mid'] - (df['BB_Std'] * 2)
    
    # MACD (12, 26, 9)
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    return df

# --- SIGNAL ENGINE ---
def generate_signals(df, options_data):
    """Computes a multi-factor score for trade bias."""
    if df is None or len(df) < 50: 
        return 0, 0, "Wait for data..."
    
    latest = df.iloc[-1]
    call_score = 0
    put_score = 0
    
    # 1. Price vs MA (Trend Following)
    if latest['Close'] > latest['SMA50']: 
        call_score += 20
    else: 
        put_score += 20
    
    # 2. RSI Trend (Mean Reversion)
    if pd.notnull(latest['RSI']):
        if latest['RSI'] < 35: 
            call_score += 25 # Oversold
        elif latest['RSI'] > 65: 
            put_score += 25 # Overbought
    
    # 3. MACD Momentum
    if pd.notnull(latest['MACD']) and pd.notnull(latest['MACD_Signal']):
        if latest['MACD'] > latest['MACD_Signal']: 
            call_score += 15
        else: 
            put_score += 15
    
    # 4. Options Volume Skew
    if options_data is not None:
        call_vol = options_data['calls']['volume'].sum()
        put_vol = options_data['puts']['volume'].sum()
        if call_vol > put_vol: 
            call_score += 20
        else: 
            put_score += 20
            
    # Normalize scores
    total = call_score + put_score
    if total > 0:
        call_pct = int((call_score / 80) * 100)
        put_pct = int((put_score / 80) * 100)
    else:
        call_pct, put_pct = 0, 0

    status = "Weak"
    if call_pct >= 80 or put_pct >= 80: 
        status = "Strong"
    elif call_pct >= 60 or put_pct >= 60: 
        status = "Moderate"
    
    return min(call_pct, 100), min(put_pct, 100), status

# --- MARKET HOURS LOGIC ---
def get_market_status():
    tz = pytz.timezone('US/Eastern')
    now = datetime.now(tz)
    if now.weekday() >= 5: 
        return False, "Closed (Weekend)"
    
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    
    if market_open <= now <= market_close:
        return True, "Open"
    return False, "Closed (Market Hours: 9:30-16:00 ET)"

# --- APP UI ---
def main():
    # Sidebar: Watchlist Management
    st.sidebar.title("📁 Watchlist")
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = ["AAPL", "TSLA", "SPY", "NFLX", "AMZN", "GOOGL", "IWM"]
    
    new_ticker = st.sidebar.text_input("Add Symbol").upper().strip()
    if st.sidebar.button("Add Ticker"):
        if new_ticker and new_ticker not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_ticker)
            st.rerun()
            
    selected_ticker = st.sidebar.selectbox("Active Analysis", st.session_state.watchlist)
    
    if st.sidebar.button("Remove Selected"):
        if len(st.session_state.watchlist) > 1:
            st.session_state.watchlist.remove(selected_ticker)
            st.rerun()

    # Header
    isOpen, status_str = get_market_status()
    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        st.title(f"🚀 Analysis: {selected_ticker}")
    with col_h2:
        st.write(f"**Market Status:** {status_str}")

    # Data Loading
    df = get_history_data(selected_ticker)
    options_info = get_options_data(selected_ticker)
    
    if df is not None and not df.empty:
        df = calculate_technical_indicators(df)
        
        # Top Metrics
        c1, c2, c3, c4 = st.columns(4)
        call_s, put_s, strength = generate_signals(df, options_info)
        
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2] if len(df) > 1 else current_price
        price_diff = current_price - prev_price
        
        c1.metric("Current Price", f"${current_price:.2f}", f"{price_diff:.2f}")
        c2.metric("RSI (14)", f"{df['RSI'].iloc[-1]:.1f}" if pd.notnull(df['RSI'].iloc[-1]) else "N/A")
        c3.metric("Call Score", f"{call_s}%")
        c4.metric("Put Score", f"{put_s}%")

        # Visual Signal Badge
        if strength == "Strong":
            color = "#238636" if call_s > put_s else "#da3633"
            bias = "CALL (Bullish)" if call_s > put_s else "PUT (Bearish)"
            st.markdown(f"<div style='background-color:{color}; padding:15px; border-radius:8px; text-align:center; color:white; font-weight:bold; margin-bottom: 20px;'>🔥 STRONG SIGNAL DETECTED: {bias}</div>", unsafe_allow_html=True)
        
        # Main Chart
        st.subheader("Interactive Price History & Indicators")
        fig = go.Figure()
        fig.add_trace(go.Candlestick(
            x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
            name="Candlesticks"
        ))
        
        if 'SMA50' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='#3b82f6', width=2), name="SMA 50"))
        
        if 'BB_Upper' in df.columns and 'BB_Lower' in df.columns:
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='rgba(75, 85, 99, 0.3)', width=1, dash='dash'), name="BB Upper"))
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='rgba(75, 85, 99, 0.3)', width=1, dash='dash'), name="BB Lower", fill='tonexty', fillcolor='rgba(75, 85, 99, 0.1)'))
        
        fig.update_layout(
            template="plotly_dark",
            height=600,
            xaxis_rangeslider_visible=False,
            margin=dict(l=0, r=0, t=30, b=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Options Table
        if options_info:
            st.subheader(f"Flow: Top Volume Contracts ({options_info['expiry']})")
            calls = options_info['calls'].sort_values('volume', ascending=False).head(8)
            puts = options_info['puts'].sort_values('volume', ascending=False).head(8)
            
            tab1, tab2 = st.tabs(["📞 Calls", "📉 Puts"])
            with tab1:
                st.dataframe(calls[['strike', 'lastPrice', 'volume', 'openInterest', 'impliedVolatility']], use_container_width=True)
            with tab2:
                st.dataframe(puts[['strike', 'lastPrice', 'volume', 'openInterest', 'impliedVolatility']], use_container_width=True)

        # Signal Logging
        st.sidebar.divider()
        if st.sidebar.button("💾 Log Current Signal"):
            log_entry = {
                'Time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'Ticker': selected_ticker,
                'Call_Score': call_s,
                'Put_Score': put_s,
                'Price': f"{current_price:.2f}",
                'Strength': strength
            }
            log_df = pd.DataFrame([log_entry])
            log_file = 'signals_log.csv'
            if not os.path.isfile(log_file):
                log_df.to_csv(log_file, index=False)
            else:
                log_df.to_csv(log_file, mode='a', header=False, index=False)
            st.sidebar.success(f"Logged {selected_ticker} signal.")

    else:
        st.error(f"No data found for {selected_ticker}. This may be due to ticker availability or API limits.")
        st.info("Try a major index like SPY or QQQ to verify your connection.")

if __name__ == "__main__":
    main()
