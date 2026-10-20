-- ==========================================
-- 1. POPULATE TENANT MASTER
-- ==========================================
INSERT INTO TENANT_MASTER VALUES ('T-01', 'Alpha Corp', 'Tier 1', 'Ops Lead T-01', 'ops@t-01.com');
INSERT INTO TENANT_MASTER VALUES ('T-02', 'Beta Retail', 'Tier 2', 'Ops Lead T-02', 'ops@t-02.com');
INSERT INTO TENANT_MASTER VALUES ('T-03', 'Gamma Health', 'Tier 1', 'Ops Lead T-03', 'ops@t-03.com');
INSERT INTO TENANT_MASTER VALUES ('T-04', 'Delta Logistics', 'Tier 2', 'Ops Lead T-04', 'ops@t-04.com');
INSERT INTO TENANT_MASTER VALUES ('T-05', 'Epsilon Media', 'Tier 2', 'Ops Lead T-05', 'ops@t-05.com');
INSERT INTO TENANT_MASTER VALUES ('T-06', 'Zeta Finance', 'Tier 2', 'Ops Lead T-06', 'ops@t-06.com');

-- ==========================================
-- 2. POPULATE REPORT MASTER
-- ==========================================
INSERT INTO REPORT_MASTER VALUES ('REP_T-01', 'T-01', 'Monthly Statement', 'Medium');
INSERT INTO REPORT_MASTER VALUES ('REP_T-02', 'T-02', 'Monthly Statement', 'Medium');
INSERT INTO REPORT_MASTER VALUES ('REP_T-03', 'T-03', 'Monthly Statement', 'Critical'); -- Gamma Health is critical
INSERT INTO REPORT_MASTER VALUES ('REP_T-04', 'T-04', 'Monthly Statement', 'Medium');
INSERT INTO REPORT_MASTER VALUES ('REP_T-05', 'T-05', 'Monthly Statement', 'Medium');
INSERT INTO REPORT_MASTER VALUES ('REP_T-06', 'T-06', 'Monthly Statement', 'Medium');

-- ==========================================
-- 3. POPULATE REPORT SCHEDULE MASTER
-- ==========================================
INSERT INTO REPORT_SCHEDULE_MASTER VALUES ('SCH_REP_T-01', 'REP_T-01', 'Weekly', '02:00:00', 3, 300);
INSERT INTO REPORT_SCHEDULE_MASTER VALUES ('SCH_REP_T-02', 'REP_T-02', 'Weekly', '02:00:00', 3, 300);
INSERT INTO REPORT_SCHEDULE_MASTER VALUES ('SCH_REP_T-03', 'REP_T-03', 'Weekly', '02:00:00', 3, 300);
INSERT INTO REPORT_SCHEDULE_MASTER VALUES ('SCH_REP_T-04', 'REP_T-04', 'Weekly', '02:00:00', 3, 300);
INSERT INTO REPORT_SCHEDULE_MASTER VALUES ('SCH_REP_T-05', 'REP_T-05', 'Weekly', '02:00:00', 3, 300);
INSERT INTO REPORT_SCHEDULE_MASTER VALUES ('SCH_REP_T-06', 'REP_T-06', 'Weekly', '02:00:00', 3, 300);

-- ==========================================
-- 4. POPULATE REPORT RUN LOG (15 JSON Records)
-- ==========================================

-- J-001 (Alpha Corp)
INSERT INTO REPORT_RUN_LOG VALUES ('LOG_J-001', 'REP_T-01', 'SCH_REP_T-01', '2026-09-01T02:00:00', 'completed', 1, 42, 1820, 'NONE', 0);

-- J-002 (Alpha Corp)
INSERT INTO REPORT_RUN_LOG VALUES ('LOG_J-002', 'REP_T-01', 'SCH_REP_T-01', '2026-09-08T02:00:00', 'completed', 1, 39, 1904, 'NONE', 0);

-- J-003 (Beta Retail - Attempt 1: Failed)
INSERT INTO REPORT_RUN_LOG VALUES ('LOG_J-003', 'REP_T-02', 'SCH_REP_T-02', '2026-09-01T02:00:00', 'failed', 1, 11, NULL, 'DATABASE_ERROR', 0);

-- J-004 (Beta Retail - Attempt 2: Recovered)
INSERT INTO REPORT_RUN_LOG VALUES ('LOG_J-004', 'REP_T-02', 'SCH_REP_T-02', '2026-09-01T02:05:00', 'completed', 2, 55, 3210, 'NONE', 1);

-- J-005 (Beta Retail)
INSERT INTO REPORT_RUN_LOG VALUES ('LOG_J-005', 'REP_T-02', 'SCH_REP_T-02', '2026-09-08T02:00:00', 'completed', 1, 48, 3305, 'NONE', 0);

-- J-006 (Gamma Health - Attempt 1: Timed Out)
INSERT INTO REPORT_RUN_LOG VALUES ('LOG_J-006', 'REP_T-03', 'SCH_REP_T-03', '2026-09-07T02:00:00', 'timed-out', 1, 300, NULL, 'TIMED_OUT', 0);

-- J-007 (Gamma Health - Attempt 2: Timed Out)
INSERT INTO REPORT_RUN_LOG VALUES ('LOG_J-007', 'REP_T-03', 'SCH_REP_T-03', '2026-09-07T02:10:00', 'timed-out', 2, 300, NULL, 'TIMED_OUT', 1);

-- J-008 (Gamma Health - Attempt 3: Timed Out - Max Retries Reached)
INSERT INTO REPORT_RUN_LOG VALUES ('LOG_J-008', 'REP_T-03', 'SCH_REP_T-03', '2026-09-07T02:20:00', 'timed-out', 3, 300, NULL, 'TIMED_OUT', 1);

-- J-009 (Gamma Health)
INSERT INTO REPORT_RUN_LOG VALUES ('LOG_J-009', 'REP_T-03', 'SCH_REP_T-03', '2026-09-08T02:00:00', 'completed', 1, 51, 4110, 'NONE', 0);

-- J-010 (Delta Logistics)
INSERT INTO REPORT_RUN_LOG VALUES ('LOG_J-010', 'REP_T-04', 'SCH_REP_T-04', '2026-09-01T02:00:00', 'completed', 1, 37, 980, 'NONE', 0);

-- J-011 (Delta Logistics)
INSERT INTO REPORT_RUN_LOG VALUES ('LOG_J-011', 'REP_T-04', 'SCH_REP_T-04', '2026-09-08T02:00:00', 'completed', 1, 40, 1015, 'NONE', 0);

-- J-012 (Epsilon Media)
INSERT INTO REPORT_RUN_LOG VALUES ('LOG_J-012', 'REP_T-05', 'SCH_REP_T-05', '2026-09-01T02:00:00', 'completed', 1, 45, 2260, 'NONE', 0);

-- J-013 (Epsilon Media - Unresolved Error, Needs Retry)
INSERT INTO REPORT_RUN_LOG VALUES ('LOG_J-013', 'REP_T-05', 'SCH_REP_T-05', '2026-09-08T02:00:00', 'error', 1, 6, NULL, 'DATABASE_ERROR', 0);

-- J-014 (Zeta Finance)
INSERT INTO REPORT_RUN_LOG VALUES ('LOG_J-014', 'REP_T-06', 'SCH_REP_T-06', '2026-09-01T02:00:00', 'completed', 1, 33, 760, 'NONE', 0);

-- J-015 (Zeta Finance)
INSERT INTO REPORT_RUN_LOG VALUES ('LOG_J-015', 'REP_T-06', 'SCH_REP_T-06', '2026-09-08T02:00:00', 'completed', 1, 31, 802, 'NONE', 0);