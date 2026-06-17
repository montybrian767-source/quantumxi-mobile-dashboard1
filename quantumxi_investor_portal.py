
import hashlib
import hmac
from datetime import datetime
import pandas as pd
import numpy as np
import streamlit as st

st.set_page_config(
    page_title="QuantumXI Investor Portal",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

DEFAULT_ADMIN_EMAIL = "admin@quantumxi.local"
DEFAULT_ADMIN_PASSWORD = "admin123"

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at top left, rgba(34, 211, 238, 0.18), transparent 34%),
        radial-gradient(circle at top right, rgba(168, 85, 247, 0.16), transparent 30%),
        linear-gradient(180deg, #020617 0%, #07111f 45%, #020617 100%);
    color: #e5f6ff;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617 0%, #0f172a 100%);
    border-right: 1px solid rgba(34, 211, 238, .25);
}

div[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(15, 23, 42, .95), rgba(8, 17, 31, .95));
    border: 1px solid rgba(34, 211, 238, .30);
    border-radius: 18px;
    padding: 18px 18px 14px 18px;
    box-shadow: 0 0 28px rgba(34, 211, 238, .08);
}

div[data-testid="stMetric"] label {
    color: #93c5fd !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: .08em;
}

div[data-testid="stMetricValue"] {
    color: #67e8f9 !important;
    font-weight: 800 !important;
}

h1, h2, h3 {
    color: #f8fafc;
    letter-spacing: -0.04em;
}

.qxi-hero {
    border: 1px solid rgba(34, 211, 238, .38);
    border-radius: 26px;
    padding: 30px;
    background:
        linear-gradient(135deg, rgba(14, 165, 233, .18), rgba(168, 85, 247, .10)),
        rgba(2, 6, 23, .72);
    box-shadow: 0 0 45px rgba(34, 211, 238, .12);
    margin-bottom: 22px;
}

.qxi-title {
    font-size: 52px;
    font-weight: 900;
    margin: 0;
    color: #ffffff;
    letter-spacing: -0.06em;
}

.qxi-subtitle {
    color: #22d3ee;
    font-size: 18px;
    font-weight: 700;
    margin-top: 4px;
}

.qxi-pill {
    display: inline-block;
    padding: 7px 13px;
    margin-right: 8px;
    border-radius: 999px;
    background: rgba(34, 211, 238, .10);
    border: 1px solid rgba(34, 211, 238, .35);
    color: #a5f3fc;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: .05em;
}

.qxi-card {
    border: 1px solid rgba(148, 163, 184, .22);
    border-radius: 22px;
    padding: 22px;
    background: rgba(15, 23, 42, .82);
    box-shadow: 0 0 36px rgba(2, 132, 199, .08);
}

.qxi-buy {
    color: #4ade80;
    font-weight: 900;
}

.qxi-watch {
    color: #fbbf24;
    font-weight: 900;
}

.qxi-avoid {
    color: #fb7185;
    font-weight: 900;
}

.qxi-small {
    color: #94a3b8;
    font-size: 13px;
}

.stDataFrame {
    border: 1px solid rgba(34, 211, 238, .18);
    border-radius: 18px;
    overflow: hidden;
}

.stButton > button {
    background: linear-gradient(135deg, #0891b2, #7c3aed);
    color: white;
    border: 0;
    border-radius: 12px;
    font-weight: 800;
    padding: .65rem 1rem;
    box-shadow: 0 0 24px rgba(34, 211, 238, .18);
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #10b981, #0891b2);
    color: white;
    border: 0;
    border-radius: 12px;
    font-weight: 800;
}

[data-testid="stAlert"] {
    border-radius: 16px;
}
</style>
"""

def hash_pw(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def init_state():
    if "users" not in st.session_state:
        st.session_state.users = {
            DEFAULT_ADMIN_EMAIL: {
                "password_hash": hash_pw(DEFAULT_ADMIN_PASSWORD),
                "role": "admin",
                "created_at": datetime.now().isoformat()
            }
        }
    if "watchlists" not in st.session_state:
        st.session_state.watchlists = {}
    if "consensus_df" not in st.session_state:
        st.session_state.consensus_df = pd.DataFrame()

def authenticate(email, password):
    email = email.lower().strip()
    user = st.session_state.users.get(email)
    if not user:
        return None
    if hmac.compare_digest(user["password_hash"], hash_pw(password)):
        return user["role"]
    return None

def create_user(email, password, role="client"):
    email = email.lower().strip()
    if not email or not password:
        return False, "Email and password required."
    if email in st.session_state.users:
        return False, "User already exists."
    st.session_state.users[email] = {
        "password_hash": hash_pw(password),
        "role": role,
        "created_at": datetime.now().isoformat()
    }
    st.session_state.watchlists.setdefault(email, [])
    return True, "Client login created."

def normalize_columns(df):
    rename = {}
    for c in df.columns:
        key = str(c).lower().strip()
        if key in ["symbol", "ticker"]:
            rename[c] = "symbol"
        elif key in ["decision", "rating"]:
            rename[c] = "decision"
        elif key in ["consensus_score", "consensus", "score"]:
            rename[c] = "consensus_score"
        elif key in ["live_score", "live"]:
            rename[c] = "live_score"
        elif key in ["adaptive_score", "adaptive"]:
            rename[c] = "adaptive_score"
        elif key in ["historical_score", "historical"]:
            rename[c] = "historical_score"
        elif key in ["risk_score", "risk"]:
            rename[c] = "risk_score"
        elif key in ["reason", "note", "notes"]:
            rename[c] = "reason"
    df = df.rename(columns=rename)
    if "symbol" in df.columns:
        df["symbol"] = df["symbol"].astype(str).str.upper()
    for c in ["consensus_score","live_score","adaptive_score","historical_score","risk_score"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "decision" not in df.columns:
        if "consensus_score" in df.columns:
            df["decision"] = df["consensus_score"].apply(score_to_decision)
        else:
            df["decision"] = "WATCH"
    if "reason" not in df.columns:
        df["reason"] = "QuantumXI consensus output"
    return df

def score_to_decision(x):
    try:
        x = float(x)
        if x >= 75: return "STRONG BUY"
        if x >= 65: return "BUY"
        if x >= 50: return "WATCH"
        return "AVOID"
    except Exception:
        return "WATCH"

def demo_data():
    return pd.DataFrame([
        {"symbol":"NVDA","decision":"STRONG BUY","consensus_score":86.4,"live_score":78.2,"adaptive_score":91.5,"historical_score":88.1,"risk_score":63.4,"reason":"adaptive strong, historical strong, live positive"},
        {"symbol":"PANW","decision":"BUY","consensus_score":73.8,"live_score":66.4,"adaptive_score":82.1,"historical_score":91.2,"risk_score":58.9,"reason":"historical strong, adaptive positive"},
        {"symbol":"MSFT","decision":"BUY","consensus_score":70.2,"live_score":63.1,"adaptive_score":76.3,"historical_score":80.4,"risk_score":72.7,"reason":"quality and risk profile positive"},
        {"symbol":"AMAT","decision":"BUY","consensus_score":69.6,"live_score":61.2,"adaptive_score":79.4,"historical_score":83.5,"risk_score":61.0,"reason":"semiconductor leadership, historical strength"},
        {"symbol":"AAPL","decision":"WATCH","consensus_score":58.7,"live_score":54.2,"adaptive_score":62.3,"historical_score":68.2,"risk_score":74.1,"reason":"mixed evidence"},
        {"symbol":"TSLA","decision":"AVOID","consensus_score":42.9,"live_score":44.1,"adaptive_score":38.7,"historical_score":51.2,"risk_score":29.5,"reason":"higher risk, weak consensus"}
    ])

def get_df():
    df = st.session_state.consensus_df
    if df.empty:
        return demo_data()
    return df

def decision_badge(decision):
    d = str(decision).upper()
    if "STRONG" in d:
        return "🟢 STRONG BUY"
    if d == "BUY":
        return "🟩 BUY"
    if d == "WATCH":
        return "🟨 WATCH"
    return "🔴 AVOID"

def hero(title, subtitle, pills=None):
    pills = pills or []
    pill_html = "".join([f"<span class='qxi-pill'>{p}</span>" for p in pills])
    st.markdown(f"""
    <div class="qxi-hero">
        <div class="qxi-title">{title}</div>
        <div class="qxi-subtitle">{subtitle}</div>
        <div style="margin-top:18px;">{pill_html}</div>
    </div>
    """, unsafe_allow_html=True)

def login_screen():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.25, 1])
    with c2:
        st.markdown("""
        <div class="qxi-hero" style="text-align:center;">
            <div class="qxi-title">QUANTUMXI</div>
            <div class="qxi-subtitle">Professional Investor Portal</div>
            <div style="margin-top:16px;">
                <span class="qxi-pill">AI RANKINGS</span>
                <span class="qxi-pill">20-YEAR DATA</span>
                <span class="qxi-pill">CONSENSUS SIGNALS</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        with st.container(border=True):
            st.subheader("Secure Client Login")
            email = st.text_input("Email", value=DEFAULT_ADMIN_EMAIL)
            password = st.text_input("Password", type="password", value=DEFAULT_ADMIN_PASSWORD)
            if st.button("Login", use_container_width=True):
                role = authenticate(email, password)
                if role:
                    st.session_state.logged_in = True
                    st.session_state.email = email.lower().strip()
                    st.session_state.role = role
                    st.rerun()
                else:
                    st.error("Invalid login.")
            st.caption("Demo login: admin@quantumxi.local / admin123")

def sidebar():
    st.sidebar.title("⚡ QuantumXI")
    st.sidebar.caption(f"User: {st.session_state.email}")
    st.sidebar.caption(f"Role: {st.session_state.role}")
    page = st.sidebar.radio("Navigation", ["Command Center", "Top Ideas", "Watchlist", "Research Reports", "Admin"])
    if st.sidebar.button("Logout"):
        for k in ["logged_in", "email", "role"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()
    return page

def command_center():
    df = get_df()
    hero("Investor Command Center", "Client-facing consensus intelligence dashboard", ["LIVE PORTAL", "DECISION SUPPORT", "RESEARCH ONLY"])

    strong = int((df["decision"] == "STRONG BUY").sum()) if "decision" in df else 0
    buy = int((df["decision"] == "BUY").sum()) if "decision" in df else 0
    watch = int((df["decision"] == "WATCH").sum()) if "decision" in df else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Consensus Rows", f"{len(df):,}")
    c2.metric("Strong Buy", strong)
    c3.metric("Buy", buy)
    c4.metric("Watch", watch)
    c5.metric("Portal Status", "ONLINE")

    st.divider()

    top = df.iloc[0]
    left, right = st.columns([1.1, 1])
    with left:
        st.markdown("### Top Consensus Idea")
        st.markdown(f"""
        <div class="qxi-card">
            <div style="font-size:48px;font-weight:900;color:#ffffff;">{top.get("symbol","-")}</div>
            <div style="font-size:24px;margin-top:4px;" class="qxi-buy">{decision_badge(top.get("decision","-"))}</div>
            <div style="margin-top:18px;color:#93c5fd;">Consensus Score</div>
            <div style="font-size:42px;font-weight:900;color:#22d3ee;">{float(top.get("consensus_score",0)):.2f}</div>
            <div class="qxi-small">Reason: {top.get("reason","-")}</div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("### Signal Mix")
        chart_cols = [c for c in ["live_score","adaptive_score","historical_score","risk_score"] if c in df.columns]
        if chart_cols:
            chart_data = pd.DataFrame({
                "Signal": ["Live", "Adaptive", "Historical", "Risk"],
                "Score": [
                    float(top.get("live_score", 0) or 0),
                    float(top.get("adaptive_score", 0) or 0),
                    float(top.get("historical_score", 0) or 0),
                    float(top.get("risk_score", 0) or 0),
                ]
            })
            st.bar_chart(chart_data.set_index("Signal"))

    st.markdown("### Top 10 Consensus Rankings")
    cols = [x for x in ["symbol","decision","consensus_score","live_score","adaptive_score","historical_score","risk_score","reason"] if x in df.columns]
    st.dataframe(df[cols].head(10), use_container_width=True, hide_index=True)

def top_ideas():
    df = get_df()
    hero("Top Ideas", "Ranked opportunities simplified for clients", ["STRONG BUY", "BUY", "WATCH", "AVOID"])
    selected = st.multiselect("Decision Filter", ["STRONG BUY","BUY","WATCH","AVOID"], default=["STRONG BUY","BUY"])
    view = df[df["decision"].isin(selected)] if "decision" in df.columns else df

    cols = [x for x in ["symbol","decision","consensus_score","live_score","adaptive_score","historical_score","risk_score","reason"] if x in view.columns]
    st.dataframe(view[cols], use_container_width=True, hide_index=True)

    st.subheader("Add to Watchlist")
    sym = st.text_input("Symbol").upper()
    if st.button("Add Symbol") and sym:
        wl = st.session_state.watchlists.setdefault(st.session_state.email, [])
        if sym not in wl:
            wl.append(sym)
        st.success(f"{sym} added to watchlist.")

def watchlist():
    df = get_df()
    hero("Watchlist", "Track the names clients care about", ["PORTFOLIO MONITOR", "RATINGS", "RESEARCH"])
    wl = st.session_state.watchlists.setdefault(st.session_state.email, [])
    if not wl:
        st.info("No symbols added yet. Add symbols from Top Ideas.")
        return
    view = df[df["symbol"].isin(wl)] if "symbol" in df.columns else pd.DataFrame({"symbol": wl})
    st.dataframe(view, use_container_width=True, hide_index=True)
    rem = st.text_input("Remove Symbol").upper()
    if st.button("Remove") and rem in wl:
        wl.remove(rem)
        st.rerun()

def reports():
    df = get_df()
    hero("Research Reports", "One-click client research snapshots", ["DOWNLOADABLE", "EXPLAINABLE", "CLIENT READY"])
    symbol = st.selectbox("Choose symbol", df["symbol"].tolist())
    row = df[df["symbol"] == symbol].iloc[0]

    a, b, c, d = st.columns(4)
    a.metric("Decision", row.get("decision","-"))
    b.metric("Consensus", f"{float(row.get('consensus_score',0)):.2f}")
    c.metric("Adaptive", f"{float(row.get('adaptive_score',0)):.2f}" if "adaptive_score" in row else "-")
    d.metric("Risk", f"{float(row.get('risk_score',0)):.2f}" if "risk_score" in row else "-")

    st.markdown("### Explanation")
    st.write(row.get("reason","-"))

    report = f"""QUANTUMXI RESEARCH SNAPSHOT

Symbol: {symbol}
Decision: {row.get('decision','-')}
Consensus Score: {row.get('consensus_score','-')}
Live Score: {row.get('live_score','-')}
Adaptive Score: {row.get('adaptive_score','-')}
Historical Score: {row.get('historical_score','-')}
Risk Score: {row.get('risk_score','-')}

Reason:
{row.get('reason','-')}

Disclaimer:
Research and decision-support software only. Not financial advice.
"""
    st.download_button("Download Client Report", report, file_name=f"{symbol}_QuantumXI_Report.txt")

def admin():
    hero("Admin Console", "Upload consensus files and manage demo client access", ["CSV UPLOAD", "CLIENT LOGINS", "DATA REFRESH"])
    if st.session_state.role != "admin":
        st.error("Admin only.")
        return

    st.subheader("Upload v38 Consensus CSV")
    uploaded = st.file_uploader("Upload v38_consensus_rankings.csv", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)
        df = normalize_columns(df)
        st.session_state.consensus_df = df
        st.success(f"Loaded {len(df)} consensus rows.")
        st.dataframe(df.head(20), use_container_width=True, hide_index=True)

    st.subheader("Create Client Login")
    email = st.text_input("Client email")
    pw = st.text_input("Temporary password", type="password")
    if st.button("Create Client"):
        ok, msg = create_user(email, pw)
        st.success(msg) if ok else st.error(msg)

    st.subheader("Current Users")
    users = pd.DataFrame([
        {"email": k, "role": v["role"], "created_at": v["created_at"]}
        for k, v in st.session_state.users.items()
    ])
    st.dataframe(users, use_container_width=True, hide_index=True)

    st.warning("Cloud demo note: data and users are session-based. Production should use Supabase/Postgres for persistent users and client data.")

def main():
    init_state()
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    if not st.session_state.get("logged_in"):
        login_screen()
        return
    page = sidebar()
    if page == "Command Center":
        command_center()
    elif page == "Top Ideas":
        top_ideas()
    elif page == "Watchlist":
        watchlist()
    elif page == "Research Reports":
        reports()
    elif page == "Admin":
        admin()

if __name__ == "__main__":
    main()
