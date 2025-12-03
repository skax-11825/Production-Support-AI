-- Error Code 통계 조회 SQL
-- 동적 부분: {period_select}, {group_by_clause}, {order_by_clause}

SELECT
    {period_select},
    n.process_id,
    p.process_name,
    n.model_id,
    m.model_name,
    n.eqp_id,
    e.eqp_name,
    n.error_code,
    ec.error_desc AS error_des,
    COUNT(*) AS event_cnt,
    SUM(n.down_time_minutes) AS total_down_time_minutes
FROM INFORM_NOTE n
LEFT JOIN PROCESS p ON n.process_id = p.process_id
LEFT JOIN EQUIPMENT e ON n.eqp_id = e.eqp_id
LEFT JOIN MODEL m ON n.model_id = m.model_id
LEFT JOIN ERROR_CODE ec ON n.error_code = ec.error_code
WHERE (:start_date IS NULL OR n.down_start_time >= TO_DATE(:start_date, 'YYYY-MM-DD'))
  AND (:end_date IS NULL OR n.down_start_time < TO_DATE(:end_date, 'YYYY-MM-DD') + 1)
  AND (:process_id IS NULL OR n.process_id = :process_id)
  AND (:model_id IS NULL OR n.model_id = :model_id)
  AND (:eqp_id IS NULL OR n.eqp_id = :eqp_id)
  AND (:error_code IS NULL OR n.error_code = :error_code)
  AND n.down_type_id = 1
GROUP BY {group_by_clause}
ORDER BY {order_by_clause}

