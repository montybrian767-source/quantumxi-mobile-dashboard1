
import hashlib, hmac
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="QuantumXI Investor Portal", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

ADMIN_EMAIL = "admin@quantumxi.local"
ADMIN_PASSWORD = "admin123"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp {
    background: radial-gradient(circle at top left, rgba(34,211,238,.15), transparent 32%),
                radial-gradient(circle at top right, rgba(124,58,237,.15), transparent 28%),
                linear-gradient(180deg,#020617 0%,#07111f 45%,#020617 100%);
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#020617 0%,#0f172a 100%);
    border-right: 1px solid rgba(34,211,238,.22);
}
div[data-testid="stMetric"] {
    background: rgba(15,23,42,.86);
    border: 1px solid rgba(34,211,238,.25);
    border-radius: 18px;
    padding: 17px;
    box-shadow: 0 0 30px rgba(34,211,238,.08);
}
div[data-testid="stMetric"] label {
    color:#93c5fd!important;
    font-weight:700!important;
    text-transform:uppercase;
    letter-spacing:.08em;
}
div[data-testid="stMetricValue"] {
    color:#67e8f9!important;
    font-weight:800!important;
}
.qxi-hero {
    border:1px solid rgba(34,211,238,.35);
    border-radius:26px;
    padding:28px;
    background:linear-gradient(135deg,rgba(14,165,233,.16),rgba(168,85,247,.09)),rgba(2,6,23,.76);
    box-shadow:0 0 45px rgba(34,211,238,.10);
    margin-bottom:22px;
}
.qxi-title { font-size:48px; font-weight:900; color:#fff; margin:0; letter-spacing:-.06em; }
.qxi-subtitle { color:#22d3ee; font-size:17px; font-weight:700; margin-top:5px; }
.qxi-pill {
    display:inline-block; padding:7px 13px; margin-right:8px; border-radius:999px;
    background:rgba(34,211,238,.10); border:1px solid rgba(34,211,238,.32);
    color:#a5f3fc; font-size:12px; font-weight:700; letter-spacing:.05em;
}
.qxi-card {
    border:1px solid rgba(148,163,184,.22); border-radius:22px; padding:24px;
    background:rgba(15,23,42,.82); box-shadow:0 0 36px rgba(2,132,199,.07);
}
.qxi-big-symbol { font-size:52px; font-weight:900; color:#fff; letter-spacing:-.06em; }
.qxi-decision { font-size:24px; font-weight:900; color:#4ade80; }
.qxi-note { color:#94a3b8; font-size:14px; }
.stDataFrame { border:1px solid rgba(34,211,238,.18); border-radius:18px; overflow:hidden; }
.stButton>button {
    background:linear-gradient(135deg,#0891b2,#7c3aed);
    color:white; border:0; border-radius:12px; font-weight:800; padding:.65rem 1rem;
}
.stDownloadButton>button {
    background:linear-gradient(135deg,#10b981,#0891b2);
    color:white; border:0; border-radius:12px; font-weight:800;
}
</style>
"""

def hash_pw(p): 
    return hashlib.sha256(p.encode("utf-8")).hexdigest()

def init_state():
    if "users" not in st.session_state:
        st.session_state.users = {ADMIN_EMAIL: {"password_hash": hash_pw(ADMIN_PASSWORD), "role": "admin", "created_at": datetime.now().isoformat()}}
    if "watchlists" not in st.session_state:
        st.session_state.watchlists = {}
    if "consensus_df" not in st.session_state:
        st.session_state.consensus_df = pd.DataFrame()

def authenticate(email, password):
    user = st.session_state.users.get(email.lower().strip())
    if not user:
        return None
    return user["role"] if hmac.compare_digest(user["password_hash"], hash_pw(password)) else None

def create_user(email, password):
    email = email.lower().strip()
    if not email or not password:
        return False, "Email and password required."
    if email in st.session_state.users:
        return False, "User already exists."
    st.session_state.users[email] = {"password_hash": hash_pw(password), "role": "client", "created_at": datetime.now().isoformat()}
    st.session_state.watchlists.setdefault(email, [])
    return True, "Client login created."

def score_to_decision(x):
    try:
        x = float(x)
        if x >= 75: return "STRONG BUY"
        if x >= 65: return "BUY"
        if x >= 50: return "WATCH"
        return "AVOID"
    except Exception:
        return "WATCH"

def normalize_columns(df):
    rename = {}
    for c in df.columns:
        key = str(c).lower().strip()
        if key in ["symbol", "ticker"]: rename[c] = "symbol"
        elif key in ["decision", "rating"]: rename[c] = "decision"
        elif key in ["consensus_score", "consensus", "score"]: rename[c] = "consensus_score"
        elif key in ["live_score", "live"]: rename[c] = "live_score"
        elif key in ["adaptive_score", "adaptive"]: rename[c] = "adaptive_score"
        elif key in ["historical_score", "historical"]: rename[c] = "historical_score"
        elif key in ["risk_score", "risk"]: rename[c] = "risk_score"
        elif key in ["reason", "note", "notes"]: rename[c] = "reason"
    df = df.rename(columns=rename)
    if "symbol" in df.columns:
        df["symbol"] = df["symbol"].astype(str).str.upper()
    for c in ["consensus_score", "live_score", "adaptive_score", "historical_score", "risk_score"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    if "decision" not in df.columns:
        df["decision"] = df["consensus_score"].apply(score_to_decision) if "consensus_score" in df.columns else "WATCH"
    if "reason" not in df.columns:
        df["reason"] = "QuantumXI consensus output"
    return df

def demo_data():
    return pd.DataFrame([
        {"symbol":"NVDA","decision":"STRONG BUY","consensus_score":86.4,"live_score":78.2,"adaptive_score":91.5,"historical_score":88.1,"risk_score":63.4,"reason":"Adaptive strong, historical strong, live positive"},
        {"symbol":"PANW","decision":"BUY","consensus_score":73.8,"live_score":66.4,"adaptive_score":82.1,"historical_score":91.2,"risk_score":58.9,"reason":"Historical strength and adaptive confirmation"},
        {"symbol":"MSFT","decision":"BUY","consensus_score":70.2,"live_score":63.1,"adaptive_score":76.3,"historical_score":80.4,"risk_score":72.7,"reason":"Quality profile with stable risk"},
        {"symbol":"AMAT","decision":"BUY","consensus_score":69.6,"live_score":61.2,"adaptive_score":79.4,"historical_score":83.5,"risk_score":61.0,"reason":"Semiconductor leadership and historical strength"},
        {"symbol":"AAPL","decision":"WATCH","consensus_score":58.7,"live_score":54.2,"adaptive_score":62.3,"historical_score":68.2,"risk_score":74.1,"reason":"Mixed evidence"},
        {"symbol":"TSLA","decision":"AVOID","consensus_score":42.9,"live_score":44.1,"adaptive_score":38.7,"historical_score":51.2,"risk_score":29.5,"reason":"Higher risk and weak consensus"}
    ])

def get_df():
    return demo_data() if st.session_state.consensus_df.empty else st.session_state.consensus_df

def hero(title, subtitle, pills=None):
    pill_html = "".join([f"<span class='qxi-pill'>{p}</span>" for p in (pills or [])])
    st.markdown(f"""<div class="qxi-hero"><div class="qxi-title">{title}</div><div class="qxi-subtitle">{subtitle}</div><div style="margin-top:18px;">{pill_html}</div></div>""", unsafe_allow_html=True)

def login_screen():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1.25, 1])
    with c2:
        st.markdown("""<div class="qxi-hero" style="text-align:center;"><div class="qxi-title">QUANTUMXI</div><div class="qxi-subtitle">Professional Investor Portal</div><div style="margin-top:16px;"><span class="qxi-pill">CONSENSUS RATINGS</span><span class="qxi-pill">WATCHLISTS</span><span class="qxi-pill">REPORTS</span></div></div>""", unsafe_allow_html=True)
        with st.container(border=True):
            st.subheader("Client Login")
            email = st.text_input("Email", value=ADMIN_EMAIL)
            password = st.text_input("Password", type="password", value=ADMIN_PASSWORD)
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
    page = st.sidebar.radio("Navigation", ["Dashboard", "Top Ideas", "Watchlist", "Reports", "Admin"])
    if st.sidebar.button("Logout"):
        for k in ["logged_in", "email", "role"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()
    return page

def dashboard():
    df = get_df()
    hero("Investor Dashboard", "Clean decision-support dashboard for clients", ["SIMPLE", "PROFESSIONAL", "ACTIONABLE"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Top Ideas", len(df))
    c2.metric("Strong Buy", int((df["decision"] == "STRONG BUY").sum()))
    c3.metric("Buy", int((df["decision"] == "BUY").sum()))
    c4.metric("Watch", int((df["decision"] == "WATCH").sum()))
    st.divider()
    top = df.iloc[0]
    left, right = st.columns([1.05, 1])
    with left:
        st.markdown("### Today's Top Idea")
        st.markdown(f"""<div class="qxi-card"><div class="qxi-big-symbol">{top.get("symbol","-")}</div><div class="qxi-decision">{top.get("decision","-")}</div><div style="margin-top:18px;color:#93c5fd;">Consensus Score</div><div style="font-size:42px;font-weight:900;color:#22d3ee;">{float(top.get("consensus_score",0)):.2f}</div><div class="qxi-note">{top.get("reason","-")}</div></div>""", unsafe_allow_html=True)
    with right:
        st.markdown("### Signal Breakdown")
        chart = pd.DataFrame({"Signal":["Live","Adaptive","Historical","Risk"], "Score":[float(top.get("live_score",0) or 0), float(top.get("adaptive_score",0) or 0), float(top.get("historical_score",0) or 0), float(top.get("risk_score",0) or 0)]})
        st.bar_chart(chart.set_index("Signal"))
    st.markdown("### Top 10 Rankings")
    cols = [x for x in ["symbol", "decision", "consensus_score", "reason"] if x in df.columns]
    st.dataframe(df[cols].head(10), use_container_width=True, hide_index=True)
    st.info("Research and decision-support only. Not financial advice.")

def top_ideas():
    df = get_df()
    hero("Top Ideas", "A simple ranked list clients can understand", ["STRONG BUY", "BUY", "WATCH", "AVOID"])
    selected = st.multiselect("Decision Filter", ["STRONG BUY", "BUY", "WATCH", "AVOID"], default=["STRONG BUY", "BUY"])
    view = df[df["decision"].isin(selected)]
    cols = [x for x in ["symbol", "decision", "consensus_score", "live_score", "adaptive_score", "historical_score", "risk_score", "reason"] if x in view.columns]
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
    hero("Watchlist", "Track selected ideas without overwhelming the client", ["PERSONAL", "FOCUSED", "MONITOR"])
    wl = st.session_state.watchlists.setdefault(st.session_state.email, [])
    if not wl:
        st.info("No symbols added yet. Add symbols from Top Ideas.")
        return
    view = df[df["symbol"].isin(wl)] if "symbol" in df.columns else pd.DataFrame({"symbol": wl})
    cols = [x for x in ["symbol", "decision", "consensus_score", "reason"] if x in view.columns]
    st.dataframe(view[cols], use_container_width=True, hide_index=True)
    rem = st.text_input("Remove Symbol").upper()
    if st.button("Remove") and rem in wl:
        wl.remove(rem)
        st.rerun()

def reports():
    df = get_df()
    hero("Research Reports", "Simple client-ready stock snapshots", ["EXPLAINABLE", "DOWNLOADABLE", "CLEAN"])
    symbol = st.selectbox("Choose symbol", df["symbol"].tolist())
    row = df[df["symbol"] == symbol].iloc[0]
    c1, c2, c3 = st.columns(3)
    c1.metric("Decision", row.get("decision", "-"))
    c2.metric("Consensus", f"{float(row.get('consensus_score',0)):.2f}")
    c3.metric("Risk", f"{float(row.get('risk_score',0)):.2f}" if "risk_score" in row else "-")
    st.markdown("### Why it ranks here")
    st.write(row.get("reason", "-"))
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
    hero("Admin", "Upload rankings and manage demo client access", ["CSV UPLOAD", "CLIENTS", "REFRESH"])
    if st.session_state.role != "admin":
        st.error("Admin only.")
        return
    st.subheader("Upload v38 Consensus CSV")
    uploaded = st.file_uploader("Upload v38_consensus_rankings.csv", type=["csv"])
    if uploaded:
        df = normalize_columns(pd.read_csv(uploaded))
        st.session_state.consensus_df = df
        st.success(f"Loaded {len(df)} rows.")
        st.dataframe(df.head(15), use_container_width=True, hide_index=True)
    st.subheader("Create Client Login")
    email = st.text_input("Client email")
    pw = st.text_input("Temporary password", type="password")
    if st.button("Create Client"):
        ok, msg = create_user(email, pw)
        st.success(msg) if ok else st.error(msg)
    st.caption("Cloud demo note: users and uploads are session-based. Production version should use Supabase/Postgres.")

def main():
    init_state()
    st.markdown(CSS, unsafe_allow_html=True)
    if not st.session_state.get("logged_in"):
        login_screen()
        return
    page = sidebar()
    if page == "Dashboard":
        dashboard()
    elif page == "Top Ideas":
        top_ideas()
    elif page == "Watchlist":
        watchlist()
    elif page == "Reports":
        reports()
    elif page == "Admin":
        admin()

if __name__ == "__main__":
    main()
