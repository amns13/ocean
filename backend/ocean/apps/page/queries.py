PAGE_BLOCKS_QUERY = """
WITH RECURSIVE page AS ( SELECT id, first_block_id FROM page_page WHERE id = %s),
blocks AS (
    SELECT
        page_block.id,
        uid,
        content,
        next_id,
        1 as index
    FROM
        page_block
    JOIN
        page ON page_block.id = page.first_block_id AND page_block.page_id = page.id
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
