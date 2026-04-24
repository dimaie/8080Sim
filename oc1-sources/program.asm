; =========================================================================
; SAP-3 PS/2 Keyboard Test (True I/O Ports)
; Polls PS/2 port 0x01 and prints hex scan codes to the screen from 0x00
; =========================================================================

TXT_RAM   EQU 0A000h
KB_DATA   EQU 00h
KB_STATUS EQU 01h
UART_DATA   EQU 02h
UART_STATUS EQU 03h

    ORG 0000h
    LXI SP, 3FFFh
    
    ; Clear Text RAM
    LXI H, TXT_RAM
    LXI D, 2400
Clear_Txt:
    MVI M, 00h
    INX H
    DCX D
    MOV A, D
    ORA E
    JNZ Clear_Txt
    
    ; Set colors (Bright Green on Black)
    MVI A, 1Ch
    STA 0C001h
    MVI A, 00h
    STA 0C002h
    
    ; Set starting cursor position
    LXI H, TXT_RAM
    
Poll_Loop:
    IN KB_STATUS
    ANI 01h
    JNZ Process_KB
    
    IN UART_STATUS
    ANI 02h         ; Check bit 1 (uart_ready)
    JNZ Process_UART
    
    JMP Poll_Loop
    
Process_KB:
    IN KB_DATA
    MOV B, A
    
    ; High nibble
    RRC \ RRC \ RRC \ RRC
    ANI 0Fh
    CALL HexToChar
    CALL SerialTx
    MOV M, A
    INX H
    
    ; Low nibble
    MOV A, B
    ANI 0Fh
    CALL HexToChar
    CALL SerialTx
    MOV M, A
    INX H
    
    ; Add space separator
    MVI A, 20h
    CALL SerialTx
    MOV M, A
    INX H
    
    JMP Poll_Loop

Process_UART:
    IN UART_DATA
    MOV M, A
    INX H
    JMP Poll_Loop

HexToChar:
    CPI 0Ah
    JC IsDigit
    ADI 07h
IsDigit:
    ADI 30h
    RET

; Waits for the UART to be ready, then transmits character in A
SerialTx:
    PUSH PSW
TxWait:
    IN UART_STATUS
    ANI 01h         ; Check bit 0 (tx_busy)
    JNZ TxWait      ; Loop while UART is busy (1)
    POP PSW
    OUT UART_DATA
    RET