import tkinter as tk
from tkinter import ttk

from src.debugger import Debugger
from src.code_editor import CodeEditor


CODE_SAMPLES = {
    '': '',
    'add-array-indirect': """
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
""",
    'labeljump': """
  mvi a, 1h
  dcr a
  jz YesZero
  jnz NoZero

YesZero:
  mvi c, 20
  hlt

NoZero:
  mvi c, 50
  hlt
""",
    'capitalize': """
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
""",
    'memcpy': """
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
"""
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("js-8080-sim (Python Edition)")
        self.geometry("1100x800")

        self.cpu_state_vars = {} # Maps reg name to tk.StringVar
        self.cpu_state_entries = {} # Maps reg name to tk.Entry widget
        self.flags_state_vars = {} # Maps flag name to tk.StringVar
        self.flags_entries = {} # Maps flag name to tk.Entry widget
        self.ram_vars = [] # List of tk.StringVar for RAM cells
        self.ram_entries = [] # List of tk.Entry for RAM cells
        self.ram_row_headers = [] # List of tk.StringVar for RAM row headers
        self.last_highlighted_entries = []
        self.animating = False

        self.debugger = Debugger()

        self.create_widgets()
        self.set_status_ready()
        self.update_button_states()

    def create_widgets(self):
        # --- Top Control Frame ---
        control_frame = tk.Frame(self, pady=5, padx=5)
        control_frame.pack(side=tk.TOP, fill=tk.X)

        self.btn_run = tk.Button(control_frame, text="Run", command=self.on_run)
        self.btn_run.pack(side=tk.LEFT, padx=5)
        
        self.btn_animate = tk.Button(control_frame, text="Animate", command=self.on_animate)
        self.btn_animate.pack(side=tk.LEFT, padx=5)
        
        self.btn_stop = tk.Button(control_frame, text="Stop", command=self.on_stop, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=5)
        
        self.btn_step = tk.Button(control_frame, text="Step", command=self.on_step)
        self.btn_step.pack(side=tk.LEFT, padx=5)
        
        self.btn_reset = tk.Button(control_frame, text="Reset", command=self.on_reset)
        self.btn_reset.pack(side=tk.LEFT, padx=5)

        tk.Label(control_frame, text="Code sample:").pack(side=tk.LEFT, padx=(30, 0))
        self.sample_cb = ttk.Combobox(control_frame, values=list(CODE_SAMPLES.keys()), state="readonly")
        self.sample_cb.pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="Set", command=self.on_set_sample).pack(side=tk.LEFT)

        # --- Status Bar ---
        self.status_var = tk.StringVar()
        self.status_label = tk.Label(self, textvariable=self.status_var, fg="black", anchor="w", font=("Arial", 10, "bold"))
        self.status_label.pack(side=tk.TOP, fill=tk.X, padx=10)
        
        ttk.Separator(self, orient=tk.HORIZONTAL).pack(side=tk.TOP, fill=tk.X, pady=5)

        # --- Main Layout (Left: Code, Right: CPU/RAM) ---
        main_frame = tk.Frame(self)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Left Column (Code & Labels)
        left_frame = tk.Frame(main_frame, padx=10)
        left_frame.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left_frame, text="Code", font=("Arial", 10, "bold")).pack(anchor="w")

        labels_frame = tk.Frame(left_frame)
        labels_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(0, 15))
        
        tk.Label(labels_frame, text="Labels", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 0))
        
        columns = ("Label", "Address")
        self.labels_tree = ttk.Treeview(labels_frame, columns=columns, show="headings", height=8)
        self.labels_tree.heading("Label", text="Label")
        self.labels_tree.heading("Address", text="Address")
        self.labels_tree.column("Label", width=150)
        self.labels_tree.column("Address", width=100)
        self.labels_tree.pack(fill=tk.X)

        self.code_editor = CodeEditor(left_frame, self)
        self.code_editor.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Right Column (CPU State, Flags, RAM)
        right_frame = tk.Frame(main_frame, padx=10)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(right_frame, text="CPU State", font=("Arial", 10, "bold")).pack(anchor="w")
        
        # CPU State Table
        cpu_table = tk.Frame(right_frame)
        cpu_table.pack(anchor="w", pady=5)
        
        registers = ['a', 'b', 'c', 'd', 'e', 'h', 'l', 'pc', 'sp', 'halted']
        
        for i, reg in enumerate(registers):
            row, col = divmod(i, 5)
            tk.Label(cpu_table, text=f"{reg}:", bg="#ffffc1", width=6, anchor="e", font=("Courier", 10, "bold"), relief="ridge").grid(row=row, column=col*2, padx=1, pady=1)
            
            var = tk.StringVar(value="")
            self.cpu_state_vars[reg] = var
            entry = tk.Entry(cpu_table, textvariable=var, width=6, font=("Courier", 10))
            self.cpu_state_entries[reg] = entry
            entry.grid(row=row, column=col*2+1, padx=1, pady=1)
            entry.bind("<Return>", lambda e, r=reg: self.on_reg_edit(r))
            entry.bind("<FocusOut>", lambda e, r=reg: self.on_reg_edit(r))

        # Flags Table
        tk.Label(right_frame, text="Flags", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 0))
        flags_table = tk.Frame(right_frame)
        flags_table.pack(anchor="w", pady=5)
        
        flags = ['Sign', 'Zero', 'Parity', 'Carry']
        for i, flag in enumerate(flags):
            tk.Label(flags_table, text=f"{flag}:", bg="#feeeb6", width=8, anchor="e", font=("Courier", 10, "bold"), relief="ridge").grid(row=0, column=i*2, padx=1, pady=1)
            var = tk.StringVar(value="")
            self.flags_state_vars[flag] = var
            entry = tk.Entry(flags_table, textvariable=var, width=4, font=("Courier", 10))
            self.flags_entries[flag] = entry
            entry.grid(row=0, column=i*2+1, padx=1, pady=1)
            entry.bind("<Return>", lambda e, f=flag: self.on_flag_edit(f))
            entry.bind("<FocusOut>", lambda e, f=flag: self.on_flag_edit(f))

        # RAM Config
        ram_config_frame = tk.Frame(right_frame)
        ram_config_frame.pack(anchor="w", pady=(10, 0))
        tk.Label(ram_config_frame, text="RAM", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.ram_show_mode = ttk.Combobox(ram_config_frame, values=["Hex", "ASCII"], state="readonly", width=8)
        self.ram_show_mode.set("Hex")
        self.ram_show_mode.pack(side=tk.LEFT, padx=10)
        self.ram_show_mode.bind("<<ComboboxSelected>>", lambda e: self.update_ui())

        # RAM View Table
        ram_table = tk.Frame(right_frame)
        ram_table.pack(anchor="w", pady=5)
        
        # RAM header row
        tk.Label(ram_table, text="", width=4).grid(row=0, column=0)
        for i in range(16):
            tk.Label(ram_table, text=f"{i:01X}", bg="#cde9fa", width=3, font=("Courier", 9, "bold"), relief="ridge").grid(row=0, column=i+1)
            
        for row in range(16):
            row_hdr_var = tk.StringVar(value=f"{row:03X}")
            self.ram_row_headers.append(row_hdr_var)
            tk.Label(ram_table, textvariable=row_hdr_var, bg="#cde9fa", width=4, font=("Courier", 9, "bold"), relief="ridge").grid(row=row+1, column=0)
            
            for col in range(16):
                var = tk.StringVar(value="00")
                self.ram_vars.append(var)
                entry = tk.Entry(ram_table, textvariable=var, width=3, font=("Courier", 9))
                self.ram_entries.append(entry)
                entry.grid(row=row+1, column=col+1)
                idx = row * 16 + col
                entry.bind("<Return>", lambda e, i=idx: self.on_ram_edit(i))
                entry.bind("<FocusOut>", lambda e, i=idx: self.on_ram_edit(i))

        # RAM Address Input
        ram_start_frame = tk.Frame(right_frame)
        ram_start_frame.pack(anchor="w", pady=5)
        tk.Label(ram_start_frame, text="From address (hex):").pack(side=tk.LEFT)
        self.ram_start_var = tk.StringVar(value="0000")
        ram_start_entry = tk.Entry(ram_start_frame, textvariable=self.ram_start_var, width=6)
        ram_start_entry.pack(side=tk.LEFT, padx=5)
        ram_start_entry.bind("<Return>", lambda e: self.update_ui())
        tk.Button(ram_start_frame, text="Show", command=self.update_ui).pack(side=tk.LEFT)

    def set_status_ready(self):
        self.status_var.set("Ready to run")
        self.status_label.config(fg="black")

    def set_status_fail(self, msg):
        self.status_var.set(f"FAIL: {msg}")
        self.status_label.config(fg="red")

    def set_status_success(self):
        self.status_var.set("SUCCESS")
        self.status_label.config(fg="green")

    def update_button_states(self):
        if self.debugger.running:
            self.btn_run.config(state=tk.DISABLED)
            self.btn_animate.config(state=tk.DISABLED)
            self.btn_step.config(state=tk.DISABLED)
            self.btn_stop.config(state=tk.NORMAL)
        else:
            has_code = bool(self.code_editor.get_text().strip())
            state_val = tk.NORMAL if has_code else tk.DISABLED
            self.btn_run.config(state=state_val)
            self.btn_animate.config(state=state_val)
            self.btn_step.config(state=state_val)
            self.btn_stop.config(state=tk.DISABLED)

    def on_reg_edit(self, reg):
        try:
            val = int(self.cpu_state_vars[reg].get(), 16)
            self.debugger.set_register(reg, val)
        except ValueError:
            pass
        self.update_ui()

    def on_flag_edit(self, flag):
        try:
            val = int(self.flags_state_vars[flag].get())
            if val in (0, 1):
                state = self.debugger.get_state()
                f_val = state.f
                bit = {'Sign': 7, 'Zero': 6, 'Parity': 2, 'Carry': 0}[flag]
                if val: f_val |= (1 << bit)
                else: f_val &= ~(1 << bit)
                self.debugger.set_register('f', f_val)
        except ValueError:
            pass
        self.update_ui()

    def on_ram_edit(self, index):
        try:
            val_str = self.ram_vars[index].get()
            start_addr = int(self.ram_start_var.get(), 16) & 0xFFF0
            if start_addr > 0xFF00: start_addr = 0xFF00
            addr = start_addr + index
            
            if self.ram_show_mode.get() == "ASCII":
                if len(val_str) == 2 and val_str.startswith('.'): val = ord(val_str[1])
                elif len(val_str) == 1: val = ord(val_str)
                else: val = int(val_str, 16)
            else: val = int(val_str, 16)
                
            self.debugger.set_memory(addr, val & 0xFF)
        except ValueError:
            pass
        self.update_ui()

    def compile_code(self, quiet=False):
        try:
            prog = self.code_editor.get_text()
            self.debugger.compile(prog)
            
            # Validate existing breakpoints
            self.code_editor.update_breakpoints()
            
            if not quiet:
                self.set_status_success()
            return True
        except Exception as e:
            if not quiet:
                self.set_status_fail(str(e))
            return False

    def on_set_sample(self):
        sample_name = self.sample_cb.get()
        if sample_name in CODE_SAMPLES:
            code = CODE_SAMPLES[sample_name].lstrip('\n')
            self.code_editor.set_text(code)
            self.debugger.is_dirty = True
            self.on_reset()

    def on_reset(self):
        if self.debugger.running:
            self.on_stop()
        if self.debugger.is_dirty:
            if self.compile_code():
                self.update_ui()
            self.code_editor.highlight_syntax()
        else:
            self.debugger.reset()
            self.set_status_ready()
            self.update_ui()
        self.update_button_states()

    def on_step(self):
        if self.debugger.is_dirty and not self.compile_code():
            return
        self.debugger.step()
        self.update_ui()

    def on_run(self):
        if self.debugger.is_dirty and not self.compile_code():
            return
        if self.debugger.get_state().halted:
            return
            
        self.debugger.run()
        self.update_button_states()
        self.set_status_ready()
        self.status_var.set("Running...")
        
        self.execution_loop()

    def on_animate(self):
        if self.debugger.is_dirty and not self.compile_code():
            return
        if self.debugger.get_state().halted:
            return
            
        self.animating = True
        self.debugger.run()
        self.update_button_states()
        self.set_status_ready()
        self.status_var.set("Animating...")
        
        self.animation_loop()

    def on_stop(self):
        self.debugger.stop()
        self.animating = False
        self.update_button_states()
        self.set_status_success()
        self.update_ui()

    def execution_loop(self):
        if not self.debugger.running:
            return
            
        if not self.debugger.execute_batch(100):
            self.on_stop()
            return

        if self.debugger.running:
            self.after(10, self.execution_loop)

    def animation_loop(self):
        if not self.animating or not self.debugger.running:
            return
            
        if not self.debugger.execute_batch(1):
            self.on_stop()
            return
            
        self.update_ui()
        
        if self.animating and self.debugger.running:
            self.after(500, self.animation_loop)

    def update_ui(self):
        # Clear previous highlights
        for entry in self.last_highlighted_entries:
            entry.config(bg="white")
        self.last_highlighted_entries.clear()

        state = self.debugger.get_state()
        
        self.cpu_state_vars['a'].set(f"{state.a:02X}")
        self.cpu_state_vars['b'].set(f"{state.b:02X}")
        self.cpu_state_vars['c'].set(f"{state.c:02X}")
        self.cpu_state_vars['d'].set(f"{state.d:02X}")
        self.cpu_state_vars['e'].set(f"{state.e:02X}")
        self.cpu_state_vars['h'].set(f"{state.h:02X}")
        self.cpu_state_vars['l'].set(f"{state.l:02X}")
        self.cpu_state_vars['pc'].set(f"{state.pc:04X}")
        self.cpu_state_vars['sp'].set(f"{state.sp:04X}")
        self.cpu_state_vars['halted'].set(str(int(state.halted)))
        
        f_val = state.f
        self.flags_state_vars['Sign'].set(str((f_val >> 7) & 1))
        self.flags_state_vars['Zero'].set(str((f_val >> 6) & 1))
        self.flags_state_vars['Parity'].set(str((f_val >> 2) & 1))
        self.flags_state_vars['Carry'].set(str(f_val & 1))

        self.populate_ram_table()
        
        for item in self.labels_tree.get_children():
            self.labels_tree.delete(item)
        for label, addr in self.debugger.label_to_addr.items():
            self.labels_tree.insert("", tk.END, values=(f"{label}:", f"{addr:04X}"))
            
        self.code_editor.clear_execution_highlight()
        highlight_addr = state.pc - 1 if state.halted else state.pc
        
        if highlight_addr in self.debugger.addr_to_line:
            line_num = self.debugger.addr_to_line[highlight_addr]
            is_modified = self.debugger.memory[highlight_addr] != self.debugger.original_memory[highlight_addr]
            if is_modified:
                self.status_var.set(f"Warning: Executing modified memory at {highlight_addr:04X} which differs from source!")
                self.status_label.config(fg="#d97706") # Orange warning
            self.code_editor.highlight_execution_line(line_num, is_modified)

        # Highlight modified registers and flags
        for reg in self.debugger.last_modified_regs:
            if reg == 'f':
                for flag_entry in self.flags_entries.values():
                    flag_entry.config(bg="#d2f8d2")
                    self.last_highlighted_entries.append(flag_entry)
            elif reg in self.cpu_state_entries:
                entry = self.cpu_state_entries[reg]
                entry.config(bg="#d2f8d2")
                self.last_highlighted_entries.append(entry)

        # Highlight modified memory and current execution cell
        try:
            start_addr = int(self.ram_start_var.get(), 16) & 0xFFF0
            if start_addr > 0xFF00: start_addr = 0xFF00
            end_addr = start_addr + 256
            
            for addr in self.debugger.last_modified_mem:
                if start_addr <= addr < end_addr:
                    index = addr - start_addr
                    entry = self.ram_entries[index]
                    entry.config(bg="#d2f8d2")
                    self.last_highlighted_entries.append(entry)
                    
            if start_addr <= highlight_addr < end_addr:
                index = highlight_addr - start_addr
                entry = self.ram_entries[index]
                entry.config(bg="#b3d7ff") # Match the blue 'current_line' tag color
                self.last_highlighted_entries.append(entry)
        except ValueError:
            pass # Ignore if ram start address is invalid
            
        self.after_idle(self.code_editor.update_gutter)

    def populate_ram_table(self):
        try:
            start_addr = int(self.ram_start_var.get(), 16) & 0xFFF0
            if start_addr > 0xFF00:
                start_addr = 0xFF00
                self.ram_start_var.set(f"{start_addr:04X}")
        except ValueError:
            start_addr = 0
            self.ram_start_var.set("0000")
            
        header_start = start_addr
        for i in range(16):
            self.ram_row_headers[i].set(f"{header_start:04X}"[:3])
            header_start += 16
            
        use_ascii = (self.ram_show_mode.get() == "ASCII")
        
        for i in range(256):
            mem_index = start_addr + i
            val = self.debugger.memory[mem_index]
            
            if use_ascii:
                display_val = f".{chr(val)}" if 33 <= val <= 126 else ".."
            else:
                display_val = f"{val:02X}"
                
            self.ram_vars[i].set(display_val)

if __name__ == "__main__":
    app = App()
    app.mainloop()