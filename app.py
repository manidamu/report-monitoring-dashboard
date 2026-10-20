import streamlit as st
import pandas as pd
import os
import sqlite3
from seed_database import seed_database
from utils.db_helpers import get_failed_reports, get_auto_retried_jobs,  execute_retry , init_evaluate_and_notify
from utils.notifier import evaluate_and_notify

# Page Config
st.set_page_config(
    page_title="Report Run Monitor & Triage",
    page_icon="🚨",
    layout="wide"
)

DB_NAME = "report_monitor.db"

# Auto-initialize and seed DB on first load if it doesn't exist
if not os.path.exists(DB_NAME):
    with st.spinner("Initializing database and loading historical logs..."):
        seed_database()
        init_evaluate_and_notify()


st.title("🚨 Report Run Monitor & Auto-Triage Dashboard")
st.markdown("Proactive monitoring, failure categorization, and self-healing tracking for client scheduled reports.")

# Top-level metrics
conn = sqlite3.connect(DB_NAME)
df_logs = pd.read_sql("SELECT * FROM REPORT_RUN_LOG", conn)
conn.close()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Jobs Logged", len(df_logs))
with col2:
    failed_count = len(df_logs[df_logs['RR_STATUS'].isin(['failed', 'timed-out', 'error']) & (df_logs['RR_IS_AUTO_RETRY'] == 0)])
    st.metric("Unresolved Failures", failed_count, delta=f"-{failed_count}" if failed_count > 0 else "0", delta_color="inverse")
with col3:
    auto_fixed = len(df_logs[df_logs['RR_IS_AUTO_RETRY'] == 1])
    st.metric("Self-Healed / Auto-Retried", auto_fixed)

st.divider()

# Tabs for Navigation
tab1, tab2, tab3,tab4 = st.tabs(["🔥 Triage & Active Failures", "🛡️ Auto-Retry Feed", "📋 All Job Logs" ,"📬 Notification" ])

with tab1:
    st.subheader("Reports Needing Admin Attention")
    st.markdown("These runs failed all automated attempts or errored out without a retry.")
    
    df_failed = get_failed_reports()
    if df_failed.empty:
        st.success("🎉 No active failures requiring intervention!")
    else:
        st.dataframe(df_failed, use_container_width=True)
        
        selected_run = st.selectbox("Select Run ID to Trigger Manual Retry:", df_failed['RR_ID'].tolist())
        if st.button("🚀 Trigger Manual Retry Now"):
            execute_retry(selected_run)
            evaluate_and_notify(selected_run)
            st.success(f"Retry triggered for Run ID: {selected_run}!")
            st.rerun()

with tab2:
    st.subheader("Auto-Remediation & Self-Healing Feed")
    st.markdown("Jobs that initially failed but were safely caught and retried by the system.")
    df_retries = get_auto_retried_jobs()
    st.dataframe(df_retries, use_container_width=True)

with tab3:
    st.subheader("Complete Historical Execution Log")
    st.dataframe(df_logs, use_container_width=True)

# Add this inside app.py as a new tab:
with tab4:
    st.subheader("📬 Notification Audit Log")
    st.markdown("A history of all Emails and SMS alerts dispatched by the Notification Engine.")

    conn = sqlite3.connect(DB_NAME)
    df_notifs = pd.read_sql("""
        SELECT n.NOTIF_ID, t.TENANT_NAME, n.NOTIF_TYPE, n.CHANNELS_USED, 
               n.RECIPIENTS, n.MESSAGE_BODY, n.SENT_AT
        FROM NOTIFICATION_LOG n
        JOIN TENANT_MASTER t ON n.TENANT_ID = t.TENANT_ID
        ORDER BY n.SENT_AT DESC
    """, conn)
    conn.close()

    st.dataframe(df_notifs, use_container_width=True)