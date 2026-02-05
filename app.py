
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import pytz

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Optix | Pro Options Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THEME INJECTION ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #020617 !important;
        color: #f8fafc;
    }
    
    .stApp { background-color: #020617; }
    [data-testid="stVerticalBlock"] { gap: 0rem !important; }
    [data-testid="column"] { padding: 0 0.2rem !important; }

    #MainMenu, footer, header, [data-testid="stHeader"] { visibility: hidden !important; }
    .stDeployButton { display:none; }

    .optix-card {
        background-color: rgba(15, 23, 42, 0.4);
        border: 1px solid rgba(30, 41, 59, 0.8);
        padding: 16px;
        border-radius: 10px;
        margin-bottom: 12px;
        backdrop-filter: blur(12px);
    }

    .signal-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        height: 55px;
        gap: 12px;
        margin: 15px 0 20px 0;
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
        border-radius: 3px 3px 0 0;
        transition: height 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
    }
    .signal-bar-value {
        position: absolute;
        top: -16px;
        font-size: 8px;
        font-weight: 900;
    }
    .signal-label {
        font-size: 7px;
        font-weight: 900;
        color: #475569;
        margin-top: 6px;
        letter-spacing: 0.5px;
    }

    .breakdown-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 7px 0;
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

    .options-terminal {
        display: flex;
        gap: 1px;
        background: #1e293b;
        border-radius: 6px;
        overflow: hidden;
        border: 1px solid #1e293b;
        margin-top: 5px;
    }
    .options-pane {
        flex: 1;
        background: #0f172a;
        display: flex;
        flex-direction: column;
    }
    .pane-header {
        padding: 6px 10px;
        font-size: 8px;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 1px;
        border-bottom: 1px solid #1e293b;
    }
    .pane-header.calls { background: rgba(34, 197, 94, 0.1); color: #22c55e; }
    .pane-header.puts { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
    
    .optix-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 9px;
    }
    .optix-table th {
        text-align: left;
        padding: 5px 8px;
        color: #475569;
        font-size: 7.5px;
        font-weight: 800;
        text-transform: uppercase;
        background: rgba(15, 23, 42, 0.8);
    }
    .optix-table td {
        padding: 6px 8px;
        border-bottom: 1px solid rgba(30, 41, 59, 0.15);
        font-family: 'JetBrains Mono', monospace;
    }
    .unusual-row { background: rgba(37, 99, 235, 0.08); }
    .unusual-vol { color: #3b82f6; font-weight: 800; }
    .strike-cell { font-weight: 700; color: #cbd5e1; }

    .val-bullish { background: rgba(34, 197, 94, 0.15); color: #4ade80; border-color: rgba(34, 197, 94, 0.3); }
    .val-bearish { background: rgba(239, 68, 68, 0.15); color: #f87171; border-color: rgba(239, 68, 68, 0.3); }
    .val-neutral { background: rgba(30, 41, 59, 0.6); color: #94a3b8; border-color: rgba(71, 85, 105, 0.4); }
    .val-warning { background: rgba(245, 158, 11, 0.15); color: #fbbf24; border-color: rgba(245, 158, 11, 0.3); }

    .enhanced-calendar {
        width: 26px;
        height: 30px;
        background: #020617;
        border: 1px solid #334155;
        border-radius: 4px;
        display: flex;
        flex-direction: column;
        overflow: hidden;
    }
    .cal-header {
        font-size: 4px;
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
    .cal-day { font-size: 9px; font-weight: 900; color: #f1f5f9; }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.6; }
        100% { opacity: 1; }
    }

    [data-testid="stSidebar"] { background-color: #020617; border-right: 1px solid #1e293b; }
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
    return (m_open <= now <= m_close), ("OPEN" if m_open <= now <= m_close else "CLOSED")

@st.cache_data(ttl=60)
def fetch_history(symbol):
    try:
        t = yf.Ticker(symbol)
        df = t.history(period="5d", interval="1m")
        if df is None or df.empty: raise ValueError("Empty Data")
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-9))))
        return df, False
    except Exception as e:
        prices = 150 + np.cumsum(np.random.normal(0, 0.5, 100))
        dates = pd.date_range(end=datetime.now(), periods=100, freq='1min')
        df = pd.DataFrame({'Open': prices-0.2, 'High': prices+0.4, 'Low': prices-0.4, 'Close': prices, 'Volume': np.random.randint(1000, 50000, 100)}, index=dates)
        df['SMA50'] = df['Close'].rolling(window=50).mean()
        df['RSI'] = 50 + np.random.normal(0, 10, 100)
        return df, True

@st.cache_data(ttl=300)
def fetch_options(symbol):
    try:
        t = yf.Ticker(symbol)
        exp = t.options[0]
        chain = t.option_chain(exp)
        avg = (chain.calls['volume'].mean() + chain.puts['volume'].mean()) / 2
        chain.calls['isUnusual'] = chain.calls['volume'] > (avg * 2.5)
        chain.puts['isUnusual'] = chain.puts['volume'] > (avg * 2.5)
        return {'calls': chain.calls, 'puts': chain.puts}, False
    except:
        strikes = [150+i for i in range(-5, 6)]
        def mk(): return pd.DataFrame({'strike': strikes, 'lastPrice': np.random.uniform(1, 10, 11), 'volume': np.random.randint(50, 5000, 11), 'impliedVolatility': np.random.uniform(0.2, 0.8, 11), 'isUnusual': [False]*10 + [True]})
        return {'calls': mk(), 'puts': mk()}, True

@st.cache_data(ttl=3600)
def fetch_earnings_days(symbol):
    try:
        t = yf.Ticker(symbol)
        cal = t.calendar
        if isinstance(cal, dict): ed = cal.get('Earnings Date', [None])[0]
        else: ed = cal.iloc[0, 0]
        if ed is None: return 14, False
        days = (ed.date() - datetime.now().date()).days
        return max(0, int(days)), False
    except: return 14, True

def get_scores(df, opts, ed):
    c, p = 35, 35
    latest = df.iloc[-1]
    factors = {'trend': 'Neutral', 'rsi': 'Neutral', 'vol': 'Balanced', 'earn': 'Safe'}
    
    if latest['Close'] > latest['SMA50']: c += 15; factors['trend'] = 'Above MA50 (+15c)'
    else: p += 15; factors['trend'] = 'Below MA50 (+15p)'
    
    if latest['RSI'] < 30: c += 20; factors['rsi'] = 'Oversold (+20c)'
    elif latest['RSI'] > 70: p += 20; factors['rsi'] = 'Overbought (+20p)'
    
    cv, pv = opts['calls']['volume'].sum(), opts['puts']['volume'].sum()
    if cv > pv * 1.5: c += 20; factors['vol'] = 'Call Heavy (+20c)'
    elif pv > cv * 1.5: p += 20; factors['vol'] = 'Put Heavy (+20p)'
    
    if ed <= 7: c -= 25; p -= 25; factors['earn'] = f'CRITICAL ({ed}d)'
    else: factors['earn'] = f'Safe ({ed}d)'
    
    c, p = max(0, min(100, c)), max(0, min(100, p))
    strength = "Strong" if max(c, p) >= 80 else "Moderate" if max(c, p) >= 60 else "Weak"
    return c, p, strength, factors

# --- RENDERERS ---
def render_pane(df):
    html = '<table class="optix-table"><thead><tr><th>Strike</th><th>Price</th><th>Vol</th><th style="text-align:right">IV</th></tr></thead><tbody>'
    for _, r in df.iterrows():
        row_cls = 'unusual-row' if r['isUnusual'] else ''
        vol_cls = 'unusual-vol' if r['isUnusual'] else ''
        v_str = f"{r['volume']/1000:.1f}k" if r['volume'] > 1000 else int(r['volume'])
        html += f'<tr class="{row_cls}"><td class="strike-cell">{r["strike"]:.1f}</td><td>${r["lastPrice"]:.2f}</td><td class="{vol_cls}">{v_str}</td><td style="text-align:right">{r["impliedVolatility"]*100:.1f}%</td></tr>'
    return html + '</tbody></table>'

# --- MAIN ---
def main():
    st.sidebar.markdown("<div style='font-size: 10px; font-weight: 900; color: #475569; letter-spacing: 2px; margin-bottom: 15px;'>WATCHLIST</div>", unsafe_allow_html=True)
    symbol = st.sidebar.selectbox("Symbol", ["AAPL", "TSLA", "SPY", "NFLX", "AMZN", "GOOGL"], label_visibility="collapsed")
    
    df, is_mock_d = fetch_history(symbol)
    opts, is_mock_o = fetch_options(symbol)
    ed, is_mock_e = fetch_earnings_days(symbol)
    c_s, p_s, strength, f = get_scores(df, opts, ed)
    isOpen, status = get_market_status()

    st.markdown(f"""
        <div style="display:flex; justify-content:space-between; align-items:center; padding:10px 0 20px 0; border-bottom:1px solid #1e293b; margin-bottom:20px;">
            <div style="display:flex; align-items:center; gap:12px;">
                <div style="background:#2563eb; width:30px; height:30px; border-radius:6px; display:flex; align-items:center; justify-content:center; font-weight:900; color:white;">O</div>
                <h1 style="font-size:1.2rem; font-weight:800; margin:0;">Optix <span style="color:#475569; font-size:0.7rem; font-weight:600; margin-left:8px;">PRO TERMINAL</span></h1>
            </div>
            <div style="display:flex; align-items:center; gap:10px;">
                {f'<div style="font-size:8px; background:rgba(180,83,9,0.1); color:#fbbf24; padding:3px 10px; border-radius:15px; border:1px solid rgba(180,83,9,0.2);">SIMULATION ACTIVE</div>' if (is_mock_d or is_mock_o) else ''}
                <div style="font-size:9px; font-weight:800; padding:4px 12px; border-radius:20px; background:{"rgba(34,197,94,0.1)" if isOpen else "rgba(239,68,68,0.1)"}; color:{"#4ade80" if isOpen else "#f87171"}; border:1px solid {"rgba(34,197,94,0.2)" if isOpen else "rgba(239,68,68,0.2)"};">● {status}</div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 3])
    
    with col_l:
        def b_cls(v):
            v_low = v.lower()
            if any(x in v_low for x in ['above', 'oversold', 'heavy']): return 'val-bullish'
            if any(x in v_low for x in ['below', 'overbought']): return 'val-bearish'
            if 'critical' in v_low: return 'val-warning'
            return 'val-neutral'

        cal_h_cls = "imminent" if ed <= 7 else ""
        st.markdown(f"""
            <div class="optix-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:15px;">
                    <span style="font-size:9px; font-weight:900; color:#475569;">SIGNAL ENGINE</span>
                    <span style="font-size:8px; font-weight:900; background:{"#2563eb" if strength=="Strong" else "#1e293b"}; color:white; padding:2px 8px; border-radius:20px;">{strength.upper()}</span>
                </div>
                <div class="signal-container">
                    <div class="signal-bar-wrapper">
                        <span class="signal-bar-value" style="color:#4ade80;">{c_s}%</span>
                        <div class="signal-bar" style="height:{c_s}%; background:rgba(34,197,94,0.15); border-top:2px solid #22c55e;"></div>
                        <div class="signal-label">CALLS</div>
                    </div>
                    <div class="signal-bar-wrapper">
                        <span class="signal-bar-value" style="color:#f87171;">{p_s}%</span>
                        <div class="signal-bar" style="height:{p_s}%; background:rgba(239,68,68,0.15); border-top:2px solid #ef4444;"></div>
                        <div class="signal-label">PUTS</div>
                    </div>
                </div>
                <div style="border-top:1px solid #1e293b; padding-top:10px;">
                    <div class="breakdown-row"><span class="breakdown-label">Trend</span><span class="breakdown-badge {b_cls(f['trend'])}">{f['trend']}</span></div>
                    <div class="breakdown-row"><span class="breakdown-label">RSI</span><span class="breakdown-badge {b_cls(f['rsi'])}">{f['rsi']}</span></div>
                    <div class="breakdown-row"><span class="breakdown-label">Flow</span><span class="breakdown-badge {b_cls(f['vol'])}">{f['vol']}</span></div>
                    <div class="breakdown-row">
                        <span class="breakdown-label">Earnings</span>
                        <div style="display:flex; align-items:center; gap:6px;">
                            <div class="enhanced-calendar"><div class="cal-header {cal_h_cls}">T-MINUS</div><div class="cal-body"><div class="cal-day">{ed}</div></div></div>
                            <span class="breakdown-badge {b_cls(f['earn'])}">{f['earn']}</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="optix-card" style="padding:12px;">
                <div style="font-size:8px; font-weight:900; color:#475569;">{symbol} SPOT</div>
                <div style="font-size:1.4rem; font-weight:900; color:#f1f5f9; letter-spacing:-0.5px;">${df['Close'].iloc[-1]:.2f}</div>
            </div>
        """, unsafe_allow_html=True)

    with col_r:
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.75, 0.25])
        
        bins = np.linspace(df['Low'].min(), df['High'].max(), 30)
        hist, edges = np.histogram(df['Close'], bins=bins, weights=df['Volume'])
        max_h = hist.max() if hist.max() > 0 else 1
        for i in range(len(hist)):
            w = (hist[i] / max_h) * (len(df) * 0.2)
            fig.add_shape(type="rect", x0=df.index[0], x1=df.index[int(w)], y0=edges[i], y1=edges[i+1], fillcolor="rgba(37,99,235,0.12)", line=dict(width=0), row=1, col=1)

        fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], increasing_line_color='#22c55e', decreasing_line_color='#ef4444', name="Price"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='#fbbf24', width=1.5), name="SMA50"), row=1, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#3b82f6', width=1.2), name="RSI"), row=2, col=1)
        
        fig.update_layout(template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=420, xaxis_rangeslider_visible=False, margin=dict(l=0, r=40, t=10, b=10), showlegend=False)
        fig.update_yaxes(side='right', gridcolor='rgba(30,41,59,0.3)', row=1, col=1)
        fig.update_yaxes(side='right', gridcolor='rgba(30,41,59,0.3)', range=[0, 100], row=2, col=1)
        
        st.markdown('<div class="optix-card" style="padding:8px; height:440px;">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="optix-card" style="padding:12px;">', unsafe_allow_html=True)
        st.markdown('<div style="font-size:9px; font-weight:900; color:#475569; letter-spacing:1px; margin-bottom:8px;">OPTIONS TERMINAL (TOP FLOW)</div>', unsafe_allow_html=True)
        
        c_p = opts['calls'].sort_values('volume', ascending=False).head(10)
        p_p = opts['puts'].sort_values('volume', ascending=False).head(10)
        
        st.markdown(f"""
            <div class="options-terminal">
                <div class="options-pane"><div class="pane-header calls">Calls</div>{render_pane(c_p)}</div>
                <div class="options-pane"><div class="pane-header puts">Puts</div>{render_pane(p_p)}</div>
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
