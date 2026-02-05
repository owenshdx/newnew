
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz
import os
import re

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Optix | Professional Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State
if 'data_failed' not in st.session_state:
    st.session_state.data_failed = False
if 'frozen_signals' not in st.session_state:
    st.session_state.frozen_signals = {}

# --- THEME INJECTION ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        background-color: #020617 !important;
        color: #f8fafc;
    }
    
    .stApp {
        background-color: #020617;
    }

    [data-testid="stVerticalBlock"] {
        gap: 0rem !important;
    }
    [data-testid="column"] {
        padding: 0 0.5rem !important;
    }

    .optix-card {
        background-color: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(30, 41, 59, 0.8);
        padding: 24px;
        border-radius: 14px;
        margin-bottom: 20px;
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5);
    }

    /* Mock Data Banner */
    .mock-banner {
        background: linear-gradient(90deg, rgba(217, 119, 6, 0.9) 0%, rgba(180, 83, 9, 0.9) 100%);
        border-bottom: 1px solid rgba(251, 191, 36, 0.3);
        padding: 10px 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
        font-size: 12px;
        font-weight: 600;
        margin: -1rem -5rem 2rem -5rem;
        z-index: 100;
    }
    .mock-banner i { margin-right: 8px; color: #fde68a; }

    .signal-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        height: 80px;
        gap: 20px;
        margin: 28px 0 35px 0;
    }
    .signal-bar-wrapper {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
    }
    .signal-bar {
        width: 100%;
        border-radius: 4px 4px 0 0;
        transition: height 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .signal-bar-value {
        position: absolute;
        top: -26px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 11px;
        font-weight: 900;
        letter-spacing: -0.5px;
    }
    .signal-label {
        font-size: 9px;
        font-weight: 900;
        color: #475569;
        margin-top: 14px;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }
    
    .breakdown-section {
        margin-top: 25px;
        border-top: 1px solid rgba(30, 41, 59, 1);
        padding-top: 22px;
    }
    .breakdown-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid rgba(30, 41, 59, 0.5);
    }
    .breakdown-label {
        font-size: 11px;
        color: #94a3b8;
        font-weight: 500;
    }
    .breakdown-value {
        font-size: 10px;
        font-weight: 800;
        padding: 3px 12px;
        border-radius: 4px;
        text-transform: uppercase;
    }
    
    .val-bullish { background: rgba(34, 197, 94, 0.15); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
    .val-bearish { background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    .val-neutral { background: rgba(30, 41, 59, 0.6); color: #94a3b8; border: 1px solid rgba(71, 85, 105, 0.4); }
    .val-warning { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3); }
    
    .mini-calendar {
        background: #020617;
        border: 1px solid #334155;
        border-radius: 6px;
        width: 32px;
        height: 32px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        overflow: hidden;
    }
    .mini-calendar-header {
        font-size: 5px;
        text-transform: uppercase;
        background: rgba(239, 68, 68, 1);
        color: white;
        font-weight: 900;
        width: 100%;
        text-align: center;
        padding: 2px 0;
    }
    .mini-calendar-body {
        font-size: 11px;
        font-weight: 800;
        color: #f1f5f9;
        flex: 1;
        display: flex;
        align-items: center;
    }

    .cognitive-layer {
        margin-top: 24px;
        padding-top: 22px;
        border-top: 1px solid rgba(30, 41, 59, 1);
    }

    .terminal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 15px 0 30px 0;
        margin-bottom: 10px;
        border-bottom: 1px solid rgba(30, 41, 59, 0.8);
    }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- MARKET LOGIC ---
def get_market_status():
    tz = pytz.timezone('US/Eastern')
    now = datetime.now(tz)
    day = now.weekday()
    if day >= 5: return False, "CLOSED (Weekend)"
    m_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    m_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    if m_open <= now <= m_close:
        return True, "OPEN"
    return False, f"CLOSED ({'After Hours' if now > m_close else 'Pre-Market'})"

# --- DATA RELIABILITY ENGINE ---
@st.cache_data(ttl=60)
def fetch_raw_history(symbol, period="5d", interval="1m"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df is None or df.empty:
            raise ValueError("No data returned from yfinance")
        return df, False
    except Exception as e:
        # LOGGING
        print(f"yfinance fetch error for {symbol}: {str(e)}")
        # FALLBACK TO DETERMINISTIC MOCK DATA
        np.random.seed(abs(hash(symbol)) % 10000)
        base = 150.0 if symbol != 'SPY' else 500.0
        dates = pd.date_range(end=datetime.now(), periods=100, freq='15min')
        prices = base + np.cumsum(np.random.normal(0, 0.5, 100))
        mock_df = pd.DataFrame({
            'Open': prices-0.3, 'High': prices+0.6, 'Low': prices-0.6, 
            'Close': prices, 'Volume': np.random.randint(10000, 1000000, 100)
        }, index=dates)
        return mock_df, True

@st.cache_data(ttl=300)
def fetch_raw_options(symbol):
    try:
        ticker = yf.Ticker(symbol)
        if not ticker.options:
            raise ValueError("No options found")
        expiry = ticker.options[0]
        chain = ticker.option_chain(expiry)
        return {'calls': chain.calls, 'puts': chain.puts}, False
    except Exception as e:
        print(f"Options fetch error for {symbol}: {str(e)}")
        strikes = [150 + i for i in range(-5, 6)]
        def mock_c(): return pd.DataFrame({
            'strike': strikes, 'lastPrice': np.random.uniform(1, 5, 11), 
            'volume': np.random.randint(10, 5000, 11), 
            'openInterest': np.random.randint(100, 10000, 11), 
            'impliedVolatility': np.random.uniform(0.2, 0.8, 11)
        })
        return {'calls': mock_c(), 'puts': mock_c()}, True

@st.cache_data(ttl=3600)
def fetch_raw_earnings(symbol):
    try:
        ticker = yf.Ticker(symbol)
        cal = ticker.calendar
        if cal is not None:
            ed = cal['Earnings Date'][0] if isinstance(cal, dict) else cal.iloc[0, 0]
            if ed and isinstance(ed, (datetime, pd.Timestamp)):
                return max(0, (ed.date() - datetime.now().date()).days), False
        return 99, False
    except:
        return 99, True

def calculate_indicators(df):
    if df is None or df.empty: return df
    df = df.copy()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

def get_scores(df, options, earnings_days, symbol):
    is_open, _ = get_market_status()
    if not is_open and symbol in st.session_state.frozen_signals:
        return st.session_state.frozen_signals[symbol]
    
    if df is None or len(df) < 2: return 0, 0, "Wait", {}
    
    latest = df.iloc[-1]
    b = {'trend': 'Neutral', 'rsi': 'Neutral', 'macdDesc': 'Neutral', 'volume': 'Balanced', 'iv': 'Normal Regime', 'earningsDesc': 'Safe'}
    c_score, p_score = 30, 30 
    
    sma50 = latest.get('SMA50', latest['Close'])
    if latest['Close'] > (sma50 * 1.002): 
        c_score += 15
        b['trend'] = "Above MA50 (+15c)"
    elif latest['Close'] < (sma50 * 0.998): 
        p_score += 15
        b['trend'] = "Below MA50 (+15p)"
    
    rsi = latest.get('RSI', 50)
    if rsi < 35: 
        c_score += 15
        b['rsi'] = f"{int(rsi)} Oversold (+15c)"
    elif rsi > 65: 
        p_score += 15
        b['rsi'] = f"{int(rsi)} Overbought (+15p)"
    else: 
        b['rsi'] = f"{int(rsi)} Neutral"

    macd = latest.get('MACD', 0)
    sig_line = latest.get('Signal_Line', 0)
    if macd > sig_line:
        c_score += 15
        b['macdDesc'] = "Bullish Cross (+15c)"
    elif macd < sig_line:
        p_score += 15
        b['macdDesc'] = "Bearish Cross (+15p)"

    if options:
        c_v, p_v = options['calls']['volume'].sum(), options['puts']['volume'].sum()
        total_v = c_v + p_v
        if total_v > 0:
            c_pct = (c_v / total_v) * 100
            if c_pct > 60: 
                c_score += 20
                b['volume'] = "Call Heavy (+20c)"
            elif c_pct < 40: 
                p_score += 20
                b['volume'] = "Put Heavy (+20p)"
            else: 
                b['volume'] = f"Balanced ({int(c_pct)}% Call)"

    if earnings_days <= 7:
        c_score -= 25; p_score -= 25
        b['earningsDesc'] = f"CRITICAL ({earnings_days}d) -25 Pnlty"
    else: 
        b['earningsDesc'] = f"Safe ({earnings_days}d)"

    c_s, p_s = max(0, min(100, c_score)), max(0, min(100, p_score))
    max_val = max(c_s, p_s)
    if max_val >= 80: strength = "Strong"
    elif max_val >= 60: strength = "Moderate"
    else: strength = "Weak"
    
    res = (int(c_s), int(p_s), strength, b)
    if is_open: st.session_state.frozen_signals[symbol] = res
    return res

# --- APP UI ---
def main():
    # DATA LOADING WITH ERROR TRACKING
    st.sidebar.markdown("<div style='font-size: 8px; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: 2px; margin-bottom: 20px;'>Market Directory</div>", unsafe_allow_html=True)
    if 'watchlist' not in st.session_state: st.session_state.watchlist = ["AAPL", "TSLA", "SPY", "NFLX", "AMZN", "GOOGL"]
    selected_ticker = st.sidebar.selectbox("WATCHLIST", st.session_state.watchlist, label_visibility="collapsed")
    
    # REFRESH ACTION
    if st.sidebar.button("Force Global Refresh"):
        st.cache_data.clear()
        st.rerun()

    # CORE FETCH
    df_raw, df_is_mock = fetch_raw_history(selected_ticker)
    opts_raw, opts_is_mock = fetch_raw_options(selected_ticker)
    ed_raw, ed_is_mock = fetch_raw_earnings(selected_ticker)
    
    # Update state for UI
    st.session_state.data_failed = any([df_is_mock, opts_is_mock])

    # Header
    isOpen, status_str = get_market_status()
    st.markdown(f"""
        <div class="terminal-header">
            <div style="display: flex; align-items: center; gap: 16px;">
                <div style="background-color: #2563eb; width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 900; color: white; font-size: 1.2rem; box-shadow: 0 4px 15px rgba(37, 99, 235, 0.4);">O</div>
                <h1 style="font-size: 1.6rem; font-weight: 800; margin: 0; letter-spacing: -1px; color: #f8fafc;">Optix <span style="color: #475569; font-weight: 600; font-size: 0.85rem; letter-spacing: 1px; margin-left: 12px; text-transform: uppercase;">PRO TERMINAL</span></h1>
            </div>
            <div style="font-size: 10px; font-weight: 800; padding: 6px 16px; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.8px; background-color: {'rgba(34, 197, 94, 0.1)' if isOpen else 'rgba(239, 68, 68, 0.1)'}; color: {'#4ade80' if isOpen else '#f87171'}; border: 1px solid {'rgba(34, 197, 94, 0.3)' if isOpen else 'rgba(239, 68, 68, 0.3)'};">● {status_str}</div>
        </div>
    """, unsafe_allow_html=True)

    # DATA SOURCE BANNER
    if st.session_state.data_failed:
        col_banner_text, col_banner_btn = st.columns([4, 1])
        with col_banner_text:
            st.markdown("""
                <div style="background: rgba(180, 83, 9, 0.2); border: 1px solid rgba(251, 191, 36, 0.3); border-radius: 8px; padding: 12px 20px; color: #fbbf24; display: flex; align-items: center; font-size: 11px; margin-bottom: 20px;">
                    <span style="font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-right: 12px;">MOCK DATA ACTIVE</span>
                    <span>Live yfinance connection failed. Showing deterministic simulation.</span>
                </div>
            """, unsafe_allow_html=True)
        with col_banner_btn:
            if st.button("RETRY LIVE DATA", type="primary", use_container_width=True):
                st.cache_data.clear()
                st.rerun()

    col_left, col_right = st.columns([1, 2.8])
    df = calculate_indicators(df_raw)
    c_s, p_s, strength, b = get_scores(df, opts_raw, ed_raw, selected_ticker)

    with col_left:
        def get_cls(val):
            v = str(val).lower()
            if any(x in v for x in ['+15c', '+20c', 'bullish', 'oversold', 'call heavy']): return 'val-bullish'
            if any(x in v for x in ['+15p', '+20p', 'bearish', 'overbought', 'put heavy']): return 'val-bearish'
            if any(x in v for x in ['pnlty', 'critical', 'approaching']): return 'val-warning'
            return 'val-neutral'

        dm = re.search(r'\((\d+)d\)', b['earningsDesc']); days_v = dm.group(1) if dm else "?"

        st.markdown(f"""
            <div class="optix-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <div>
                        <div style="font-size: 10px; font-weight: 900; color: #64748b; letter-spacing: 1.8px; text-transform: uppercase;">Signal Engine</div>
                        <div style="font-size: 8px; color: #475569; font-weight: 600; margin-top: 3px; letter-spacing: 0.5px;">WEIGHTED ANALYSIS</div>
                    </div>
                    <span style="font-size: 9px; font-weight: 900; background: { '#2563eb' if strength == 'Strong' else '#1e293b' }; color: { '#fff' if strength == 'Strong' else '#94a3b8' }; padding: 5px 14px; border-radius: 20px; box-shadow: { '0 4px 15px rgba(37, 99, 235, 0.3)' if strength == 'Strong' else 'none' };">{strength.upper()}</span>
                </div>
                
                <div class="signal-container">
                    <div class="signal-bar-wrapper">
                        <span class="signal-bar-value" style="color:#4ade80;">{c_s}%</span>
                        <div class="signal-bar" style="height: {c_s}%; background: rgba(34, 197, 94, 0.2); border-top: 3px solid #22c55e;"></div>
                        <div class="signal-label">CALL BIAS</div>
                    </div>
                    <div class="signal-bar-wrapper">
                        <span class="signal-bar-value" style="color:#f87171;">{p_s}%</span>
                        <div class="signal-bar" style="height: {p_s}%; background: rgba(239, 68, 68, 0.2); border-top: 3px solid #ef4444;"></div>
                        <div class="signal-label">PUT BIAS</div>
                    </div>
                </div>
                
                <div class="breakdown-section">
                    <div class="breakdown-item"><span class="breakdown-label">Trend (MA50)</span><span class="breakdown-value {get_cls(b['trend'])}">{b['trend']}</span></div>
                    <div class="breakdown-item"><span class="breakdown-label">RSI Strategy</span><span class="breakdown-value {get_cls(b['rsi'])}">{b['rsi']}</span></div>
                    <div class="breakdown-item"><span class="breakdown-label">MACD Cross</span><span class="breakdown-value {get_cls(b['macdDesc'])}">{b['macdDesc']}</span></div>
                    <div class="breakdown-item"><span class="breakdown-label">Option Flow</span><span class="breakdown-value {get_cls(b['volume'])}">{b['volume']}</span></div>
                    <div class="breakdown-item">
                        <span class="breakdown-label">Earnings Prox</span>
                        <div style="display: flex; align-items: center; gap: 12px;">
                            <div class="mini-calendar"><span class="mini-calendar-header">Days</span><span class="mini-calendar-body">{days_v}</span></div>
                            <span class="breakdown-value {get_cls(b['earningsDesc'])}">{b['earningsDesc']}</span>
                        </div>
                    </div>
                    <div class="breakdown-item" style="border-bottom: none;"><span class="breakdown-label">IV Regime</span><span class="breakdown-value {get_cls(b['iv'])}">{b['iv']}</span></div>
                </div>

                <div class="cognitive-layer">
                    <div style="font-size: 10px; font-weight: 900; color: #3b82f6; margin-bottom: 12px; letter-spacing: 0.6px; text-transform: uppercase;">COGNITIVE LAYER</div>
                    <p style="font-size: 11px; color: #94a3b8; font-style: italic; line-height: 1.7;">High-fidelity multi-factor alignment suggests {strength.lower()} conviction for {selected_ticker}. RSI and MACD metrics currently driving bias calculation.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if df is not None:
            price = df['Close'].iloc[-1]
            st.markdown(f"""
                <div class="optix-card" style="padding: 20px;">
                    <div style="font-size: 0.75rem; font-weight: 900; color: #475569; margin-bottom: 8px; letter-spacing: 1.5px; text-transform: uppercase;">{selected_ticker} Spot</div>
                    <div style="font-size: 2.1rem; font-weight: 900; color: #f1f5f9; letter-spacing: -1.5px; line-height: 1;">${price:.2f}</div>
                </div>
            """, unsafe_allow_html=True)

    with col_right:
        if df is not None:
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.72, 0.28])
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#22c55e', decreasing_line_color='#ef4444', increasing_fillcolor='#22c55e', decreasing_fillcolor='#ef4444', opacity=0.9), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], mode='lines', line=dict(color='#fbbf24', width=2), name="SMA 50"), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], mode='lines', line=dict(color='#3b82f6', width=1.5), name="RSI"), row=2, col=1)
            fig.add_hline(y=70, line_dash="dash", line_color="rgba(239, 68, 68, 0.35)", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="rgba(34, 197, 94, 0.35)", row=2, col=1)
            fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=550, xaxis_rangeslider_visible=False, margin=dict(l=0, r=40, t=10, b=10), showlegend=False, hovermode='x unified', font=dict(family="Inter", size=10))
            fig.update_yaxes(showgrid=True, gridcolor='rgba(30, 41, 59, 0.5)', side='right', tickfont=dict(color='#64748b'), row=1, col=1)
            fig.update_yaxes(showgrid=True, gridcolor='rgba(30, 41, 59, 0.5)', side='right', tickfont=dict(color='#64748b'), range=[0, 100], row=2, col=1)
            st.markdown('<div class="optix-card" style="padding: 12px; height: 580px;">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        if opts_raw:
            st.markdown('<div class="optix-card" style="padding: 0; overflow: hidden; height: 380px;">', unsafe_allow_html=True)
            t1, t2 = st.tabs(["CALL FLOW", "PUT FLOW"])
            cols = ['strike', 'lastPrice', 'volume', 'openInterest', 'impliedVolatility']
            with t1: st.dataframe(opts_raw['calls'][cols].head(15), use_container_width=True)
            with t2: st.dataframe(opts_raw['puts'][cols].head(15), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
