import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

PYTHON_QUANT_URL = "http://localhost:8003/analyze"
RAG_URL          = "http://localhost:8002/ask"

st.set_page_config(
    page_title="Quant Trading Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp { background-color: #0d0f14; color: #e2e8f0; }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #111318 0%, #0d0f14 100%); border-right: 1px solid #1e2433; }
    [data-testid="stSidebar"] * { color: #c9d1e0 !important; }
    .card { background: #161a24; border: 1px solid #1e2843; border-radius: 10px; padding: 18px 22px; margin-bottom: 14px; }
    .card-title { font-size: 0.75rem; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: #6b7fa3; margin-bottom: 6px; }
    .card-value { font-size: 1.65rem; font-weight: 700; color: #e2e8f0; }
    .card-sub { font-size: 0.8rem; color: #4a5568; margin-top: 2px; }
    .badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 0.72rem; font-weight: 600; }
    .badge-bull { background: #0f3d2e; color: #34d399; border: 1px solid #34d399; }
    .badge-bear { background: #3d0f1a; color: #f87171; border: 1px solid #f87171; }
    .badge-neutral { background: #1e2433; color: #94a3b8; border: 1px solid #475569; }
    .ob-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 14px; border-radius: 8px; margin-bottom: 7px; border-left: 3px solid transparent; }
    .ob-bull { background: #0f2d22; border-left-color: #34d399; }
    .ob-bear { background: #2d0f17; border-left-color: #f87171; }
    .ob-label { font-size: 0.78rem; color: #94a3b8; }
    .ob-price { font-weight: 700; font-size: 0.95rem; color: #e2e8f0; }
    .chat-msg-user { background: #1a2744; border: 1px solid #2d4a8a; border-radius: 12px 12px 4px 12px; padding: 10px 14px; margin: 6px 0 6px 40px; color: #bfdbfe; font-size: 0.9rem; }
    .chat-msg-ai { background: #161e30; border: 1px solid #1e2843; border-radius: 12px 12px 12px 4px; padding: 10px 14px; margin: 6px 40px 6px 0; color: #c9d1e0; font-size: 0.9rem; }
    .chat-sender { font-size: 0.68rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 4px; }
    .chat-sender-user { color: #60a5fa; }
    .chat-sender-ai   { color: #34d399; }
    hr { border-color: #1e2433; }
    .stButton > button { background: linear-gradient(135deg, #1d4ed8, #2563eb); color: white; border: none; border-radius: 8px; padding: 10px 24px; font-weight: 600; }
    .section-header { display: flex; align-items: center; gap: 10px; margin: 24px 0 14px; padding-bottom: 8px; border-bottom: 1px solid #1e2433; }
    .section-header h3 { margin: 0; font-size: 1rem; color: #e2e8f0; }
    .section-header .dot { width: 8px; height: 8px; border-radius: 50%; background: #3b82f6; flex-shrink: 0; }
    .status-up   { color: #34d399; font-weight: 700; }
    .status-down { color: #f87171; font-weight: 700; }
    .js-plotly-plot .plotly { background: transparent !important; }
</style>
""", unsafe_allow_html=True)

if "analysis_data"   not in st.session_state: st.session_state.analysis_data   = None
if "chat_history"    not in st.session_state: st.session_state.chat_history    = []
if "last_symbol"     not in st.session_state: st.session_state.last_symbol     = None
if "analysis_error"  not in st.session_state: st.session_state.analysis_error  = None

def call_quant_analyze(symbol: str) -> dict:
    import numpy as np
    mock_prices = [100 + i + np.random.uniform(-2, 2) for i in range(50)]
    payload = {
        "symbol": symbol,
        "prices": mock_prices
    }
    try:
        resp = requests.post(PYTHON_QUANT_URL, json=payload, timeout=30)
        resp.raise_for_status()
        return {"ok": True, "data": resp.json()}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": "Cannot connect to Python Quant Worker (port 8003)."}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "Timeout from Quant Worker."}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def call_rag_ask(question: str) -> dict:
    payload = {"question": question}
    try:
        resp = requests.post(RAG_URL, json=payload, timeout=60)
        resp.raise_for_status()
        body = resp.json()
        answer = body.get("result", "No answer provided.")
        return {"ok": True, "answer": answer}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "answer": "RAG Worker offline (port 8002)."}
    except requests.exceptions.Timeout:
        return {"ok": False, "answer": "Timeout from RAG Worker."}
    except Exception as e:
        return {"ok": False, "answer": f"Error: {e}"}

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#10131c",
    font=dict(color="#94a3b8", size=11),
    margin=dict(l=10, r=10, t=36, b=10),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e2433"),
    xaxis=dict(gridcolor="#1a2035", zerolinecolor="#1a2035"),
    yaxis=dict(gridcolor="#1a2035", zerolinecolor="#1a2035"),
)

def build_macd_chart(macd_data: list) -> go.Figure:
    df = pd.DataFrame(macd_data)
    idx = list(range(len(df)))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=idx, y=df.get("macd",    pd.Series([])),
                             name="MACD",   line=dict(color="#3b82f6", width=1.8)))
    fig.add_trace(go.Scatter(x=idx, y=df.get("signal",  pd.Series([])),
                             name="Signal", line=dict(color="#f59e0b", width=1.5, dash="dash")))
    if "histogram" in df.columns:
        colors = ["#34d399" if v >= 0 else "#f87171" for v in df["histogram"]]
        fig.add_trace(go.Bar(x=idx, y=df["histogram"], name="Histogram",
                             marker_color=colors, opacity=0.6))

    fig.update_layout(**PLOTLY_LAYOUT, title="MACD", height=280)
    return fig

def build_rsi_chart(rsi_series: list) -> go.Figure:
    idx = list(range(len(rsi_series)))
    fig = go.Figure()
    fig.add_hrect(y0=70, y1=100, fillcolor="#3d0f1a", opacity=0.25, line_width=0)
    fig.add_hrect(y0=0,  y1=30,  fillcolor="#0f3d2e", opacity=0.25, line_width=0)
    fig.add_hline(y=70, line_color="#f87171", line_dash="dot", line_width=1)
    fig.add_hline(y=30, line_color="#34d399", line_dash="dot", line_width=1)
    fig.add_trace(go.Scatter(x=idx, y=rsi_series, name="RSI",
                             line=dict(color="#a78bfa", width=2), fill="tozeroy",
                             fillcolor="rgba(139,92,246,0.08)"))
    fig.update_layout(**PLOTLY_LAYOUT, title="RSI (14)", height=220,
                      yaxis=dict(**PLOTLY_LAYOUT["yaxis"], range=[0, 100]))
    return fig

def build_price_chart(prices: list, order_blocks: list = None) -> go.Figure:
    closes = [p.get("close", 0) if isinstance(p, dict) else p for p in prices]
    idx    = list(range(len(closes)))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=idx, y=closes, name="Close", line=dict(color="#38bdf8", width=1.8)))

    if order_blocks:
        for ob in order_blocks[:6]:
            color = "rgba(52,211,153,0.08)" if ob.get("type") == "BULLISH_OB" else "rgba(248,113,113,0.08)"
            border = "#34d399" if ob.get("type") == "BULLISH_OB" else "#f87171"
            fig.add_hrect(
                y0=ob.get("zone_low",  0),
                y1=ob.get("zone_high", 0),
                fillcolor=color,
                line=dict(color=border, width=1),
                opacity=1,
            )

    fig.update_layout(**PLOTLY_LAYOUT, title="Price + Order Blocks", height=320)
    return fig

with st.sidebar:
    st.markdown("## Quant Dashboard")
    st.markdown("---")
    st.markdown("### Symbol")
    symbol = st.selectbox("Select symbol", ["GOLD", "XAUUSD", "BTCUSD", "EURUSD", "NASDAQ", "SP500"], index=0, label_visibility="collapsed")
    st.markdown("---")
    st.markdown("### Analysis")
    run_analysis = st.button("Full Analysis", use_container_width=True)
    st.markdown("---")
    st.markdown("### Services")

    def ping(url, timeout=2):
        try:
            requests.get(url, timeout=timeout)
            return True
        except Exception:
            return False

    quant_up = ping(f"http://localhost:8003/health")
    rag_up  = ping("http://localhost:8002/health", timeout=2)

    quant_dot = '<span class="status-up">UP</span>'   if quant_up  else '<span class="status-down">DOWN</span>'
    rag_dot  = '<span class="status-up">UP</span>'   if rag_up   else '<span class="status-down">DOWN</span>'

    st.markdown(f"**Quant :8003** {quant_dot}", unsafe_allow_html=True)
    st.markdown(f"**RAG  :8002** {rag_dot}",  unsafe_allow_html=True)
    st.markdown("---")
    st.caption(f"{datetime.now().strftime('%H:%M:%S')}")

if run_analysis:
    with st.spinner(f"Analyzing {symbol}..."):
        result = call_quant_analyze(symbol)
    if result["ok"]:
        st.session_state.analysis_data  = result["data"]
        st.session_state.last_symbol    = symbol
        st.session_state.analysis_error = None
    else:
        st.session_state.analysis_error = result["error"]
        st.session_state.analysis_data  = None

col_title, col_ts = st.columns([3, 1])
with col_title:
    sym_label = st.session_state.last_symbol or symbol
    st.markdown(f"# {sym_label} Trading Dashboard")

if st.session_state.analysis_error:
    st.error(st.session_state.analysis_error)

if not st.session_state.analysis_data and not st.session_state.analysis_error:
    st.markdown("""
    <div style="text-align:center;padding:80px 20px;color:#4a5568">
        <h3 style="color:#4a5568;margin-top:12px">No Data</h3>
    </div>
    """, unsafe_allow_html=True)

if st.session_state.analysis_data:
    inner = st.session_state.analysis_data
    indicators = inner.get("indicators", {})
    order_blocks = inner.get("smart_money", {}).get("order_blocks", [])
    fvgs = inner.get("smart_money", {}).get("fair_value_gaps", [])
    wyckoff = inner.get("wyckoff", {})
    
    rsi_val = indicators.get("rsi", {}).get("value")
    macd_data = indicators.get("macd", {})
    atr_val = indicators.get("atr", {}).get("value")
    
    st.markdown('<div class="section-header"><div class="dot"></div><h3>Key Indicators</h3></div>', unsafe_allow_html=True)

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    def kpi_card(col, title, value, sub="", badge=None, badge_type="neutral"):
        badge_html = f'<span class="badge badge-{badge_type}">{badge}</span>' if badge else ""
        col.markdown(f"""
        <div class="card">
            <div class="card-title">{title}</div>
            <div class="card-value">{value}</div>
            <div class="card-sub">{sub} {badge_html}</div>
        </div>
        """, unsafe_allow_html=True)

    kpi_card(kpi1, "RSI (14)", rsi_val if rsi_val else "N/A")
    kpi_card(kpi2, "MACD", macd_data.get("macd_line") if macd_data else "N/A")
    kpi_card(kpi3, "ATR", atr_val if atr_val else "N/A")
    kpi_card(kpi4, "Wyckoff Phase", wyckoff.get("phase", "N/A"))

st.markdown('<div class="section-header"><div class="dot" style="background:#34d399"></div><h3>AI Financial Analyst (RAG)</h3></div>', unsafe_allow_html=True)

chat_container = st.container()
with chat_container:
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div class="chat-msg-user">
                <div class="chat-sender chat-sender-user">You</div>
                {msg["content"]}
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-msg-ai">
                <div class="chat-sender chat-sender-ai">AI Analyst</div>
                {msg["content"]}
            </div>""", unsafe_allow_html=True)

input_col, btn_col = st.columns([5, 1])
with input_col:
    user_question = st.text_input("question_input", label_visibility="collapsed", key="chat_input")
with btn_col:
    send_btn = st.button("Send", use_container_width=True)

if send_btn and user_question.strip():
    st.session_state.chat_history.append({"role": "user", "content": user_question.strip()})
    with st.spinner("AI Analyst thinking..."):
        rag_result = call_rag_ask(user_question.strip())
    st.session_state.chat_history.append({"role": "assistant", "content": rag_result["answer"]})
    st.rerun()

if st.session_state.chat_history:
    if st.button("Clear Chat", key="clear_chat"):
        st.session_state.chat_history = []
        st.rerun()