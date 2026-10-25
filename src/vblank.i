"""The vblank's lines, for the DMAs src/vblank.s times."""


VBLANK_LINE = 225
LAST_LINE = 257  ; a DMA ends before it: an NMI's tail and a console a hair slower than ares still fit
