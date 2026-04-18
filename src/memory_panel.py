import tkinter as tk
from tkinter import ttk

class MemoryPanel(tk.Frame):
    def __init__(self, parent, app, initial_start="0000", initial_rows="16", closable=True):
        super().__init__(parent, relief=tk.RIDGE, borderwidth=2)
        self.app = app
        self.ram_vars = []
        self.ram_entries = []
        self.ram_row_headers = []
        self.last_highlighted_entries = []
        
        ctrl = tk.Frame(self)
        ctrl.pack(fill=tk.X, padx=5, pady=2)
        
        tk.Label(ctrl, text="Addr(Hex):").pack(side=tk.LEFT)
        self.start_var = tk.StringVar(value=initial_start)
        entry_start = tk.Entry(ctrl, textvariable=self.start_var, width=6)
        entry_start.pack(side=tk.LEFT, padx=2)
        entry_start.bind("<Return>", lambda e: self.app.update_ui())
        
        tk.Label(ctrl, text="Rows:").pack(side=tk.LEFT)
        self.rows_var = tk.StringVar(value=str(initial_rows))
        entry_rows = tk.Entry(ctrl, textvariable=self.rows_var, width=4)
        entry_rows.pack(side=tk.LEFT, padx=2)
        entry_rows.bind("<Return>", lambda e: self.rebuild_grid())
        
        self.format_var = ttk.Combobox(ctrl, values=["Hex", "Binary", "Oct", "Char"], state="readonly", width=8)
        self.format_var.set("Hex")
        self.format_var.pack(side=tk.LEFT, padx=5)
        self.format_var.bind("<<ComboboxSelected>>", lambda e: self.app.update_ui())
        
        tk.Button(ctrl, text="Apply", command=self.rebuild_grid).pack(side=tk.LEFT, padx=2)
        if closable:
            tk.Button(ctrl, text="X", fg="red", command=self.destroy_panel).pack(side=tk.RIGHT, padx=2)
        
        self.grid_frame = tk.Frame(self)
        self.grid_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=2)
        
        self.rebuild_grid()

    def destroy_panel(self):
        if self in self.app.memory_panels:
            self.app.memory_panels.remove(self)
        self.destroy()
        self.app.update_ui()

    def rebuild_grid(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()
        
        self.ram_vars = []
        self.ram_entries = []
        self.ram_row_headers = []
        self.last_highlighted_entries = []
        
        try:
            rows = int(self.rows_var.get())
            rows = max(1, min(rows, 256))
        except ValueError:
            rows = 16
            self.rows_var.set("16")
            
        tk.Label(self.grid_frame, text="", width=4).grid(row=0, column=0)
        for i in range(16):
            tk.Label(self.grid_frame, text=f"{i:01X}", bg="#cde9fa", width=3, font=("Courier", 9, "bold"), relief="ridge").grid(row=0, column=i+1)
            
        for r in range(rows):
            row_hdr = tk.StringVar(value="")
            self.ram_row_headers.append(row_hdr)
            tk.Label(self.grid_frame, textvariable=row_hdr, bg="#cde9fa", width=4, font=("Courier", 9, "bold"), relief="ridge").grid(row=r+1, column=0)
            
            for c in range(16):
                var = tk.StringVar(value="00")
                self.ram_vars.append(var)
                entry = tk.Entry(self.grid_frame, textvariable=var, width=3, font=("Courier", 9))
                self.ram_entries.append(entry)
                entry.grid(row=r+1, column=c+1)
                
                idx = r * 16 + c
                entry.bind("<Return>", lambda e, i=idx: self.on_edit(i))
                entry.bind("<FocusOut>", lambda e, i=idx: self.on_edit(i))
        
        self.app.update_ui()

    def on_edit(self, index):
        try:
            val_str = self.ram_vars[index].get()
            start_addr = int(self.start_var.get(), 16) & 0xFFF0
            addr = start_addr + index
            
            fmt = self.format_var.get()
            if fmt == "Char": val = ord(val_str[0]) if len(val_str) > 0 else 0
            elif fmt == "Binary": val = int(val_str, 2)
            elif fmt == "Oct": val = int(val_str, 8)
            else: val = int(val_str, 16)
                
            self.app.debugger.set_memory(addr, val & 0xFF)
        except ValueError:
            pass
        self.app.update_ui()

    def update_display(self, memory, pc, modified_mem):
        for entry in self.last_highlighted_entries:
            entry.config(bg="white")
        self.last_highlighted_entries.clear()

        try:
            start_addr = int(self.start_var.get(), 16) & 0xFFF0
            if start_addr > 0xFFFF: start_addr = 0xFFF0
        except ValueError:
            start_addr = 0
            self.start_var.set("0000")

        rows = len(self.ram_row_headers)
        for r in range(rows):
            self.ram_row_headers[r].set(f"{(start_addr + r*16):04X}"[:3])

        fmt = self.format_var.get()
        entry_width = 8 if fmt == "Binary" else 3 if fmt == "Oct" else 2 if fmt == "Hex" else 2
        
        for i in range(rows * 16):
            addr = start_addr + i
            entry = self.ram_entries[i]
            
            if addr > 0xFFFF:
                self.ram_vars[i].set("")
                entry.config(state=tk.DISABLED, width=entry_width)
                continue
            else:
                entry.config(state=tk.NORMAL, width=entry_width)

            val = memory[addr]
            if fmt == "Char": display = chr(val) if 32 <= val <= 126 else "."
            elif fmt == "Binary": display = f"{val:08b}"
            elif fmt == "Oct": display = f"{val:03o}"
            else: display = f"{val:02X}"
            
            self.ram_vars[i].set(display)

            if addr == pc:
                entry.config(bg="#b3d7ff")
                self.last_highlighted_entries.append(entry)
            elif addr in modified_mem:
                entry.config(bg="#d2f8d2")
                self.last_highlighted_entries.append(entry)

class StackPanel(MemoryPanel):
    def __init__(self, parent, app, initial_rows="2"):
        super().__init__(parent, app, initial_start="0000", initial_rows=initial_rows, closable=False)
        ctrl = self.winfo_children()[0]
        for widget in ctrl.winfo_children():
            if isinstance(widget, tk.Label) and widget.cget("text") == "Addr(Hex):":
                widget.config(text="Track SP:")
        
    def update_display(self, memory, pc, modified_mem):
        state = self.app.debugger.get_state()
        sp = state.sp
        
        sp_aligned = sp & 0xFFF0
        start_view = max(0, sp_aligned - 16) # Show one row above current SP
        self.start_var.set(f"{start_view:04X}")
        
        super().update_display(memory, pc, modified_mem)
        
        rows = len(self.ram_row_headers)
        for i in range(rows * 16):
            if start_view + i == sp:
                entry = self.ram_entries[i]
                entry.config(bg="#ffccdc") # Stack pointer pink color
                if entry not in self.last_highlighted_entries:
                    self.last_highlighted_entries.append(entry)