import json
import sqlite3
import os

DB_NAME = "report_monitor.db"
JSON_FILE = "report_jobs.json"

def classify_failure(status, row_count, duration):
    """Normalizes messy log statuses into clean failure categories."""
    status_lower = status.lower()
    if status_lower in ["completed", "success"]:
        if row_count == 0 or row_count is None:
            return "NULL_REPORT"
        return "NONE"
    elif "time" in status_lower:
        return "TIMED_OUT"
    elif "error" in status_lower or "fail" in status_lower:
        return "DATABASE_ERROR"
    return "UNKNOWN_ERROR"

def seed_database():
    # 1. Clean up existing DB
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
        
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 2. Execute DDL
    with open("schema.sql", "r") as f:
        cursor.executescript(f.read())


    # 3. Load JSON Data
    with open(JSON_FILE, "r") as f:
        data = json.load(f)

    # Track unique entities to populate Master tables safely
    tenants = {}
    reports = {}
    schedules = {}

    for job in data["jobs"]:
        t_id = job["tenant_id"]
        r_id = f"REP_{t_id}" # Assuming 1 default report per tenant for this dataset
        s_id = f"SCH_{r_id}"
        
        # Populate Tenant Master
        if t_id not in tenants:
            tenants[t_id] = {
                "name": job["tenant_name"],
                "tier": "Tier 1" if t_id in ["T-01", "T-03"] else "Tier 2", # Dummy tier logic
                "contact": f"Ops Lead {t_id}",
                "email": f"ops@{t_id.lower()}.com"
            }
            cursor.execute("""
                INSERT INTO TENANT_MASTER VALUES (?, ?, ?, ?, ?)
            """, (t_id, tenants[t_id]["name"], tenants[t_id]["tier"], tenants[t_id]["contact"], tenants[t_id]["email"]))

        # Populate Report Master
        if r_id not in reports:
            reports[r_id] = True
            cursor.execute("""
                INSERT INTO REPORT_MASTER VALUES (?, ?, ?, ?)
            """, (r_id, t_id, job["report_name"], "Critical" if t_id == "T-03" else "Medium"))

        # Populate Schedule Master
        if s_id not in schedules:
            schedules[s_id] = True
            cursor.execute("""
                INSERT INTO REPORT_SCHEDULE_MASTER VALUES (?, ?, ?, ?, ?, ?)
            """, (s_id, r_id, "Weekly", "02:00:00", 3, 300))

        # Populate Run Log
        rr_id = f"LOG_{job['job_id']}"
        failure_cat = classify_failure(job["status"], job["row_count"], job["duration_seconds"])
        is_auto_retry = 1 if job["attempt_number"] > 1 else 0
        
        # Fixing the date anomaly in JSON for T-03 (2026-09-00 -> 2026-09-07)
        sched_at = job["scheduled_at"].replace("2026-09-00", "2026-09-07")

        cursor.execute("""
            INSERT INTO REPORT_RUN_LOG VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            rr_id, r_id, s_id, sched_at, job["status"], 
            job["attempt_number"], job["duration_seconds"], 
            job["row_count"], failure_cat, is_auto_retry
        )

        )



    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' successfully created and seeded from '{JSON_FILE}'!")



if __name__ == "__main__":
    seed_database()