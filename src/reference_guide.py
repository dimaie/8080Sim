import tkinter as tk
from tkinter import ttk

I8080_DB = {
    # --- Data Transfer ---
    "MOV": [
        {"params": "r1, r2", "desc": "Move data from source register (r2) to destination register (r1).", "bin": "01dddsss (d=dest, s=src)", "example": "MOV A, B    ; A <- B", "regs": "r1 (A, B, C, D, E, H, L)", "flags": "None"},
        {"params": "r, M", "desc": "Move data from memory (address in HL) to register r.", "bin": "01ddd110", "example": "MOV C, M    ; C <- (HL)", "regs": "r", "flags": "None"},
        {"params": "M, r", "desc": "Move data from register r to memory (address in HL).", "bin": "01110sss", "example": "MOV M, D    ; (HL) <- D", "regs": "M (Memory)", "flags": "None"}
    ],
    "MVI": [
        {"params": "r, data8", "desc": "Move immediate 8-bit data to register r.", "bin": "00ddd110, d8", "example": "MVI A, 5Ah  ; A <- 0x5A", "regs": "r", "flags": "None"},
        {"params": "M, data8", "desc": "Move immediate 8-bit data to memory (address in HL).", "bin": "00110110, d8", "example": "MVI M, FFh  ; (HL) <- 0xFF", "regs": "M (Memory)", "flags": "None"}
    ],
    "LXI": [{"params": "rp, data16", "desc": "Load immediate 16-bit data into register pair rp (BC, DE, HL, SP).", "bin": "00rp0001, d8(low), d8(high)", "example": "LXI H, 1234h ; H <- 12h, L <- 34h", "regs": "rp (Register Pair)", "flags": "None"}],
    "LDA": [{"params": "addr16", "desc": "Load Accumulator direct from memory.", "bin": "00111010, a8, a8", "example": "LDA 2000h", "regs": "A", "flags": "None"}],
    "STA": [{"params": "addr16", "desc": "Store Accumulator direct to memory.", "bin": "00110010, a8, a8", "example": "STA 2000h", "regs": "Memory", "flags": "None"}],
    "LHLD": [{"params": "addr16", "desc": "Load HL direct from memory.", "bin": "00101010, a8, a8", "example": "LHLD 2000h", "regs": "H, L", "flags": "None"}],
    "SHLD": [{"params": "addr16", "desc": "Store HL direct to memory.", "bin": "00100010, a8, a8", "example": "SHLD 2000h", "regs": "Memory", "flags": "None"}],
    "LDAX": [{"params": "rp", "desc": "Load Accumulator indirect (from address in BC or DE).", "bin": "00rp1010", "example": "LDAX B", "regs": "A", "flags": "None"}],
    "STAX": [{"params": "rp", "desc": "Store Accumulator indirect (to address in BC or DE).", "bin": "00rp0010", "example": "STAX D", "regs": "Memory", "flags": "None"}],
    "XCHG": [{"params": "None", "desc": "Exchange HL and DE registers.", "bin": "11101011", "example": "XCHG", "regs": "H, L, D, E", "flags": "None"}],

    # --- Arithmetic ---
    "ADD": [
        {"params": "r", "desc": "Add the contents of register r to the accumulator (A).", "bin": "10000sss", "example": "ADD B       ; A <- A + B", "regs": "A", "flags": "Z, S, P, CY, AC"},
        {"params": "M", "desc": "Add the contents of memory (address in HL) to the accumulator (A).", "bin": "10000110", "example": "ADD M       ; A <- A + (HL)", "regs": "A", "flags": "Z, S, P, CY, AC"}
    ],
    "ADC": [
        {"params": "r", "desc": "Add register r and Carry flag to the accumulator (A).", "bin": "10001sss", "example": "ADC B", "regs": "A", "flags": "Z, S, P, CY, AC"},
        {"params": "M", "desc": "Add memory (HL) and Carry flag to the accumulator (A).", "bin": "10001110", "example": "ADC M", "regs": "A", "flags": "Z, S, P, CY, AC"}
    ],
    "ADI": [{"params": "data8", "desc": "Add immediate 8-bit data to the accumulator (A).", "bin": "11000110, d8", "example": "ADI 05h", "regs": "A", "flags": "Z, S, P, CY, AC"}],
    "ACI": [{"params": "data8", "desc": "Add immediate 8-bit data and Carry flag to the accumulator (A).", "bin": "11001110, d8", "example": "ACI 05h", "regs": "A", "flags": "Z, S, P, CY, AC"}],
    "SUB": [
        {"params": "r", "desc": "Subtract the contents of register r from the accumulator (A).", "bin": "10010sss", "example": "SUB C", "regs": "A", "flags": "Z, S, P, CY, AC"},
        {"params": "M", "desc": "Subtract the contents of memory (address in HL) from the accumulator (A).", "bin": "10010110", "example": "SUB M", "regs": "A", "flags": "Z, S, P, CY, AC"}
    ],
    "SBB": [
        {"params": "r", "desc": "Subtract register r and Borrow (Carry) from the accumulator (A).", "bin": "10011sss", "example": "SBB C", "regs": "A", "flags": "Z, S, P, CY, AC"},
        {"params": "M", "desc": "Subtract memory (HL) and Borrow (Carry) from the accumulator (A).", "bin": "10011110", "example": "SBB M", "regs": "A", "flags": "Z, S, P, CY, AC"}
    ],
    "SUI": [{"params": "data8", "desc": "Subtract immediate 8-bit data from the accumulator (A).", "bin": "11010110, d8", "example": "SUI 05h", "regs": "A", "flags": "Z, S, P, CY, AC"}],
    "SBI": [{"params": "data8", "desc": "Subtract immediate 8-bit data and Borrow (Carry) from the accumulator (A).", "bin": "11011110, d8", "example": "SBI 05h", "regs": "A", "flags": "Z, S, P, CY, AC"}],
    "INR": [
        {"params": "r", "desc": "Increment register r by 1.", "bin": "00ddd100", "example": "INR B", "regs": "r", "flags": "Z, S, P, AC"},
        {"params": "M", "desc": "Increment memory (HL) by 1.", "bin": "00110100", "example": "INR M", "regs": "M (Memory)", "flags": "Z, S, P, AC"}
    ],
    "DCR": [
        {"params": "r", "desc": "Decrement register r by 1.", "bin": "00ddd101", "example": "DCR B", "regs": "r", "flags": "Z, S, P, AC"},
        {"params": "M", "desc": "Decrement memory (HL) by 1.", "bin": "00110101", "example": "DCR M", "regs": "M (Memory)", "flags": "Z, S, P, AC"}
    ],
    "INX": [{"params": "rp", "desc": "Increment register pair by 1.", "bin": "00rp0011", "example": "INX H", "regs": "rp", "flags": "None"}],
    "DCX": [{"params": "rp", "desc": "Decrement register pair by 1.", "bin": "00rp1011", "example": "DCX H", "regs": "rp", "flags": "None"}],
    "DAD": [{"params": "rp", "desc": "Add register pair to HL.", "bin": "00rp1001", "example": "DAD D", "regs": "H, L", "flags": "CY"}],
    "DAA": [{"params": "None", "desc": "Decimal Adjust Accumulator.", "bin": "00100111", "example": "DAA", "regs": "A", "flags": "Z, S, P, CY, AC"}],

    # --- Logical ---
    "ANA": [
        {"params": "r", "desc": "Logical AND register r with Accumulator.", "bin": "10100sss", "example": "ANA B", "regs": "A", "flags": "Z, S, P, CY, AC"},
        {"params": "M", "desc": "Logical AND memory (HL) with Accumulator.", "bin": "10100110", "example": "ANA M", "regs": "A", "flags": "Z, S, P, CY, AC"}
    ],
    "ANI": [{"params": "data8", "desc": "Logical AND immediate data with Accumulator.", "bin": "11100110, d8", "example": "ANI 0Fh", "regs": "A", "flags": "Z, S, P, CY, AC"}],
    "ORA": [
        {"params": "r", "desc": "Logical OR register r with Accumulator.", "bin": "10110sss", "example": "ORA B", "regs": "A", "flags": "Z, S, P, CY, AC"},
        {"params": "M", "desc": "Logical OR memory (HL) with Accumulator.", "bin": "10110110", "example": "ORA M", "regs": "A", "flags": "Z, S, P, CY, AC"}
    ],
    "ORI": [{"params": "data8", "desc": "Logical OR immediate data with Accumulator.", "bin": "11110110, d8", "example": "ORI 0Fh", "regs": "A", "flags": "Z, S, P, CY, AC"}],
    "XRA": [
        {"params": "r", "desc": "Logical XOR register r with Accumulator.", "bin": "10101sss", "example": "XRA B", "regs": "A", "flags": "Z, S, P, CY, AC"},
        {"params": "M", "desc": "Logical XOR memory (HL) with Accumulator.", "bin": "10101110", "example": "XRA M", "regs": "A", "flags": "Z, S, P, CY, AC"}
    ],
    "XRI": [{"params": "data8", "desc": "Logical XOR immediate data with Accumulator.", "bin": "11101110, d8", "example": "XRI 0Fh", "regs": "A", "flags": "Z, S, P, CY, AC"}],
    "CMP": [
        {"params": "r", "desc": "Compare register r with Accumulator.", "bin": "10111sss", "example": "CMP D", "regs": "None (Flags)", "flags": "Z, S, P, CY, AC"},
        {"params": "M", "desc": "Compare memory (HL) with Accumulator.", "bin": "10111110", "example": "CMP M", "regs": "None (Flags)", "flags": "Z, S, P, CY, AC"}
    ],
    "CPI": [{"params": "data8", "desc": "Compare immediate data with Accumulator.", "bin": "11111110, d8", "example": "CPI 05h", "regs": "None (Flags)", "flags": "Z, S, P, CY, AC"}],

    # --- Rotate ---
    "RLC": [{"params": "None", "desc": "Rotate Accumulator Left.", "bin": "00000111", "example": "RLC", "regs": "A", "flags": "CY"}],
    "RRC": [{"params": "None", "desc": "Rotate Accumulator Right.", "bin": "00001111", "example": "RRC", "regs": "A", "flags": "CY"}],
    "RAL": [{"params": "None", "desc": "Rotate Accumulator Left through Carry.", "bin": "00010111", "example": "RAL", "regs": "A", "flags": "CY"}],
    "RAR": [{"params": "None", "desc": "Rotate Accumulator Right through Carry.", "bin": "00011111", "example": "RAR", "regs": "A", "flags": "CY"}],

    # --- Control / Special ---
    "CMA": [{"params": "None", "desc": "Complement Accumulator.", "bin": "00101111", "example": "CMA", "regs": "A", "flags": "None"}],
    "CMC": [{"params": "None", "desc": "Complement Carry flag.", "bin": "00111111", "example": "CMC", "regs": "None", "flags": "CY"}],
    "STC": [{"params": "None", "desc": "Set Carry flag.", "bin": "00110111", "example": "STC", "regs": "None", "flags": "CY"}],
    "HLT": [{"params": "None", "desc": "Halt the processor until an interrupt occurs.", "bin": "01110110", "example": "HLT", "regs": "None", "flags": "None"}],
    "NOP": [{"params": "None", "desc": "No Operation.", "bin": "00000000", "example": "NOP", "regs": "None", "flags": "None"}],
    "EI": [{"params": "None", "desc": "Enable Interrupts.", "bin": "11111011", "example": "EI", "regs": "None", "flags": "None"}],
    "DI": [{"params": "None", "desc": "Disable Interrupts.", "bin": "11110011", "example": "DI", "regs": "None", "flags": "None"}],

    # --- Branch ---
    "JMP": [{"params": "addr16", "desc": "Jump unconditionally to the 16-bit address.", "bin": "11000011, a8, a8", "example": "JMP 0800h", "regs": "PC", "flags": "None"}],
    "JC": [{"params": "addr16", "desc": "Jump if Carry (CY=1).", "bin": "11011010, a8, a8", "example": "JC 0800h", "regs": "PC", "flags": "None"}],
    "JNC": [{"params": "addr16", "desc": "Jump if No Carry (CY=0).", "bin": "11010010, a8, a8", "example": "JNC 0800h", "regs": "PC", "flags": "None"}],
    "JZ": [{"params": "addr16", "desc": "Jump if Zero (Z=1).", "bin": "11001010, a8, a8", "example": "JZ 0800h", "regs": "PC", "flags": "None"}],
    "JNZ": [{"params": "addr16", "desc": "Jump if Not Zero (Z=0).", "bin": "11000010, a8, a8", "example": "JNZ 0800h", "regs": "PC", "flags": "None"}],
    "JP": [{"params": "addr16", "desc": "Jump if Positive/Plus (S=0).", "bin": "11110010, a8, a8", "example": "JP 0800h", "regs": "PC", "flags": "None"}],
    "JM": [{"params": "addr16", "desc": "Jump if Minus/Negative (S=1).", "bin": "11111010, a8, a8", "example": "JM 0800h", "regs": "PC", "flags": "None"}],
    "JPE": [{"params": "addr16", "desc": "Jump if Parity Even (P=1).", "bin": "11101010, a8, a8", "example": "JPE 0800h", "regs": "PC", "flags": "None"}],
    "JPO": [{"params": "addr16", "desc": "Jump if Parity Odd (P=0).", "bin": "11100010, a8, a8", "example": "JPO 0800h", "regs": "PC", "flags": "None"}],
    "PCHL": [{"params": "None", "desc": "Copy HL to Program Counter (PC). Jump to (HL).", "bin": "11101001", "example": "PCHL", "regs": "PC", "flags": "None"}],

    "CALL": [{"params": "addr16", "desc": "Push PC to stack and jump to address.", "bin": "11001101, a8, a8", "example": "CALL 1000h", "regs": "PC, SP, Memory", "flags": "None"}],
    "CC": [{"params": "addr16", "desc": "Call if Carry (CY=1).", "bin": "11011100, a8, a8", "example": "CC 1000h", "regs": "PC, SP, Memory", "flags": "None"}],
    "CNC": [{"params": "addr16", "desc": "Call if No Carry (CY=0).", "bin": "11010100, a8, a8", "example": "CNC 1000h", "regs": "PC, SP, Memory", "flags": "None"}],
    "CZ": [{"params": "addr16", "desc": "Call if Zero (Z=1).", "bin": "11001100, a8, a8", "example": "CZ 1000h", "regs": "PC, SP, Memory", "flags": "None"}],
    "CNZ": [{"params": "addr16", "desc": "Call if Not Zero (Z=0).", "bin": "11000100, a8, a8", "example": "CNZ 1000h", "regs": "PC, SP, Memory", "flags": "None"}],
    "CP": [{"params": "addr16", "desc": "Call if Positive/Plus (S=0).", "bin": "11110100, a8, a8", "example": "CP 1000h", "regs": "PC, SP, Memory", "flags": "None"}],
    "CM": [{"params": "addr16", "desc": "Call if Minus/Negative (S=1).", "bin": "11111100, a8, a8", "example": "CM 1000h", "regs": "PC, SP, Memory", "flags": "None"}],
    "CPE": [{"params": "addr16", "desc": "Call if Parity Even (P=1).", "bin": "11101100, a8, a8", "example": "CPE 1000h", "regs": "PC, SP, Memory", "flags": "None"}],
    "CPO": [{"params": "addr16", "desc": "Call if Parity Odd (P=0).", "bin": "11100100, a8, a8", "example": "CPO 1000h", "regs": "PC, SP, Memory", "flags": "None"}],
    
    "RET": [{"params": "None", "desc": "Pop 16-bit address from stack into PC.", "bin": "11001001", "example": "RET", "regs": "PC, SP", "flags": "None"}],
    "RC": [{"params": "None", "desc": "Return if Carry (CY=1).", "bin": "11011000", "example": "RC", "regs": "PC, SP", "flags": "None"}],
    "RNC": [{"params": "None", "desc": "Return if No Carry (CY=0).", "bin": "11010000", "example": "RNC", "regs": "PC, SP", "flags": "None"}],
    "RZ": [{"params": "None", "desc": "Return if Zero (Z=1).", "bin": "11001000", "example": "RZ", "regs": "PC, SP", "flags": "None"}],
    "RNZ": [{"params": "None", "desc": "Return if Not Zero (Z=0).", "bin": "11000000", "example": "RNZ", "regs": "PC, SP", "flags": "None"}],
    "RP": [{"params": "None", "desc": "Return if Positive/Plus (S=0).", "bin": "11110000", "example": "RP", "regs": "PC, SP", "flags": "None"}],
    "RM": [{"params": "None", "desc": "Return if Minus/Negative (S=1).", "bin": "11111000", "example": "RM", "regs": "PC, SP", "flags": "None"}],
    "RPE": [{"params": "None", "desc": "Return if Parity Even (P=1).", "bin": "11101000", "example": "RPE", "regs": "PC, SP", "flags": "None"}],
    "RPO": [{"params": "None", "desc": "Return if Parity Odd (P=0).", "bin": "11100000", "example": "RPO", "regs": "PC, SP", "flags": "None"}],
    "RST": [{"params": "n", "desc": "Restart. Call to subroutine at address n * 8 (n = 0..7).", "bin": "11nnn111", "example": "RST 1", "regs": "PC, SP, Memory", "flags": "None"}],

    # --- Stack / I-O ---
    "PUSH": [{"params": "rp", "desc": "Push register pair (BC, DE, HL, PSW) onto stack.", "bin": "11rp0101", "example": "PUSH B", "regs": "SP, Memory", "flags": "None"}],
    "POP": [{"params": "rp", "desc": "Pop register pair (BC, DE, HL, PSW) from stack.", "bin": "11rp0001", "example": "POP H", "regs": "rp, SP", "flags": "None (Unless PSW)"}],
    "XTHL": [{"params": "None", "desc": "Exchange top of stack with HL.", "bin": "11100011", "example": "XTHL", "regs": "H, L, Memory", "flags": "None"}],
    "SPHL": [{"params": "None", "desc": "Copy HL to Stack Pointer (SP).", "bin": "11111001", "example": "SPHL", "regs": "SP", "flags": "None"}],
    "IN": [{"params": "port8", "desc": "Input byte from port to Accumulator.", "bin": "11011011, p8", "example": "IN 01h", "regs": "A", "flags": "None"}],
    "OUT": [{"params": "port8", "desc": "Output byte from Accumulator to port.", "bin": "11010011, p8", "example": "OUT 02h", "regs": "None", "flags": "None"}],
}

CMD_TO_COLOR = {
    **{cmd: "#0055cc" for cmd in ["MOV", "MVI", "LXI", "LDA", "STA", "LHLD", "SHLD", "LDAX", "STAX", "XCHG"]},
    **{cmd: "#0f7b0f" for cmd in ["ADD", "ADC", "ADI", "ACI", "SUB", "SBB", "SUI", "SBI", "INR", "DCR", "INX", "DCX", "DAD", "DAA"]},
    **{cmd: "#6b238e" for cmd in ["ANA", "ANI", "ORA", "ORI", "XRA", "XRI", "CMP", "CPI"]},
    **{cmd: "#b05e00" for cmd in ["RLC", "RRC", "RAL", "RAR"]},
    **{cmd: "#555555" for cmd in ["CMA", "CMC", "STC", "HLT", "NOP", "EI", "DI"]},
    **{cmd: "#d62728" for cmd in ["JMP", "JC", "JNC", "JZ", "JNZ", "JP", "JM", "JPE", "JPO", "PCHL", "CALL", "CC", "CNC", "CZ", "CNZ", "CP", "CM", "CPE", "CPO", "RET", "RC", "RNC", "RZ", "RNZ", "RP", "RM", "RPE", "RPO", "RST"]},
    **{cmd: "#008080" for cmd in ["PUSH", "POP", "XTHL", "SPHL", "IN", "OUT"]}
}

class ReferenceGuide(tk.Tk):
    def __init__(self):
        super().__init__()
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
        details_frame = tk.LabelFrame(right_frame, text=" Instruction Details ", padx=10, pady=10, font=("Arial", 10, "bold"))
        details_frame.pack(fill=tk.BOTH, expand=True)
        
        # Description
        tk.Label(details_frame, text="Description:", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="nw", pady=5)
        self.lbl_desc = tk.Label(details_frame, text="", justify="left", wraplength=300)
        self.lbl_desc.grid(row=0, column=1, sticky="nw", pady=5)
        
        # Binary Code
        tk.Label(details_frame, text="Binary Format:", font=("Arial", 9, "bold")).grid(row=1, column=0, sticky="nw", pady=5)
        self.lbl_bin = tk.Label(details_frame, text="", font=("Courier", 10, "bold"), fg="#5c0099")
        self.lbl_bin.grid(row=1, column=1, sticky="nw", pady=5)
        
        # Example
        tk.Label(details_frame, text="Example:", font=("Arial", 9, "bold")).grid(row=2, column=0, sticky="nw", pady=5)
        self.lbl_example = tk.Label(details_frame, text="", font=("Courier", 10), bg="#f0f0f0", padx=5, pady=2, relief="ridge")
        self.lbl_example.grid(row=2, column=1, sticky="nw", pady=5)
        
        # Affected Registers (Highlighted)
        tk.Label(details_frame, text="Registers:", font=("Arial", 9, "bold")).grid(row=3, column=0, sticky="nw", pady=15)
        self.lbl_regs = tk.Label(details_frame, text="", font=("Arial", 10, "bold"), fg="#0055cc")
        self.lbl_regs.grid(row=3, column=1, sticky="nw", pady=15)
        
        # Affected Flags (Highlighted)
        tk.Label(details_frame, text="Flags:", font=("Arial", 9, "bold")).grid(row=4, column=0, sticky="nw", pady=5)
        self.lbl_flags = tk.Label(details_frame, text="", font=("Arial", 10, "bold"), fg="#d62728")
        self.lbl_flags.grid(row=4, column=1, sticky="nw", pady=5)

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
        
        self.lbl_desc.config(text=variant["desc"])
        self.lbl_bin.config(text=variant["bin"])
        self.lbl_example.config(text=variant["example"])
        self.lbl_regs.config(text=variant["regs"])
        self.lbl_flags.config(text=variant["flags"])

if __name__ == "__main__":
    app = ReferenceGuide()
    app.mainloop()