PAGE_BLOCKS_QUERY = """
WITH RECURSIVE blocks AS (
    SELECT
        id,
        uid,
        content,
        next_id,
        1 as index
    FROM
        page_block
    WHERE
        page_id = %s and previous_id IS NULL
UNION ALL
    SELECT
        pb.id,
        pb.uid,
        pb.content,
        pb.next_id,
        blocks.index + 1 as index
    FROM
        page_block pb
    JOIN 
        blocks ON blocks.next_id = pb.id
)
SELECT id, uid, content FROM blocks ORDER BY index;
"""
