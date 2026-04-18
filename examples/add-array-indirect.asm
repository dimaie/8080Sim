; The sum will be accumulated into d
  mvi d, 0

; Demonstrates indirect addressing, by keeping
; a "pointer" to myArray in bc.
  lxi bc, myArray

; Each iteration: load next item from myArray
; (until finding 0) into a. Then accumulate into d.
Loop:
  ldax bc
  cpi 0
  jz Done
  add d
  mov d, a
  inr c
  jmp Loop

Done:
  hlt

myArray:
  db 10h, 20h, 30h, 10h, 20h, 0