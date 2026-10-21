# AI-Driven Enhancements Specification: Report Monitoring & Auto-Triage

**Objective:** Transition the system from rule-based monitoring to autonomous, self-healing operations using Generative AI and Machine Learning.

---

## 1. Overview
While the core deterministic engine (rule-based retry policies and tiered notifications) successfully automates baseline triage, complex enterprise
environments present unstructured challenges—such as messy, evolving log formats and deep-seated database bottlenecks. 

By strategically layering AI into the architecture, we can eliminate manual log parsing, predict failures before they impact customers, 
and provide instant Root Cause Analysis (RCA).

---

## 2. Detailed AI Enhancements

### Enhancement 1: LLM-Powered Log Normalization
* **Problem Addressed:** Client logs use inconsistent terminology (`failed`, `error`, `timed-out`, custom stack traces) requiring constant manual regex maintenance.
* **Proposed Solution:** Pass raw, unstructured log blobs or stack traces through a lightweight LLM configured with structured JSON output.
* **Technical Implementation:**
  ```json
  {
    "normalized_status": "TRANSIENT_FAILURE",
    "safe_to_retry": true,
    "confidence_score": 0.98,
    "extracted_error_signature": "DB_DEADLOCK_TABLE_LOCK"
  }
  ```
* **Operational Impact:** Completely automates the messy log problem without needing custom regex rules for every new error type.

---

### Enhancement 2: Automated Root Cause Analysis (RCA)
* **Problem Addressed:** When a report fails repeatedly (e.g., Gamma Health's 3 consecutive timeouts), engineers must manually query database logs and inspect execution graphs to find the root cause.
* **Proposed Solution:** When a report hits max retry exhaustion, trigger an asynchronous background AI agent. The agent synthesizes run history, row count deviations, and error payloads.
* **Technical Implementation:**
  ```python
  # Background worker snippet
  if attempt >= max_retries and status == "timed-out":
      rca_summary = generate_ai_rca(report_name, tenant_name, error_logs)
      save_to_database(rr_id, rca_summary)
  ```
* **UI/UX Impact:** Displays an **"AI RCA Summary"** card directly in the Streamlit Triage tab:
  > 🤖 **AI Diagnostic:** *Gamma Health's monthly statement timed out 3 consecutive times due to a 400% spike in row volume, triggering a shared lock on `invoices_2026`. Recommended action: Increase timeout threshold to 600 seconds.*

---

### Enhancement 3: Predictive Anomaly Detection
* **Problem Addressed:** The current system reacts *after* a report fails or hits a hard timeout limit.
* **Proposed Solution:** Implement an Isolation Forest or rolling z-score model that monitors live execution metrics (`duration_seconds`, `row_count`).
* **Technical Implementation:**
  ```python
  # Anomaly check logic
  historical_avg_duration = get_historical_average(rep_id)
  if current_duration > (historical_avg_duration * 2.5) and job_is_still_running:
      trigger_predictive_warning(rep_id)
  ```
* **Operational Impact:** If a report's execution duration deviates significantly from its historical baseline while running, the system flags a **"Predictive Timeout Warning"** and alerts the admin *before* the job officially fails.

---

### Enhancement 4: Natural Language Operations Assistant (Streamlit Copilot)
* **Problem Addressed:** Admins have to manually filter and aggregate tables in the dashboard to find cross-tenant trends and operational insights.
* **Proposed Solution:** Embed a conversational LLM chat widget ("Ops Copilot") into a dedicated tab in the Streamlit app, connected to SQLite via Text-to-SQL or semantic search over logs.
* **Example Prompts:**
  * *"Which tenant had the most database errors this week?"*
  * *"Show me all critical Tier 1 reports that auto-retried successfully."*
  * *"Draft an incident summary email for Delta Logistics regarding yesterday's outage."*
* **Technical Implementation:** Built using LangChain or OpenAI's function-calling API to safely query the local SQLite database in read-only mode.

---

## 3. Updated Architecture Flow (With AI Integration)

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
       │                    │                    │
       └────────────────────┼────────────────────> [ 🤖 AI Copilot & RCA Agent ]
                            │                      (Parses logs, predicts timeouts,
                            │                       generates summaries)
```

---

## 4. Enterprise Considerations & Data Privacy

To deploy AI enhancements safely in enterprise environments:
1. **Data Masking:** PII (tenant names, emails) is scrubbed or tokenized before payloads are sent to any external LLM endpoint.
2. **Local LLM Option:** For clients with strict compliance/security requirements, the log-parsing and RCA agents can be hosted locally via **Ollama** running open-source models (e.g., `Llama-3-8B`), ensuring zero data leaves their private VPC.
