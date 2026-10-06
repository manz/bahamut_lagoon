"""tile_pool's interface: set tile_pool.source, .destination and .format, then jsl.l tile_blit."""

TILE_2BPP = 0  ; the 2bpp tile as it is (16 bytes)
TILE_4BPP = 1  ; 4bpp, planes 2 and 3 clear: the glyph in colours 1 and 3 over colour 0 (32 bytes)
TILE_4BPP_FILL = 2  ; 4bpp, plane 2 where planes 0 and 1 are clear: the glyph over colour 4, a window's (32 bytes)
