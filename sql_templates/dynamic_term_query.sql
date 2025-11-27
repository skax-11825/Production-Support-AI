WITH params AS (
    SELECT
        :term_id        AS term_id,
        :term_en        AS term_en,
        :term_kor       AS term_kor,
        :keyword        AS keyword,
        NVL(:limit_rows, 30) AS limit_rows
    FROM dual
)
SELECT
    t.term_id,
    t.term_en,
    t.term_kor_reading,
    t.meaning_short,
    t.meaning_field,
    t.search_keywords
FROM FAB_TERMS_DICTIONARY t
CROSS JOIN params p
WHERE (p.term_id IS NULL OR t.term_id = p.term_id)
  AND (p.term_en IS NULL OR LOWER(t.term_en) LIKE LOWER('%' || p.term_en || '%'))
  AND (p.term_kor IS NULL OR t.term_kor_reading LIKE '%' || p.term_kor || '%')
  AND (
        p.keyword IS NULL
        OR LOWER(t.search_keywords) LIKE LOWER('%' || p.keyword || '%')
        OR LOWER(t.meaning_short) LIKE LOWER('%' || p.keyword || '%')
        OR LOWER(t.meaning_field) LIKE LOWER('%' || p.keyword || '%')
      )
ORDER BY t.term_en
FETCH FIRST (SELECT limit_rows FROM params) ROWS ONLY;

