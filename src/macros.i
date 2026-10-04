.macro draw_inline_string_patch_call(pointer, jump_to) {
    jsr.w draw_inline_string_patched ; 3
    .dw pointer ; 2
    bra jump_to
}
