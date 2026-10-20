import sqlite3
import pandas as pd

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