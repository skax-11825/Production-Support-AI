-- PM 이력 조회 SQL

SELECT
    TO_CHAR(n.down_start_time, 'YYYY-MM-DD') as down_date,
    dt.down_type_name,
    n.down_time_minutes,
    n.operator
FROM INFORM_NOTE n
LEFT JOIN DOWN_TYPE dt ON n.down_type_id = dt.down_type_id
WHERE (:start_date IS NULL OR n.down_start_time >= TO_DATE(:start_date, 'YYYY-MM-DD'))
  AND (:end_date IS NULL OR n.down_start_time < TO_DATE(:end_date, 'YYYY-MM-DD') + 1)
  AND (:process_id IS NULL OR n.process_id = :process_id)
  AND (:eqp_id IS NULL OR n.eqp_id = :eqp_id)
  AND (:operator IS NULL OR n.operator LIKE '%' || :operator || '%')
  AND n.down_type_id = 0
ORDER BY n.down_start_time DESC
FETCH FIRST :limit_val ROWS ONLY

