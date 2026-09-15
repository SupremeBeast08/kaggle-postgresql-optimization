INSERT INTO public.table2 (
    id_column_2,
    integer_column_1,
    integer_column_2,
    text_column_1,
    integer_column_3,
    integer_column_4,
    integer_column_5,
    integer_column_6
)
SELECT
    main_row.id_column_1,
    position_data.position_number,
    ROUND(
        NULLIF(BTRIM(position_data.weight_text), '')::numeric * 1000
    )::integer,
    UPPER(BTRIM(position_data.type_text)),
    NULL::integer,
    NULL::integer,
    NULL::integer,
    CASE
        WHEN NULLIF(BTRIM(position_data.gap_text), '')::numeric > 0
        THEN ROUND(
            NULLIF(BTRIM(position_data.gap_text), '')::numeric * 1000
        )::integer
        ELSE NULL::integer
    END
FROM {{source}} AS source_row
CROSS JOIN LATERAL jsonb_to_record(source_row.raw -> 'values') AS payload(
    integer_column_2 text, text_column_4 text, numeric_column_3 text, numeric_column_4 text,
    integer_column_3 text, text_column_5 text, numeric_column_5 text, numeric_column_6 text,
    integer_column_4 text, text_column_6 text, numeric_column_7 text, numeric_column_8 text,
    integer_column_5 text, text_column_7 text, numeric_column_9 text, numeric_column_10 text,
    integer_column_6 text, text_column_8 text, numeric_column_11 text, numeric_column_12 text,
    integer_column_7 text, text_column_9 text, numeric_column_13 text, numeric_column_14 text,
    integer_column_8 text, text_column_10 text, numeric_column_15 text, numeric_column_16 text,
    integer_column_9 text, text_column_11 text, numeric_column_17 text, numeric_column_18 text,
    integer_column_10 text, text_column_12 text, numeric_column_19 text, numeric_column_20 text,
    integer_column_11 text, text_column_13 text, numeric_column_21 text, numeric_column_22 text,
    integer_column_12 text, text_column_14 text, numeric_column_23 text, numeric_column_24 text,
    integer_column_13 text, text_column_15 text, numeric_column_25 text, numeric_column_26 text,
    integer_column_14 text, text_column_16 text, numeric_column_27 text, numeric_column_28 text,
    integer_column_15 text, text_column_17 text, numeric_column_29 text, numeric_column_30 text
)
CROSS JOIN LATERAL (
    VALUES
        (1::smallint, payload.integer_column_2, payload.text_column_4, payload.numeric_column_3, payload.numeric_column_4),
        (2::smallint, payload.integer_column_3, payload.text_column_5, payload.numeric_column_5, payload.numeric_column_6),
        (3::smallint, payload.integer_column_4, payload.text_column_6, payload.numeric_column_7, payload.numeric_column_8),
        (4::smallint, payload.integer_column_5, payload.text_column_7, payload.numeric_column_9, payload.numeric_column_10),
        (5::smallint, payload.integer_column_6, payload.text_column_8, payload.numeric_column_11, payload.numeric_column_12),
        (6::smallint, payload.integer_column_7, payload.text_column_9, payload.numeric_column_13, payload.numeric_column_14),
        (7::smallint, payload.integer_column_8, payload.text_column_10, payload.numeric_column_15, payload.numeric_column_16),
        (8::smallint, payload.integer_column_9, payload.text_column_11, payload.numeric_column_17, payload.numeric_column_18),
        (9::smallint, payload.integer_column_10, payload.text_column_12, payload.numeric_column_19, payload.numeric_column_20),
        (10::smallint, payload.integer_column_11, payload.text_column_13, payload.numeric_column_21, payload.numeric_column_22),
        (11::smallint, payload.integer_column_12, payload.text_column_14, payload.numeric_column_23, payload.numeric_column_24),
        (12::smallint, payload.integer_column_13, payload.text_column_15, payload.numeric_column_25, payload.numeric_column_26),
        (13::smallint, payload.integer_column_14, payload.text_column_16, payload.numeric_column_27, payload.numeric_column_28),
        (14::smallint, payload.integer_column_15, payload.text_column_17, payload.numeric_column_29, payload.numeric_column_30)
) AS position_data(position_number, declared_number_text, type_text, weight_text, gap_text)
JOIN public.table1 AS main_row
  ON main_row.id_column_3 = source_row.raw_id
WHERE NULLIF(BTRIM(position_data.declared_number_text), '')::smallint
        = position_data.position_number
  AND NULLIF(BTRIM(position_data.weight_text), '')::numeric >= 0
  AND UPPER(BTRIM(position_data.type_text)) IN ('X', 'Y', 'Z');
