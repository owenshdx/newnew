
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pytz
import os

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

# --- CONSTANTS & LOGGING ---
LOG_FILE = "signals_log.csv"

def log_signal(symbol, c_score, p_score, strength):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_entry = pd.DataFrame([{
        "timestamp": now,
        "symbol": symbol,
        "call_score": c_score,
        "put_score": p_score,
        "strength": strength
    }])
    if not os.path.isfile(LOG_FILE):
        new_entry.to_csv(LOG_FILE, index=False)
    else:
        new_entry.to_csv(LOG_FILE, mode='a', header=False, index=False)

# --- THEME INJECTION ---
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

    .optix-card {
        background-color: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(51, 65, 85, 0.5);
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }

    [data-testid="stSidebar"] {
        background-color: #0d1117;
        border-right: 1px solid #1e293b;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
    }

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
    .val-warning { background: rgba(245, 158, 11, 0.1); color: #f59e0b; }
    
    .market-badge {
        font-size: 10px;
        font-weight: 700;
        padding: 4px 12px;
        border-radius: 20px;
        display: inline-block;
    }
    .badge-open { background-color: rgba(34, 197, 94, 0.1); color: #22c55e; border: 1px solid rgba(34, 197, 94, 0.2); }
    .badge-closed { background-color: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); }
    
    .mock-banner-v2 {
        background: linear-gradient(90deg, #d97706 0%, #b45309 100%);
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        margin-bottom: 24px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .mock-banner-text {
        font-weight: 700;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
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

# --- MOCK DATA GENERATORS ---
def generate_mock_history(symbol):
    np.random.seed(abs(hash(symbol)) % 10000)
    base_price = 150.0 if symbol != 'SPY' else 500.0
    dates = pd.date_range(end=datetime.now(), periods=100, freq='15min')
    prices = base_price + np.cumsum(np.random.normal(0, 1, 100))
    df = pd.DataFrame({
        'Open': prices - np.random.uniform(0, 1, 100),
        'High': prices + np.random.uniform(0, 2, 100),
        'Low': prices - np.random.uniform(0, 2, 100),
        'Close': prices,
        'Volume': np.random.randint(10000, 1000000, 100)
    }, index=dates)
    return df

def generate_mock_options(symbol):
    np.random.seed(abs(hash(symbol)) % 10000)
    base_price = 150.0 if symbol != 'SPY' else 500.0
    strikes = [base_price + i for i in range(-5, 6)]
    def create_chain(is_call=True):
        return pd.DataFrame({
            'strike': strikes,
            'lastPrice': [max(0.1, (base_price - s if not is_call else s - base_price) + np.random.uniform(1, 5)) for s in strikes],
            'volume': np.random.randint(10, 5000, len(strikes)),
            'openInterest': np.random.randint(100, 10000, len(strikes)),
            'impliedVolatility': np.random.uniform(0.2, 0.8, len(strikes))
        })
    return {
        'calls': create_chain(True),
        'puts': create_chain(False),
        'expiry': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
    }

# --- DATA ENGINE ---
@st.cache_data(ttl=60)
def get_history_data(symbol, period="5d", interval="1m"):
    try:
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df is None or df.empty:
            raise ValueError("Yahoo Finance returned empty DataFrame.")
        st.session_state.is_mock = False
        return df
    except Exception as e:
        st.session_state.is_mock = True
        st.session_state.last_error = str(e)
        return generate_mock_history(symbol)

@st.cache_data(ttl=300)
def get_options_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        if not ticker.options:
            raise ValueError(f"No options listed for {symbol}.")
        expiry = ticker.options[0]
        chain = ticker.option_chain(expiry)
        st.session_state.is_mock = False
        return {'calls': chain.calls, 'puts': chain.puts, 'expiry': expiry}
    except Exception as e:
        st.session_state.is_mock = True
        return generate_mock_options(symbol)

@st.cache_data(ttl=3600)
def get_earnings_days(symbol):
    try:
        ticker = yf.Ticker(symbol)
        calendar = ticker.calendar
        if calendar is not None and not calendar.empty:
            earning_date = calendar.iloc[0, 0]
            if isinstance(earning_date, datetime):
                days_to = (earning_date.date() - datetime.now().date()).days
                return days_to
        return 99
    except:
        return 99

def calculate_indicators(df):
    if df is None or df.empty: return df
    df = df.copy()
    df['SMA50'] = df['Close'].rolling(window=50).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    df['RSI'] = 100 - (100 / (1 + rs))
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp12 - exp26
    df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['BB_Mid'] = df['Close'].rolling(window=20).mean()
    df['BB_Std'] = df['Close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Mid'] + (df['BB_Std'] * 2)
    df['BB_Lower'] = df['BB_Mid'] - (df['BB_Std'] * 2)
    return df

def get_scores(df, options, earnings_days, symbol):
    # Market Hours Check
    is_open, _ = get_market_status()
    if not is_open and symbol in st.session_state.frozen_signals:
        return st.session_state.frozen_signals[symbol]

    if df is None or len(df) < 2: return 0, 0, "Wait", {}
    
    latest = df.iloc[-1]
    breakdown = {
        'trend': 'Neutral', 
        'rsi': 'Neutral', 
        'macd': 'Neutral', 
        'volume': 'Neutral', 
        'iv': 'Neutral',
        'earningsDesc': 'Safe'
    }
    
    # Base Neutrality
    c_score, p_score = 30, 30 
    
    # 1. Trend (Price vs SMA50) - 15 pts
    sma50 = latest.get('SMA50', latest['Close'])
    if latest['Close'] > sma50: 
        c_score += 15
        breakdown['trend'] = f"Above MA50 (+15c)"
    else: 
        p_score += 15
        breakdown['trend'] = f"Below MA50 (+15p)"
        
    # 2. RSI (Relative Strength) - 20 pts
    rsi = latest.get('RSI', 50)
    if rsi < 35: 
        c_score += 20
        breakdown['rsi'] = f"{int(rsi)} Oversold (+20c)"
    elif rsi > 65: 
        p_score += 20
        breakdown['rsi'] = f"{int(rsi)} Overbought (+20p)"
    else:
        breakdown['rsi'] = f"{int(rsi)} Neutral"

    # 3. MACD Cross - 15 pts
    macd = latest.get('MACD', 0)
    signal = latest.get('MACD_Signal', 0)
    if macd > signal:
        c_score += 15
        breakdown['macd'] = f"Bullish Cross (+15c)"
    else:
        p_score += 15
        breakdown['macd'] = f"Bearish Cross (+15p)"
        
    # 4. Options Volume Imbalance - 15 pts
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
            
    # 5. IV Regime - 10 pts
    if options:
        avg_iv = options['calls']['impliedVolatility'].mean()
        if avg_iv < 0.25:
            c_score += 5
            p_score += 5
            breakdown['iv'] = "Low IV (Cheap Options)"
        elif avg_iv > 0.60:
            c_score -= 5
            p_score -= 5
            breakdown['iv'] = "High IV (Expensive/Risk)"
        else:
            breakdown['iv'] = "Normal"

    # 6. Earnings Proximity Penalty
    if earnings_days <= 7:
        penalty = 15
        c_score -= penalty
        p_score -= penalty
        breakdown['earningsDesc'] = f"Close ({earnings_days}d) -{penalty} Penalty"
    else:
        breakdown['earningsDesc'] = f"Safe ({earnings_days}d)"

    # Final Classification
    c_score = max(0, min(100, c_score))
    p_score = max(0, min(100, p_score))
    
    strength = "Strong" if c_score >= 80 or p_score >= 80 else "Moderate" if c_score >= 60 or p_score >= 60 else "Weak"
    
    result = (int(c_score), int(p_score), strength, breakdown)
    
    # Store for freeze logic and log to CSV
    if is_open:
        st.session_state.frozen_signals[symbol] = result
        log_signal(symbol, c_score, p_score, strength)
        
    return result

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
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
            <div style="display: flex; align-items: center; gap: 15px;">
                <div style="background-color: #3b82f6; width: 35px; height: 35px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 900; color: white;">O</div>
                <h1 style="font-size: 1.5rem; font-weight: 800; margin: 0;">Optix <span style="color: #64748b; font-weight: 400; font-size: 0.9rem;">PRO TERMINAL</span></h1>
            </div>
            <div class="market-badge {badge_class}">● {status_str}</div>
        </div>
    """, unsafe_allow_html=True)

    # Fallback Banner
    if st.session_state.is_mock:
        col_b1, col_b2 = st.columns([4, 1])
        with col_b1:
            st.markdown(f"""
                <div class="mock-banner-v2">
                    <div class="mock-banner-text">⚠️ MOCK DATA ACTIVE — Fetching failed: {st.session_state.last_error or "Empty Response"}</div>
                </div>
            """, unsafe_allow_html=True)
        with col_b2:
            if st.button("Retry Live Data", type="primary", use_container_width=True):
                st.cache_data.clear()
                st.session_state.is_mock = False
                st.rerun()

    col_left, col_right = st.columns([1, 3])

    df = get_history_data(selected_ticker)
    options = get_options_data(selected_ticker)
    earnings_days = get_earnings_days(selected_ticker)
    df = calculate_indicators(df)
    c_score, p_score, strength, bdown = get_scores(df, options, earnings_days, selected_ticker)

    with col_left:
        # Signal Engine Card
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
                        <span class="breakdown-label">Trend (MA50)</span>
                        <span class="breakdown-value {'val-bullish' if '+15c' in bdown.get('trend', '') else 'val-bearish'}">{bdown.get('trend', 'N/A')}</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label">RSI Trend</span>
                        <span class="breakdown-value {'val-bullish' if '+20c' in bdown.get('rsi', '') else 'val-bearish' if '+20p' in bdown.get('rsi', '') else 'val-neutral'}">{bdown.get('rsi', 'N/A')}</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label">MACD Momentum</span>
                        <span class="breakdown-value {'val-bullish' if '+15c' in bdown.get('macd', '') else 'val-bearish'}">{bdown.get('macd', 'N/A')}</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label">Option Flow</span>
                        <span class="breakdown-value {'val-bullish' if '+15c' in bdown.get('volume', '') else 'val-bearish' if '+15p' in bdown.get('volume', '') else 'val-neutral'}">{bdown.get('volume', 'N/A')}</span>
                    </div>
                    <div class="breakdown-item">
                        <span class="breakdown-label">Earnings Prox</span>
                        <span class="breakdown-value {'val-warning' if 'Penalty' in bdown.get('earningsDesc', '') else 'val-neutral'}">{bdown.get('earningsDesc', 'Safe')}</span>
                    </div>
                    <div class="breakdown-item" style="border-bottom: none;">
                        <span class="breakdown-label">IV Regime</span>
                        <span class="breakdown-value val-neutral">{bdown.get('iv', 'Normal')}</span>
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
            
        # Log Review Section
        if os.path.exists(LOG_FILE):
            st.markdown('<div class="optix-card">', unsafe_allow_html=True)
            st.markdown("<span style='font-size: 10px; font-weight: 700; color: #64748b; letter-spacing: 1px;'>SIGNAL HISTORY</span>", unsafe_allow_html=True)
            log_df = pd.read_csv(LOG_FILE).tail(5)
            st.dataframe(log_df, use_container_width=True)
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
            
            # Review past signals on chart
            if os.path.exists(LOG_FILE):
                past_sigs = pd.read_csv(LOG_FILE)
                past_sigs = past_sigs[past_sigs['symbol'] == selected_ticker]
                # Filter signals to match current chart date range if possible
                for i, row in past_sigs.tail(5).iterrows():
                    fig.add_annotation(
                        text=f"S:{row['strength'][:1]}",
                        showarrow=True, arrowhead=1,
                        x=df.index[-1], y=row['call_score'] if row['call_score'] > row['put_score'] else row['put_score'],
                        bgcolor="#3b82f6", font=dict(color="white", size=8)
                    )

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
                st.dataframe(calls_df[['strike', 'lastPrice', 'volume', 'openInterest', 'impliedVolatility']], use_container_width=True)
            with t2:
                puts_df = process_contracts(options['puts'], unusual_only)
                st.dataframe(puts_df[['strike', 'lastPrice', 'volume', 'openInterest', 'impliedVolatility']], use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
