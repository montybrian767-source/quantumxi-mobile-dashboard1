
import hashlib
import hmac
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(page_title="QuantumXI Investor Portal", page_icon="📈", layout="wide")

DEFAULT_ADMIN_EMAIL = "admin@quantumxi.local"
DEFAULT_ADMIN_PASSWORD = "admin123"

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
    if "decision" not in df.columns:
        if "consensus_score" in df.columns:
            def dec(x):
                try:
                    x = float(x)
                    if x >= 75: return "STRONG BUY"
                    if x >= 65: return "BUY"
                    if x >= 50: return "WATCH"
                    return "AVOID"
                except Exception:
                    return "WATCH"
            df["decision"] = df["consensus_score"].apply(dec)
        else:
            df["decision"] = "WATCH"
    if "reason" not in df.columns:
        df["reason"] = "QuantumXI consensus output"
    return df

def demo_data():
    return pd.DataFrame([
        {"symbol":"NVDA","decision":"STRONG BUY","consensus_score":86.4,"live_score":78.2,"adaptive_score":91.5,"historical_score":88.1,"risk_score":63.4,"reason":"adaptive strong, historical strong, live positive"},
        {"symbol":"PANW","decision":"BUY","consensus_score":73.8,"live_score":66.4,"adaptive_score":82.1,"historical_score":91.2,"risk_score":58.9,"reason":"historical strong, adaptive positive"},
        {"symbol":"MSFT","decision":"BUY","consensus_score":70.2,"live_score":63.1,"adaptive_score":76.3,"historical_score":80.4,"risk_score":72.7,"reason":"quality and risk profile positive"},
        {"symbol":"AAPL","decision":"WATCH","consensus_score":58.7,"live_score":54.2,"adaptive_score":62.3,"historical_score":68.2,"risk_score":74.1,"reason":"mixed evidence"},
        {"symbol":"TSLA","decision":"AVOID","consensus_score":42.9,"live_score":44.1,"adaptive_score":38.7,"historical_score":51.2,"risk_score":29.5,"reason":"higher risk, weak consensus"}
    ])

def login_screen():
    st.markdown("<h1 style='text-align:center;font-size:54px;'>QuantumXI</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align:center;color:#22d3ee;'>Investor Portal</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;color:#64748b;'>Cloud-ready client dashboard</p>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        with st.container(border=True):
            st.subheader("Client Login")
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
    st.sidebar.title("QuantumXI")
    st.sidebar.caption(f"User: {st.session_state.email}")
    st.sidebar.caption(f"Role: {st.session_state.role}")
    page = st.sidebar.radio("Menu", ["Dashboard", "Top Ideas", "My Watchlist", "Reports", "Admin"])
    if st.sidebar.button("Logout"):
        for k in ["logged_in", "email", "role"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()
    return page

def get_df():
    df = st.session_state.consensus_df
    if df.empty:
        return demo_data()
    return df

def dashboard_page():
    df = get_df()
    st.title("Investor Dashboard")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Portal Status", "ONLINE")
    c2.metric("Consensus Rows", f"{len(df):,}")
    c3.metric("Strong Buy", int((df["decision"] == "STRONG BUY").sum()) if "decision" in df else 0)
    c4.metric("Buy", int((df["decision"] == "BUY").sum()) if "decision" in df else 0)

    st.divider()

    top = df.iloc[0]
    st.subheader("Top Consensus Idea")
    a, b, c, d = st.columns(4)
    a.metric("Symbol", top.get("symbol", "-"))
    b.metric("Decision", top.get("decision", "-"))
    c.metric("Consensus", f"{float(top.get('consensus_score', 0)):.2f}")
    d.metric("Reason", str(top.get("reason", "-"))[:30])

    st.subheader("Top 10 Ideas")
    cols = [x for x in ["symbol","decision","consensus_score","live_score","adaptive_score","historical_score","risk_score","reason"] if x in df.columns]
    st.dataframe(df[cols].head(10), use_container_width=True, hide_index=True)
    st.info("Research and decision-support only. Not financial advice.")

def top_ideas_page():
    df = get_df()
    st.title("Top Ideas")
    selected = st.multiselect("Decision Filter", ["STRONG BUY","BUY","WATCH","AVOID"], default=["STRONG BUY","BUY"])
    view = df[df["decision"].isin(selected)] if "decision" in df.columns else df
    st.dataframe(view, use_container_width=True, hide_index=True)

    sym = st.text_input("Add symbol to watchlist").upper()
    if st.button("Add to Watchlist") and sym:
        wl = st.session_state.watchlists.setdefault(st.session_state.email, [])
        if sym not in wl:
            wl.append(sym)
        st.success(f"{sym} added.")

def watchlist_page():
    df = get_df()
    st.title("My Watchlist")
    wl = st.session_state.watchlists.setdefault(st.session_state.email, [])
    if not wl:
        st.info("No symbols added yet.")
        return
    view = df[df["symbol"].isin(wl)] if "symbol" in df.columns else pd.DataFrame({"symbol": wl})
    st.dataframe(view, use_container_width=True, hide_index=True)

    rem = st.text_input("Remove symbol").upper()
    if st.button("Remove") and rem in wl:
        wl.remove(rem)
        st.rerun()

def reports_page():
    df = get_df()
    st.title("Research Reports")
    symbol = st.selectbox("Choose symbol", df["symbol"].tolist())
    row = df[df["symbol"] == symbol].iloc[0]

    st.subheader(f"{symbol} Research Snapshot")
    st.write(f"**Decision:** {row.get('decision','-')}")
    st.write(f"**Consensus Score:** {row.get('consensus_score','-')}")
    st.write(f"**Reason:** {row.get('reason','-')}")

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
    st.download_button("Download Report", report, file_name=f"{symbol}_QuantumXI_Report.txt")

def admin_page():
    st.title("Admin")
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

    st.subheader("Create client login")
    email = st.text_input("Client email")
    pw = st.text_input("Temporary password", type="password")
    if st.button("Create Client"):
        ok, msg = create_user(email, pw)
        st.success(msg) if ok else st.error(msg)

    st.subheader("Current users")
    st.dataframe(pd.DataFrame([
        {"email": k, "role": v["role"], "created_at": v["created_at"]}
        for k, v in st.session_state.users.items()
    ]), use_container_width=True, hide_index=True)

    st.caption("Cloud demo note: users and uploaded data are session-based in this version. Production version should use Supabase/Postgres.")

def main():
    init_state()
    if not st.session_state.get("logged_in"):
        login_screen()
        return
    page = sidebar()
    if page == "Dashboard":
        dashboard_page()
    elif page == "Top Ideas":
        top_ideas_page()
    elif page == "My Watchlist":
        watchlist_page()
    elif page == "Reports":
        reports_page()
    elif page == "Admin":
        admin_page()

if __name__ == "__main__":
    main()
