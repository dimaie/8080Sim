; =========================================================================
; SAP-3 Snake Game
; Architecture: Intel 8080 / SAP-3
; Video: 80x30 Text Mode (0xA000)
; Controls: PS/2 Arrow Keys
; =========================================================================

ORG 0x3000          ; Load into User RAM via Monitor

; --- Hardware Addresses ---
VID_INK     EQU 0xC001
VID_BG      EQU 0xC002
TXT_RAM     EQU 0xA000
KB_DATA     EQU 0x00
KB_STATUS   EQU 0x01
VID_CSR     EQU 0xC005

; =========================================================================
; 1. INITIALIZATION
; =========================================================================
START:
    ; Reset Game State Variables
    XRA A
    STA VAR_KB_SKIP
    STA VAR_SCORE
    STA VAR_TAIL_PTR
    
    MVI A, 1
    STA VAR_DIR         ; Initial Direction: Right
    STA VAR_DIR_NEXT
    
    MVI A, 2
    STA VAR_HEAD_PTR    ; Initial Head Pointer
    
    ; Setup Colors (Bright Green on Black)
    MVI A, 0x1C
    STA VID_INK
    MVI A, 0x00
    STA VID_BG
    
    ; Hide Hardware Cursor
    MVI A, 0
    STA VID_CSR
    
    CALL CLEAR_SCREEN
    CALL CLEAR_GFX
    CALL DRAW_BORDERS
    CALL UPDATE_SCORE
    
    ; Initialize Snake Body (Length = 3)
    ; Tail Segment [0]
    MVI A, 40
    STA VAR_SNAKE_X
    MVI A, 15
    STA VAR_SNAKE_Y
    MVI B, 40
    MVI C, 15
    CALL CALC_VRAM_ADDR
    MVI M, 'O'
    
    ; Middle Segment [1]
    MVI A, 41
    STA VAR_SNAKE_X + 1
    MVI A, 15
    STA VAR_SNAKE_Y + 1
    MVI B, 41
    MVI C, 15
    CALL CALC_VRAM_ADDR
    MVI M, 'O'
    
    ; Head Segment [2]
    MVI A, 42
    STA VAR_SNAKE_X + 2
    MVI A, 15
    STA VAR_SNAKE_Y + 2
    MVI B, 42
    MVI C, 15
    CALL CALC_VRAM_ADDR
    MVI M, '@'
    
    CALL SPAWN_FOOD

; =========================================================================
; 2. MAIN GAME LOOP
; =========================================================================
MAIN_LOOP:
    CALL DELAY          ; Control game speed
    CALL CHECK_INPUT    ; Read Keyboard
    
    ; Lock in the next direction for this frame
    LDA VAR_DIR_NEXT
    STA VAR_DIR
    
    ; Retrieve Current Head Coordinates
    LDA VAR_HEAD_PTR
    CALL GET_SNAKE_X
    MOV B, A            ; B = Head X
    LDA VAR_HEAD_PTR
    CALL GET_SNAKE_Y
    MOV C, A            ; C = Head Y
    
    ; Apply Movement
    LDA VAR_DIR
    CPI 0
    JZ MOVE_UP
    CPI 1
    JZ MOVE_RIGHT
    CPI 2
    JZ MOVE_DOWN
    CPI 3
    JZ MOVE_LEFT

MOVE_UP:
    DCR C
    JMP CHECK_COLLISIONS
MOVE_RIGHT:
    INR B
    JMP CHECK_COLLISIONS
MOVE_DOWN:
    INR C
    JMP CHECK_COLLISIONS
MOVE_LEFT:
    DCR B
    JMP CHECK_COLLISIONS

CHECK_COLLISIONS:
    ; --- 1. Wall Collisions ---
    MOV A, B
    CPI 0
    JZ GAME_OVER
    CPI 79
    JZ GAME_OVER
    MOV A, C
    CPI 0
    JZ GAME_OVER
    CPI 29
    JZ GAME_OVER
    
    ; --- 2. Self Collisions ---
    LDA VAR_TAIL_PTR
    MOV D, A            ; D = loop index
COLLISION_LOOP:
    LDA VAR_HEAD_PTR
    CMP D
    JZ COLLISION_DONE   ; Checked all segments
    
    MOV A, D
    CALL GET_SNAKE_X
    CMP B
    JNZ NEXT_COLLISION  ; X doesn't match
    
    MOV A, D
    CALL GET_SNAKE_Y
    CMP C
    JZ GAME_OVER        ; Both X and Y match = Bite self!
    
NEXT_COLLISION:
    INR D
    JMP COLLISION_LOOP
COLLISION_DONE:

    ; --- 3. Advance Head Pointer ---
    LDA VAR_HEAD_PTR
    INR A
    STA VAR_HEAD_PTR
    
    ; Store new X,Y
    MOV E, A
    MVI D, 0
    LXI H, VAR_SNAKE_X
    DAD D
    MOV M, B            ; Store X
    LXI H, VAR_SNAKE_Y
    DAD D
    MOV M, C            ; Store Y
    
    ; Erase OLD Head Graphic ('@' -> 'O')
    LDA VAR_HEAD_PTR
    DCR A
    CALL GET_SNAKE_X
    MOV B, A
    LDA VAR_HEAD_PTR
    DCR A
    CALL GET_SNAKE_Y
    MOV C, A
    CALL CALC_VRAM_ADDR
    MVI M, 'O'
    
    ; Draw NEW Head Graphic ('@')
    LDA VAR_HEAD_PTR
    CALL GET_SNAKE_X
    MOV B, A
    LDA VAR_HEAD_PTR
    CALL GET_SNAKE_Y
    MOV C, A
    CALL CALC_VRAM_ADDR
    MVI M, '@'
    
    ; --- 4. Check Food ---
    LDA VAR_FOOD_X
    CMP B
    JNZ NO_FOOD
    LDA VAR_FOOD_Y
    CMP C
    JNZ NO_FOOD
    
    ; Food Eaten! Spawn new food, DO NOT advance tail (snake grows).
    LDA VAR_SCORE
    INR A
    STA VAR_SCORE
    CALL UPDATE_SCORE
    CALL SPAWN_FOOD
    JMP MAIN_LOOP
    
NO_FOOD:
    ; Erase Tail Graphic
    LDA VAR_TAIL_PTR
    CALL GET_SNAKE_X
    MOV B, A
    LDA VAR_TAIL_PTR
    CALL GET_SNAKE_Y
    MOV C, A
    CALL CALC_VRAM_ADDR
    MVI M, ' '
    
    ; Advance Tail Pointer
    LDA VAR_TAIL_PTR
    INR A
    STA VAR_TAIL_PTR
    
    JMP MAIN_LOOP

; =========================================================================
; 3. GAME OVER & RESTART
; =========================================================================
GAME_OVER:
    LXI D, MSG_GAME_OVER
    MVI B, 35           ; Center X
    MVI C, 14           ; Center Y
    CALL DRAW_STRING
    
    LXI D, MSG_PLAY_AGAIN
    MVI B, 31           ; Center X
    MVI C, 16           ; Center Y
    CALL DRAW_STRING
    
WAIT_RESTART:
    IN KB_STATUS
    ANI 0x01
    JZ WAIT_RESTART
    
    IN KB_DATA          ; Consume key
    MOV B, A
    
    CPI 0xE0            ; Ignore extended prefix
    JZ WAIT_RESTART
    CPI 0xF0            ; Handle Break code
    JZ WAIT_RESTART_BREAK
    
    MOV A, B
    CPI 0x35            ; 'Y' Make Code
    JZ START
    CPI 0x31            ; 'N' Make Code
    JZ EXIT_GAME
    JMP WAIT_RESTART

WAIT_RESTART_BREAK:
    IN KB_STATUS
    ANI 0x01
    JZ WAIT_RESTART_BREAK
    IN KB_DATA          ; Consume break key
    JMP WAIT_RESTART
    
EXIT_GAME:
    MVI A, 2            ; Restore cursor to full block
    STA VID_CSR
    CALL CLEAR_SCREEN
    CALL CLEAR_GFX
    RET

; =========================================================================
; SUBROUTINE: CHECK_INPUT
; Non-blocking PS/2 parser. Validates direction changes to prevent reverse.
; =========================================================================
CHECK_INPUT:
    IN KB_STATUS
    ANI 0x01
    RZ                  ; No key pressed
    
    IN KB_DATA
    MOV E, A            ; Save Scan Code
    
    LDA VAR_KB_SKIP
    ORA A
    JNZ CLEAR_SKIP      ; If flag is set, ignore this byte
    
    MOV A, E
    CPI 0xE0            ; Ignore Extended Prefix
    RZ
    CPI 0xF0            ; Break Code Prefix
    JZ SET_SKIP
    
    ; Parse valid MAKE codes
    CPI 0x75            ; Up
    JZ SET_UP
    CPI 0x72            ; Down
    JZ SET_DOWN
    CPI 0x6B            ; Left
    JZ SET_LEFT
    CPI 0x74            ; Right
    JZ SET_RIGHT
    RET

CLEAR_SKIP:
    XRA A
    STA VAR_KB_SKIP
    RET
SET_SKIP:
    MVI A, 1
    STA VAR_KB_SKIP
    RET

SET_UP:
    LDA VAR_DIR
    CPI 2               ; Prevent reversing into self
    RZ
    MVI A, 0
    STA VAR_DIR_NEXT
    RET
SET_RIGHT:
    LDA VAR_DIR
    CPI 3
    RZ
    MVI A, 1
    STA VAR_DIR_NEXT
    RET
SET_DOWN:
    LDA VAR_DIR
    CPI 0
    RZ
    MVI A, 2
    STA VAR_DIR_NEXT
    RET
SET_LEFT:
    LDA VAR_DIR
    CPI 1
    RZ
    MVI A, 3
    STA VAR_DIR_NEXT
    RET

; =========================================================================
; SUBROUTINES: VIDEO & DRAWING
; =========================================================================
CALC_VRAM_ADDR:
    ; Inputs: B = X, C = Y
    ; Output: HL = 0xA000 + (Y * 80) + X
    MOV L, C
    MVI H, 0
    DAD H               ; Y * 2
    DAD H               ; Y * 4
    DAD H               ; Y * 8
    DAD H               ; Y * 16
    MOV E, L
    MOV D, H            ; DE = Y * 16
    DAD H               ; Y * 32
    DAD H               ; Y * 64
    DAD D               ; Y * 80
    MOV E, B
    MVI D, 0
    DAD D               ; Y * 80 + X
    LXI D, TXT_RAM
    DAD D               ; 0xA000 + Y * 80 + X
    RET

CLEAR_SCREEN:
    LXI H, TXT_RAM
    LXI B, 2400         ; 80 * 30
CS_LOOP:
    MVI M, ' '
    INX H
    DCX B
    MOV A, B
    ORA C
    JNZ CS_LOOP
    RET

CLEAR_GFX:
    LXI H, 0x4000       ; GFX_RAM Base Address
    LXI B, 9600         ; 320x240 resolution / 8 bits = 9600 bytes
CG_LOOP:
    MVI M, 0            ; Write 0 (empty pixels)
    INX H
    DCX B
    MOV A, B
    ORA C
    JNZ CG_LOOP
    RET

DRAW_BORDERS:
    ; Top & Bottom
    MVI B, 0
DB_TB_LOOP:
    MVI C, 0
    CALL CALC_VRAM_ADDR
    MVI M, '#'
    MVI C, 29
    CALL CALC_VRAM_ADDR
    MVI M, '#'
    INR B
    MOV A, B
    CPI 80
    JC DB_TB_LOOP
    
    ; Left & Right
    MVI C, 0
DB_LR_LOOP:
    MVI B, 0
    CALL CALC_VRAM_ADDR
    MVI M, '#'
    MVI B, 79
    CALL CALC_VRAM_ADDR
    MVI M, '#'
    INR C
    MOV A, C
    CPI 30
    JC DB_LR_LOOP
    RET

DRAW_STRING:
    ; Inputs: DE = String Ptr, B = X, C = Y
    PUSH D              ; Save DE before it is clobbered by math!
    CALL CALC_VRAM_ADDR
    POP D               ; Restore DE
DS_LOOP:
    LDAX D
    ORA A
    RZ
    MOV M, A
    INX D
    INX H
    JMP DS_LOOP

UPDATE_SCORE:
    ; Convert VAR_SCORE to 3 ASCII digits
    LDA VAR_SCORE
    MVI B, 0        ; B = Hundreds count
US_HUNDREDS:
    CPI 100
    JC US_TENS_SETUP
    SUI 100
    INR B
    JMP US_HUNDREDS
US_TENS_SETUP:
    MVI C, 0        ; C = Tens count
US_TENS:
    CPI 10
    JC US_ONES
    SUI 10
    INR C
    JMP US_TENS
US_ONES:
    ; A = Ones. Convert all to ASCII and save.
    ADI '0'
    STA MSG_SCORE_VAL + 2
    MOV A, C
    ADI '0'
    STA MSG_SCORE_VAL + 1
    MOV A, B
    ADI '0'
    STA MSG_SCORE_VAL + 0
    
    LXI D, MSG_SCORE
    MVI B, 0        ; X = 0 (Overwrite '#' borders)
    MVI C, 0        ; Y = 0
    CALL DRAW_STRING
    RET

; =========================================================================
; SUBROUTINES: LOGIC & MATH
; =========================================================================
GET_SNAKE_X:
    MOV E, A
    PUSH D
    MVI D, 0
    LXI H, VAR_SNAKE_X
    DAD D
    MOV A, M
    POP D
    RET

GET_SNAKE_Y:
    MOV E, A
    PUSH D
    MVI D, 0
    LXI H, VAR_SNAKE_Y
    DAD D
    MOV A, M
    POP D
    RET

SPAWN_FOOD:
    CALL RANDOM_X
    MOV B, A
    CALL RANDOM_Y
    MOV C, A
    MOV A, B
    STA VAR_FOOD_X
    MOV A, C
    STA VAR_FOOD_Y
    CALL CALC_VRAM_ADDR
    MVI M, '*'
    RET

RANDOM_X:
    CALL LFSR
MOD_78:
    CPI 78
    JC MOD_X_DONE
    SUI 78
    JMP MOD_78
MOD_X_DONE:
    INR A               ; Range 1..78
    RET

RANDOM_Y:
    CALL LFSR
MOD_28:
    CPI 28
    JC MOD_Y_DONE
    SUI 28
    JMP MOD_28
MOD_Y_DONE:
    INR A               ; Range 1..28
    RET

LFSR:
    ; 8-Bit Galois LFSR (Maximal sequence: 255)
    LDA VAR_LFSR
    ORA A               ; Sets Z flag, CLEARS Carry flag
    JNZ LFSR_STEP
    MVI A, 1
LFSR_STEP:
    RAR                 ; Logical right shift (Shifts 0 into MSB)
    JNC LFSR_SAVE
    XRI 0xB8            ; Taps: 8, 6, 5, 4
LFSR_SAVE:
    STA VAR_LFSR
    RET

DELAY:
    LXI B, 0x4000       ; Tweak this loop count for game speed!
DELAY_LOOP:
    CALL LFSR           ; Keep entropy generator spinning
    IN KB_STATUS
    ANI 0x01
    CNZ CHECK_INPUT     ; Check keys during wait for max responsiveness
    DCX B
    MOV A, B
    ORA C
    JNZ DELAY_LOOP
    RET

; =========================================================================
; VARIABLES
; =========================================================================
MSG_GAME_OVER:  DB "GAME OVER!", 0
MSG_PLAY_AGAIN: DB "PLAY AGAIN? (Y/N)", 0
MSG_SCORE:      DB "  SCORE: "
MSG_SCORE_VAL:  DB "000  ", 0

VAR_SCORE:      DS 1

VAR_TAIL_PTR:   DS 1
VAR_HEAD_PTR:   DS 1
VAR_DIR:        DS 1
VAR_DIR_NEXT:   DS 1
VAR_FOOD_X:     DS 1
VAR_FOOD_Y:     DS 1
VAR_KB_SKIP:    DS 1
VAR_LFSR:       DS 1

; 256-Byte Circular Arrays (Perfectly wraps 8-bit index bounds automatically)
VAR_SNAKE_X:    DS 256
VAR_SNAKE_Y:    DS 256
