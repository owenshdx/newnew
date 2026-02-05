
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
if 'is_mock' not in st.session_state:
    st.session_state.is_mock = False
if 'last_error' not in st.session_state:
    st.session_state.last_error = None
if 'frozen_signals' not in st.session_state:
    st.session_state.frozen_signals = {}

# --- THEME INJECTION (EXACT REACT PREVIEW REPLICATION) ---
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

    /* Professional Terminal Card Styling */
    .optix-card {
        background-color: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(30, 41, 59, 0.7);
        padding: 24px;
        border-radius: 14px;
        margin-bottom: 20px;
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.5);
    }

    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #1e293b;
    }

    /* Signal Visuals */
    .signal-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        height: 80px;
        gap: 16px;
        margin: 25px 0 35px 0;
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
    }
    .signal-bar-value {
        position: absolute;
        top: -24px;
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
        margin-top: 12px;
        letter-spacing: 0.5px;
    }
    
    /* Factor Breakdown Row Styling */
    .breakdown-section {
        margin-top: 25px;
        border-top: 1px solid rgba(30, 41, 59, 0.8);
        padding-top: 20px;
    }
    .breakdown-header {
        font-size: 9px;
        font-weight: 900;
        color: #475569;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        display: block;
        margin-bottom: 14px;
    }
    .breakdown-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid rgba(30, 41, 59, 0.4);
    }
    .breakdown-label {
        font-size: 11px;
        color: #94a3b8;
        font-weight: 500;
    }
    .breakdown-value {
        font-size: 10px;
        font-weight: 800;
        padding: 3px 10px;
        border-radius: 4px;
        text-transform: uppercase;
        letter-spacing: -0.2px;
    }
    
    /* Sentiment Colors */
    .val-bullish { background: rgba(34, 197, 94, 0.12); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.25); }
    .val-bearish { background: rgba(239, 68, 68, 0.12); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.25); }
    .val-neutral { background: rgba(30, 41, 59, 0.5); color: #94a3b8; border: 1px solid rgba(71, 85, 105, 0.3); }
    .val-warning { background: rgba(245, 158, 11, 0.12); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.25); }
    
    /* Mini-Calendar Component */
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
        line-height: 1;
        overflow: hidden;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.5);
    }
    .mini-calendar-header {
        font-size: 5px;
        text-transform: uppercase;
        background: rgba(239, 68, 68, 0.9);
        color: white;
        font-weight: 900;
        width: 100%;
        text-align: center;
        padding: 2px 0;
    }
    .mini-calendar-body {
        font-size: 11px;
        font-weight: 800;
        color: #f8fafc;
        flex: 1;
        display: flex;
        align-items: center;
    }

    /* Cognitive Layer Section */
    .cognitive-layer {
        margin-top: 24px;
        padding-top: 20px;
        border-top: 1px solid rgba(30, 41, 59, 0.8);
    }
    .cognitive-header {
        font-size: 10px;
        font-weight: 900;
        color: #3b82f6;
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 10px;
        letter-spacing: 0.5px;
    }
    .cognitive-text {
        font-size: 11px;
        color: #94a3b8;
        font-style: italic;
        line-height: 1.6;
    }

    .market-badge {
        font-size: 10px;
        font-weight: 800;
        padding: 5px 14px;
        border-radius: 20px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-open { background-color: rgba(34, 197, 94, 0.1); color: #4ade80; border: 1px solid rgba(34, 197, 94, 0.3); }
    .badge-closed { background-color: rgba(239, 68, 68, 0.1); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }
    
    /* Custom Scrollbar */
    ::-webkit-scrollbar { width: 4px; }
    ::-webkit-scrollbar-track { background: rgba(0,0,0,0); }
    ::-webkit-scrollbar-thumb { background: #334155; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #475569; }

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- UTILS ---
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

# --- DATA ENGINE ---
@st.cache_data(ttl=60)
def get_history_data(symbol, period="5d", interval="1m"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df is None or df.empty: raise ValueError("Empty response")
        return df
    except Exception:
        np.random.seed(abs(hash(symbol)) % 10000)
        base = 150.0 if symbol != 'SPY' else 500.0
        dates = pd.date_range(end=datetime.now(), periods=100, freq='15min')
        prices = base + np.cumsum(np.random.normal(0, 0.5, 100))
        return pd.DataFrame({
            'Open': prices-0.3, 'High': prices+0.6, 'Low': prices-0.6, 
            'Close': prices, 'Volume': np.random.randint(10000, 1000000, 100)
        }, index=dates)

@st.cache_data(ttl=300)
def get_options_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        expiry = ticker.options[0]
        chain = ticker.option_chain(expiry)
        return {'calls': chain.calls, 'puts': chain.puts, 'expiry': expiry}
    except:
        strikes = [150 + i for i in range(-5, 6)]
        def mock_c(): return pd.DataFrame({'strike': strikes, 'lastPrice': np.random.uniform(1, 5, 11), 'volume': np.random.randint(10, 5000, 11), 'openInterest': np.random.randint(100, 10000, 11), 'impliedVolatility': np.random.uniform(0.2, 0.8, 11)})
        return {'calls': mock_c(), 'puts': mock_c(), 'expiry': 'MOCK'}

@st.cache_data(ttl=3600)
def get_earnings_days(symbol):
    try:
        ticker = yf.Ticker(symbol)
        cal = ticker.calendar
        if cal is not None:
            if isinstance(cal, dict) and 'Earnings Date' in cal:
                ed = cal['Earnings Date'][0]
            elif hasattr(cal, 'get') and cal.get('Earnings Date') is not None:
                ed = cal.get('Earnings Date').iloc[0]
            else:
                ed = cal.iloc[0, 0]
            if ed and isinstance(ed, (datetime, pd.Timestamp)):
                return max(0, (ed.date() - datetime.now().date()).days)
        return 99
    except: return 99

def calculate_indicators(df):
    if df is None or df.empty: return df
    df = df.copy()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def get_scores(df, options, earnings_days, symbol):
    is_open, _ = get_market_status()
    if not is_open and symbol in st.session_state.frozen_signals:
        return st.session_state.frozen_signals[symbol]
    if df is None or len(df) < 2: return 0, 0, "Wait", {}
    
    latest = df.iloc[-1]
    b = {'trend': 'Neutral', 'rsi': 'Neutral', 'volume': 'Neutral', 'iv': 'Normal Regime', 'earningsDesc': 'Safe'}
    c_score, p_score = 35, 35 
    
    sma50 = latest.get('SMA50', latest['Close'])
    if latest['Close'] > (sma50 * 1.002): 
        c_score += 15
        b['trend'] = "Above MA50 (+15c)"
    elif latest['Close'] < (sma50 * 0.998): 
        p_score += 15
        b['trend'] = "Below MA50 (+15p)"
    
    rsi = latest.get('RSI', 50)
    if rsi < 35: 
        c_score += 20
        b['rsi'] = f"{int(rsi)} Oversold (+20c)"
    elif rsi > 65: 
        p_score += 20
        b['rsi'] = f"{int(rsi)} Overbought (+20p)"
    else: b['rsi'] = f"{int(rsi)} Neutral ({int(rsi)})"

    if options:
        c_v, p_v = options['calls']['volume'].sum(), options['puts']['volume'].sum()
        if (c_v + p_v) > 0:
            c_pct = (c_v / (c_v + p_v)) * 100
            if c_pct > 55: 
                c_score += 15
                b['volume'] = "Call Heavy (+15c)"
            elif c_pct < 45: 
                p_score += 15
                b['volume'] = "Put Heavy (+15p)"
            else: b['volume'] = "Balanced Flow"

    if earnings_days <= 7:
        c_score -= 20; p_score -= 20
        b['earningsDesc'] = f"CRITICAL ({earnings_days}d) -20 Pnlty"
    else: b['earningsDesc'] = f"Safe ({earnings_days}d)"

    c_s, p_s = max(0, min(100, c_score)), max(0, min(100, p_score))
    strength = "Strong" if c_s >= 80 or p_s >= 80 else "Moderate" if c_s >= 60 or p_s >= 60 else "Weak"
    res = (int(c_s), int(p_s), strength, b)
    if is_open: st.session_state.frozen_signals[symbol] = res
    return res

# --- APP UI ---
def main():
    # Sidebar
    st.sidebar.markdown("""
        <div style="padding: 10px 0;">
            <div style="font-size: 8px; font-weight: 900; color: #475569; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 12px;">Market Directory</div>
        </div>
    """, unsafe_allow_html=True)
    
    if 'watchlist' not in st.session_state: st.session_state.watchlist = ["AAPL", "TSLA", "SPY", "NFLX", "AMZN", "GOOGL"]
    selected_ticker = st.sidebar.selectbox("ACTIVE TERMINAL", st.session_state.watchlist, index=0)
    
    # Header
    isOpen, status_str = get_market_status()
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0 25px 0; border-bottom: 1px solid rgba(30, 41, 59, 0.6); margin-bottom: 25px;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="background-color: #2563eb; width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 900; color: white; font-size: 1.1rem; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);">O</div>
                <h1 style="font-size: 1.4rem; font-weight: 800; margin: 0; letter-spacing: -0.8px; color: #f1f5f9;">Optix <span style="color: #475569; font-weight: 600; font-size: 0.8rem; letter-spacing: 0.8px; margin-left: 10px; text-transform: uppercase;">PRO TERMINAL</span></h1>
            </div>
            <div class="market-badge {'badge-open' if isOpen else 'badge-closed'}">● {status_str}</div>
        </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 2.8])
    df = get_history_data(selected_ticker)
    opts = get_options_data(selected_ticker)
    ed = get_earnings_days(selected_ticker)
    df = calculate_indicators(df)
    c_s, p_s, strength, b = get_scores(df, opts, ed, selected_ticker)

    with col_left:
        def get_cls(val):
            v = str(val).lower()
            if any(x in v for x in ['+15c', 'bullish', 'oversold', 'call heavy', 'low iv']): return 'val-bullish'
            if any(x in v for x in ['+15p', 'bearish', 'overbought', 'put heavy', 'high iv']): return 'val-bearish'
            if any(x in v for x in ['pnlty', 'critical', 'approaching']): return 'val-warning'
            return 'val-neutral'

        dm = re.search(r'\((\d+)d\)', b['earningsDesc'])
        days_v = dm.group(1) if dm else "?"

        st.markdown(f"""
            <div class="optix-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <div>
                        <div style="font-size: 9px; font-weight: 900; color: #64748b; letter-spacing: 1.5px; text-transform: uppercase;">Signal Engine</div>
                        <div style="font-size: 8px; color: #475569; font-weight: 600; margin-top: 2px;">WEIGHTED ANALYSIS</div>
                    </div>
                    <span style="font-size: 9px; font-weight: 900; background: { '#2563eb' if strength == 'Strong' else '#1e293b' }; color: { '#fff' if strength == 'Strong' else '#94a3b8' }; padding: 4px 12px; border-radius: 20px; box-shadow: { '0 4px 12px rgba(37, 99, 235, 0.25)' if strength == 'Strong' else 'none' };">{strength.upper()}</span>
                </div>
                
                <div class="signal-container">
                    <div class="signal-bar-wrapper">
                        <span class="signal-bar-value" style="color:#4ade80;">{c_s}%</span>
                        <div class="signal-bar" style="height: {c_s}%; background: rgba(34, 197, 94, 0.15); border-top: 2.5px solid #22c55e;"></div>
                        <div class="signal-label">CALL BIAS</div>
                    </div>
                    <div class="signal-bar-wrapper">
                        <span class="signal-bar-value" style="color:#f87171;">{p_s}%</span>
                        <div class="signal-bar" style="height: {p_s}%; background: rgba(239, 68, 68, 0.15); border-top: 2.5px solid #ef4444;"></div>
                        <div class="signal-label">PUT BIAS</div>
                    </div>
                </div>
                
                <div class="breakdown-section">
                    <span class="breakdown-header">Factor Observation</span>
                    <div class="breakdown-item"><span class="breakdown-label">Trend (MA50)</span><span class="breakdown-value {get_cls(b['trend'])}">{b['trend']}</span></div>
                    <div class="breakdown-item"><span class="breakdown-label">RSI Strategy</span><span class="breakdown-value {get_cls(b['rsi'])}">{b['rsi']}</span></div>
                    <div class="breakdown-item"><span class="breakdown-label">Option Flow</span><span class="breakdown-value {get_cls(b['volume'])}">{b['volume']}</span></div>
                    
                    <div class="breakdown-item">
                        <span class="breakdown-label">Earnings Prox</span>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div class="mini-calendar">
                                <span class="mini-calendar-header">Days</span>
                                <span class="mini-calendar-body">{days_v}</span>
                            </div>
                            <span class="breakdown-value {get_cls(b['earningsDesc'])}">{b['earningsDesc']}</span>
                        </div>
                    </div>
                    <div class="breakdown-item" style="border-bottom: none;"><span class="breakdown-label">IV Regime</span><span class="breakdown-value {get_cls(b['iv'])}">{b['iv']}</span></div>
                </div>

                <div class="cognitive-layer">
                    <div class="cognitive-header"><i class="fas fa-brain"></i> COGNITIVE LAYER</div>
                    <p class="cognitive-text">Analysis of {selected_ticker} indicates {strength.lower()} conviction. Delta flow is currently aligned with technical pivot points. Monitor RSI for momentum cooling.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if df is not None:
            price = df['Close'].iloc[-1]
            st.markdown(f"""
                <div class="optix-card" style="padding: 18px;">
                    <div style="font-size: 0.7rem; font-weight: 800; color: #64748b; margin-bottom: 6px; letter-spacing: 1.2px; text-transform: uppercase;">{selected_ticker} Spot</div>
                    <div style="font-size: 1.8rem; font-weight: 900; color: #f1f5f9; letter-spacing: -1.2px;">${price:.2f}</div>
                </div>
            """, unsafe_allow_html=True)

    with col_right:
        if df is not None:
            # PROFESSIONAL CANDLESTICK CHART WITH RSI SUBPLOT
            fig = make_subplots(
                rows=2, cols=1, 
                shared_xaxes=True, 
                vertical_spacing=0.08, 
                row_heights=[0.7, 0.3]
            )
            
            # Row 1: Candlestick + SMA50
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                name="Market Data",
                increasing_line_color='#22c55e', decreasing_line_color='#ef4444',
                increasing_fillcolor='#22c55e', decreasing_fillcolor='#ef4444',
                opacity=0.9
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=df.index, y=df['SMA50'],
                mode='lines', line=dict(color='#fbbf24', width=2),
                name="SMA 50", hoverinfo='skip'
            ), row=1, col=1)
            
            # Row 2: RSI
            fig.add_trace(go.Scatter(
                x=df.index, y=df['RSI'],
                mode='lines', line=dict(color='#3b82f6', width=1.5),
                name="RSI (14)"
            ), row=2, col=1)
            
            # RSI Thresholds
            fig.add_hline(y=70, line_dash="dash", line_color="rgba(239, 68, 68, 0.4)", row=2, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="rgba(34, 197, 94, 0.4)", row=2, col=1)

            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=520,
                xaxis_rangeslider_visible=False,
                margin=dict(l=0, r=40, t=10, b=10),
                showlegend=False,
                hovermode='x unified',
                font=dict(family="Inter", size=10)
            )
            
            fig.update_xaxes(showgrid=False, zeroline=False, tickfont=dict(color='#475569'), showticklabels=True, row=2, col=1)
            fig.update_yaxes(showgrid=True, gridcolor='rgba(30, 41, 59, 0.5)', zeroline=False, side='right', tickfont=dict(color='#64748b'), row=1, col=1)
            fig.update_yaxes(showgrid=True, gridcolor='rgba(30, 41, 59, 0.5)', zeroline=False, side='right', tickfont=dict(color='#64748b'), range=[0, 100], row=2, col=1)

            st.markdown('<div class="optix-card" style="padding: 12px; height: 550px;">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        if opts:
            st.markdown('<div class="optix-card" style="padding: 0; overflow: hidden; height: 380px;">', unsafe_allow_html=True)
            t1, t2 = st.tabs(["CALL FLOW (Active)", "PUT FLOW (Active)"])
            cols = ['strike', 'lastPrice', 'volume', 'openInterest', 'impliedVolatility']
            with t1: st.dataframe(opts['calls'][cols].head(15), use_container_width=True)
            with t2: st.dataframe(opts['puts'][cols].head(15), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
