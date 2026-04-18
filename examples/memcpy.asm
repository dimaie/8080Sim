  lxi de, SourceArray
  lxi hl, TargetArray
  mvi b, 0
  mvi c, 5
  call memcpy
  hlt

SourceArray:
  db 11h, 22h, 33h, 44h, 55h

TargetArray:
  db 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

  ; bc: number of bytes to copy
  ; de: source block
  ; hl: target block
memcpy:
  mov     a,b         ;Copy register B to register A
  ora     c           ;Bitwise OR of A and C into register A
  rz                  ;Return if the zero-flag is set high.
loop:
  ldax    de          ;Load A from the address pointed by DE
  mov     m,a         ;Store A into the address pointed by HL
  inx     de          ;Increment DE
  inx     hl          ;Increment HL
  dcx     bc          ;Decrement BC   (does not affect Flags)
  mov     a,b         ;Copy B to A    (so as to compare BC with zero)
  ora     c           ;A = A | C      (set zero)
  jnz     loop        ;Jump to 'loop:' if the zero-flag is not set.
  ret                 ;Return