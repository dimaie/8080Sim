import tkinter as tk
from tkinter import ttk

I8080_DB = {
    # --- Data Transfer ---
    "MOV": [
        {"params": "r1, r2", "desc": "Move data from source register (r2) to destination register (r1).", "bin": "01dddsss (d=dest, s=src)", "example": "MOV A, B    ; Copy B to A\nORA A       ; Check if it's zero", "regs": "r1 (A, B, C, D, E, H, L)", "flags": "None"},
        {"params": "r, M", "desc": "Move data from memory (address in HL) to register r.", "bin": "01ddd110", "example": "LXI H, 1000h ; Point to data\nMOV C, M     ; Read byte into C", "regs": "r", "flags": "None"},
        {"params": "M, r", "desc": "Move data from register r to memory (address in HL).", "bin": "01110sss", "example": "LXI H, 1000h ; Point to data\nMOV M, D     ; Write byte from D", "regs": "M (Memory)", "flags": "None"}
    ],
    "MVI": [
        {"params": "r, data8", "desc": "Move immediate 8-bit data to register r.", "bin": "00ddd110, d8", "example": "MVI C, 0Ah  ; Initialize loop counter to 10", "regs": "r", "flags": "None"},
        {"params": "M, data8", "desc": "Move immediate 8-bit data to memory (address in HL).", "bin": "00110110, d8", "example": "LXI H, 2000h ; Point to flag\nMVI M, FFh   ; Set flag to true", "regs": "M (Memory)", "flags": "None"}
    ],
    "LXI": [{"params": "rp, data16", "desc": "Load immediate 16-bit data into register pair rp (BC, DE, HL, SP).", "bin": "00rp0001, d8(low), d8(high)", "example": "LXI H, StrData ; HL points to string\nLXI SP, FFFFh  ; Initialize Stack Pointer", "regs": "rp (Register Pair)", "flags": "None"}],
    "LDA": [{"params": "addr16", "desc": "Load Accumulator direct from memory.", "bin": "00111010, a8, a8", "example": "LDA FlagValue  ; Read global flag\nORA A          ; Test if zero", "regs": "A", "flags": "None"}],
    "STA": [{"params": "addr16", "desc": "Store Accumulator direct to memory.", "bin": "00110010, a8, a8", "example": "MOV A, C       ; Move result to A\nSTA Result     ; Save to memory", "regs": "Memory", "flags": "None"}],
    "LHLD": [{"params": "addr16", "desc": "Load HL direct from memory.", "bin": "00101010, a8, a8", "example": "LHLD Pointer   ; Load 16-bit address into HL\nMOV A, M       ; Dereference it", "regs": "H, L", "flags": "None"}],
    "SHLD": [{"params": "addr16", "desc": "Store HL direct to memory.", "bin": "00100010, a8, a8", "example": "INX H          ; Advance pointer\nSHLD Pointer   ; Save updated 16-bit address", "regs": "Memory", "flags": "None"}],
    "LDAX": [{"params": "rp", "desc": "Load Accumulator indirect (from address in BC or DE).", "bin": "00rp1010", "example": "LXI B, 1000h   ; BC points to source\nLDAX B         ; Load byte into A", "regs": "A", "flags": "None"}],
    "STAX": [{"params": "rp", "desc": "Store Accumulator indirect (to address in BC or DE).", "bin": "00rp0010", "example": "LXI D, 2000h   ; DE points to dest\nSTAX D         ; Store byte from A", "regs": "Memory", "flags": "None"}],
    "XCHG": [{"params": "None", "desc": "Exchange HL and DE registers.", "bin": "11101011", "example": "LHLD SrcPtr    ; HL = source\nLXI D, DestPtr ; DE = dest\nXCHG           ; Now HL=dest, DE=source", "regs": "H, L, D, E", "flags": "None"}],

    # --- Arithmetic ---
    "ADD": [
        {"params": "r", "desc": "Add the contents of register r to the accumulator (A).", "bin": "10000sss", "example": "ADD B       ; Add B to A\nJC Overflow ; Jump if carry occurred", "regs": "A", "flags": "Z, S, P, CY, AC"},
        {"params": "M", "desc": "Add the contents of memory (address in HL) to the accumulator (A).", "bin": "10000110", "example": "ADD M       ; Add array element to A\nINX H       ; Next element", "regs": "A", "flags": "Z, S, P, CY, AC"}
    ],
    "ADC": [
        {"params": "r", "desc": "Add register r and Carry flag to the accumulator (A).", "bin": "10001sss", "example": "ADD C       ; Add low bytes\nMOV A, B    ; Load high byte\nADC D       ; Add high bytes with carry", "regs": "A", "flags": "Z, S, P, CY, AC"},
        {"params": "M", "desc": "Add memory (HL) and Carry flag to the accumulator (A).", "bin": "10001110", "example": "ADC M       ; Multi-byte addition step", "regs": "A", "flags": "Z, S, P, CY, AC"}
    ],
    "ADI": [{"params": "data8", "desc": "Add immediate 8-bit data to the accumulator (A).", "bin": "11000110, d8", "example": "ADI 30h     ; Convert binary 0-9 to ASCII '0'-'9'", "regs": "A", "flags": "Z, S, P, CY, AC"}],
    "ACI": [{"params": "data8", "desc": "Add immediate 8-bit data and Carry flag to the accumulator (A).", "bin": "11001110, d8", "example": "ACI 00h     ; Add carry to high byte in A", "regs": "A", "flags": "Z, S, P, CY, AC"}],
    "SUB": [
        {"params": "r", "desc": "Subtract the contents of register r from the accumulator (A).", "bin": "10010sss", "example": "SUB B       ; A = A - B\nJM Negative ; Jump if result is negative", "regs": "A", "flags": "Z, S, P, CY, AC"},
        {"params": "M", "desc": "Subtract the contents of memory (address in HL) from the accumulator (A).", "bin": "10010110", "example": "SUB M       ; Compare A with memory, set flags", "regs": "A", "flags": "Z, S, P, CY, AC"}
    ],
    "SBB": [
        {"params": "r", "desc": "Subtract register r and Borrow (Carry) from the accumulator (A).", "bin": "10011sss", "example": "SUB C       ; Subtract low bytes\nMOV A, B    ; Load high byte\nSBB D       ; Subtract high bytes with borrow", "regs": "A", "flags": "Z, S, P, CY, AC"},
        {"params": "M", "desc": "Subtract memory (HL) and Borrow (Carry) from the accumulator (A).", "bin": "10011110", "example": "SBB M       ; Multi-byte subtraction step", "regs": "A", "flags": "Z, S, P, CY, AC"}
    ],
    "SUI": [{"params": "data8", "desc": "Subtract immediate 8-bit data from the accumulator (A).", "bin": "11010110, d8", "example": "SUI 30h     ; Convert ASCII '0'-'9' to binary 0-9", "regs": "A", "flags": "Z, S, P, CY, AC"}],
    "SBI": [{"params": "data8", "desc": "Subtract immediate 8-bit data and Borrow (Carry) from the accumulator (A).", "bin": "11011110, d8", "example": "SBI 00h     ; Subtract borrow from high byte in A", "regs": "A", "flags": "Z, S, P, CY, AC"}],
    "INR": [
        {"params": "r", "desc": "Increment register r by 1.", "bin": "00ddd100", "example": "INR C       ; Increment counter\nJNZ Loop    ; Loop until zero (wrap to 0)", "regs": "r", "flags": "Z, S, P, AC"},
        {"params": "M", "desc": "Increment memory (HL) by 1.", "bin": "00110100", "example": "INR M       ; Increment value in memory directly", "regs": "M (Memory)", "flags": "Z, S, P, AC"}
    ],
    "DCR": [
        {"params": "r", "desc": "Decrement register r by 1.", "bin": "00ddd101", "example": "DCR C       ; Decrement counter\nJNZ Loop    ; Loop until zero", "regs": "r", "flags": "Z, S, P, AC"},
        {"params": "M", "desc": "Decrement memory (HL) by 1.", "bin": "00110101", "example": "DCR M       ; Decrement semaphore/lock in memory", "regs": "M (Memory)", "flags": "Z, S, P, AC"}
    ],
    "INX": [{"params": "rp", "desc": "Increment register pair by 1.", "bin": "00rp0011", "example": "INX H       ; Advance pointer to next byte", "regs": "rp", "flags": "None"}],
    "DCX": [{"params": "rp", "desc": "Decrement register pair by 1.", "bin": "00rp1011", "example": "DCX B       ; Decrement 16-bit counter\nMOV A, B\nORA C       ; Check if BC is zero\nJNZ Loop", "regs": "rp", "flags": "None"}],
    "DAD": [{"params": "rp", "desc": "Add register pair to HL.", "bin": "00rp1001", "example": "LXI H, BaseAddr\nLXI D, Offset\nDAD D       ; HL = BaseAddr + Offset", "regs": "H, L", "flags": "CY"}],
    "DAA": [{"params": "None", "desc": "Decimal Adjust Accumulator.", "bin": "00100111", "example": "ADD B       ; Add two BCD numbers\nDAA         ; Adjust result back to BCD", "regs": "A", "flags": "Z, S, P, CY, AC"}],
    "MUL": [{"params": "B", "desc": "Hardware-accelerated 8-bit unsigned multiplication of the Accumulator (A) and register B. The 16-bit product is stored in the HL register pair.", "bin": "11101101", "example": "MVI A, 10\nMVI B, 20\nMUL B       ; HL = 200", "regs": "H, L", "flags": "None"}],

    # --- Logical ---
    "ANA": [
        {"params": "r", "desc": "Logical AND register r with Accumulator.", "bin": "10100sss", "example": "ANA A       ; Test if A is zero or minus (clears Carry)", "regs": "A", "flags": "Z, S, P, CY, AC"},
        {"params": "M", "desc": "Logical AND memory (HL) with Accumulator.", "bin": "10100110", "example": "ANA M       ; Mask A with memory bits", "regs": "A", "flags": "Z, S, P, CY, AC"}
    ],
    "ANI": [{"params": "data8", "desc": "Logical AND immediate data with Accumulator.", "bin": "11100110, d8", "example": "ANI 0Fh     ; Mask out the upper 4 bits\nANI 7Fh     ; Clear MSB (e.g. ASCII conversion)", "regs": "A", "flags": "Z, S, P, CY, AC"}],
    "ORA": [
        {"params": "r", "desc": "Logical OR register r with Accumulator.", "bin": "10110sss", "example": "ORA A       ; Clear Carry flag, set Z/S based on A\nORA B       ; Combine bits", "regs": "A", "flags": "Z, S, P, CY, AC"},
        {"params": "M", "desc": "Logical OR memory (HL) with Accumulator.", "bin": "10110110", "example": "ORA M       ; Combine A with memory bits", "regs": "A", "flags": "Z, S, P, CY, AC"}
    ],
    "ORI": [{"params": "data8", "desc": "Logical OR immediate data with Accumulator.", "bin": "11110110, d8", "example": "ORI 80h     ; Set the Most Significant Bit", "regs": "A", "flags": "Z, S, P, CY, AC"}],
    "XRA": [
        {"params": "r", "desc": "Logical XOR register r with Accumulator.", "bin": "10101sss", "example": "XRA A       ; Quick way to clear Accumulator (A=0) and Carry", "regs": "A", "flags": "Z, S, P, CY, AC"},
        {"params": "M", "desc": "Logical XOR memory (HL) with Accumulator.", "bin": "10101110", "example": "XRA M       ; Toggle bits in A based on memory", "regs": "A", "flags": "Z, S, P, CY, AC"}
    ],
    "XRI": [{"params": "data8", "desc": "Logical XOR immediate data with Accumulator.", "bin": "11101110, d8", "example": "XRI FFh     ; Invert all bits in A (same as CMA)", "regs": "A", "flags": "Z, S, P, CY, AC"}],
    "CMP": [
        {"params": "r", "desc": "Compare register r with Accumulator.", "bin": "10111sss", "example": "CMP B       ; Compare A and B\nJZ Equal    ; Jump if A == B\nJC ALess    ; Jump if A < B", "regs": "None (Flags)", "flags": "Z, S, P, CY, AC"},
        {"params": "M", "desc": "Compare memory (HL) with Accumulator.", "bin": "10111110", "example": "CMP M       ; Compare A with memory value", "regs": "None (Flags)", "flags": "Z, S, P, CY, AC"}
    ],
    "CPI": [{"params": "data8", "desc": "Compare immediate data with Accumulator.", "bin": "11111110, d8", "example": "CPI 'A'     ; Check if char is 'A'\nJZ FoundA", "regs": "None (Flags)", "flags": "Z, S, P, CY, AC"}],

    # --- Rotate ---
    "RLC": [{"params": "None", "desc": "Rotate Accumulator Left.", "bin": "00000111", "example": "RLC         ; Shift MSB to LSB and Carry", "regs": "A", "flags": "CY"}],
    "RRC": [{"params": "None", "desc": "Rotate Accumulator Right.", "bin": "00001111", "example": "RRC         ; Shift LSB to MSB and Carry", "regs": "A", "flags": "CY"}],
    "RAL": [{"params": "None", "desc": "Rotate Accumulator Left through Carry.", "bin": "00010111", "example": "RAL         ; Multiply by 2 (16-bit: ADD L, ADC H -> DAD H)", "regs": "A", "flags": "CY"}],
    "RAR": [{"params": "None", "desc": "Rotate Accumulator Right through Carry.", "bin": "00011111", "example": "RAR         ; Divide by 2 (shift right through Carry)", "regs": "A", "flags": "CY"}],

    # --- Control / Special ---
    "CMA": [{"params": "None", "desc": "Complement Accumulator.", "bin": "00101111", "example": "CMA         ; 1's complement of A\nINR A       ; 2's complement (negation)", "regs": "A", "flags": "None"}],
    "CMC": [{"params": "None", "desc": "Complement Carry flag.", "bin": "00111111", "example": "CMC         ; Invert carry flag", "regs": "None", "flags": "CY"}],
    "STC": [{"params": "None", "desc": "Set Carry flag.", "bin": "00110111", "example": "STC         ; Set carry flag to 1", "regs": "None", "flags": "CY"}],
    "HLT": [{"params": "None", "desc": "Halt the processor until an interrupt occurs.", "bin": "01110110", "example": "HLT         ; Stop execution until interrupt", "regs": "None", "flags": "None"}],
    "NOP": [{"params": "None", "desc": "No Operation.", "bin": "00000000", "example": "NOP         ; Delay 4 clock cycles, or pad code", "regs": "None", "flags": "None"}],
    "EI": [{"params": "None", "desc": "Enable Interrupts.", "bin": "11111011", "example": "EI          ; Enable interrupts after setup", "regs": "None", "flags": "None"}],
    "DI": [{"params": "None", "desc": "Disable Interrupts.", "bin": "11110011", "example": "DI          ; Disable interrupts for critical section", "regs": "None", "flags": "None"}],

    # --- Branch ---
    "JMP": [{"params": "addr16", "desc": "Jump unconditionally to the 16-bit address.", "bin": "11000011, a8, a8", "example": "JMP Main    ; Unconditional branch to Main", "regs": "PC", "flags": "None"}],
    "JC": [{"params": "addr16", "desc": "Jump if Carry (CY=1).", "bin": "11011010, a8, a8", "example": "CPI 10      ; Compare A with 10\nJC LessThan ; Jump if A < 10", "regs": "PC", "flags": "None"}],
    "JNC": [{"params": "addr16", "desc": "Jump if No Carry (CY=0).", "bin": "11010010, a8, a8", "example": "ADD B       ; Add B to A\nJNC NoCarry ; Jump if no overflow", "regs": "PC", "flags": "None"}],
    "JZ": [{"params": "addr16", "desc": "Jump if Zero (Z=1).", "bin": "11001010, a8, a8", "example": "DCR C       ; Decrement counter\nJZ Done     ; Jump when counter hits 0", "regs": "PC", "flags": "None"}],
    "JNZ": [{"params": "addr16", "desc": "Jump if Not Zero (Z=0).", "bin": "11000010, a8, a8", "example": "DCR C       ; Decrement counter\nJNZ Loop    ; Loop until counter is 0", "regs": "PC", "flags": "None"}],
    "JP": [{"params": "addr16", "desc": "Jump if Positive/Plus (S=0).", "bin": "11110010, a8, a8", "example": "DCR C       ; Decrement\nJP Positive ; Jump if result >= 0", "regs": "PC", "flags": "None"}],
    "JM": [{"params": "addr16", "desc": "Jump if Minus/Negative (S=1).", "bin": "11111010, a8, a8", "example": "SUB B       ; Subtract\nJM Negative ; Jump if result < 0", "regs": "PC", "flags": "None"}],
    "JPE": [{"params": "addr16", "desc": "Jump if Parity Even (P=1).", "bin": "11101010, a8, a8", "example": "ANA A       ; Set flags\nJPE EvenBits; Jump if even number of 1s", "regs": "PC", "flags": "None"}],
    "JPO": [{"params": "addr16", "desc": "Jump if Parity Odd (P=0).", "bin": "11100010, a8, a8", "example": "ANA A       ; Set flags\nJPO OddBits ; Jump if odd number of 1s", "regs": "PC", "flags": "None"}],
    "PCHL": [{"params": "None", "desc": "Copy HL to Program Counter (PC). Jump to (HL).", "bin": "11101001", "example": "LXI H, JumpTable\nDAD D       ; Add offset\nMOV A, M    ; (Read table logic)\nPCHL        ; Jump to address in HL", "regs": "PC", "flags": "None"}],

    "CALL": [{"params": "addr16", "desc": "Push PC to stack and jump to address.", "bin": "11001101, a8, a8", "example": "CALL Print  ; Call Print subroutine\n; Execution returns here", "regs": "PC, SP, Memory", "flags": "None"}],
    "CC": [{"params": "addr16", "desc": "Call if Carry (CY=1).", "bin": "11011100, a8, a8", "example": "SUB B       ; Subtract\nCC Borrow   ; Call handler if borrow occurred", "regs": "PC, SP, Memory", "flags": "None"}],
    "CNC": [{"params": "addr16", "desc": "Call if No Carry (CY=0).", "bin": "11010100, a8, a8", "example": "ADD B\nCNC NoOverf ; Call if no overflow", "regs": "PC, SP, Memory", "flags": "None"}],
    "CZ": [{"params": "addr16", "desc": "Call if Zero (Z=1).", "bin": "11001100, a8, a8", "example": "CMP B\nCZ EqualRtn ; Call if A == B", "regs": "PC, SP, Memory", "flags": "None"}],
    "CNZ": [{"params": "addr16", "desc": "Call if Not Zero (Z=0).", "bin": "11000100, a8, a8", "example": "CMP B\nCNZ NotEq   ; Call if A != B", "regs": "PC, SP, Memory", "flags": "None"}],
    "CP": [{"params": "addr16", "desc": "Call if Positive/Plus (S=0).", "bin": "11110100, a8, a8", "example": "DCR C\nCP IsPos    ; Call if positive", "regs": "PC, SP, Memory", "flags": "None"}],
    "CM": [{"params": "addr16", "desc": "Call if Minus/Negative (S=1).", "bin": "11111100, a8, a8", "example": "SUB B\nCM IsNeg    ; Call if negative", "regs": "PC, SP, Memory", "flags": "None"}],
    "CPE": [{"params": "addr16", "desc": "Call if Parity Even (P=1).", "bin": "11101100, a8, a8", "example": "ANA A\nCPE ParEven ; Call if parity even", "regs": "PC, SP, Memory", "flags": "None"}],
    "CPO": [{"params": "addr16", "desc": "Call if Parity Odd (P=0).", "bin": "11100100, a8, a8", "example": "ANA A\nCPO ParOdd  ; Call if parity odd", "regs": "PC, SP, Memory", "flags": "None"}],
    
    "RET": [{"params": "None", "desc": "Pop 16-bit address from stack into PC.", "bin": "11001001", "example": "MySub:\n  ADD B\n  RET       ; Return to caller", "regs": "PC, SP", "flags": "None"}],
    "RC": [{"params": "None", "desc": "Return if Carry (CY=1).", "bin": "11011000", "example": "SUB B\nRC          ; Return if borrow", "regs": "PC, SP", "flags": "None"}],
    "RNC": [{"params": "None", "desc": "Return if No Carry (CY=0).", "bin": "11010000", "example": "ADD B\nRNC         ; Return if no carry", "regs": "PC, SP", "flags": "None"}],
    "RZ": [{"params": "None", "desc": "Return if Zero (Z=1).", "bin": "11001000", "example": "CMP B\nRZ          ; Return early if equal", "regs": "PC, SP", "flags": "None"}],
    "RNZ": [{"params": "None", "desc": "Return if Not Zero (Z=0).", "bin": "11000000", "example": "CMP B\nRNZ         ; Return early if not equal", "regs": "PC, SP", "flags": "None"}],
    "RP": [{"params": "None", "desc": "Return if Positive/Plus (S=0).", "bin": "11110000", "example": "DCR C\nRP          ; Return if positive", "regs": "PC, SP", "flags": "None"}],
    "RM": [{"params": "None", "desc": "Return if Minus/Negative (S=1).", "bin": "11111000", "example": "SUB B\nRM          ; Return if negative", "regs": "PC, SP", "flags": "None"}],
    "RPE": [{"params": "None", "desc": "Return if Parity Even (P=1).", "bin": "11101000", "example": "ANA A\nRPE         ; Return if parity even", "regs": "PC, SP", "flags": "None"}],
    "RPO": [{"params": "None", "desc": "Return if Parity Odd (P=0).", "bin": "11100000", "example": "ANA A\nRPO         ; Return if parity odd", "regs": "PC, SP", "flags": "None"}],
    "RST": [{"params": "n", "desc": "Restart. Call to subroutine at address n * 8 (n = 0..7).", "bin": "11nnn111", "example": "RST 1       ; Call address 0x0008 (often used for interrupts/API)", "regs": "PC, SP, Memory", "flags": "None"}],

    # --- Stack / I-O ---
    "PUSH": [{"params": "rp", "desc": "Push register pair (BC, DE, HL, PSW) onto stack.", "bin": "11rp0101", "example": "PUSH PSW    ; Save Accumulator and Flags\nPUSH B      ; Save BC", "regs": "SP, Memory", "flags": "None"}],
    "POP": [{"params": "rp", "desc": "Pop register pair (BC, DE, HL, PSW) from stack.", "bin": "11rp0001", "example": "POP B       ; Restore BC\nPOP PSW     ; Restore A and Flags", "regs": "rp, SP", "flags": "None (Unless PSW)"}],
    "XTHL": [{"params": "None", "desc": "Exchange top of stack with HL.", "bin": "11100011", "example": "XTHL        ; Swap HL with the two bytes at the top of the stack", "regs": "H, L, Memory", "flags": "None"}],
    "SPHL": [{"params": "None", "desc": "Copy HL to Stack Pointer (SP).", "bin": "11111001", "example": "LXI H, 0F000h\nSPHL        ; Quick way to set Stack Pointer", "regs": "SP", "flags": "None"}],
    "IN": [{"params": "port8", "desc": "Input byte from port to Accumulator.", "bin": "11011011, p8", "example": "WaitReady:\n  IN 01h      ; Read status port\n  ANI 01h     ; Check ready bit\n  JZ WaitReady", "regs": "A", "flags": "None"}],
    "OUT": [{"params": "port8", "desc": "Output byte from Accumulator to port.", "bin": "11010011, p8", "example": "MOV A, C    ; Get data\nOUT 02h     ; Send to data port", "regs": "None", "flags": "None"}],
}

CMD_TO_COLOR = {
    **{cmd: "#0055cc" for cmd in ["MOV", "MVI", "LXI", "LDA", "STA", "LHLD", "SHLD", "LDAX", "STAX", "XCHG"]},
    **{cmd: "#0f7b0f" for cmd in ["ADD", "ADC", "ADI", "ACI", "SUB", "SBB", "SUI", "SBI", "INR", "DCR", "INX", "DCX", "DAD", "DAA", "MUL"]},
    **{cmd: "#6b238e" for cmd in ["ANA", "ANI", "ORA", "ORI", "XRA", "XRI", "CMP", "CPI"]},
    **{cmd: "#b05e00" for cmd in ["RLC", "RRC", "RAL", "RAR"]},
    **{cmd: "#555555" for cmd in ["CMA", "CMC", "STC", "HLT", "NOP", "EI", "DI"]},
    **{cmd: "#d62728" for cmd in ["JMP", "JC", "JNC", "JZ", "JNZ", "JP", "JM", "JPE", "JPO", "PCHL", "CALL", "CC", "CNC", "CZ", "CNZ", "CP", "CM", "CPE", "CPO", "RET", "RC", "RNC", "RZ", "RNZ", "RP", "RM", "RPE", "RPO", "RST"]},
    **{cmd: "#008080" for cmd in ["PUSH", "POP", "XTHL", "SPHL", "IN", "OUT"]}
}

class ReferenceGuide(tk.Toplevel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.title("Intel 8080 Instruction Reference Guide")
        self.geometry("600x500")
        self.minsize(550, 450)
        
        self.create_widgets()
        self.populate_list()

    def create_widgets(self):
        # --- Left Panel: Search & List ---
        left_frame = tk.Frame(self, width=200, padx=10, pady=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Label(left_frame, text="Search Command:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search)
        search_entry = tk.Entry(left_frame, textvariable=self.search_var)
        search_entry.pack(fill=tk.X, pady=(0, 10))
        
        self.cmd_listbox = tk.Listbox(left_frame, exportselection=False, font=("Courier", 10))
        self.cmd_listbox.pack(fill=tk.BOTH, expand=True)
        self.cmd_listbox.bind("<<ListboxSelect>>", self.on_command_select)
        
        # --- Right Panel: Parameters & Details ---
        right_frame = tk.Frame(self, padx=15, pady=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(right_frame, text="Valid Parameters:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.param_combo = ttk.Combobox(right_frame, state="readonly", font=("Courier", 10))
        self.param_combo.pack(fill=tk.X, pady=(0, 20))
        self.param_combo.bind("<<ComboboxSelected>>", self.on_parameter_select)
        
        # Details Container
        details_outer = tk.LabelFrame(right_frame, text=" Instruction Details ", font=("Arial", 10, "bold"))
        details_outer.pack(fill=tk.BOTH, expand=True)
        
        details_canvas = tk.Canvas(details_outer, highlightthickness=0)
        h_scrollbar = ttk.Scrollbar(details_outer, orient="horizontal", command=details_canvas.xview)
        details_canvas.configure(xscrollcommand=h_scrollbar.set)
        
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        details_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        details_frame = tk.Frame(details_canvas, padx=10, pady=10)
        details_canvas.create_window((0, 0), window=details_frame, anchor="nw")
        
        details_frame.bind("<Configure>", lambda e: details_canvas.configure(scrollregion=details_canvas.bbox("all")))
        
        # Title
        self.lbl_title = tk.Label(details_frame, text="", font=("Courier", 12, "bold"))
        self.lbl_title.grid(row=0, column=0, columnspan=2, sticky="nw", pady=(0, 10))

        # Description
        tk.Label(details_frame, text="Description:", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky="nw", pady=5)
        self.lbl_desc = tk.Label(details_frame, text="", justify="left", wraplength=300)
        self.lbl_desc.grid(row=1, column=1, sticky="nw", pady=5)
        
        # Binary Code
        tk.Label(details_frame, text="Binary Format:", font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="nw", pady=5)
        self.lbl_bin = tk.Label(details_frame, text="", font=("Courier", 10, "bold"), fg="#5c0099")
        self.lbl_bin.grid(row=2, column=1, sticky="nw", pady=5)
        
        # Example
        tk.Label(details_frame, text="Example:", font=("Arial", 9, "bold")).grid(row=3, column=0, sticky="nw", pady=5)
        self.lbl_example = tk.Label(details_frame, text="", font=("Courier", 10), bg="#f0f0f0", padx=5, pady=2, relief="ridge", justify="left")
        self.lbl_example.grid(row=3, column=1, sticky="nw", pady=5)
        
        # Affected Registers (Highlighted)
        tk.Label(details_frame, text="Registers:", font=("Arial", 9, "bold")).grid(row=4, column=0, sticky="nw", pady=15)
        self.lbl_regs = tk.Label(details_frame, text="", font=("Arial", 10, "bold"), fg="#0055cc")
        self.lbl_regs.grid(row=4, column=1, sticky="nw", pady=15)
        
        # Affected Flags (Highlighted)
        tk.Label(details_frame, text="Flags:", font=("Arial", 9, "bold")).grid(row=5, column=0, sticky="nw", pady=5)
        self.lbl_flags = tk.Label(details_frame, text="", font=("Arial", 10, "bold"), fg="#d62728")

    def populate_list(self, filter_text=""):
        self.cmd_listbox.delete(0, tk.END)
        for cmd in sorted(I8080_DB.keys()):
            if filter_text.upper() in cmd:
                self.cmd_listbox.insert(tk.END, cmd)
                color = CMD_TO_COLOR.get(cmd)
                idx = self.cmd_listbox.size() - 1
                if color:
                    self.cmd_listbox.itemconfig(idx, {'bg': color, 'fg': 'white'})

    def on_search(self, *args):
        self.populate_list(self.search_var.get())
        self.param_combo.set('')
        self.param_combo['values'] = []

    def on_command_select(self, event):
        selection = self.cmd_listbox.curselection()
        if not selection:
            return
            
        cmd = self.cmd_listbox.get(selection[0])
        variants = I8080_DB[cmd]
        
        self.param_combo['values'] = [v["params"] for v in variants]
        if variants:
            self.param_combo.current(0)
            self.on_parameter_select(None)

    def on_parameter_select(self, event):
        cmd = self.cmd_listbox.get(self.cmd_listbox.curselection()[0])
        variant = I8080_DB[cmd][self.param_combo.current()]
        
        params = variant["params"]
        title_text = f"{cmd} {params}" if params != "None" else cmd
        self.lbl_title.config(text=title_text)

        self.lbl_desc.config(text=variant["desc"])
        self.lbl_bin.config(text=variant["bin"])
        self.lbl_example.config(text=variant["example"])
        self.lbl_regs.config(text=variant["regs"])
        self.lbl_flags.config(text=variant["flags"])

    def show_instruction(self, instr, args_str=""):
        instr = instr.upper()
        if instr not in I8080_DB:
            return
            
        variants = I8080_DB[instr]
        best_idx = 0
        for i, variant in enumerate(variants):
            if self._match_args(variant["params"], args_str):
                best_idx = i
                break
                
        current_selection = self.cmd_listbox.curselection()
        items = self.cmd_listbox.get(0, tk.END)
        
        if current_selection and items[current_selection[0]] == instr and self.param_combo.current() == best_idx and not self.search_var.get():
            return
            
        if self.search_var.get():
            self.search_var.set("")
            items = self.cmd_listbox.get(0, tk.END)
            
        if instr in items:
            idx = items.index(instr)
            self.cmd_listbox.selection_clear(0, tk.END)
            self.cmd_listbox.selection_set(idx)
            self.cmd_listbox.see(idx)
            self.on_command_select(None)
            
            if variants:
                self.param_combo.current(best_idx)
                self.on_parameter_select(None)

    def _match_args(self, variant_params, user_args):
        v_parts = [p.strip() for p in variant_params.split(',')] if variant_params != "None" else []
        u_parts = [p.strip() for p in user_args.split(',')] if user_args else []
        
        if len(v_parts) != len(u_parts):
            return False
            
        for v, u in zip(v_parts, u_parts):
            u_upper = u.upper()
            if v in ("r", "r1", "r2"):
                if u_upper not in ("A", "B", "C", "D", "E", "H", "L"): return False
            elif v == "M":
                if u_upper != "M": return False
            elif v == "rp":
                if u_upper not in ("B", "D", "H", "SP", "PSW", "BC", "DE", "HL"): return False
            elif v == "B":
                if u_upper != "B": return False
        return True

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = ReferenceGuide(root)
    root.mainloop()