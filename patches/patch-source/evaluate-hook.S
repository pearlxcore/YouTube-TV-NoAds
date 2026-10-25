.syntax unified
.arm
.section .text,"ax",%progbits
.global x90h_hook
.global x90h_trampoline
.global x90h_payload
.type x90h_hook,%function
x90h_hook:
  push {r0,r1,r2,r3,r12,lr}
  sub sp,sp,#48
  mov r2,#0
  str r2,[sp,#0]
  str r2,[sp,#4]
  str r2,[sp,#8]
  str r2,[sp,#12]
  str r2,[sp,#16]
  str r2,[sp,#20]
  str r2,[sp,#24]
  str r2,[sp,#28]
  str r2,[sp,#32]
  str r2,[sp,#36]
  str r2,[sp,#40]
  ldr r2,[r1]
  ldr r2,[r2]
  str r2,[sp,#0]        /* Borrow vtable; Compile only reads this object. */
  mov r2,#1
  str r2,[sp,#4]        /* Refcount placeholder; not owned or destroyed. */
  str r2,[sp,#8]        /* libc++ long string tag. */
  str r2,[sp,#32]       /* SourceLocation line. */
  str r2,[sp,#36]       /* SourceLocation column. */
  ldr r2,payload_length
  str r2,[sp,#12]
  adr r2,x90h_payload
  str r2,[sp,#16]
  mov r2,sp
  str r2,[sp,#44]
  add r1,sp,#44
  bl x90h_trampoline    /* Evaluate local hook in the already entered realm. */
  add sp,sp,#48
  pop {r0,r1,r2,r3,r12,lr}
  b x90h_trampoline     /* Evaluate original source with original arguments. */
.size x90h_hook,.-x90h_hook
.balign 4
x90h_trampoline:
  .word 0xe92d4bf0      /* Exact original push {r4-r9,r11,lr}. */
  .word 0xe28db018      /* Exact original add fp,sp,#24. */
  b x90h_resume
payload_length:
  .word x90h_payload_end-x90h_payload-1
x90h_payload:
  .incbin "response-filter.js"
  .incbin "about-marker.js"
  .incbin "loading-indicator.js"
  .byte 0
x90h_payload_end:
