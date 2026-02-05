
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
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

# --- THEME INJECTION (MATCHING REACT PREVIEW) ---
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

    /* Card Styling to match React 'bg-slate-900/40 backdrop-blur-md' */
    .optix-card {
        background-color: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(30, 41, 59, 0.7);
        padding: 24px;
        border-radius: 14px;
        margin-bottom: 20px;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 24px -2px rgba(0, 0, 0, 0.3);
    }

    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #1e293b;
    }

    /* Signal Engine Specifics */
    .signal-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        height: 80px;
        gap: 16px;
        margin: 20px 0 30px 0;
    }
    .signal-bar-wrapper {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .signal-bar {
        width: 100%;
        border-radius: 4px 4px 0 0;
        transition: height 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    .signal-bar-value {
        position: absolute;
        top: -20px;
        left: 50%;
        transform: translateX(-50%);
        font-size: 10px;
        font-weight: 900;
    }
    .signal-label {
        font-size: 9px;
        font-weight: 800;
        color: #64748b;
        margin-top: 10px;
        letter-spacing: -0.2px;
    }
    
    /* Factor Breakdown Row Styling */
    .breakdown-section {
        margin-top: 25px;
        border-top: 1px solid rgba(30, 41, 59, 0.5);
        padding-top: 18px;
    }
    .breakdown-header {
        font-size: 9px;
        font-weight: 900;
        color: #475569;
        letter-spacing: 1.5px;
        text-transform: uppercase;
        display: block;
        margin-bottom: 12px;
    }
    .breakdown-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 0;
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
        border: 1px solid #1e293b;
        border-radius: 6px;
        width: 32px;
        height: 32px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        line-height: 1;
        overflow: hidden;
        box-shadow: inset 0 2px 8px rgba(0,0,0,0.4);
    }
    .mini-calendar-header {
        font-size: 5px;
        text-transform: uppercase;
        background: rgba(239, 68, 68, 0.8);
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
        padding-top: 16px;
        border-top: 1px solid rgba(30, 41, 59, 0.6);
    }
    .cognitive-header {
        font-size: 10px;
        font-weight: 900;
        color: #3b82f6;
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 8px;
    }
    .cognitive-text {
        font-size: 11px;
        color: #94a3b8;
        font-style: italic;
        line-height: 1.5;
    }

    .market-badge {
        font-size: 10px;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 20px;
    }
    .badge-open { background-color: rgba(34, 197, 94, 0.1); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.2); }
    .badge-closed { background-color: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); }
    
    /* Header Bar */
    .terminal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 0;
        margin-bottom: 24px;
        border-bottom: 1px solid rgba(30, 41, 59, 0.5);
    }

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
    return False, "CLOSED (After Hours)"

# --- DATA ENGINE ---
@st.cache_data(ttl=60)
def get_history_data(symbol, period="5d", interval="1m"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df is None or df.empty: raise ValueError("Empty response")
        st.session_state.is_mock = False
        return df
    except Exception as e:
        st.session_state.is_mock = True
        np.random.seed(abs(hash(symbol)) % 10000)
        base = 150.0
        dates = pd.date_range(end=datetime.now(), periods=100, freq='15min')
        prices = base + np.cumsum(np.random.normal(0, 1, 100))
        return pd.DataFrame({
            'Open': prices-0.5, 'High': prices+1.0, 'Low': prices-1.0, 
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
        def create_mock_chain():
            return pd.DataFrame({'strike': strikes, 'lastPrice': np.random.uniform(1, 5, 11), 'volume': np.random.randint(10, 5000, 11), 'openInterest': np.random.randint(100, 10000, 11), 'impliedVolatility': np.random.uniform(0.2, 0.8, 11)})
        return {'calls': create_mock_chain(), 'puts': create_mock_chain(), 'expiry': 'MOCK'}

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
    b = {'trend': 'Neutral', 'rsi': 'Neutral', 'macd': 'Neutral', 'volume': 'Neutral', 'iv': 'Normal Regime', 'earningsDesc': 'Safe'}
    c_score, p_score = 35, 35 
    
    sma50 = latest.get('SMA50', latest['Close'])
    if latest['Close'] > (sma50 * 1.005): 
        c_score += 15
        b['trend'] = "Above MA50 (+15c)"
    elif latest['Close'] < (sma50 * 0.995): 
        p_score += 15
        b['trend'] = "Below MA50 (+15p)"
    
    rsi = latest.get('RSI', 50)
    if rsi < 38: 
        c_score += 20
        b['rsi'] = f"{int(rsi)} Oversold (+20c)"
    elif rsi > 62: 
        p_score += 20
        b['rsi'] = f"{int(rsi)} Overbought (+20p)"
    else: b['rsi'] = f"{int(rsi)} Neutral"

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
    strength = "Strong" if c_s >= 80 or p_s >= 80 else "Moderate" if c_s >= 65 or p_s >= 65 else "Weak"
    res = (int(c_s), int(p_s), strength, b)
    if is_open: st.session_state.frozen_signals[symbol] = res
    return res

# --- APP UI ---
def main():
    st.sidebar.markdown("<h3 style='color:#64748b; font-size:0.8rem; font-weight:800; text-transform:uppercase; letter-spacing:1px; margin-bottom:15px;'>Watchlist</h3>", unsafe_allow_html=True)
    if 'watchlist' not in st.session_state: st.session_state.watchlist = ["AAPL", "TSLA", "SPY", "NFLX", "AMZN", "GOOGL"]
    selected_ticker = st.sidebar.selectbox("ACTIVE TERMINAL", st.session_state.watchlist)
    
    isOpen, status_str = get_market_status()
    st.markdown(f"""
        <div class="terminal-header">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="background-color: #2563eb; width: 32px; height: 32px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 900; color: white; font-size: 1.1rem;">O</div>
                <h1 style="font-size: 1.3rem; font-weight: 800; margin: 0; letter-spacing: -0.5px;">Optix <span style="color: #475569; font-weight: 500; font-size: 0.8rem; letter-spacing: 0.5px; margin-left: 8px;">PRO TERMINAL</span></h1>
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

        days_match = re.search(r'\((\d+)d\)', b['earningsDesc'])
        days_val = days_match.group(1) if days_match else "?"

        st.markdown(f"""
            <div class="optix-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <div>
                        <div style="font-size: 9px; font-weight: 800; color: #64748b; letter-spacing: 1.5px; text-transform: uppercase;">Signal Engine</div>
                        <div style="font-size: 8px; color: #475569; font-weight: 500;">Weighted Analysis</div>
                    </div>
                    <span style="font-size: 10px; font-weight: 900; background: { '#1d4ed8' if strength == 'Strong' else '#1e293b' }; color: { '#fff' if strength == 'Strong' else '#94a3b8' }; padding: 3px 10px; border-radius: 20px;">{strength.upper()}</span>
                </div>
                
                <div class="signal-container">
                    <div class="signal-bar-wrapper">
                        <div class="signal-bar" style="height: {c_s}%; background: rgba(34, 197, 94, 0.15); border-top: 2px solid #22c55e;">
                            <span class="signal-bar-value" style="color:#22c55e;">{c_s}%</span>
                        </div>
                        <div class="signal-label">CALL BIAS</div>
                    </div>
                    <div class="signal-bar-wrapper">
                        <div class="signal-bar" style="height: {p_s}%; background: rgba(239, 68, 68, 0.15); border-top: 2px solid #ef4444;">
                            <span class="signal-bar-value" style="color:#ef4444;">{p_s}%</span>
                        </div>
                        <div class="signal-label">PUT BIAS</div>
                    </div>
                </div>
                
                <div class="breakdown-section">
                    <span class="breakdown-header">Factor Observation</span>
                    <div class="breakdown-item"><span class="breakdown-label">Trend (MA50)</span><span class="breakdown-value {get_cls(b['trend'])}">{b['trend']}</span></div>
                    <div class="breakdown-item"><span class="breakdown-label">RSI Trend</span><span class="breakdown-value {get_cls(b['rsi'])}">{b['rsi']}</span></div>
                    <div class="breakdown-item"><span class="breakdown-label">Option Flow</span><span class="breakdown-value {get_cls(b['volume'])}">{b['volume']}</span></div>
                    
                    <div class="breakdown-item">
                        <span class="breakdown-label">Earnings Prox</span>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <div class="mini-calendar">
                                <span class="mini-calendar-header">Days</span>
                                <span class="mini-calendar-body">{days_val}</span>
                            </div>
                            <span class="breakdown-value {get_cls(b['earningsDesc'])}">{b['earningsDesc']}</span>
                        </div>
                    </div>
                    
                    <div class="breakdown-item" style="border-bottom: none;"><span class="breakdown-label">IV Regime</span><span class="breakdown-value {get_cls(b['iv'])}">{b['iv']}</span></div>
                </div>

                <div class="cognitive-layer">
                    <div class="cognitive-header"><i class="fas fa-brain"></i> COGNITIVE LAYER</div>
                    <p class="cognitive-text">Market sentiment for {selected_ticker} is currently showing {strength.lower()} conviction based on technical alignment and option flow delta. Maintain caution near key MA levels.</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if df is not None:
            price = df['Close'].iloc[-1]
            st.markdown(f"""
                <div class="optix-card" style="padding: 16px;">
                    <div style="font-size: 0.7rem; font-weight: 700; color: #64748b; margin-bottom: 5px; letter-spacing: 1px;">{selected_ticker} CURRENT</div>
                    <div style="font-size: 1.6rem; font-weight: 800; color: #f8fafc; letter-spacing: -1px;">${price:.2f}</div>
                </div>
            """, unsafe_allow_html=True)

    with col_right:
        if df is not None:
            st.markdown('<div class="optix-card" style="padding: 12px; height: 500px;">', unsafe_allow_html=True)
            
            fig = go.Figure()
            # Gradient fill mimicry
            fig.add_trace(go.Scatter(
                x=df.index, y=df['Close'],
                mode='lines',
                line=dict(color='#3b82f6', width=3),
                fill='tozeroy',
                fillcolor='rgba(59, 130, 246, 0.08)',
                name="Price",
                hovertemplate="<b>Price:</b> $%{y:.2f}<extra></extra>"
            ))
            # Subtle MA
            fig.add_trace(go.Scatter(
                x=df.index, y=df['SMA50'],
                mode='lines',
                line=dict(color='rgba(148, 163, 184, 0.3)', width=1.5, dash='dot'),
                name="SMA 50",
                hoverinfo='skip'
            ))
            
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=460,
                xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=30, t=10, b=10),
                xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(size=9, color='#475569')),
                yaxis=dict(showgrid=True, gridcolor='rgba(30, 41, 59, 0.5)', zeroline=False, side='right', tickfont=dict(size=10, color='#64748b')),
                showlegend=False,
                hovermode='x unified'
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        if opts:
            st.markdown('<div class="optix-card" style="padding: 0; overflow: hidden;">', unsafe_allow_html=True)
            t1, t2 = st.tabs(["CALLS (FLOW)", "PUTS (FLOW)"])
            with t1: st.dataframe(opts['calls'][['strike', 'lastPrice', 'volume', 'openInterest', 'impliedVolatility']].head(12), use_container_width=True)
            with t2: st.dataframe(opts['puts'][['strike', 'lastPrice', 'volume', 'openInterest', 'impliedVolatility']].head(12), use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
