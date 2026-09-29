import json
import sqlite3
import time
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

DB = Path("data/risk.db")
st.set_page_config(page_title="Trade Risk Monitor", layout="wide")
st.title("Real-Time Trade Risk & Analytics")
st.caption("Simulated market + trade event stream • portfolio risk materialized to SQLite")

if not DB.exists():
    st.warning("No risk database yet. Start the risk engine and simulators.")
    st.stop()

conn = sqlite3.connect(DB, check_same_thread=False)
df = pd.read_sql_query("SELECT * FROM risk_snapshots ORDER BY id DESC LIMIT 300", conn)
if df.empty:
    st.info("Waiting for the first risk snapshot...")
    st.stop()
df = df.sort_values("ts")
latest = df.iloc[-1]

cols = st.columns(6)
cols[0].metric("P&L", f"${latest.pnl:,.0f}")
cols[1].metric("Gross Exposure", f"${latest.gross_exposure:,.0f}")
cols[2].metric("Net Exposure", f"${latest.net_exposure:,.0f}")
cols[3].metric("Delta", f"{latest.delta:,.1f}")
cols[4].metric("95% VaR", f"${latest.var95:,.0f}")
cols[5].metric("Anomalies", int(latest.anomaly_count))

left, right = st.columns(2)
with left:
    st.subheader("P&L / VaR")
    plot_df = df[["ts", "pnl", "var95"]].copy()
    plot_df["time"] = pd.to_datetime(plot_df.ts, unit="s")
    chart = plot_df.set_index("time")[["pnl", "var95"]]
    st.line_chart(chart)
with right:
    st.subheader("Greeks")
    greek_df = df[["ts", "delta", "gamma", "vega", "theta"]].copy()
    greek_df["time"] = pd.to_datetime(greek_df.ts, unit="s")
    st.line_chart(greek_df.set_index("time")[["delta", "gamma", "vega", "theta"]])

st.subheader("Latest Positions")
positions = json.loads(latest.positions_json)
pos_df = pd.DataFrame(positions)
if not pos_df.empty:
    st.dataframe(pos_df.sort_values("pnl", ascending=False), use_container_width=True)
else:
    st.info("No positions yet.")

st.caption(f"Last update: {pd.to_datetime(latest.ts, unit='s', utc=True)}")
time.sleep(1)
st.rerun()
