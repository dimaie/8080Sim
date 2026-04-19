import tkinter as tk

class RegistersPanel(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self.cpu_state_vars = {}
        self.cpu_state_entries = {}
        self.flags_state_vars = {}
        self.flags_entries = {}
        self.last_highlighted_entries = []
        
        tk.Label(self, text="CPU State", font=("Arial", 10, "bold")).pack(anchor="w")
        
        # CPU State Table
        cpu_table = tk.Frame(self)
        cpu_table.pack(anchor="w", pady=5)
        
        registers = ['a', 'b', 'c', 'd', 'e', 'h', 'l', 'm', 'pc', 'sp', 'hlt']
        
        for i, reg in enumerate(registers):
            row, col = divmod(i, 6)
            tk.Label(cpu_table, text=f"{reg}:", bg="#ffffc1", width=6, anchor="e", font=("Courier", 10, "bold"), relief="ridge").grid(row=row, column=col*2, padx=1, pady=1)
            
            var = tk.StringVar(value="")
            self.cpu_state_vars[reg] = var
            entry = tk.Entry(cpu_table, textvariable=var, width=6, font=("Courier", 10))
            self.cpu_state_entries[reg] = entry
            entry.grid(row=row, column=col*2+1, padx=1, pady=1)
            entry.bind("<Return>", lambda e, r=reg: self.on_reg_edit(r))
            entry.bind("<FocusOut>", lambda e, r=reg: self.on_reg_edit(r))

        # Flags Table
        tk.Label(self, text="Flags", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 0))
        flags_table = tk.Frame(self)
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

    def on_reg_edit(self, reg):
        try:
            val = int(self.cpu_state_vars[reg].get(), 16)
            if reg == 'm':
                state = self.app.debugger.get_state()
                hl = (state.h << 8) | state.l
                self.app.debugger.set_memory(hl, val & 0xFF)
            else:
                target_reg = 'halted' if reg == 'hlt' else reg
                self.app.debugger.set_register(target_reg, val)
        except ValueError:
            pass
        self.app.update_ui()

    def on_flag_edit(self, flag):
        try:
            val = int(self.flags_state_vars[flag].get())
            if val in (0, 1):
                state = self.app.debugger.get_state()
                f_val = state.f
                bit = {'Sign': 7, 'Zero': 6, 'Parity': 2, 'Carry': 0}[flag]
                if val: f_val |= (1 << bit)
                else: f_val &= ~(1 << bit)
                self.app.debugger.set_register('f', f_val)
        except ValueError:
            pass
        self.app.update_ui()

    def update_display(self, state, modified_regs):
        for entry in self.last_highlighted_entries:
            entry.config(bg="white")
        self.last_highlighted_entries.clear()

        self.cpu_state_vars['a'].set(f"{state.a:02X}")
        self.cpu_state_vars['b'].set(f"{state.b:02X}")
        self.cpu_state_vars['c'].set(f"{state.c:02X}")
        self.cpu_state_vars['d'].set(f"{state.d:02X}")
        self.cpu_state_vars['e'].set(f"{state.e:02X}")
        self.cpu_state_vars['h'].set(f"{state.h:02X}")
        self.cpu_state_vars['l'].set(f"{state.l:02X}")
        
        hl = (state.h << 8) | state.l
        m_val = self.app.debugger.memory[hl]
        self.cpu_state_vars['m'].set(f"{m_val:02X}")
        
        self.cpu_state_vars['pc'].set(f"{state.pc:04X}")
        self.cpu_state_vars['sp'].set(f"{state.sp:04X}")
        self.cpu_state_vars['hlt'].set(str(int(state.halted)))
        
        f_val = state.f
        self.flags_state_vars['Sign'].set(str((f_val >> 7) & 1))
        self.flags_state_vars['Zero'].set(str((f_val >> 6) & 1))
        self.flags_state_vars['Parity'].set(str((f_val >> 2) & 1))
        self.flags_state_vars['Carry'].set(str(f_val & 1))

        for reg in modified_regs:
            ui_reg = 'hlt' if reg == 'halted' else reg
            if ui_reg == 'f':
                for flag_entry in self.flags_entries.values():
                    flag_entry.config(bg="#d2f8d2")
                    self.last_highlighted_entries.append(flag_entry)
            elif ui_reg in self.cpu_state_entries:
                entry = self.cpu_state_entries[ui_reg]
                entry.config(bg="#d2f8d2")
                self.last_highlighted_entries.append(entry)

        if hl in self.app.debugger.last_modified_mem:
            entry = self.cpu_state_entries['m']
            entry.config(bg="#d2f8d2")
            self.last_highlighted_entries.append(entry)