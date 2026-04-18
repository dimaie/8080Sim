; Set the Stack Pointer to a specific address
; so we can clearly watch it move in the Stack Panel!
  lxi sp, 0100h

; Load some distinct visual values into the register pairs
  lxi b, 1122h
  lxi d, 3344h
  lxi h, 5566h

; Watch the Stack Panel as we push these onto the stack
  push b
  push d
  push h

; Call a subroutine (this will push the 16-bit return address)
  call Subroutine

; Pop them back off the stack in reverse order
  pop h
  pop d
  pop b
  hlt

Subroutine:
; Push the Processor Status Word (A register + Flags)
  mvi a, 99h
  push psw
  pop psw
  ret