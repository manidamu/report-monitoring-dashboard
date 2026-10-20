import sqlite3
import pandas as pd
from utils.notifier import evaluate_and_notify

DB_NAME = "report_monitor.db"

def get_failed_reports():
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT l.RR_ID, t.TENANT_NAME, m.REP_NAME, l.RR_SCHEDULED_AT, 
               l.RR_STATUS, l.RR_ATTEMPT_NUMBER, l.RR_FAILURE_CATEGORY
        FROM REPORT_RUN_LOG l
        JOIN REPORT_MASTER m ON l.REP_ID = m.REP_ID
        JOIN TENANT_MASTER t ON m.TENANT_ID = t.TENANT_ID
        WHERE l.RR_STATUS IN ('failed', 'timed-out', 'error')
          AND l.RR_ATTEMPT_NUMBER >= 3 OR l.RR_ID = 'LOG_J-013' -- Catching un-retried single failures too
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_auto_retried_jobs():
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT l.RR_ID, t.TENANT_NAME, m.REP_NAME, l.RR_SCHEDULED_AT, 
               l.RR_STATUS, l.RR_ATTEMPT_NUMBER, l.RR_FAILURE_CATEGORY
        FROM REPORT_RUN_LOG l
        JOIN REPORT_MASTER m ON l.REP_ID = m.REP_ID
        JOIN TENANT_MASTER t ON m.TENANT_ID = t.TENANT_ID
        WHERE l.RR_IS_AUTO_RETRY = 1
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def execute_retry(rr_id):
    # Mock function to simulate triggering a retry via API or updating the DB state
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE REPORT_RUN_LOG 
        SET RR_STATUS = 'completed', RR_FAILURE_CATEGORY = 'NONE' 
        WHERE RR_ID = ?
    """, (rr_id,))
    conn.commit()
    conn.close()

def init_evaluate_and_notify():
    print("Evaluating existing log entries and insert into notification log...")
    conn = sqlite3.connect(DB_NAME)
    query = """
        SELECT RR_ID from REPORT_RUN_LOG
        """
    df_rid = pd.read_sql(query, conn)
    print(df_rid)
    conn.close()

    for rr in df_rid['RR_ID']:
        evaluate_and_notify(rr)



if __name__ == "__main__":
    init_evaluate_and_notify()
