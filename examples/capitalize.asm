  lxi hl, str
  mvi c, 14
  call Capitalize
  hlt

Capitalize:
  mov a, c
  cpi 0
  jz AllDone

  mov a, m
  cpi 61h
  jc SkipIt

  cpi 7bh
  jnc SkipIt

  sui 20h
  mov m, a

SkipIt:
  inx hl
  dcr c
  jmp Capitalize

AllDone:
  ret

str:
  db 'hello, friends'