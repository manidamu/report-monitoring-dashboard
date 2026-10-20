# report-monitoring-dashboard

As a Forward Deployed Engineer (FDE), my immediate goal is to transition this client from a **reactive** (customer-complaint-driven) posture to a **proactive** (self-healing/alerting) posture. Because I am deployed directly with the client, I need to balance a quick MVP (to stop the bleeding) with a robust architectural fix for their messy logs.

Here is my structured thought process, followed by the requested breakdown of ambiguities, missing requirements, and assumptions.

---

### Part 1: My Thought Process as an FDE

1.  **Triage & Immediate Relief:**
    *   I need to stop the current bleeding where customers are the ones reporting missing reports. 
    *   Even before untangling the messy logs, can I build a simple cron job that runs every hour, queries the last $X$ hours of job history, and flags anything that looks like an obvious failure?
2.  **Define "Failure" (The Log Mess):**
    *   The client admits log statuses are inconsistent. I need to ingest a sample of historical logs, categorize the error states (e.g., HTTP 5xx, timeouts, database deadlocks, silent failures where a job finished with 0 bytes, vs. hard rejections like "invalid user"), and map them to a unified status enum (`SUCCESS`, `RETRYABLE_FAIL`, `FATAL_FAIL`).
3.  **Determine "Safety" for Retries:**
    *   Not all reports are safe to retry. (e.g., Does retrying duplicate a financial transaction email? Is the report generating heavy queries that will crash the DB during peak hours?). 
    *   I need to implement an **Idempotency Check** or a **Safe-to-Retry Policy Engine** based on report type.
4.  **Architect the Solution:**
    *   **Data Source:** Where do the logs live? (SQL DB, Elasticsearch, CloudWatch, S3?)
    *   **Processor:** A lightweight worker (e.g., a serverless Lambda or a dedicated cron worker) that polls the logs, evaluates failure definitions, and triggers retries.
    *   **Action Layer:** Interface with their existing Job Runner API to kick off retries.
    *   **Fallback/Alerting Layer:** If a job fails and is *not* safe to retry automatically, or if retries are exhausted, ping the engineering/support team via Slack/PagerDuty *before* the customer emails.
5.  **Iterate with the Client:**
    *   Deploy the detection-and-alerting part first (so they know *when* things break).
    *   Add the safe-retry mechanism second (once we trust the failure logic).

---

### Part 2: Ambiguities in the Problem Statement

1.  **What constitutes "Never Succeeded"?** 
    *   Does this mean a single scheduled run failed once, or does it mean a schedule ran, failed 3 times in a row, and never achieved a success state for that specific time window?
2.  **Definition of "Safe to Retry":**
    *   The client mentions wanting to retry "safe" ones, but provides no criteria for what makes a report safe. Is it based on the *error type* (e.g., timeout vs. bad syntax), the *report category* (e.g., analytics vs. billing), or side effects (e.g., does it trigger external webhooks)?
3.  **The "Messy Logs":**
    *   How inconsistent are the logs? Are we dealing with varying string formats ("FAILED", "Error", "Err", "failed_execution"), missing status fields entirely, or unstructured plain-text log files?
4.  **Frequency and Window:**
    *   How often should this watcher run? (Every 15 minutes? Once a day?) How far back should it look for missed reports?

---

### Part 3: Clear Requirements Missing from the Statement

1.  **Notification & Escalation Protocol:** 
    *   What happens when a job fails and is *not* safe to retry? Where should the alert go (Slack, Email, PagerDuty), and what metadata needs to be in that alert?
2.  **Retry Limits and Backoff Policy:**
    *   If we retry a failed report, how many times should we try? Is there a backoff period (e.g., wait 10 minutes, then 30 minutes) to prevent hammering a struggling database?
3.  **Rate Limiting / Resource Throttling:**
    *   If a database outage caused 500 reports to fail simultaneously, retrying all of them at once might crash the system again. We need a requirement for concurrency limits on retries.
4.  **Auditability / Observability of the Fix Tool:**
    *   We need a log or dashboard for *our* new tool so the client can see: "X reports failed, Y were safely retried, Z required manual intervention."
5.  **Tenant SLA/Timezone Awareness:**
    *   When is a scheduled report actually considered "late"? (e.g., If a tenant expects a report by 8:00 AM in their local timezone, our watcher needs to account for timezones, not just UTC).

---

### Part 4: Assumptions to Make to Develop a Solution

To build an MVP rapidly, I will make the following working assumptions (which I will validate with the client during kick-off):

1.  **Data Access:** We have read access to the job runner's log store and write/trigger access to the job runner's execution API (i.e., we can programmatically trigger a job re-run).
2.  **Retry Safety Rule of Thumb (Default):** 
    *   *Safe to retry:* Infrastructure errors, timeouts, database connection drops, rate limits.
    *   *Not safe to retry:* Authentication failures, invalid report parameters/syntax, missing data sources, or reports explicitly tagged as `non_idempotent`.
3.  **Idempotency:** Re-running a failed report generation overwrites or safely appends to the previous output, rather than duplicating external side effects (like charging a credit card or sending duplicate customer emails).
4.  **Retry Threshold:** We will attempt a maximum of **3 automatic retries** with exponential backoff before escalating to a human.
5.  **Log Normalization:** We can write a deterministic regex/parsing layer to normalize the messy log statuses into a standard internal state machine for our watcher service.