import tkinter as tk
from tkinter import ttk
from tkinter import filedialog

from src.debugger import Debugger
from src.code_editor import CodeEditor
from src.memory_panel import MemoryPanel, StackPanel

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("js-8080-sim (Python Edition)")
        self.geometry("1100x800")

        self.cpu_state_vars = {} # Maps reg name to tk.StringVar
        self.cpu_state_entries = {} # Maps reg name to tk.Entry widget
        self.flags_state_vars = {} # Maps flag name to tk.StringVar
        self.flags_entries = {} # Maps flag name to tk.Entry widget
        self.last_highlighted_entries = []
        self.animating = False
        self.memory_panels = []
        self.current_file = None
        self.stack_panel = None

        self.debugger = Debugger()

        self.create_widgets()
        self.set_status_ready()
        self.update_menu_states()

    def create_widgets(self):
        # --- Menu Bar ---
        menubar = tk.Menu(self)
        
        self.file_menu = tk.Menu(menubar, tearoff=0)
        self.file_menu.add_command(label="Open", command=self.on_open)
        self.file_menu.add_command(label="Save", command=self.on_save)
        self.file_menu.add_command(label="Save As..", command=self.on_save_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.on_exit)
        menubar.add_cascade(label="Files", menu=self.file_menu)
        
        self.debug_menu = tk.Menu(menubar, tearoff=0)
        self.debug_menu.add_command(label="Run", command=self.on_run)
        self.debug_menu.add_command(label="Step", command=self.on_step)
        self.debug_menu.add_command(label="Stop", command=self.on_stop)
        self.debug_menu.add_command(label="Reset", command=self.on_reset)
        self.debug_menu.add_command(label="Animate", command=self.on_animate)
        menubar.add_cascade(label="Debug", menu=self.debug_menu)
        
        self.config(menu=menubar)

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

        # --- STACK PANEL ---
        tk.Frame(right_frame, height=10).pack() # spacer
        tk.Label(right_frame, text="Stack View", font=("Arial", 10, "bold")).pack(anchor="w")
        self.stack_panel = StackPanel(right_frame, self, initial_rows="2")
        self.stack_panel.pack(fill=tk.X, pady=5)

        # --- MEMORY PANELS ---
        tk.Frame(right_frame, height=10).pack() # spacer
        
        mem_hdr_frame = tk.Frame(right_frame)
        mem_hdr_frame.pack(fill=tk.X)
        tk.Label(mem_hdr_frame, text="Memory Panels", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        tk.Button(mem_hdr_frame, text="+ Add Panel", command=self.add_memory_panel).pack(side=tk.RIGHT)
        
        mem_outer = tk.Frame(right_frame)
        mem_outer.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.mem_canvas = tk.Canvas(mem_outer, highlightthickness=0)
        mem_scrollbar = ttk.Scrollbar(mem_outer, orient="vertical", command=self.mem_canvas.yview)
        self.mem_scrollable_frame = tk.Frame(self.mem_canvas)
        
        self.mem_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.mem_canvas.configure(scrollregion=self.mem_canvas.bbox("all"))
        )
        
        self.mem_canvas_window = self.mem_canvas.create_window((0, 0), window=self.mem_scrollable_frame, anchor="nw")
        self.mem_canvas.bind("<Configure>", lambda e: self.mem_canvas.itemconfig(self.mem_canvas_window, width=e.width))
        self.mem_canvas.configure(yscrollcommand=mem_scrollbar.set)
        
        self.mem_canvas.pack(side="left", fill="both", expand=True)
        mem_scrollbar.pack(side="right", fill="y")
        
        self.add_memory_panel()

    def set_status_ready(self):
        self.status_var.set("Ready to run")
        self.status_label.config(fg="black")

    def set_status_fail(self, msg):
        self.status_var.set(f"FAIL: {msg}")
        self.status_label.config(fg="red")

    def set_status_success(self):
        self.status_var.set("SUCCESS")
        self.status_label.config(fg="green")

    def add_memory_panel(self):
        panel = MemoryPanel(self.mem_scrollable_frame, self)
        panel.pack(fill=tk.X, pady=5, padx=2)
        self.memory_panels.append(panel)
        self.update_ui()

    def update_menu_states(self):
        has_code = bool(self.code_editor.get_text().strip())
        state_val = tk.NORMAL if has_code else tk.DISABLED
        
        self.file_menu.entryconfig("Save", state=state_val)
        self.file_menu.entryconfig("Save As..", state=state_val)

        if self.debugger.running:
            self.debug_menu.entryconfig("Run", state=tk.DISABLED)
            self.debug_menu.entryconfig("Animate", state=tk.DISABLED)
            self.debug_menu.entryconfig("Step", state=tk.DISABLED)
            self.debug_menu.entryconfig("Reset", state=tk.DISABLED)
            self.debug_menu.entryconfig("Stop", state=tk.NORMAL)
        else:
            self.debug_menu.entryconfig("Run", state=state_val)
            self.debug_menu.entryconfig("Animate", state=state_val)
            self.debug_menu.entryconfig("Step", state=state_val)
            self.debug_menu.entryconfig("Reset", state=tk.NORMAL)
            self.debug_menu.entryconfig("Stop", state=tk.DISABLED)

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

    def on_open(self):
        file_path = filedialog.askopenfilename(defaultextension=".asm", filetypes=[("Assembly Files", "*.asm"), ("All Files", "*.*")])
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    self.code_editor.set_text(f.read())
                self.current_file = file_path
                self.debugger.is_dirty = True
                self.on_reset()
                self.set_status_success()
                self.status_var.set(f"Loaded {self.current_file}")
            except Exception as e:
                self.set_status_fail(f"Failed to open file: {e}")

    def on_save(self):
        if self.current_file:
            try:
                with open(self.current_file, "w", encoding="utf-8") as f:
                    f.write(self.code_editor.get_text())
                self.set_status_success()
                self.status_var.set(f"Saved to {self.current_file}")
            except Exception as e:
                self.set_status_fail(f"Failed to save file: {e}")
        else:
            self.on_save_as()

    def on_save_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".asm", filetypes=[("Assembly Files", "*.asm"), ("All Files", "*.*")])
        if file_path:
            self.current_file = file_path
            self.on_save()

    def on_exit(self):
        self.destroy()

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
        self.update_menu_states()

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
        self.update_menu_states()
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
        self.update_menu_states()
        self.set_status_ready()
        self.status_var.set("Animating...")
        
        self.animation_loop()

    def on_stop(self):
        self.debugger.stop()
        self.animating = False
        self.update_menu_states()
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

        # Update Stack Panel
        if self.stack_panel:
            self.stack_panel.update_display(self.debugger.memory, highlight_addr, self.debugger.last_modified_mem)
                
        # Update all memory panels
        for panel in self.memory_panels:
            panel.update_display(self.debugger.memory, highlight_addr, self.debugger.last_modified_mem)
            
        self.after_idle(self.code_editor.update_gutter)

if __name__ == "__main__":
    app = App()
    app.mainloop()