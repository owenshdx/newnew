
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
    page_title="Optix | Pro Options Terminal",
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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap');
    
    /* Global Overrides */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #020617 !important;
        color: #f8fafc;
    }
    
    .stApp { background-color: #020617; }
    [data-testid="stVerticalBlock"] { gap: 0rem !important; }
    [data-testid="column"] { padding: 0 0.3rem !important; }

    /* Hide Streamlit Clutter */
    #MainMenu, footer, header, [data-testid="stHeader"] { visibility: hidden !important; }
    .stDeployButton { display:none; }

    /* Glass Cards */
    .optix-card {
        background-color: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(30, 41, 59, 0.8);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 12px;
        backdrop-filter: blur(12px);
    }

    /* Signal Engine Styling */
    .signal-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        height: 60px;
        gap: 15px;
        margin: 20px 0 25px 0;
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
        top: -18px;
        font-size: 9px;
        font-weight: 900;
    }
    .signal-label {
        font-size: 8px;
        font-weight: 900;
        color: #475569;
        margin-top: 8px;
        letter-spacing: 0.5px;
    }

    /* Factor Breakdown Table */
    .breakdown-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid rgba(30, 41, 59, 0.3);
    }
    .breakdown-row:last-child { border-bottom: none; }
    .breakdown-label { font-size: 10px; color: #94a3b8; font-weight: 500; }
    .breakdown-badge {
        font-size: 8px;
        font-weight: 800;
        padding: 2px 6px;
        border-radius: 3px;
        text-transform: uppercase;
        border: 1px solid transparent;
    }

    /* Custom Side-by-Side Options Terminal */
    .options-terminal {
        display: flex;
        gap: 1px;
        background: #1e293b;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #1e293b;
    }
    .options-pane {
        flex: 1;
        background: #0f172a;
    }
    .pane-header {
        padding: 8px 12px;
        font-size: 9px;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .pane-header.calls { background: rgba(34, 197, 94, 0.1); color: #22c55e; border-bottom: 1px solid rgba(34, 197, 94, 0.2); }
    .pane-header.puts { background: rgba(239, 68, 68, 0.1); color: #ef4444; border-bottom: 1px solid rgba(239, 68, 68, 0.2); }
    
    .optix-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 10px;
    }
    .optix-table th {
        text-align: left;
        padding: 6px 12px;
        color: #475569;
        font-size: 8px;
        font-weight: 800;
        text-transform: uppercase;
        border-bottom: 1px solid #1e293b;
    }
    .optix-table td {
        padding: 8px 12px;
        border-bottom: 1px solid rgba(30, 41, 59, 0.2);
        font-family: 'JetBrains Mono', monospace;
    }
    .unusual-row { background: rgba(37, 99, 235, 0.05); }
    .unusual-vol { color: #3b82f6; font-weight: 800; }
    .strike-cell { font-weight: 700; color: #cbd5e1; }

    /* Indicator Colors */
    .val-bullish { background: rgba(34, 197, 94, 0.15); color: #4ade80; border-color: rgba(34, 197, 94, 0.3); }
    .val-bearish { background: rgba(239, 68, 68, 0.15); color: #f87171; border-color: rgba(239, 68, 68, 0.3); }
    .val-neutral { background: rgba(30, 41, 59, 0.6); color: #94a3b8; border-color: rgba(71, 85, 105, 0.4); }
    .val-warning { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border-color: rgba(245, 158, 11, 0.3); }

    /* Enhanced Mini Calendar */
    .enhanced-calendar {
        width: 28px;
        height: 32px;
        background: #020617;
        border: 1px solid #334155;
        border-radius: 4px;
        display: flex;
        flex-direction: column;
        overflow: hidden;
        position: relative;
    }
    .cal-header {
        font-size: 4.5px;
        font-weight: 900;
        text-align: center;
        background: #ef4444;
        color: white;
        padding: 1px 0;
    }
    .cal-header.imminent { background: #f97316; animation: pulse 2s infinite; }
    .cal-body {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        line-height: 1;
    }
    .cal-day { font-size: 10px; font-weight: 900; color: #f1f5f9; }
    .cal-label { font-size: 4px; font-weight: 700; color: #475569; }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.7; }
        100% { opacity: 1; }
    }

    /* Sidebar Fixes */
    [data-testid="stSidebar"] { background-color: #020617; border-right: 1px solid #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# --- MARKET DATA LOGIC ---
def get_market_status():
    tz = pytz.timezone('US/Eastern')
    now = datetime.now(tz)
    day = now.weekday()
    if day >= 5: return False, "CLOSED (Weekend)"
    m_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    m_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
    if m_open <= now <= m_close: return True, "OPEN"
    return False, f"CLOSED ({'After Hours' if now > m_close else 'Pre-Market'})"

@st.cache_data(ttl=60)
def fetch_raw_history(symbol, period="5d", interval="1m"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df is None or df.empty: raise ValueError("No data")
        return df, False
    except:
        np.random.seed(abs(hash(symbol)) % 10000)
        base = 150.0 if symbol != 'SPY' else 500.0
        dates = pd.date_range(end=datetime.now(), periods=100, freq='15min')
        prices = base + np.cumsum(np.random.normal(0, 0.5, 100))
        return pd.DataFrame({'Open': prices-0.3, 'High': prices+0.6, 'Low': prices-0.6, 'Close': prices, 'Volume': np.random.randint(10000, 1000000, 100)}, index=dates), True

@st.cache_data(ttl=300)
def fetch_raw_options(symbol):
    try:
        ticker = yf.Ticker(symbol)
        expiry = ticker.options[0]
        chain = ticker.option_chain(expiry)
        avg_vol = (chain.calls['volume'].mean() + chain.puts['volume'].mean()) / 2
        chain.calls['isUnusual'] = chain.calls['volume'] > (avg_vol * 2.5)
        chain.puts['isUnusual'] = chain.puts['volume'] > (avg_vol * 2.5)
        return {'calls': chain.calls, 'puts': chain.puts}, False
    except:
        strikes = [150 + i for i in range(-5, 6)]
        def mock_c(): return pd.DataFrame({'strike': strikes, 'lastPrice': np.random.uniform(1, 5, 11), 'volume': np.random.randint(10, 5000, 11), 'openInterest': np.random.randint(100, 10000, 11), 'impliedVolatility': np.random.uniform(0.2, 0.8, 11), 'isUnusual': [False]*10 + [True]})
        return {'calls': mock_c(), 'puts': mock_c()}, True

@st.cache_data(ttl=3600)
def fetch_raw_earnings(symbol):
    try:
        ticker = yf.Ticker(symbol)
        cal = ticker.calendar
        ed = cal['Earnings Date'][0] if isinstance(cal, dict) else cal.iloc[0, 0]
        return max(0, (ed.date() - datetime.now().date()).days), False
    except: return 14, True

def calculate_indicators(df):
    df = df.copy()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

def get_scores(df, options, earnings_days):
    latest = df.iloc[-1]
    b = {'trend': 'Neutral', 'rsi': 'Neutral', 'volume': 'Balanced', 'earningsDesc': 'Safe'}
    c_s, p_s = 35, 35
    
    sma50 = latest.get('SMA50', latest['Close'])
    if latest['Close'] > (sma50 * 1.002): c_s += 15; b['trend'] = "Above MA50 (+15c)"
    elif latest['Close'] < (sma50 * 0.998): p_s += 15; b['trend'] = "Below MA50 (+15p)"
    
    rsi = latest.get('RSI', 50)
    if rsi < 35: c_s += 20; b['rsi'] = f"{int(rsi)} Oversold (+20c)"
    elif rsi > 65: p_s += 20; b['rsi'] = f"{int(rsi)} Overbought (+20p)"
    
    if options:
        c_v, p_v = options['calls']['volume'].sum(), options['puts']['volume'].sum()
        c_pct = (c_v / (c_v + p_v)) * 100
        if c_pct > 60: c_s += 20; b['volume'] = "Call Heavy (+20c)"
        elif c_pct < 40: p_s += 20; b['volume'] = "Put Heavy (+20p)"

    if earnings_days <= 7: c_s -= 25; p_s -= 25; b['earningsDesc'] = f"CRITICAL ({earnings_days}d)"
    else: b['earningsDesc'] = f"Safe ({earnings_days}d)"

    c_s, p_s = max(0, min(100, c_s)), max(0, min(100, p_s))
    strength = "Strong" if max(c_s, p_s) >= 80 else "Moderate" if max(c_s, p_s) >= 60 else "Weak"
    return c_s, p_s, strength, b

# --- CUSTOM RENDERERS ---
def render_pane_table(df):
    html = '<table class="optix-table"><thead><tr><th>Strike</th><th>Price</th><th>Vol</th><th style="text-align:right">IV</th></tr></thead><tbody>'
    for _, row in df.iterrows():
        cls = 'unusual-row' if row['isUnusual'] else ''
        vol_cls = 'unusual-vol' if row['isUnusual'] else ''
        vol_val = f"{row['volume']/1000:.1f}k" if row['volume'] > 1000 else int(row['volume'])
        html += f'''<tr class="{cls}">
            <td class="strike-cell">{row['strike']:.1f}</td>
            <td>${row['lastPrice']:.2f}</td>
            <td class="{vol_cls}">{vol_val}</td>
            <td style="text-align:right">{(row['impliedVolatility']*100):.1f}%</td>
        </tr>'''
    html += '</tbody></table>'
    return html

def render_options_terminal(opts, filter_unusual=False):
    calls = opts['calls'][opts['calls']['isUnusual']] if filter_unusual else opts['calls']
    puts = opts['puts'][opts['puts']['isUnusual']] if filter_unusual else opts['puts']
    calls = calls.head(12)
    puts = puts.head(12)
    
    html = f'''
    <div class="options-terminal">
        <div class="options-pane">
            <div class="pane-header calls">Calls</div>
            {render_pane_table(calls)}
        </div>
        <div class="options-pane">
            <div class="pane-header puts">Puts</div>
            {render_pane_table(puts)}
        </div>
    </div>
    '''
    return html

# --- APP UI ---
def main():
    st.sidebar.markdown("<div style='font-size: 10px; font-weight: 900; color: #64748b; letter-spacing: 2px; margin-bottom: 20px;'>MARKET DIRECTORY</div>", unsafe_allow_html=True)
    selected_ticker = st.sidebar.selectbox("WATCHLIST", ["AAPL", "TSLA", "SPY", "NFLX", "AMZN", "GOOGL"], label_visibility="collapsed")
    
    df_raw, df_is_mock = fetch_raw_history(selected_ticker)
    opts_raw, opts_is_mock = fetch_raw_options(selected_ticker)
    ed_raw, ed_is_mock = fetch_raw_earnings(selected_ticker)
    
    isOpen, status_str = get_market_status()
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; padding: 15px 0 25px 0; border-bottom: 1px solid #1e293b; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="background:#2563eb; width:34px; height:34px; border-radius:6px; display:flex; align-items:center; justify-content:center; font-weight:900; color:white;">O</div>
                <h1 style="font-size: 1.3rem; font-weight: 800; margin: 0; letter-spacing: -0.5px;">Optix <span style="color:#475569; font-size:0.75rem; letter-spacing:1px; margin-left:10px; font-weight:600;">PRO TERMINAL</span></h1>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                {f'<div style="font-size:9px; background:rgba(180,83,9,0.1); color:#fbbf24; padding:3px 10px; border-radius:15px; border:1px solid rgba(180,83,9,0.2);">SIMULATION ACTIVE</div>' if df_is_mock else ''}
                <div style="font-size: 9px; font-weight: 800; padding: 4px 12px; border-radius: 20px; background: {"rgba(34,197,94,0.1)" if isOpen else "rgba(239,68,68,0.1)"}; color: {"#4ade80" if isOpen else "#f87171"}; border: 1px solid {"rgba(34,197,94,0.2)" if isOpen else "rgba(239,68,68,0.2)"};">● {status_str}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns([1.1, 2.9])
    df = calculate_indicators(df_raw)
    c_s, p_s, strength, b = get_scores(df, opts_raw, ed_raw)

    with col_l:
        def get_cls(val):
            v = str(val).lower()
            if any(x in v for x in ['+15c', '+20c', 'bullish', 'oversold']): return 'val-bullish'
            if any(x in v for x in ['+15p', '+20p', 'bearish', 'overbought']): return 'val-bearish'
            if 'critical' in v: return 'val-warning'
            return 'val-neutral'

        cal_cls = "imminent" if ed_raw <= 7 else ""
        st.markdown(f"""
            <div class="optix-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <div style="font-size: 9px; font-weight: 900; color: #64748b; letter-spacing: 1.5px;">SIGNAL ENGINE</div>
                    <span style="font-size: 9px; font-weight: 900; background: {'#2563eb' if strength == 'Strong' else '#1e293b'}; color: white; padding: 2px 10px; border-radius: 20px;">{strength.upper()}</span>
                </div>
                <div class="signal-container">
                    <div class="signal-bar-wrapper">
                        <span class="signal-bar-value" style="color:#4ade80;">{c_s}%</span>
                        <div class="signal-bar" style="height: {c_s}%; background: rgba(34, 197, 94, 0.15); border-top: 2px solid #22c55e;"></div>
                        <div class="signal-label">CALL BIAS</div>
                    </div>
                    <div class="signal-bar-wrapper">
                        <span class="signal-bar-value" style="color:#f87171;">{p_s}%</span>
                        <div class="signal-bar" style="height: {p_s}%; background: rgba(239, 68, 68, 0.15); border-top: 2px solid #ef4444;"></div>
                        <div class="signal-label">PUT BIAS</div>
                    </div>
                </div>
                <div style="margin-top:20px; border-top:1px solid rgba(30,41,59,0.8); padding-top:15px;">
                    <div class="breakdown-row"><span class="breakdown-label">Trend (MA50)</span><span class="breakdown-badge {get_cls(b['trend'])}">{b['trend']}</span></div>
                    <div class="breakdown-row"><span class="breakdown-label">RSI Strategy</span><span class="breakdown-badge {get_cls(b['rsi'])}">{b['rsi']}</span></div>
                    <div class="breakdown-row"><span class="breakdown-label">Option Flow</span><span class="breakdown-badge {get_cls(b['volume'])}">{b['volume']}</span></div>
                    <div class="breakdown-row">
                        <span class="breakdown-label">Earnings Prox</span>
                        <div style="display:flex; align-items:center; gap:8px;">
                            <div class="enhanced-calendar"><div class="cal-header {cal_cls}">T-MINUS</div><div class="cal-body"><div class="cal-day">{ed_raw}</div><div class="cal-label">DAYS</div></div></div>
                            <span class="breakdown-badge {get_cls(b['earningsDesc'])}">{b['earningsDesc']}</span>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="optix-card" style="padding: 15px;">
                <div style="font-size: 9px; font-weight: 900; color: #475569; margin-bottom: 2px;">{selected_ticker} SPOT</div>
                <div style="font-size: 1.6rem; font-weight: 900; color: #f1f5f9; letter-spacing: -1px;">${df['Close'].iloc[-1]:.2f}</div>
            </div>
        """, unsafe_allow_html=True)

    with col_r:
        # CHART WITH VOLUME PROFILE
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.08, row_heights=[0.7, 0.3])
        
        # Overlay Volume Profile (Simplified Horizontal Histogram)
        min_p, max_p = df['Low'].min(), df['High'].max()
        bins = np.linspace(min_p, max_p, 40)
        hist, edges = np.histogram(df['Close'], bins=bins, weights=df['Volume'])
        max_h = hist.max() if hist.max() > 0 else 1
        
        for i in range(len(hist)):
            w = (hist[i] / max_h) * (len(df) * 0.25) # Max 25% of width
            fig.add_shape(type="rect", x0=df.index[0], x1=df.index[int(w)], y0=edges[i], y1=edges[i+1], fillcolor="rgba(59, 130, 246, 0.15)", line=dict(width=0), row=1, col=1)

        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#22c55e', decreasing_line_color='#ef4444', name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='#fbbf24', width=1.5), name="SMA50"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#3b82f6', width=1.5), name="RSI"), row=2, col=1)
        
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=480, xaxis_rangeslider_visible=False, margin=dict(l=0, r=40, t=10, b=10), showlegend=False, font=dict(family="Inter", size=10))
        fig.update_yaxes(side='right', gridcolor='rgba(30,41,59,0.4)', row=1, col=1)
        fig.update_yaxes(side='right', gridcolor='rgba(30,41,59,0.4)', range=[0, 100], row=2, col=1)
        
        st.markdown('<div class="optix-card" style="padding: 10px; height: 500px;">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

        # OPTIONS TERMINAL
        st.markdown('<div class="optix-card" style="padding: 15px;">', unsafe_allow_html=True)
        t_col1, t_col2 = st.columns([1, 1])
        with t_col1: st.markdown('<div style="font-size: 10px; font-weight: 900; color: #64748b; letter-spacing: 1px; margin-top:5px;">OPTIONS ACTIVITY TERMINAL</div>', unsafe_allow_html=True)
        with t_col2: filter_unusual = st.checkbox("Unusual Volume Detection", value=False)
        
        st.markdown(render_options_terminal(opts_raw, filter_unusual), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
