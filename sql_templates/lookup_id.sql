-- ID/NAME 조회 SQL 템플릿
-- 동적 부분: {id_col}, {name_col}, {table}, {where_conditions}

SELECT {id_col}
FROM {table}
WHERE {where_conditions}
FETCH FIRST 1 ROWS ONLY

