
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
        height: 80px;
        gap: 10px;
        margin-top: 15px;
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
    
    /* Breakdown Items */
    .breakdown-item {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px solid rgba(51, 65, 85, 0.3);
    }
    .breakdown-label {
        font-size: 11px;
        color: #94a3b8;
    }
    .breakdown-value {
        font-size: 10px;
        font-weight: 700;
        padding: 2px 6px;
        border-radius: 4px;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 4px;
    }
    .val-bullish { background: rgba(34, 197, 94, 0.1); color: #22c55e; }
    .val-bearish { background: rgba(239, 68, 68, 0.1); color: #ef4444; }
    .val-neutral { background: rgba(148, 163, 184, 0.1); color: #94a3b8; }
    
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
    
    /* Checkbox Styling */
    .stCheckbox > label {
        color: #94a3b8 !important;
        font-size: 11px !important;
        font-weight: 600 !important;
    }

    /* Hide Streamlit components */
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
    
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp12 - exp26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    
    # BB
    df['BB_Mid'] = df['Close'].rolling(window=20).mean()
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Mid'] + (df['BB_Std'] * 2)
    df['BB_Lower'] = df['BB_Mid'] - (df['BB_Std'] * 2)
    return df

def get_scores(df, options):
    if df is None or len(df) < 2: return 0, 0, "Wait", {}
    latest = df.iloc[-1]
    
    breakdown = {
        'trend': 'Neutral',
        'rsi': 'Neutral',
        'macd': 'Neutral',
        'volume': 'Neutral',
        'iv': 'Neutral'
    }
    
    c_score, p_score = 40, 40 # Base neutrality
    
    # 1. Trend (Price vs SMA50)
    sma50 = latest.get('SMA50', latest['Close'])
    if latest['Close'] > sma50: 
        c_score += 15
        breakdown['trend'] = f"Above MA50 (+15c)"
    else: 
        p_score += 15
        breakdown['trend'] = f"Below MA50 (+15p)"
        
    # 2. RSI Sentiment
    rsi = latest.get('RSI', 50)
    if rsi < 35: 
        c_score += 20
        breakdown['rsi'] = f"{int(rsi)} (Oversold +20c)"
    elif rsi > 65: 
        p_score += 20
        breakdown['rsi'] = f"{int(rsi)} (Overbought +20p)"
    else:
        breakdown['rsi'] = f"{int(rsi)} (Neutral)"

    # 3. MACD Momentum
    macd = latest.get('MACD', 0)
    signal = latest.get('MACD_Signal', 0)
    if macd > signal:
        c_score += 15
        breakdown['macd'] = f"Bullish Cross (+15c)"
    else:
        p_score += 15
        breakdown['macd'] = f"Bearish Cross (+15p)"
        
    # 4. Options Volume Imbalance
    if options:
        c_vol = options['calls']['volume'].sum()
        p_vol = options['puts']['volume'].sum()
        total_vol = c_vol + p_vol
        if total_vol > 0:
            c_pct = (c_vol / total_vol) * 100
            if c_pct > 55: 
                c_score += 15
                breakdown['volume'] = f"Call Heavy (+15c)"
            elif c_pct < 45:
                p_score += 15
                breakdown['volume'] = f"Put Heavy (+15p)"
            else:
                breakdown['volume'] = "Balanced"
        else:
            breakdown['volume'] = "No Data"
            
    # 5. IV Regime
    if options:
        avg_iv = options['calls']['impliedVolatility'].mean()
        iv_display = f"{int(avg_iv * 100)}%"
        if avg_iv < 0.2: breakdown['iv'] = f"Low ({iv_display})"
        elif avg_iv > 0.5: breakdown['iv'] = f"High ({iv_display})"
        else: breakdown['iv'] = f"Normal ({iv_display})"

    status = "Strong" if c_score > 75 or p_score > 75 else "Moderate" if c_score > 60 or p_score > 60 else "Weak"
    return min(c_score, 100), min(p_score, 100), status, breakdown

def get_market_status():
    tz = pytz.timezone('US/Eastern')
    now = datetime.now(tz)
    if now.weekday() >= 5: return False, "CLOSED"
    m_open = now.replace(hour=9, minute=30, second=0)
    m_close = now.replace(hour=16, minute=0, second=0)
    return (m_open <= now <= m_close), "OPEN" if (m_open <= now <= m_close) else "CLOSED"

# --- APP UI ---
def main():
    st.sidebar.markdown("<h2 style='color:#f8fafc; font-size:1.2rem; margin-bottom:20px;'>📁 WATCHLIST</h2>", unsafe_allow_html=True)
    if 'watchlist' not in st.session_state:
        st.session_state.watchlist = ["AAPL", "TSLA", "SPY", "NFLX", "AMZN", "GOOGL"]
    
    new_t = st.sidebar.text_input("ADD SYMBOL", placeholder="e.g. NVDA").upper().strip()
    if st.sidebar.button("ADD TO LIST", use_container_width=True):
        if new_t and new_t not in st.session_state.watchlist:
            st.session_state.watchlist.append(new_t)
            st.rerun()
            
    selected_ticker = st.sidebar.selectbox("ACTIVE TERMINAL", st.session_state.watchlist)
    
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

    col_left, col_right = st.columns([1, 3])

    with col_left:
        df = get_history_data(selected_ticker)
        options = get_options_data(selected_ticker)
        df = calculate_indicators(df)
        c_score, p_score, strength, bdown = get_scores(df, options)
        
        # Signal Engine Card with Expanded Breakdown
        st.markdown(f"""
            <div class="optix-card">
                <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
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
                
                <div style="margin-top: 25px;">
                    <span style="font-size: 9px; font-weight: 700; color: #475569; letter-spacing: 1px; text-transform: uppercase;">Factor Breakdown</span>
                    <div class="breakdown-item">
                        <span class="breakdown-label">Price vs MA50</span>
                        <span class="breakdown-value {'val-bullish' if '+15c' in bdown['trend'] else 'val-bearish'}">{bdown['trend']}</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label">RSI Trend</span>
                        <span class="breakdown-value {'val-bullish' if '+20c' in bdown['rsi'] else 'val-bearish' if '+20p' in bdown['rsi'] else 'val-neutral'}">{bdown['rsi']}</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label">MACD Cross</span>
                        <span class="breakdown-value {'val-bullish' if '+15c' in bdown['macd'] else 'val-bearish'}">{bdown['macd']}</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label">Vol Imbalance</span>
                        <span class="breakdown-value {'val-bullish' if '+15c' in bdown['volume'] else 'val-bearish' if '+15p' in bdown['volume'] else 'val-neutral'}">{bdown['volume']}</span>
                    </div>
                    <div class="breakdown-item" style="border-bottom: none;">
                        <span class="breakdown-label">IV Regime</span>
                        <span class="breakdown-value val-neutral">{bdown['iv']}</span>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        if df is not None:
            price = df['Close'].iloc[-1]
            change = price - df['Close'].iloc[-2]
            st.markdown('<div class="optix-card">', unsafe_allow_html=True)
            st.metric(selected_ticker, f"${price:.2f}", f"{change:.2f}")
            st.markdown('</div>', unsafe_allow_html=True)

    with col_right:
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

        if options:
            st.markdown('<div class="optix-card">', unsafe_allow_html=True)
            
            # Header with Unusual Volume Filter
            col_opt_h1, col_opt_h2 = st.columns([2, 1])
            with col_opt_h1:
                st.markdown(f"<span style='font-size: 10px; font-weight: 700; color: #64748b; letter-spacing: 1px; display: block;'>OPTIONS FLOW: {options['expiry']}</span>", unsafe_allow_html=True)
            with col_opt_h2:
                unusual_only = st.checkbox("UNUSUAL VOL ONLY", key="unusual_filter")
            
            t1, t2 = st.tabs(["CALLS", "PUTS"])
            
            def process_contracts(df, filter_active):
                avg_vol = df['volume'].mean()
                if filter_active:
                    return df[ (df['volume'] > avg_vol * 2) | (df['volume'] > df['openInterest']) ].sort_values('volume', ascending=False)
                return df.sort_values('volume', ascending=False).head(10)

            with t1:
                calls_df = process_contracts(options['calls'], unusual_only)
                if calls_df.empty:
                    st.info("No unusual volume detected in Calls.")
                else:
                    st.dataframe(calls_df[['strike', 'lastPrice', 'volume', 'openInterest', 'impliedVolatility']], use_container_width=True)
            with t2:
                puts_df = process_contracts(options['puts'], unusual_only)
                if puts_df.empty:
                    st.info("No unusual volume detected in Puts.")
                else:
                    st.dataframe(puts_df[['strike', 'lastPrice', 'volume', 'openInterest', 'impliedVolatility']], use_container_width=True)
            
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
