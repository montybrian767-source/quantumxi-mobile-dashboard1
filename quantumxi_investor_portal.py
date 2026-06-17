
import hashlib, hmac
from datetime import datetime
import pandas as pd
import streamlit as st

st.set_page_config(page_title="QuantumXI Investor Portal", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

ADMIN_EMAIL = "admin@quantumxi.local"
ADMIN_PASSWORD = "admin123"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap');
html, body, [class*="css"] {font-family:'Inter',sans-serif;}
.stApp {
    background: radial-gradient(circle at 15% 10%, rgba(90,167,255,.18), transparent 24%),
                radial-gradient(circle at 85% 5%, rgba(34,211,155,.10), transparent 26%),
                linear-gradient(180deg,#202b36 0%,#1b2530 100%);
    color:#eef7ff;
}
.block-container {padding-top:1.2rem; max-width:1480px;}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#172635 0%,#132130 100%);
    border-right:1px solid rgba(148,163,184,.18);
    box-shadow:8px 0 40px rgba(0,0,0,.18);
}
section[data-testid="stSidebar"] * {color:#dbeafe;}
div[data-testid="stMetric"] {
    background:linear-gradient(145deg,rgba(35,54,74,.96),rgba(26,41,56,.96));
    border:1px solid rgba(139,173,202,.22);
    border-radius:18px;
    padding:18px;
    box-shadow:0 14px 34px rgba(0,0,0,.20), inset 0 1px 0 rgba(255,255,255,.04);
}
div[data-testid="stMetric"] label {color:#9db3c8!important;font-weight:800!important;text-transform:uppercase;letter-spacing:.08em;}
div[data-testid="stMetricValue"] {color:#eef7ff!important;font-weight:900!important;}
h1,h2,h3 {color:#eef7ff;letter-spacing:-.04em;}
.qxi-shell {
    border:1px solid rgba(139,173,202,.24); border-radius:26px;
    background:rgba(18,31,43,.78);
    box-shadow:0 30px 80px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.05);
    padding:18px; margin-bottom:18px;
}
.qxi-topbar {
    display:flex; align-items:center; justify-content:space-between;
    background:linear-gradient(135deg,#23364a,#1b2b3c);
    border:1px solid rgba(139,173,202,.22); border-radius:18px;
    padding:16px 18px; margin-bottom:14px;
}
.qxi-logo {
    width:42px;height:42px;border-radius:12px;display:flex;align-items:center;justify-content:center;
    color:white;font-weight:900;background:linear-gradient(135deg,#5aa7ff,#39d8ff);
    box-shadow:0 0 26px rgba(90,167,255,.34);
}
.qxi-brand {display:flex;align-items:center;gap:12px;}
.qxi-title {font-size:24px;font-weight:900;color:white;letter-spacing:-.05em;}
.qxi-subtitle {font-size:12px;color:#9db3c8;font-weight:600;}
.qxi-pill {
    display:inline-block;padding:7px 12px;margin-left:7px;border-radius:999px;
    background:rgba(90,167,255,.12);border:1px solid rgba(90,167,255,.25);
    color:#bfdbfe;font-size:11px;font-weight:800;letter-spacing:.05em;
}
.qxi-card {
    background:linear-gradient(135deg,rgba(90,167,255,.16),rgba(34,211,155,.07)),#1b2a39;
    border:1px solid rgba(139,173,202,.22);border-radius:20px;padding:18px;
    box-shadow:inset 0 1px 0 rgba(255,255,255,.04);
    min-height: 145px;
}
.qxi-big {font-size:48px;font-weight:950;color:white;letter-spacing:-.08em;}
.qxi-score {font-size:38px;font-weight:950;color:#5aa7ff;letter-spacing:-.06em;}
.qxi-mini {color:#9db3c8;font-size:12px;font-weight:700;}
.qxi-good {color:#22d39b;font-weight:900;}
.qxi-mid {color:#fbbf24;font-weight:900;}
.qxi-bad {color:#ff6b7a;font-weight:900;}
.stButton>button {background:linear-gradient(135deg,#3b82f6,#5aa7ff);color:white;border:0;border-radius:12px;font-weight:900;}
.stDownloadButton>button {background:linear-gradient(135deg,#22d39b,#3b82f6);color:white;border:0;border-radius:12px;font-weight:900;}
.stDataFrame {border:1px solid rgba(139,173,202,.20);border-radius:18px;overflow:hidden;}
div[data-testid="stFileUploader"] {background:rgba(35,54,74,.68);border:1px dashed rgba(90,167,255,.40);border-radius:18px;padding:16px;}
</style>
"""

def hash_pw(p): return hashlib.sha256(p.encode()).hexdigest()

def init_state():
    if "users" not in st.session_state:
        st.session_state.users = {ADMIN_EMAIL: {"password_hash": hash_pw(ADMIN_PASSWORD), "role": "admin", "created_at": datetime.now().isoformat()}}
    if "watchlists" not in st.session_state: st.session_state.watchlists = {}
    if "consensus_df" not in st.session_state: st.session_state.consensus_df = pd.DataFrame()

def auth(email,pw):
    u = st.session_state.users.get(email.lower().strip())
    if not u: return None
    return u["role"] if hmac.compare_digest(u["password_hash"], hash_pw(pw)) else None

def create_user(email,pw,role="client"):
    email=email.lower().strip()
    if not email or not pw: return False,"Email and password required."
    if email in st.session_state.users: return False,"User already exists."
    st.session_state.users[email]={"password_hash":hash_pw(pw),"role":role,"created_at":datetime.now().isoformat()}
    st.session_state.watchlists.setdefault(email,[])
    return True,"Client login created."

def score_to_decision(x):
    try:
        x=float(x)
        return "STRONG BUY" if x>=75 else "BUY" if x>=65 else "WATCH" if x>=50 else "AVOID"
    except Exception:
        return "WATCH"

def normalize(df):
    ren={}
    for c in df.columns:
        k=str(c).lower().strip()
        if k in ["symbol","ticker"]: ren[c]="symbol"
        elif k in ["decision","rating"]: ren[c]="decision"
        elif k in ["consensus_score","consensus","score"]: ren[c]="consensus_score"
        elif k in ["live_score","live"]: ren[c]="live_score"
        elif k in ["adaptive_score","adaptive"]: ren[c]="adaptive_score"
        elif k in ["historical_score","historical"]: ren[c]="historical_score"
        elif k in ["risk_score","risk"]: ren[c]="risk_score"
        elif k in ["sector"]: ren[c]="sector"
        elif k in ["asset_type","asset"]: ren[c]="asset_type"
        elif k in ["price"]: ren[c]="price"
        elif k in ["change_pct","change %","change"]: ren[c]="change_pct"
        elif k in ["reason","note","notes"]: ren[c]="reason"
    df=df.rename(columns=ren)
    if "symbol" in df: df["symbol"]=df["symbol"].astype(str).str.upper()
    for c in ["consensus_score","live_score","adaptive_score","historical_score","risk_score","price","change_pct"]:
        if c in df: df[c]=pd.to_numeric(df[c],errors="coerce")
    if "decision" not in df:
        df["decision"]=df["consensus_score"].apply(score_to_decision) if "consensus_score" in df else "WATCH"
    if "reason" not in df: df["reason"]="QuantumXI consensus output"
    if "sector" not in df: df["sector"]="Unclassified"
    if "asset_type" not in df: df["asset_type"]="Equity"
    return df

def demo():
    return pd.DataFrame([
        {"symbol":"NVDA","decision":"STRONG BUY","consensus_score":86.4,"live_score":78.2,"adaptive_score":91.5,"historical_score":88.1,"risk_score":63.4,"sector":"Technology","asset_type":"Equity","price":205.19,"change_pct":1.2,"reason":"adaptive strong, historical strong, live positive"},
        {"symbol":"PANW","decision":"BUY","consensus_score":73.8,"live_score":66.4,"adaptive_score":82.1,"historical_score":91.2,"risk_score":58.9,"sector":"Cybersecurity","asset_type":"Equity","price":403.12,"change_pct":0.7,"reason":"historical strong, adaptive positive"},
        {"symbol":"MSFT","decision":"BUY","consensus_score":70.2,"live_score":63.1,"adaptive_score":76.3,"historical_score":80.4,"risk_score":72.7,"sector":"Technology","asset_type":"Equity","price":512.21,"change_pct":0.4,"reason":"quality and risk profile positive"},
        {"symbol":"AMAT","decision":"BUY","consensus_score":69.6,"live_score":61.2,"adaptive_score":79.4,"historical_score":83.5,"risk_score":61.0,"sector":"Semiconductors","asset_type":"Equity","price":212.45,"change_pct":1.1,"reason":"semiconductor leadership, historical strength"},
        {"symbol":"AAPL","decision":"WATCH","consensus_score":58.7,"live_score":54.2,"adaptive_score":62.3,"historical_score":68.2,"risk_score":74.1,"sector":"Technology","asset_type":"Equity","price":299.24,"change_pct":0.9,"reason":"mixed evidence"},
        {"symbol":"QQQ","decision":"WATCH","consensus_score":55.2,"live_score":54.0,"adaptive_score":56.2,"historical_score":62.0,"risk_score":82.4,"sector":"ETF","asset_type":"ETF","price":610.00,"change_pct":0.3,"reason":"benchmark exposure"},
        {"symbol":"TSLA","decision":"AVOID","consensus_score":42.9,"live_score":44.1,"adaptive_score":38.7,"historical_score":51.2,"risk_score":29.5,"sector":"Consumer Cyclical","asset_type":"Equity","price":188.43,"change_pct":-1.4,"reason":"higher risk, weak consensus"}
    ])

def df(): return demo() if st.session_state.consensus_df.empty else st.session_state.consensus_df

def cls(dec):
    d=str(dec).upper()
    return "qxi-good" if "STRONG" in d or d=="BUY" else "qxi-mid" if d=="WATCH" else "qxi-bad"

def shell_open(title="QuantumXI Investor Portal", subtitle="AI market intelligence command center"):
    st.markdown(f"""
    <div class="qxi-shell"><div class="qxi-topbar">
      <div class="qxi-brand"><div class="qxi-logo">QXI</div><div>
      <div class="qxi-title">{title}</div><div class="qxi-subtitle">{subtitle}</div>
      </div></div><div><span class="qxi-pill">DARK MODE</span><span class="qxi-pill">CLIENT READY</span><span class="qxi-pill">LIVE CONSENSUS</span></div>
    </div>
    """, unsafe_allow_html=True)

def shell_close(): st.markdown("</div>", unsafe_allow_html=True)

def login_screen():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1,c2,c3=st.columns([1,1.25,1])
    with c2:
        st.markdown("""
        <div class="qxi-shell"><div class="qxi-topbar" style="justify-content:center;text-align:center;"><div>
        <div class="qxi-logo" style="margin:0 auto 14px auto;">QXI</div>
        <div class="qxi-title" style="font-size:38px;">QuantumXI</div>
        <div class="qxi-subtitle">Professional Investor Portal</div>
        <div style="margin-top:14px;"><span class="qxi-pill">AI RANKINGS</span><span class="qxi-pill">WATCHLISTS</span><span class="qxi-pill">REPORTS</span></div>
        </div></div>
        """, unsafe_allow_html=True)
        with st.container(border=True):
            st.subheader("Secure Client Login")
            email=st.text_input("Email", value=ADMIN_EMAIL)
            pw=st.text_input("Password", type="password", value=ADMIN_PASSWORD)
            if st.button("Login", use_container_width=True):
                role=auth(email,pw)
                if role:
                    st.session_state.logged_in=True; st.session_state.email=email.lower().strip(); st.session_state.role=role; st.rerun()
                else: st.error("Invalid login.")
            st.caption("Demo login: admin@quantumxi.local / admin123")
        st.markdown("</div>", unsafe_allow_html=True)

def sidebar():
    st.sidebar.markdown("## ⚡ QuantumXI")
    st.sidebar.caption(f"User: {st.session_state.email}")
    st.sidebar.caption(f"Role: {st.session_state.role}")
    st.sidebar.markdown("---")
    page=st.sidebar.radio("Navigation", ["Home","Portfolio","Top Ideas","Funds","Discover","News","Watchlist","Reports","Admin"])
    st.sidebar.markdown("---")
    st.sidebar.toggle("Dark Mode", value=True)
    if st.sidebar.button("Logout"):
        for k in ["logged_in","email","role"]:
            st.session_state.pop(k, None)
        st.rerun()
    return page

def home():
    data=df(); top=data.iloc[0]; shell_open()
    c1,c2=st.columns([1.25,2])
    with c1:
        st.markdown(f"""
        <div class="qxi-card">
          <div class="qxi-mini">Top consensus idea</div>
          <div class="qxi-big">{top.get("symbol","-")}</div>
          <div class="{cls(top.get("decision","-"))}" style="font-size:22px;">{top.get("decision","-")}</div>
          <div style="margin-top:18px;" class="qxi-mini">Consensus score</div>
          <div class="qxi-score">{float(top.get("consensus_score",0)):.2f}</div>
          <div class="qxi-mini">{top.get("reason","-")}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("### Portfolio performance signal mix")
        chart=pd.DataFrame({"Signal":["Live","Adaptive","Historical","Risk"],"Score":[float(top.get("live_score",0) or 0),float(top.get("adaptive_score",0) or 0),float(top.get("historical_score",0) or 0),float(top.get("risk_score",0) or 0)]})
        st.area_chart(chart.set_index("Signal"))
    m1,m2,m3,m4=st.columns(4)
    m1.metric("Consensus rows", f"{len(data):,}")
    m2.metric("Strong buys", int((data["decision"]=="STRONG BUY").sum()))
    m3.metric("Buys", int((data["decision"]=="BUY").sum()))
    m4.metric("Watch", int((data["decision"]=="WATCH").sum()))
    st.markdown("### Market Movers")
    cols=[x for x in ["symbol","decision","consensus_score","sector","price","change_pct","reason"] if x in data.columns]
    st.dataframe(data[cols].head(12), use_container_width=True, hide_index=True)
    shell_close()

def portfolio():
    data=df(); shell_open("Portfolio", "Client holdings and portfolio health")
    wl = st.session_state.watchlists.setdefault(st.session_state.email, [])
    if not wl:
        st.info("Your portfolio/watchlist is empty. Add symbols from Top Ideas.")
        st.markdown("### Model Portfolio Preview")
        picks = data[data["decision"].isin(["STRONG BUY","BUY"])].head(8).copy()
    else:
        picks = data[data["symbol"].isin(wl)].copy()
    if picks.empty:
        picks = data.head(5).copy()
    avg_score = picks["consensus_score"].mean() if "consensus_score" in picks else 0
    risk = picks["risk_score"].mean() if "risk_score" in picks else 0
    a,b,c,d=st.columns(4)
    a.metric("Holdings tracked", len(picks))
    b.metric("Avg consensus", f"{avg_score:.1f}")
    c.metric("Avg risk score", f"{risk:.1f}")
    d.metric("Portfolio grade", "A" if avg_score>=75 else "B" if avg_score>=65 else "C")
    cols=[x for x in ["symbol","decision","consensus_score","sector","risk_score","reason"] if x in picks.columns]
    st.dataframe(picks[cols], use_container_width=True, hide_index=True)
    st.markdown("### Sector exposure")
    if "sector" in picks:
        st.bar_chart(picks["sector"].value_counts())
    shell_close()

def funds():
    data=df(); shell_open("Funds", "ETF and fund-style exposure ideas")
    funds_df = data[(data.get("asset_type","")=="ETF") | (data["symbol"].astype(str).str.contains("QQQ|SPY|DIA|IWM|ETF", case=False, regex=True))]
    if funds_df.empty:
        funds_df = pd.DataFrame([
            {"symbol":"QQQ","decision":"WATCH","consensus_score":55.0,"sector":"Growth ETF","reason":"benchmark / growth exposure"},
            {"symbol":"SPY","decision":"WATCH","consensus_score":53.0,"sector":"Core ETF","reason":"broad market exposure"},
            {"symbol":"IWM","decision":"WATCH","consensus_score":49.0,"sector":"Small Cap ETF","reason":"small cap exposure"}
        ])
    a,b,c=st.columns(3)
    a.metric("Funds tracked", len(funds_df))
    b.metric("Best fund", funds_df.sort_values("consensus_score", ascending=False).iloc[0]["symbol"])
    c.metric("Avg score", f"{funds_df['consensus_score'].mean():.1f}")
    cols=[x for x in ["symbol","decision","consensus_score","sector","reason"] if x in funds_df.columns]
    st.dataframe(funds_df[cols], use_container_width=True, hide_index=True)
    shell_close()

def discover():
    data=df(); shell_open("Discover", "Find new ideas by sector and signal strength")
    sector = st.selectbox("Sector", ["All"] + sorted(data["sector"].dropna().unique().tolist()) if "sector" in data else ["All"])
    min_score = st.slider("Minimum consensus score", 0, 100, 60)
    view=data.copy()
    if sector!="All" and "sector" in view: view=view[view["sector"]==sector]
    if "consensus_score" in view: view=view[view["consensus_score"]>=min_score]
    st.markdown("### Discovery results")
    cols=[x for x in ["symbol","decision","consensus_score","sector","live_score","adaptive_score","historical_score","risk_score","reason"] if x in view.columns]
    st.dataframe(view[cols].sort_values("consensus_score", ascending=False), use_container_width=True, hide_index=True)
    shell_close()

def news():
    data=df(); shell_open("News", "Market intelligence notes")
    st.markdown("### Today's QuantumXI Notes")
    top = data.iloc[0]
    notes = [
        f"Top consensus idea is {top.get('symbol','-')} with a score of {float(top.get('consensus_score',0)):.2f}.",
        f"{int((data['decision']=='STRONG BUY').sum())} names currently qualify as Strong Buy.",
        f"{int((data['decision']=='BUY').sum())} names currently qualify as Buy.",
        "Client note: rankings are research signals, not automatic trade instructions.",
        "Next upgrade: connect live financial news and earnings calendar."
    ]
    for n in notes:
        st.markdown(f"- {n}")
    shell_close()

def top_ideas():
    data=df(); shell_open("Top Ideas", "Ranked opportunities simplified for clients")
    selected=st.multiselect("Decision Filter", ["STRONG BUY","BUY","WATCH","AVOID"], default=["STRONG BUY","BUY"])
    view=data[data["decision"].isin(selected)]
    cols=[x for x in ["symbol","decision","consensus_score","live_score","adaptive_score","historical_score","risk_score","sector","reason"] if x in view.columns]
    st.dataframe(view[cols], use_container_width=True, hide_index=True)
    sym=st.text_input("Add symbol to watchlist").upper()
    if st.button("Add Symbol") and sym:
        wl=st.session_state.watchlists.setdefault(st.session_state.email,[])
        if sym not in wl: wl.append(sym)
        st.success(f"{sym} added.")
    shell_close()

def watchlist():
    data=df(); shell_open("Watchlist", "Track symbols and ratings")
    wl=st.session_state.watchlists.setdefault(st.session_state.email,[])
    add = st.text_input("Add symbol").upper()
    if st.button("Add to Watchlist") and add:
        if add not in wl: wl.append(add)
        st.success(f"{add} added.")
    if not wl:
        st.info("No symbols added yet. Add symbols above or from Top Ideas.")
        shell_close(); return
    view=data[data["symbol"].isin(wl)] if "symbol" in data else pd.DataFrame({"symbol":wl})
    st.dataframe(view, use_container_width=True, hide_index=True)
    rem=st.text_input("Remove Symbol").upper()
    if st.button("Remove") and rem in wl:
        wl.remove(rem); st.rerun()
    shell_close()

def reports():
    data=df(); shell_open("Research Reports", "One-click client research snapshots")
    symbol=st.selectbox("Choose symbol", data["symbol"].tolist())
    row=data[data["symbol"]==symbol].iloc[0]
    a,b,c,d=st.columns(4)
    a.metric("Decision", row.get("decision","-"))
    b.metric("Consensus", f"{float(row.get('consensus_score',0)):.2f}")
    c.metric("Adaptive", f"{float(row.get('adaptive_score',0)):.2f}")
    d.metric("Risk", f"{float(row.get('risk_score',0)):.2f}")
    st.markdown("#### Explanation"); st.write(row.get("reason","-"))
    report=f"""QUANTUMXI RESEARCH SNAPSHOT

Symbol: {symbol}
Decision: {row.get('decision','-')}
Consensus Score: {row.get('consensus_score','-')}
Live Score: {row.get('live_score','-')}
Adaptive Score: {row.get('adaptive_score','-')}
Historical Score: {row.get('historical_score','-')}
Risk Score: {row.get('risk_score','-')}
Sector: {row.get('sector','-')}

Reason:
{row.get('reason','-')}

Disclaimer:
Research and decision-support software only. Not financial advice.
"""
    st.download_button("Download Client Report", report, file_name=f"{symbol}_QuantumXI_Report.txt")
    shell_close()

def admin():
    shell_open("Admin Console", "Upload consensus files and manage demo client access")
    if st.session_state.role!="admin":
        st.error("Admin only."); shell_close(); return
    uploaded=st.file_uploader("Upload v38_consensus_rankings.csv", type=["csv"])
    if uploaded:
        data=normalize(pd.read_csv(uploaded)); st.session_state.consensus_df=data
        st.success(f"Loaded {len(data)} consensus rows."); st.dataframe(data.head(20), use_container_width=True, hide_index=True)
    st.markdown("### Create Client Login")
    email=st.text_input("Client email"); pw=st.text_input("Temporary password", type="password")
    if st.button("Create Client"):
        ok,msg=create_user(email,pw); st.success(msg) if ok else st.error(msg)
    users=pd.DataFrame([{"email":k,"role":v["role"],"created_at":v["created_at"]} for k,v in st.session_state.users.items()])
    st.dataframe(users, use_container_width=True, hide_index=True)
    st.warning("Cloud demo note: data and users are session-based. Production should use Supabase/Postgres.")
    shell_close()

def main():
    init_state(); st.markdown(CSS, unsafe_allow_html=True)
    if not st.session_state.get("logged_in"):
        login_screen(); return
    page=sidebar()
    if page=="Home": home()
    elif page=="Portfolio": portfolio()
    elif page=="Funds": funds()
    elif page=="Discover": discover()
    elif page=="News": news()
    elif page=="Top Ideas": top_ideas()
    elif page=="Watchlist": watchlist()
    elif page=="Reports": reports()
    elif page=="Admin": admin()

if __name__ == "__main__":
    main()
