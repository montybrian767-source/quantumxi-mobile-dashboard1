
import os, sqlite3, hashlib, hmac
from pathlib import Path
from datetime import datetime
import pandas as pd
import streamlit as st

WAREHOUSE_DB = r"D:\QuantumXI_Data\Warehouse\warehouse.db"
CONSENSUS_CSV = r"D:\QuantumXI_Data\Warehouse\v38_consensus_decision_engine\v38_consensus_rankings.csv"
PORTAL_DIR = Path(r"D:\QuantumXI_Client_Portal")
USER_DB = PORTAL_DIR / "portal_users.db"

st.set_page_config(page_title="QuantumXI Investor Portal", page_icon="📈", layout="wide")

def ensure():
    PORTAL_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(USER_DB)
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (email TEXT PRIMARY KEY, password_hash TEXT, salt TEXT, role TEXT, created_at TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS watchlists (email TEXT, symbol TEXT, added_at TEXT, PRIMARY KEY(email, symbol))")
    con.commit()
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        salt = "quantumxi_default_salt"
        pw = hash_pw("admin123", salt)
        cur.execute("INSERT INTO users VALUES (?,?,?,?,?)", ("admin@quantumxi.local", pw, salt, "admin", datetime.now().isoformat()))
        con.commit()
    con.close()

def hash_pw(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100000).hex()

def login(email, password):
    con = sqlite3.connect(USER_DB)
    row = con.execute("SELECT password_hash, salt, role FROM users WHERE email=?", (email.lower().strip(),)).fetchone()
    con.close()
    if not row:
        return None
    stored, salt, role = row
    return role if hmac.compare_digest(stored, hash_pw(password, salt)) else None

def create_user(email, password, role="client"):
    email = email.lower().strip()
    if not email or not password:
        return False, "Email and password required."
    salt = hashlib.sha256((email + str(datetime.now())).encode()).hexdigest()[:16]
    try:
        con = sqlite3.connect(USER_DB)
        con.execute("INSERT INTO users VALUES (?,?,?,?,?)", (email, hash_pw(password, salt), salt, role, datetime.now().isoformat()))
        con.commit(); con.close()
        return True, "Client login created."
    except sqlite3.IntegrityError:
        return False, "User already exists."

@st.cache_data(ttl=60)
def load_consensus():
    if os.path.exists(CONSENSUS_CSV):
        df = pd.read_csv(CONSENSUS_CSV)
        if "symbol" in df.columns:
            df["symbol"] = df["symbol"].astype(str).str.upper()
        return df
    return pd.DataFrame()

@st.cache_data(ttl=300)
def warehouse_summary():
    out = {"status":"MISSING","symbols":0,"rows":0,"top_long":"-","top_short":"-"}
    if not os.path.exists(WAREHOUSE_DB):
        return out
    try:
        con = sqlite3.connect(WAREHOUSE_DB)
        out["rows"] = con.execute("SELECT COUNT(*) FROM prices").fetchone()[0]
        out["symbols"] = con.execute("SELECT COUNT(*) FROM alpha_features").fetchone()[0]
        r = con.execute("SELECT symbol FROM alpha_features ORDER BY long_score DESC LIMIT 1").fetchone()
        out["top_long"] = r[0] if r else "-"
        r = con.execute("SELECT symbol FROM alpha_features ORDER BY short_score DESC LIMIT 1").fetchone()
        out["top_short"] = r[0] if r else "-"
        con.close()
        out["status"] = "ONLINE"
    except Exception as e:
        out["status"] = "ERROR"
    return out

def get_watchlist(email):
    con = sqlite3.connect(USER_DB)
    df = pd.read_sql_query("SELECT symbol, added_at FROM watchlists WHERE email=? ORDER BY added_at DESC", con, params=(email,))
    con.close()
    return df

def add_watch(email, symbol):
    con = sqlite3.connect(USER_DB)
    con.execute("INSERT OR IGNORE INTO watchlists VALUES (?,?,?)", (email, symbol.upper(), datetime.now().isoformat()))
    con.commit(); con.close()

def remove_watch(email, symbol):
    con = sqlite3.connect(USER_DB)
    con.execute("DELETE FROM watchlists WHERE email=? AND symbol=?", (email, symbol.upper()))
    con.commit(); con.close()

def login_screen():
    st.markdown("<h1 style='text-align:center;font-size:54px;'>QuantumXI</h1><h3 style='text-align:center;color:#22d3ee;'>Investor Portal</h3>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns([1,1.1,1])
    with c2:
        with st.container(border=True):
            st.subheader("Client Login")
            email = st.text_input("Email", value="admin@quantumxi.local")
            pw = st.text_input("Password", type="password", value="admin123")
            if st.button("Login", use_container_width=True):
                role = login(email, pw)
                if role:
                    st.session_state.logged_in = True
                    st.session_state.email = email.lower().strip()
                    st.session_state.role = role
                    st.rerun()
                else:
                    st.error("Invalid login.")
            st.caption("Default demo login: admin@quantumxi.local / admin123")

def dashboard():
    email = st.session_state.email
    role = st.session_state.role
    df = load_consensus()
    summary = warehouse_summary()

    st.sidebar.title("QuantumXI")
    st.sidebar.caption(f"User: {email}")
    st.sidebar.caption(f"Role: {role}")
    page = st.sidebar.radio("Menu", ["Dashboard","Top Ideas","My Watchlist","Reports","Admin"])
    if st.sidebar.button("Logout"):
        st.session_state.clear(); st.rerun()

    if page == "Dashboard":
        st.title("Investor Dashboard")
        a,b,c,d = st.columns(4)
        a.metric("Warehouse", summary["status"])
        b.metric("Symbols", f"{summary['symbols']:,}")
        c.metric("Price Rows", f"{summary['rows']:,}")
        d.metric("Consensus Rows", f"{len(df):,}")

        if df.empty:
            st.warning("No v38 consensus rankings found. Run v38 first.")
            st.code(CONSENSUS_CSV)
            return

        st.subheader("Top Consensus Idea")
        top = df.iloc[0]
        x1,x2,x3,x4 = st.columns(4)
        x1.metric("Symbol", top.get("symbol","-"))
        x2.metric("Decision", top.get("decision","-"))
        x3.metric("Consensus", f"{float(top.get('consensus_score',0)):.2f}")
        x4.metric("Reason", str(top.get("reason","-"))[:30])

        cols = [c for c in ["symbol","decision","consensus_score","live_score","adaptive_score","historical_score","risk_score","reason"] if c in df.columns]
        st.dataframe(df[cols].head(10), use_container_width=True, hide_index=True)
        st.info("Decision-support only. Not financial advice.")

    elif page == "Top Ideas":
        st.title("Top Ideas")
        if df.empty:
            st.warning("Run v38 first.")
            return
        choices = ["STRONG BUY","BUY","WATCH","AVOID"]
        selected = st.multiselect("Decision Filter", choices, default=["STRONG BUY","BUY"])
        view = df[df["decision"].isin(selected)] if "decision" in df.columns else df
        st.dataframe(view.head(100), use_container_width=True, hide_index=True)
        sym = st.text_input("Add Symbol to Watchlist").upper()
        if st.button("Add") and sym:
            add_watch(email, sym); st.success(f"{sym} added.")

    elif page == "My Watchlist":
        st.title("My Watchlist")
        wl = get_watchlist(email)
        if wl.empty:
            st.info("No watchlist symbols yet.")
        else:
            if not df.empty:
                merged = wl.merge(df, on="symbol", how="left")
                cols = [c for c in ["symbol","decision","consensus_score","live_score","adaptive_score","historical_score","risk_score","reason"] if c in merged.columns]
                st.dataframe(merged[cols], use_container_width=True, hide_index=True)
            else:
                st.dataframe(wl, use_container_width=True, hide_index=True)
        rem = st.text_input("Remove Symbol").upper()
        if st.button("Remove") and rem:
            remove_watch(email, rem); st.rerun()

    elif page == "Reports":
        st.title("Research Reports")
        if df.empty:
            st.warning("No consensus data.")
            return
        symbol = st.selectbox("Symbol", df["symbol"].head(100).tolist())
        row = df[df["symbol"] == symbol].iloc[0]
        st.subheader(f"{symbol} Snapshot")
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

    elif page == "Admin":
        st.title("Admin")
        if role != "admin":
            st.error("Admin only.")
            return
        st.subheader("Create Client Login")
        new_email = st.text_input("Client email")
        new_pw = st.text_input("Temporary password", type="password")
        if st.button("Create Client"):
            ok,msg = create_user(new_email,new_pw)
            st.success(msg) if ok else st.error(msg)
        st.subheader("System Paths")
        st.code(f"Warehouse: {WAREHOUSE_DB}")
        st.code(f"Consensus CSV: {CONSENSUS_CSV}")
        st.code(f"User DB: {USER_DB}")
        if st.button("Reload Data"):
            st.cache_data.clear(); st.rerun()

def main():
    ensure()
    if not st.session_state.get("logged_in"):
        login_screen()
    else:
        dashboard()

if __name__ == "__main__":
    main()
