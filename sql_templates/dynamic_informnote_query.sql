-- ============================================================
-- Dynamic SQL Template for INFORM_NOTE
-- Purpose:
--   - Allow Dify → Backend → Oracle DB workflow to bind optional filters
--   - Every bind variable is nullable; if NULL, that condition is skipped
-- Columns are based on normalized_data.xlsx / Inform_note schema
-- ============================================================

/* Bind Variables (all optional unless noted)
    :site_id            VARCHAR2   -- ex) ICH, CJU, WUX
    :factory_id         VARCHAR2   -- ex) FAC_M16
    :line_id            VARCHAR2
    :process_id         VARCHAR2   -- ex) PROC_ET
    :model_id           VARCHAR2   -- ex) MDL_KE_PRO
    :eqp_id             VARCHAR2
    :down_type          VARCHAR2   -- SCHEDULED / UNSCHEDULED
    :status_id          VARCHAR2   -- COMPLETED / IN_PROGRESS
    :error_code         VARCHAR2
    :start_time_from    TIMESTAMP  -- 다운 시작 시간 범위 (시작)
    :start_time_to      TIMESTAMP  -- 다운 시작 시간 범위 (끝)
    :down_minutes_min   NUMBER     -- 다운타임 >= 값
    :down_minutes_max   NUMBER     -- 다운타임 <= 값

    -- Aggregation control
    :limit_rows         NUMBER     -- 상세 행 수 (기본 50)
*/

WITH params AS (
    SELECT
        :site_id          AS site_id,
        :factory_id       AS factory_id,
        :line_id          AS line_id,
        :process_id       AS process_id,
        :model_id         AS model_id,
        :eqp_id           AS eqp_id,
        :down_type        AS down_type,
        :status_id        AS status_id,
        :error_code       AS error_code,
        :start_time_from  AS start_time_from,
        :start_time_to    AS start_time_to,
        :down_minutes_min AS down_minutes_min,
        :down_minutes_max AS down_minutes_max,
        NVL(:limit_rows, 50) AS limit_rows
    FROM dual
)
-- 1) 통계 쿼리: 요청한 조건에 대한 개수/시간 집계
, stats AS (
    SELECT
        COUNT(*)                                   AS total_count,
        SUM(down_time_minutes)                     AS total_minutes,
        AVG(down_time_minutes)                     AS avg_minutes,
        MIN(down_time_minutes)                     AS min_minutes,
        MAX(down_time_minutes)                     AS max_minutes,
        COUNT(CASE WHEN down_type = 'SCHEDULED' THEN 1 END)    AS scheduled_count,
        COUNT(CASE WHEN down_type = 'UNSCHEDULED' THEN 1 END)  AS unscheduled_count,
        COUNT(CASE WHEN status_id = 'COMPLETED' THEN 1 END)    AS completed_count,
        COUNT(CASE WHEN status_id = 'IN_PROGRESS' THEN 1 END)  AS in_progress_count
    FROM INFORM_NOTE t, params p
    WHERE (p.site_id        IS NULL OR t.site_id = p.site_id)
      AND (p.factory_id     IS NULL OR t.factory_id = p.factory_id)
      AND (p.line_id        IS NULL OR t.line_id = p.line_id)
      AND (p.process_id     IS NULL OR t.process_id = p.process_id)
      AND (p.model_id       IS NULL OR t.model_id = p.model_id)
      AND (p.eqp_id         IS NULL OR t.eqp_id = p.eqp_id)
      AND (p.down_type      IS NULL OR t.down_type = p.down_type)
      AND (p.status_id      IS NULL OR t.status_id = p.status_id)
      AND (p.error_code     IS NULL OR t.error_code = p.error_code)
      AND (p.start_time_from IS NULL OR t.down_start_time >= p.start_time_from)
      AND (p.start_time_to   IS NULL OR t.down_start_time <= p.start_time_to)
      AND (p.down_minutes_min IS NULL OR NVL(t.down_time_minutes, 0) >= p.down_minutes_min)
      AND (p.down_minutes_max IS NULL OR NVL(t.down_time_minutes, 0) <= p.down_minutes_max)
)
-- 2) 상세 쿼리: 조건을 만족하는 행을 최신순으로 반환
SELECT
    t.informnote_id,
    t.site_id,
    t.factory_id,
    t.line_id,
    t.process_id,
    t.eqp_id,
    t.model_id,
    t.down_start_time,
    t.down_end_time,
    t.down_time_minutes,
    t.down_type,
    t.error_code,
    t.act_prob_reason,
    t.act_content,
    t.act_start_time,
    t.act_end_time,
    t.operator,
    t.first_detector,
    t.status_id,
    t.link,
    s.total_count,
    s.total_minutes,
    s.avg_minutes,
    s.min_minutes,
    s.max_minutes,
    s.scheduled_count,
    s.unscheduled_count,
    s.completed_count,
    s.in_progress_count
FROM INFORM_NOTE t
JOIN params p ON 1=1
CROSS JOIN stats s
WHERE (p.site_id        IS NULL OR t.site_id = p.site_id)
  AND (p.factory_id     IS NULL OR t.factory_id = p.factory_id)
  AND (p.line_id        IS NULL OR t.line_id = p.line_id)
  AND (p.process_id     IS NULL OR t.process_id = p.process_id)
  AND (p.model_id       IS NULL OR t.model_id = p.model_id)
  AND (p.eqp_id         IS NULL OR t.eqp_id = p.eqp_id)
  AND (p.down_type      IS NULL OR t.down_type = p.down_type)
  AND (p.status_id      IS NULL OR t.status_id = p.status_id)
  AND (p.error_code     IS NULL OR t.error_code = p.error_code)
  AND (p.start_time_from IS NULL OR t.down_start_time >= p.start_time_from)
  AND (p.start_time_to   IS NULL OR t.down_start_time <= p.start_time_to)
  AND (p.down_minutes_min IS NULL OR NVL(t.down_time_minutes, 0) >= p.down_minutes_min)
  AND (p.down_minutes_max IS NULL OR NVL(t.down_time_minutes, 0) <= p.down_minutes_max)
ORDER BY t.down_start_time DESC
FETCH FIRST (SELECT limit_rows FROM params) ROWS ONLY;

