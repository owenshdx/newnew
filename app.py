
import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import pytz
import os

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Optix | Professional Terminal",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- THEME INJECTION (REPLICATING REACT UI) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
        background-color: #0f172a !important;
    }
    
    .stApp {
        background-color: #0f172a;
    }

    /* Card Styling */
    .optix-card {
        background-color: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(51, 65, 85, 0.5);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #1e293b;
    }

    /* Metric Overrides */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
    }

    /* Signal Bar Styling */
    .signal-container {
        display: flex;
        justify-content: space-between;
        align-items: flex-end;
        height: 100px;
        gap: 10px;
        margin-top: 20px;
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
        transition: height 0.5s ease;
    }
    .signal-label {
        font-size: 10px;
        font-weight: 800;
        color: #64748b;
        margin-top: 8px;
    }
    
    /* Header Badge */
    .market-badge {
        font-size: 10px;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 20px;
        display: inline-block;
    }
    .badge-open { background-color: rgba(34, 197, 94, 0.1); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.2); }
    .badge-closed { background-color: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); }
    
    /* Hide Streamlit components for a cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- DATA ENGINE ---
@st.cache_data(ttl=60)
def get_history_data(symbol, period="5d", interval="1m"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            df = ticker.history(period="1mo", interval="1d")
        return df
    except:
        return None

@st.cache_data(ttl=300)
def get_options_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        if not ticker.options: return None
        expiry = ticker.options[0]
        chain = ticker.option_chain(expiry)
        return {'calls': chain.calls, 'puts': chain.puts, 'expiry': expiry}
    except:
        return None

def calculate_indicators(df):
    if df is None or df.empty: return df
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    df['BB_Mid'] = df['Close'].rolling(window=20).mean()
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Mid'] + (df['BB_Std'] * 2)
    df['BB_Lower'] = df['BB_Mid'] - (df['BB_Std'] * 2)
    return df

def get_scores(df, options):
    if df is None or len(df) < 2: return 0, 0, "Wait"
    latest = df.iloc[-1]
    c_score, p_score = 40, 40 # Base
    if latest['Close'] > latest.get('SMA50', 0): c_score += 15
    else: p_score += 15
    if latest.get('RSI', 50) < 35: c_score += 20
    elif latest.get('RSI', 50) > 65: p_score += 20
    if options:
        if options['calls']['volume'].sum() > options['puts']['volume'].sum(): c_score += 15
        else: p_score += 15
    status = "Strong" if c_score > 75 or p_score > 75 else "Moderate" if c_score > 60 or p_score > 60 else "Weak"
    return min(c_score, 100), min(p_score, 100), status

def get_market_status():
    tz = pytz.timezone('US/Eastern')
    now = datetime.now(tz)
    if now.weekday() >= 5: return False, "CLOSED"
    m_open = now.replace(hour=9, minute=30, second=0)
    m_close = now.replace(hour=16, minute=0, second=0)
    return (m_open <= now <= m_close), "OPEN" if (m_open <= now <= m_close) else "CLOSED"

# --- APP UI ---
def main():
    # Sidebar Watchlist
    st.sidebar.markdown("<h2 style='color:#f8fafc; font-size:1.2rem; margin-bottom:20px;'>📁 WATCHLIST</h2>", unsafe_allow_html=True)
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = ["AAPL", "TSLA", "SPY", "NFLX", "AMZN", "GOOGL"]
    
    new_t = st.sidebar.text_input("ADD SYMBOL", placeholder="e.g. NVDA").upper().strip()
    if st.sidebar.button("ADD TO LIST", use_container_width=True):
        if new_t and new_t not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_t)
            st.rerun()
            
    selected_ticker = st.sidebar.selectbox("ACTIVE TERMINAL", st.session_state.watchlist)
    
    # Header logic
    isOpen, status_str = get_market_status()
    badge_class = "badge-open" if isOpen else "badge-closed"
    
    st.markdown(f"""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="background-color: #3b82f6; width: 35px; height: 35px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 900; color: white;">O</div>
                <h1 style="font-size: 1.5rem; font-weight: 800; margin: 0;">Optix <span style="color: #64748b; font-weight: 400; font-size: 0.9rem;">PRO TERMINAL</span></h1>
            </div>
            <div class="market-badge {badge_class}">● MARKET {status_str}</div>
        </div>
    """, unsafe_allow_html=True)

    # Main Grid
    col_left, col_right = st.columns([1, 3])

    with col_left:
        # Signal Engine Card
        df = get_history_data(selected_ticker)
        options = get_options_data(selected_ticker)
        df = calculate_indicators(df)
        c_score, p_score, strength = get_scores(df, options)
        
        st.markdown(f"""
            <div class="optix-card">
                <div style="display: flex; justify-content: space-between; margin-bottom: 20px;">
                    <span style="font-size: 10px; font-weight: 700; color: #64748b; letter-spacing: 1px;">SIGNAL ENGINE</span>
                    <span style="font-size: 10px; font-weight: 700; background: #1e293b; color: #3b82f6; padding: 2px 8px; border-radius: 4px;">{strength.upper()}</span>
                </div>
                <div class="signal-container">
                    <div class="signal-bar-wrapper">
                        <div class="signal-bar" style="height: {c_score}%; background: rgba(34, 197, 94, 0.3); border-top: 2px solid #22c55e;"></div>
                        <div class="signal-label">CALL {c_score}%</div>
                    </div>
                    <div class="signal-bar-wrapper">
                        <div class="signal-bar" style="height: {p_score}%; background: rgba(239, 68, 68, 0.3); border-top: 2px solid #ef4444;"></div>
                        <div class="signal-label">PUT {p_score}%</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Stats Card
        if df is not None:
            price = df['Close'].iloc[-1]
            change = price - df['Close'].iloc[-2]
            st.markdown('<div class="optix-card">', unsafe_allow_html=True)
            st.metric(selected_ticker, f"${price:.2f}", f"{change:.2f}")
            st.metric("RSI (14)", f"{df['RSI'].iloc[-1]:.1f}")
            st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
        # Chart Card
        if df is not None:
            st.markdown('<div class="optix-card" style="padding: 10px;">', unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                name="Price", increasing_line_color='#22c55e', decreasing_line_color='#ef4444'
            ))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA50'], line=dict(color='#3b82f6', width=1.5), name="SMA 50"))
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='rgba(148, 163, 184, 0.2)', width=1, dash='dot'), name="BB Upper"))
            fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='rgba(148, 163, 184, 0.2)', width=1, dash='dot'), name="BB Lower", fill='tonexty', fillcolor='rgba(148, 163, 184, 0.05)'))
            
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=450,
                xaxis_rangeslider_visible=False,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=False, zeroline=False),
                yaxis=dict(showgrid=True, gridcolor='rgba(51, 65, 85, 0.5)', zeroline=False, side='right')
            )
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
            st.markdown('</div>', unsafe_allow_html=True)

        # Options Table Card
        if options:
            st.markdown('<div class="optix-card">', unsafe_allow_html=True)
            st.markdown(f"<span style='font-size: 10px; font-weight: 700; color: #64748b; letter-spacing: 1px; margin-bottom: 15px; display: block;'>OPTIONS FLOW: {options['expiry']}</span>", unsafe_allow_html=True)
            t1, t2 = st.tabs(["CALLS", "PUTS"])
            with t1:
                st.dataframe(options['calls'].sort_values('volume', ascending=False).head(5)[['strike', 'lastPrice', 'volume', 'impliedVolatility']], use_container_width=True)
            with t2:
                st.dataframe(options['puts'].sort_values('volume', ascending=False).head(5)[['strike', 'lastPrice', 'volume', 'impliedVolatility']], use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
