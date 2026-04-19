; Bresenham Circle Drawing Algorithm for SAP-3 / Intel 8080
; Center: (160, 120), Radius: 100

ORG 0x0000          ; Program ROM starts at 0x0000

JMP START

; Variable storage in Program RAM
ORG 0x2000
VAR_X:  DS 1
VAR_Y:  DS 1
VAR_D:  DS 2

ORG 0x0010
START:
    LXI SP, 0x3FFF  ; Initialize Stack Pointer to top of RAM
    
    ; Initialize Video Colors
    MVI A, 0xFF     ; Ink color (White)
    STA 0xC001
    MVI A, 0x00     ; Background color (Black)
    STA 0xC002

    MVI A, 0
    STA VAR_X
    MVI A, 100      ; Radius = 100
    STA VAR_Y
    LXI H, 0xFF9D   ; Initial D = 1 - R = -99 = 0xFF9D
    SHLD VAR_D
    
LOOP_START:
    LDA VAR_X
    MOV B, A
    LDA VAR_Y
    CMP B
    JC LOOP_END     ; If Y < X, we are done drawing
    
    CALL DRAW_8
    
    ; Check decision parameter D
    LHLD VAR_D
    MOV A, H
    ORA A
    JM D_LESS_THAN_ZERO
    
D_GREATER_EQUAL_ZERO:
    ; d = d + 2*x - 2*y + 5
    LDA VAR_X
    MOV B, A
    LDA VAR_Y
    MOV C, A
    MOV A, B
    SUB C           ; A = x - y
    
    ; Sign extend A to DE
    MOV E, A
    RLC
    SBB A
    MOV D, A        ; DE = x - y (16-bit signed)
    
    XCHG            ; HL = x - y, DE = d
    DAD H           ; HL = 2 * (x - y)
    
    LXI B, 5
    DAD B           ; HL = 2 * (x - y) + 5
    DAD D           ; HL = d + 2 * (x - y) + 5
    SHLD VAR_D
    
    ; x++, y--
    LDA VAR_X
    INR A
    STA VAR_X
    LDA VAR_Y
    DCR A
    STA VAR_Y
    JMP LOOP_NEXT
    
D_LESS_THAN_ZERO:
    ; d = d + 2*x + 3
    LDA VAR_X
    MOV E, A
    MVI D, 0
    XCHG            ; HL = x, DE = d
    DAD H           ; HL = 2 * x
    
    LXI B, 3
    DAD B           ; HL = 2 * x + 3
    DAD D           ; HL = d + 2 * x + 3
    SHLD VAR_D
    
    ; x++
    LDA VAR_X
    INR A
    STA VAR_X
    
LOOP_NEXT:
    JMP LOOP_START
    
LOOP_END:
    HLT             ; Halt processor when drawing is complete
    
; ---------------------------------------------------------
; DRAW_8 - Draws 8 symmetrical points
; ---------------------------------------------------------
DRAW_8:
    ; 1) (xc + x, yc + y)
    LDA VAR_X
    MOV E, A
    MVI D, 0
    LXI H, 160      ; xc = 160
    DAD D
    MOV B, H
    MOV C, L        ; BC = xc + x
    LDA VAR_Y
    ADI 120         ; yc = 120
    MOV E, A        ; E = yc + y
    CALL DRAW_PIXEL
    
    ; 2) (xc - x, yc + y)
    LDA VAR_X
    MOV E, A
    MVI A, 160
    SUB E
    MOV C, A
    MVI A, 0
    SBB D
    MOV B, A        ; BC = 160 - x
    LDA VAR_Y
    ADI 120
    MOV E, A
    CALL DRAW_PIXEL
    
    ; 3) (xc + x, yc - y)
    LDA VAR_X
    MOV E, A
    MVI D, 0
    LXI H, 160
    DAD D
    MOV B, H
    MOV C, L        ; BC = xc + x
    MVI A, 120
    LXI H, VAR_Y
    SUB M
    MOV E, A        ; E = 120 - y
    CALL DRAW_PIXEL
    
    ; 4) (xc - x, yc - y)
    LDA VAR_X
    MOV E, A
    MVI A, 160
    SUB E
    MOV C, A
    MVI A, 0
    SBB D
    MOV B, A        ; BC = 160 - x
    MVI A, 120
    LXI H, VAR_Y
    SUB M
    MOV E, A        ; E = 120 - y
    CALL DRAW_PIXEL
    
    ; 5) (xc + y, yc + x)
    LDA VAR_Y
    MOV E, A
    MVI D, 0
    LXI H, 160
    DAD D
    MOV B, H
    MOV C, L        ; BC = xc + y
    LDA VAR_X
    ADI 120
    MOV E, A        ; E = yc + x
    CALL DRAW_PIXEL
    
    ; 6) (xc - y, yc + x)
    LDA VAR_Y
    MOV E, A
    MVI A, 160
    SUB E
    MOV C, A
    MVI A, 0
    SBB D
    MOV B, A        ; BC = 160 - y
    LDA VAR_X
    ADI 120
    MOV E, A        ; E = yc + x
    CALL DRAW_PIXEL
    
    ; 7) (xc + y, yc - x)
    LDA VAR_Y
    MOV E, A
    MVI D, 0
    LXI H, 160
    DAD D
    MOV B, H
    MOV C, L        ; BC = xc + y
    MVI A, 120
    LXI H, VAR_X
    SUB M
    MOV E, A        ; E = 120 - x
    CALL DRAW_PIXEL
    
    ; 8) (xc - y, yc - x)
    LDA VAR_Y
    MOV E, A
    MVI A, 160
    SUB E
    MOV C, A
    MVI A, 0
    SBB D
    MOV B, A        ; BC = 160 - y
    MVI A, 120
    LXI H, VAR_X
    SUB M
    MOV E, A        ; E = 120 - x
    CALL DRAW_PIXEL
    
    RET
    
; ---------------------------------------------------------
; DRAW_PIXEL - Draws a single pixel at (X, Y)
; Inputs: BC = X (16-bit), E = Y (8-bit)
; ---------------------------------------------------------
DRAW_PIXEL:
    PUSH H
    PUSH D
    PUSH B
    PUSH PSW
    
    ; Calculate Y * 40 using shifts and adds
    MOV L, E
    MVI H, 0
    DAD H           ; HL = Y * 2
    DAD H           ; HL = Y * 4
    DAD H           ; HL = Y * 8
    MOV D, H
    MOV E, L        ; DE = Y * 8
    DAD H           ; HL = Y * 16
    DAD H           ; HL = Y * 32
    DAD D           ; HL = Y * 40
    
    ; Calculate X / 8 (shifts BC right 3 times securely)
    MOV A, B
    RRC
    RRC
    RRC
    ANI 0xE0
    MOV D, A
    MOV A, C
    RRC
    RRC
    RRC
    ANI 0x1F
    ORA D
    
    ; Add to HL to formulate full byte offset
    ADD L
    MOV L, A
    MOV A, H
    ACI 0x40        ; Add VRAM Base address (0x4000)
    MOV H, A        ; HL now points directly to the VRAM byte
    
    ; Calculate bit mask: 7 - (X % 8)
    MOV A, C
    ANI 0x07        ; A = X % 8
    JZ MASK_DONE_FAST
    MOV D, A        ; Loop counter
    MVI A, 0x80
MASK_LOOP:
    RRC
    DCR D
    JNZ MASK_LOOP
    JMP APPLY_MASK
    
MASK_DONE_FAST:
    MVI A, 0x80
    
APPLY_MASK:
    ORA M           ; Read from VRAM, OR with bit mask
    MOV M, A        ; Write back to VRAM
    
    POP PSW
    POP B
    POP D
    POP H
    RET