"""Named routines of the original game (`.label`): no bytes, but the .adbg, xdds and the LSP symbolicate them."""

; Bank $EE: the menu engine's tasks

"""The cooperative task switch: the calling task waits for the next frame."""
.label task_yield = 0xEE440B

"""The messages loop's end (EE5409's), past its glyph loop: the message is drawn."""
.label message_drawn = 0xEE5484

"""The chapter title task's upload (EE5510's): its 16 columns, both rows, queued to VRAM $34."""
.label queue_title = 0xEE55BB

"""The chapter title task's end, past its upload: a yield, then the task ends."""
.label title_queued = 0xEE5629
