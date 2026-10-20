import sqlite3
import uuid
from datetime import datetime

DB_NAME = "report_monitor.db"


def evaluate_and_notify(rr_id):
    """
    Evaluates a job run against Tenant Tier and Report Criticality rules
    and dispatches notifications (Email / SMS).
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Fetch run log joined with report, tenant, and schedule info
    query = """
        SELECT l.*, m.REP_NAME, m.REP_CRITICALITY_CATEGORY, 
               t.TENANT_ID, t.TENANT_NAME, t.TENANT_TIER, t.TENANT_PRIMARY_EMAIL, t.TENANT_PRIMARY_CONTACT,
               s.REP_SCHE_RETRY_ATTEMPTS
        FROM REPORT_RUN_LOG l
        JOIN REPORT_MASTER m ON l.REP_ID = m.REP_ID
        JOIN TENANT_MASTER t ON m.TENANT_ID = t.TENANT_ID
        JOIN REPORT_SCHEDULE_MASTER s ON l.REP_SCHE_ID = s.REP_SCHE_ID
        WHERE l.RR_ID = ?
    """
    run = cursor.execute(query, (rr_id,)).fetchone()
    if not run:
        conn.close()
        return

    print("Evaluating job run...",rr_id)
    # Extract variables
    status = run["RR_STATUS"].lower()
    tier = run["TENANT_TIER"]  # 'Tier 1' or 'Tier 2'
    criticality = run["REP_CRITICALITY_CATEGORY"]  # 'Critical', 'High', 'Medium', 'Low'
    attempt = run["RR_ATTEMPT_NUMBER"]
    max_retries = run["REP_SCHE_RETRY_ATTEMPTS"]

    admin_email = "admin@reportsystem.com"
    tenant_email = run["TENANT_PRIMARY_EMAIL"]
    recipients = f"Admin ({admin_email}), Tenant ({tenant_email})"

    channels = []
    message_body = ""
    notif_type = ""

    is_success = status in ["completed", "success"]
    is_max_exhausted = (attempt >= max_retries) or (run["RR_FAILURE_CATEGORY"] == "TIMED_OUT" and attempt >= 3)

    if is_success:
        # --- SUCCESS RULE ---
        notif_type = "SUCCESS"
        channels.append("EMAIL")
        message_body = f"SUCCESS: Report '{run['REP_NAME']}' for {run['TENANT_NAME']} completed successfully in {run['RR_DURATION_SECONDS']}s."

    else:
        # --- FAILURE RULES ---
        notif_type = "FAILURE"

        # Check if we should suppress email for Medium/Low until max attempts are exhausted
        send_failure_email = True
        if criticality in ["Medium", "Low"] and not is_max_exhausted:
            send_failure_email = False  # Suppress intermediate failure emails for Med/Low

        if send_failure_email:
            channels.append("EMAIL")

        # --- TIER 1 RULES ---
        if tier == "Tier 1":
            if criticality == "Critical" and attempt == 1:
                channels.append("SMS")
                message_body = f"URGENT [Tier 1 Critical]: Report '{run['REP_NAME']}' failed on attempt 1. SMS Alert dispatched."
            elif criticality == "High" and attempt == 2:
                channels.append("SMS")
                message_body = f"ALERT [Tier 1 High]: Report '{run['REP_NAME']}' failed on attempt 2. SMS Alert dispatched."
            elif criticality in ["Medium", "Low"] and is_max_exhausted:
                message_body = f"NOTICE [Tier 1 {criticality}]: Max attempts exhausted for '{run['REP_NAME']}'. Admin notified."
            else:
                if not message_body:
                    message_body = f"FAILURE [Tier 1]: Report '{run['REP_NAME']}' failed on attempt {attempt}."

        # --- TIER 2 RULES ---
        elif tier == "Tier 2":
            if criticality == "Critical" and attempt == 1:
                message_body = f"ALERT [Tier 2 Critical]: Report '{run['REP_NAME']}' failed on attempt 1. Email dispatched."
            elif criticality == "High" and attempt == 2:
                message_body = f"ALERT [Tier 2 High]: Report '{run['REP_NAME']}' failed on attempt 2. Email dispatched."
            elif criticality in ["Medium", "Low"] and is_max_exhausted:
                message_body = f"NOTICE [Tier 2 {criticality}]: Max attempts exhausted for '{run['REP_NAME']}'. Email dispatched."
            else:
                if not message_body:
                    message_body = f"FAILURE [Tier 2]: Report '{run['REP_NAME']}' failed on attempt {attempt}."

    # If channels were triggered, write to NOTIFICATION_LOG
    if channels:
        notif_id = f"NOTIF-{uuid.uuid4().hex[:8]}"
        channels_str = "+".join(channels)

        cursor.execute("""
            INSERT INTO NOTIFICATION_LOG (NOTIF_ID, RR_ID, TENANT_ID, NOTIF_TYPE, CHANNELS_USED, RECIPIENTS, MESSAGE_BODY)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (notif_id, rr_id, run["TENANT_ID"], notif_type, channels_str, recipients, message_body))

        conn.commit()
        print(f"[NOTIFICATION SENT] Channels: {channels_str} | To: {recipients} | Msg: {message_body}")

    conn.close()