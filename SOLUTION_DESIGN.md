# Solution Design Document: Proactive Report Monitoring & Auto-Triage System

**Author:** Mani Damodaran as an FDE  
**Status:** MVP Ready  
**Target Deployment:** Streamlit Community Cloud + SQLite  
The application is deployed on Streamlit Community Cloud , use the below url to access the application
[Report Run Monitor & Auto-Triage Dashboard](https://report-monitoring-dashboard-8s3rbnqsi48byxkyckokoh.streamlit.app/)
---

## 1. Executive Summary & Problem Statement
Currently, the platform suffers from a **reactive operational posture**: scheduled reports occasionally fail or time out, and the engineering/admin team only discovers the issue when a tenant emails asking *"Where is my report?"* 

Furthermore, log statuses are inconsistent (`failed`, `timed-out`, `error`), and there is no automated safety net to retry safe failures or route alerts based on business criticality.

### Objectives:
1. **Normalize Log Ingestion:** Unify messy log statuses into actionable failure categories.
2. **Proactive Triage:** Provide admins with a real-time Streamlit dashboard highlighting unresolved failures.
3. **Self-Healing (Auto-Retry):** Automatically retry transient failures (timeouts, DB drops) before a customer notices.
4. **Criticality-Based Notifications:** Dispatch tiered alerts (Email/SMS) based on Tenant Tier and Report Criticality.

---

## 2. System Architecture Overview
```text
 [ Job Runner Logs ] 
         │
         ▼
( JSON / API Ingest ) 
         │
         ▼
┌────────────────────────────────────────────────────────┐
│                   [ SQLite Database ]                  │
└───────────────────────────┬────────────────────────────┘
                            │
       ┌────────────────────┼────────────────────┐
       ▼                    ▼                    ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Auto-Retry  │     │ Notification │     │  Streamlit   │
│    Engine    │     │    Engine    │     │  Dashboard   │
└──────────────┘     └──────────────┘     └──────────────┘
  (Evaluates safe-     (Applies Tier/       (Live Triage &
   to-retry & re-run)   Criticality rules)   Audit Trail)

```



## 3. Database Schema Design

The relational database is structured around five core tables:

1. **`TENANT_MASTER`**: Stores tenant metadata, tier (`Tier 1` / `Tier 2`), and primary contacts.
2. **`REPORT_MASTER`**: Maps reports to tenants and defines their criticality (`Critical`, `High`, `Medium`, `Low`).
3. **`REPORT_SCHEDULE_MASTER`**: Defines execution frequency, timeouts, and max retry limits.
4. **`REPORT_RUN_LOG`**: Captures execution attempts, durations, row counts, and normalized failure categories.
5. **`NOTIFICATION_LOG`**: An audit trail of all automated Emails and SMS alerts dispatched by the notification engine.

*(Refer to `schema.sql` for full DDL implementation)*

---

## 4. Failure Detection & Normalization

To untangle the messy logs, an ingestion/normalization layer categorizes raw execution statuses:
*   **`NONE`**: Job completed successfully with valid row counts.
*   **`TIMED_OUT`**: Job exceeded the maximum allowed duration (e.g., 300 seconds).
*   **`DATABASE_ERROR`**: Connection drops, transient infrastructure faults, or generic run errors.
*   **`NULL_REPORT`**: Jobs marked as "completed" but outputting 0 rows unexpectedly (silent failures).

---

## 5. Auto-Remediation & Safe-Retry Engine
*   **Eligibility:** Only transient errors (`TIMED_OUT`, `DATABASE_ERROR`) are marked safe for retry. Hard errors (syntax, auth) are excluded.
*   **Thresholds:** Bounded by `REP_SCHE_RETRY_ATTEMPTS` (max 3 attempts).
*   **Action:** If a job fails on attempt 1 or 2 and is retryable, the system flags it for auto-remediation. If max attempts are exhausted, it escalates to human intervention.

---

## 6. Notification Engine Matrix

Notifications are dispatched based on a matrix of **Tenant Tier** + **Report Criticality** + **Attempt State**:

| Tenant Tier | Report Criticality | Rule / Trigger Condition | Channels |
| :--- | :--- | :--- | :--- |
| **All Tiers** | *Any* | **Success**: Every successful run | Email (Admin + Tenant) |
| **Tier 1** | Critical | **1st Failure**: Immediate alert | SMS + Email |
| **Tier 1** | High | **2nd Failure**: Escalation alert | SMS + Email |
| **Tier 1** | Medium / Low | **Max Attempts Exhausted**: Final failure | Email (Suppressed on intermediate tries) |
| **Tier 2** | Critical | **1st Failure**: Standard alert | Email |
| **Tier 2** | High | **2nd Failure**: Standard alert | Email |
| **Tier 2** | Medium / Low | **Max Attempts Exhausted**: Final failure | Email |

---

## 7. Project Structure & Deployment Guide

```text
report-monitoring-dashboard/
├── .gitignore
├── README.md
├── requirements.txt
├── schema.sql
├── seed_database.py
├── report_jobs.json
├── app.py
└── utils/
    ├── __init__.py
    ├── db_helpers.py
    └── notifier.py