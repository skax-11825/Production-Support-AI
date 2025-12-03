-- 상세 조치 내역 검색 SQL

SELECT
    n.informnote_id,
    TO_CHAR(n.down_start_time, 'YYYY-MM-DD HH24:MI:SS') as down_start_time,
    p.process_name,
    e.eqp_name,
    n.error_code,
    ec.error_desc,
    n.act_content,
    n.operator,
    n.status_id,
    s.status_name
FROM INFORM_NOTE n
LEFT JOIN PROCESS p ON n.process_id = p.process_id
LEFT JOIN EQUIPMENT e ON n.eqp_id = e.eqp_id
LEFT JOIN ERROR_CODE ec ON n.error_code = ec.error_code
LEFT JOIN STATUS s ON n.status_id = s.status_id
WHERE (:start_date IS NULL OR n.down_start_time >= TO_DATE(:start_date, 'YYYY-MM-DD'))
  AND (:end_date IS NULL OR n.down_start_time < TO_DATE(:end_date, 'YYYY-MM-DD') + 1)
  AND (:process_id IS NULL OR n.process_id = :process_id)
  AND (:eqp_id IS NULL OR n.eqp_id = :eqp_id)
  AND (:operator IS NULL OR n.operator LIKE '%' || :operator || '%')
  AND (:status_id IS NULL OR n.status_id = :status_id)
ORDER BY n.down_start_time DESC
FETCH FIRST :limit_val ROWS ONLY

