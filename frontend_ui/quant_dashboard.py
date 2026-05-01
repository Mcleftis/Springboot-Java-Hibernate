# -*- coding: utf-8 -*-
"""
quant_dashboard.py — Streamlit Frontend
Bridges:
  • Java Spring Boot  → http://localhost:8080/api/quant/analyze/{symbol}
  • Python RAG Worker → http://localhost:8002/ask
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# ──────────────────────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────────────────────
JAVA_BASE_URL = "http://localhost:8080"
RAG_URL       = "http://localhost:8002/ask"

st.set_page_config(
    page_title="⚡ Quant Trading Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# CUSTOM CSS  — dark terminal aesthetic
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Global ── */
    .stApp { background-color: #0d0f14; color: #e2e8f0; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111318 0%, #0d0f14 100%);
        border-right: 1px solid #1e2433;
    }
    [data-testid="stSidebar"] * { color: #c9d1e0 !important; }

    /* ── Cards ── */
    .card {
        background: #161a24;
        border: 1px solid #1e2843;
        border-radius: 10px;
        padding: 18px 22px;
        margin-bottom: 14px;
    }
    .card-title {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #6b7fa3;
        margin-bottom: 6px;
    }
    .card-value {
        font-size: 1.65rem;
        font-weight: 700;
        color: #e2e8f0;
    }
    .card-sub { font-size: 0.8rem; color: #4a5568; margin-top: 2px; }

    /* ── Badges ── */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    .badge-bull { background: #0f3d2e; color: #34d399; border: 1px solid #34d399; }
    .badge-bear { background: #3d0f1a; color: #f87171; border: 1px solid #f87171; }
    .badge-neutral { background: #1e2433; color: #94a3b8; border: 1px solid #475569; }

    /* ── Order Block rows ── */
    .ob-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 10px 14px;
        border-radius: 8px;
        margin-bottom: 7px;
        border-left: 3px solid transparent;
    }
    .ob-bull { background: #0f2d22; border-left-color: #34d399; }
    .ob-bear { background: #2d0f17; border-left-color: #f87171; }
    .ob-label { font-size: 0.78rem; color: #94a3b8; }
    .ob-price { font-weight: 700; font-size: 0.95rem; color: #e2e8f0; }

    /* ── Chat ── */
    .chat-msg-user {
        background: #1a2744;
        border: 1px solid #2d4a8a;
        border-radius: 12px 12px 4px 12px;
        padding: 10px 14px;
        margin: 6px 0 6px 40px;
        color: #bfdbfe;
        font-size: 0.9rem;
    }
    .chat-msg-ai {
        background: #161e30;
        border: 1px solid #1e2843;
        border-radius: 12px 12px 12px 4px;
        padding: 10px 14px;
        margin: 6px 40px 6px 0;
        color: #c9d1e0;
        font-size: 0.9rem;
    }
    .chat-sender {
        font-size: 0.68rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .chat-sender-user { color: #60a5fa; }
    .chat-sender-ai   { color: #34d399; }

    /* ── Divider ── */
    hr { border-color: #1e2433; }

    /* ── Buttons ── */
    .stButton > button {
        background: linear-gradient(135deg, #1d4ed8, #2563eb);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        letter-spacing: 0.04em;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #2563eb, #3b82f6);
        transform: translateY(-1px);
    }

    /* ── Section headers ── */
    .section-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 24px 0 14px;
        padding-bottom: 8px;
        border-bottom: 1px solid #1e2433;
    }
    .section-header h3 { margin: 0; font-size: 1rem; color: #e2e8f0; }
    .section-header .dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #3b82f6;
        flex-shrink: 0;
    }

    /* ── Status pills ── */
    .status-up   { color: #34d399; font-weight: 700; }
    .status-down { color: #f87171; font-weight: 700; }

    /* ── Plotly override ── */
    .js-plotly-plot .plotly { background: transparent !important; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────
if "analysis_data"   not in st.session_state: st.session_state.analysis_data   = None
if "chat_history"    not in st.session_state: st.session_state.chat_history    = []
if "last_symbol"     not in st.session_state: st.session_state.last_symbol     = None
if "analysis_error"  not in st.session_state: st.session_state.analysis_error  = None


# ──────────────────────────────────────────────────────────────
# HELPERS — API calls
# ──────────────────────────────────────────────────────────────
def call_quant_analyze(symbol: str) -> dict:
    url = f"{JAVA_BASE_URL}/api/quant/analyze/{symbol}"
    try:
        resp = requests.post(url, timeout=30)
        resp.raise_for_status()
        return {"ok": True, "data": resp.json()}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "error": f"❌ Δεν μπορώ να συνδεθώ στο Java backend (port 8080). Τρέχει το Spring Boot;"}
    except requests.exceptions.Timeout:
        return {"ok": False, "error": "⏱️ Timeout — το quant_worker.py αργεί. Δοκίμασε ξανά."}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def call_rag_ask(question: str, user_id: str = "streamlit_user") -> dict:
    payload = {"question": question, "userId": user_id}
    try:
        resp = requests.post(RAG_URL, json=payload, timeout=60)
        resp.raise_for_status()
        body = resp.json()
        # rag_worker.py επιστρέφει {"result": "..."}
        answer = body.get("result") or body.get("data", {}).get("answer", "Χωρίς απάντηση.")
        return {"ok": True, "answer": answer}
    except requests.exceptions.ConnectionError:
        return {"ok": False, "answer": "❌ RAG Worker offline. Τρέχει το rag_worker.py στη port 8002;"}
    except requests.exceptions.Timeout:
        return {"ok": False, "answer": "⏱️ Timeout — το LLM αργεί να απαντήσει."}
    except Exception as e:
        return {"ok": False, "answer": f"Σφάλμα: {e}"}


# ──────────────────────────────────────────────────────────────
# HELPERS — Chart builders
# ──────────────────────────────────────────────────────────────
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
    """macd_data: list of {macd, signal, histogram}"""
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
    """Simple close-price line with optional OB zones."""
    closes = [p.get("close", 0) for p in prices]
    idx    = list(range(len(closes)))

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=idx, y=closes, name="Close",
                             line=dict(color="#38bdf8", width=1.8)))

    if order_blocks:
        for ob in order_blocks[:6]:          # max 6 zones for readability
            color = "rgba(52,211,153,0.08)" if ob.get("type") == "bullish" else "rgba(248,113,113,0.08)"
            border = "#34d399" if ob.get("type") == "bullish" else "#f87171"
            fig.add_hrect(
                y0=ob.get("low",  0),
                y1=ob.get("high", 0),
                fillcolor=color,
                line=dict(color=border, width=1),
                opacity=1,
            )

    fig.update_layout(**PLOTLY_LAYOUT, title="Price + Order Blocks", height=320)
    return fig


# ──────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ Quant Dashboard")
    st.markdown("---")

    # Symbol selector
    st.markdown("### 🎯 Σύμβολο")
    symbol = st.selectbox(
        "Επίλεξε σύμβολο",
        ["GOLD", "XAUUSD", "BTCUSD", "EURUSD", "NASDAQ", "SP500"],
        index=0,
        label_visibility="collapsed",
    )

    st.markdown("---")

    # Full Analysis button
    st.markdown("### 🔍 Ανάλυση")
    run_analysis = st.button("⚡  Full Analysis", use_container_width=True)

    st.markdown("---")

    # Service status (simple ping indicators)
    st.markdown("### 🔌 Services")

    def ping(url, timeout=2):
        try:
            requests.get(url, timeout=timeout)
            return True
        except Exception:
            return False

    java_up = ping(f"{JAVA_BASE_URL}/api/quant/health")
    rag_up  = ping("http://localhost:8002/health", timeout=2)

    java_dot = '<span class="status-up">● UP</span>'   if java_up  else '<span class="status-down">● DOWN</span>'
    rag_dot  = '<span class="status-up">● UP</span>'   if rag_up   else '<span class="status-down">● DOWN</span>'

    st.markdown(f"**Java :8080** {java_dot}", unsafe_allow_html=True)
    st.markdown(f"**RAG  :8002** {rag_dot}",  unsafe_allow_html=True)

    st.markdown("---")
    st.caption(f"🕐 {datetime.now().strftime('%H:%M:%S')}")


# ──────────────────────────────────────────────────────────────
# TRIGGER ANALYSIS
# ──────────────────────────────────────────────────────────────
if run_analysis:
    with st.spinner(f"🔄 Ανάλυση {symbol} μέσω Java → Quant Engine…"):
        result = call_quant_analyze(symbol)
    if result["ok"]:
        st.session_state.analysis_data  = result["data"]
        st.session_state.last_symbol    = symbol
        st.session_state.analysis_error = None
    else:
        st.session_state.analysis_error = result["error"]
        st.session_state.analysis_data  = None


# ──────────────────────────────────────────────────────────────
# MAIN AREA — Title row
# ──────────────────────────────────────────────────────────────
col_title, col_ts = st.columns([3, 1])
with col_title:
    sym_label = st.session_state.last_symbol or symbol
    st.markdown(f"# 📊 {sym_label} — Trading Dashboard")
with col_ts:
    if st.session_state.analysis_data:
        ts = st.session_state.analysis_data.get("timestamp", "")
        st.markdown(f"<div style='text-align:right;color:#4a5568;font-size:0.78rem;padding-top:22px'>{ts[:19].replace('T',' ')}</div>",
                    unsafe_allow_html=True)

# Error banner
if st.session_state.analysis_error:
    st.error(st.session_state.analysis_error)

# ── Empty state ──
if not st.session_state.analysis_data and not st.session_state.analysis_error:
    st.markdown("""
    <div style="text-align:center;padding:80px 20px;color:#4a5568">
        <div style="font-size:4rem">📡</div>
        <h3 style="color:#4a5568;margin-top:12px">Δεν υπάρχουν δεδομένα ακόμα</h3>
        <p>Επίλεξε σύμβολο και πάτα <b>⚡ Full Analysis</b> στο sidebar.</p>
    </div>
    """, unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# DASHBOARD (εμφανίζεται μόνο μετά από analysis)
# ──────────────────────────────────────────────────────────────
if st.session_state.analysis_data:
    raw       = st.session_state.analysis_data
    payload   = raw.get("data", raw)          # unwrap Java envelope if present

    # Unwrap nested "data" from QuantController response format
    inner     = payload.get("data", payload)  if isinstance(payload, dict) else {}

    indicators   = inner.get("indicators",    {})
    order_blocks = inner.get("order_blocks",  inner.get("orderBlocks", []))
    fvgs         = inner.get("fvgs",          inner.get("fair_value_gaps", []))
    wyckoff      = inner.get("wyckoff",       {})
    prices_raw   = inner.get("prices",        [])

    macd_data    = indicators.get("macd",     [])
    rsi_series   = indicators.get("rsi",      [])
    atr_val      = indicators.get("atr",      indicators.get("atr_latest", None))
    signal       = inner.get("signal",        indicators.get("signal", "—"))

    # ── KPI Cards ──
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

    # RSI latest
    rsi_last = round(rsi_series[-1], 1) if rsi_series else "—"
    rsi_badge = ("Overbought", "bear") if (isinstance(rsi_last, float) and rsi_last > 70) \
               else ("Oversold", "bull") if (isinstance(rsi_last, float) and rsi_last < 30) \
               else ("Neutral", "neutral")
    kpi_card(kpi1, "RSI (14)", rsi_last, badge=rsi_badge[0], badge_type=rsi_badge[1])

    # MACD latest
    macd_last = round(macd_data[-1].get("macd", 0), 4) if macd_data else "—"
    macd_sign = macd_data[-1].get("histogram", 0) if macd_data else 0
    kpi_card(kpi2, "MACD", macd_last,
             badge="Bullish" if macd_sign > 0 else "Bearish",
             badge_type="bull" if macd_sign > 0 else "bear")

    # ATR
    atr_display = round(float(atr_val), 4) if atr_val is not None else "—"
    kpi_card(kpi3, "ATR", atr_display, sub="Volatility")

    # Signal
    sig_lower = str(signal).lower()
    sig_type = "bull" if "buy" in sig_lower or "long" in sig_lower or "bullish" in sig_lower \
               else "bear" if "sell" in sig_lower or "short" in sig_lower or "bearish" in sig_lower \
               else "neutral"
    kpi_card(kpi4, "Signal", signal, badge_type=sig_type)

    # ── Charts ──
    st.markdown('<div class="section-header"><div class="dot"></div><h3>Charts</h3></div>', unsafe_allow_html=True)

    ch1, ch2 = st.columns([3, 2])

    with ch1:
        if prices_raw:
            st.plotly_chart(
                build_price_chart(prices_raw, order_blocks),
                use_container_width=True, config={"displayModeBar": False}
            )
        else:
            st.info("Δεν υπάρχουν τιμές για το price chart.")

    with ch2:
        if rsi_series:
            st.plotly_chart(
                build_rsi_chart(rsi_series),
                use_container_width=True, config={"displayModeBar": False}
            )
        else:
            st.info("Δεν υπάρχουν δεδομένα RSI.")

    if macd_data:
        st.plotly_chart(
            build_macd_chart(macd_data),
            use_container_width=True, config={"displayModeBar": False}
        )
    else:
        st.info("Δεν υπάρχουν δεδομένα MACD από το quant engine.")

    # ── Order Blocks + FVGs ──
    ob_col, fvg_col = st.columns(2)

    with ob_col:
        st.markdown('<div class="section-header"><div class="dot"></div><h3>Order Blocks</h3></div>', unsafe_allow_html=True)
        if order_blocks:
            for ob in order_blocks:
                ob_type  = ob.get("type", "bullish")
                cls      = "ob-bull" if ob_type == "bullish" else "ob-bear"
                icon     = "🟢" if ob_type == "bullish" else "🔴"
                low_p    = ob.get("low",   ob.get("low_price",  "?"))
                high_p   = ob.get("high",  ob.get("high_price", "?"))
                strength = ob.get("strength", ob.get("score", "—"))
                st.markdown(f"""
                <div class="ob-row {cls}">
                    <div>
                        <div class="ob-label">{icon} {ob_type.upper()} OB</div>
                        <div class="ob-price">{low_p} – {high_p}</div>
                    </div>
                    <div style="text-align:right">
                        <div class="ob-label">Strength</div>
                        <div class="ob-price">{strength}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="card"><span style="color:#4a5568">Δεν εντοπίστηκαν Order Blocks.</span></div>',
                        unsafe_allow_html=True)

    with fvg_col:
        st.markdown('<div class="section-header"><div class="dot"></div><h3>Fair Value Gaps</h3></div>', unsafe_allow_html=True)
        if fvgs:
            for fvg in fvgs:
                fvg_type = fvg.get("type", "bullish")
                cls      = "ob-bull" if fvg_type == "bullish" else "ob-bear"
                icon     = "🟢" if fvg_type == "bullish" else "🔴"
                low_p    = fvg.get("low",  "?")
                high_p   = fvg.get("high", "?")
                st.markdown(f"""
                <div class="ob-row {cls}">
                    <div>
                        <div class="ob-label">{icon} {fvg_type.upper()} FVG</div>
                        <div class="ob-price">{low_p} – {high_p}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div class="card"><span style="color:#4a5568">Δεν εντοπίστηκαν FVGs.</span></div>',
                        unsafe_allow_html=True)

    # ── Wyckoff Phase ──
    if wyckoff:
        st.markdown('<div class="section-header"><div class="dot"></div><h3>Wyckoff Analysis</h3></div>', unsafe_allow_html=True)
        phase = wyckoff.get("phase", wyckoff.get("current_phase", "—"))
        bias  = wyckoff.get("bias",  wyckoff.get("market_bias",   "—"))
        note  = wyckoff.get("note",  wyckoff.get("description",   ""))
        w1, w2, w3 = st.columns(3)
        kpi_card(w1, "Phase",      phase)
        kpi_card(w2, "Market Bias", bias)
        kpi_card(w3, "Notes",      note[:60] + "…" if len(str(note)) > 60 else note)

    st.markdown("---")


# ──────────────────────────────────────────────────────────────
# RAG CHAT INTERFACE
# ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-header"><div class="dot" style="background:#34d399"></div><h3>🤖 AI Financial Analyst (RAG)</h3></div>', unsafe_allow_html=True)

# Render chat history
chat_container = st.container()
with chat_container:
    if not st.session_state.chat_history:
        st.markdown("""
        <div style="color:#4a5568;font-size:0.85rem;padding:12px 0">
            💬 Ρώτα τον AI Analyst για οποιοδήποτε market topic — π.χ.
            <i>"What does the RSI indicate for GOLD?"</i>
        </div>
        """, unsafe_allow_html=True)
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
                <div class="chat-sender chat-sender-ai">⚡ AI Analyst</div>
                {msg["content"]}
            </div>""", unsafe_allow_html=True)

# Input row
input_col, btn_col = st.columns([5, 1])
with input_col:
    user_question = st.text_input(
        "question_input",
        placeholder="π.χ. 'Τι δείχνει το MACD για GOLD;' ή 'Explain Wyckoff accumulation'",
        label_visibility="collapsed",
        key="chat_input",
    )
with btn_col:
    send_btn = st.button("Send ➤", use_container_width=True)

if send_btn and user_question.strip():
    st.session_state.chat_history.append({"role": "user", "content": user_question.strip()})
    with st.spinner("🤔 AI Analyst thinking…"):
        rag_result = call_rag_ask(user_question.strip())
    st.session_state.chat_history.append({
        "role": "assistant",
        "content": rag_result["answer"]
    })
    st.rerun()

# Clear chat button
if st.session_state.chat_history:
    if st.button("🗑️ Clear Chat", key="clear_chat"):
        st.session_state.chat_history = []
        st.rerun()
