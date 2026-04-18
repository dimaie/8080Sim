"""
Code Editor component handling the text area, syntax highlighting, and breakpoints.
"""
import tkinter as tk
from tkinter import ttk

class CodeEditor(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        
        self.gutter_canvas = tk.Canvas(self, width=20, bg="#f0f0f0", highlightthickness=0)
        self.gutter_canvas.pack(side=tk.LEFT, fill=tk.Y)
        self.gutter_canvas.bind("<Button-1>", self.on_gutter_click)
        
        self.code_text = tk.Text(self, width=50, height=25, font=("Courier", 10), undo=True)
        self.code_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.code_text.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.code_text.config(yscrollcommand=self.on_text_scroll)
        
        self.code_text.tag_configure("current_line", background="#b3d7ff")
        self.code_text.tag_configure("value_modified", background="#d2f8d2")
        self.code_text.tag_configure("modified_line", background="#ffeb99")
        self.code_text.tag_configure("breakpoint", background="#ffcccc")
        
        # Syntax Highlighting Tags
        self.code_text.tag_configure("syntax_comment", foreground="#008000") # Green
        self.code_text.tag_configure("syntax_string", foreground="#a31515") # Brown
        self.code_text.tag_configure("syntax_label", foreground="#800080") # Purple
        self.code_text.tag_configure("syntax_instruction", foreground="#0000ff", font=("Courier", 10, "bold")) # Blue Bold
        self.code_text.tag_configure("syntax_register", foreground="#0000a0") # Dark Blue
        self.code_text.tag_configure("syntax_number", foreground="#ff8000") # Orange

        # Ensure execution markers are visible on top of everything
        self.code_text.tag_raise("current_line", "breakpoint")
        self.code_text.tag_raise("modified_line", "breakpoint")
        
        self.code_text.bind("<Double-Button-1>", self.on_toggle_breakpoint)
        self.code_text.bind("<<Modified>>", self.on_text_modified)
        self.code_text.bind("<Configure>", lambda e: self.after_idle(self.update_gutter))

    def get_text(self):
        return self.code_text.get("1.0", tk.END)

    def set_text(self, text):
        self.code_text.delete("1.0", tk.END)
        self.code_text.insert(tk.END, text)

    def clear_execution_highlight(self):
        self.code_text.tag_remove("current_line", "1.0", tk.END)
        self.code_text.tag_remove("modified_line", "1.0", tk.END)

    def highlight_execution_line(self, line_num, is_modified):
        if is_modified:
            self.code_text.tag_add("modified_line", f"{line_num}.0", f"{line_num}.0 lineend")
        else:
            self.code_text.tag_add("current_line", f"{line_num}.0", f"{line_num}.0 lineend")
        self.code_text.see(f"{line_num}.0")

    def update_breakpoints(self):
        self.code_text.tag_remove("breakpoint", "1.0", tk.END)
        for bp in self.app.debugger.breakpoints:
            self.code_text.tag_add("breakpoint", f"{bp}.0", f"{bp}.0 lineend")
        self.after_idle(self.update_gutter)

    def highlight_syntax(self):
        for tag in ["syntax_comment", "syntax_string", "syntax_label", "syntax_instruction", "syntax_register", "syntax_number"]:
            self.code_text.tag_remove(tag, "1.0", tk.END)

        instructions = {'adc', 'add', 'aci', 'adi', 'ana', 'ani', 'call', 'cc', 'cnc', 'cnz', 'cm', 'cp', 'cpe', 'cpo', 'cz', 'cma', 'cmc', 'cmp', 'cpi', 'dad', 'db', 'dw', 'dcr', 'dcx', 'hlt', 'inr', 'inx', 'jc', 'jm', 'jmp', 'jnc', 'jnz', 'jp', 'jpe', 'jpo', 'jz', 'lda', 'ldax', 'lhld', 'lxi', 'mov', 'mvi', 'nop', 'ora', 'ori', 'pchl', 'pop', 'push', 'rc', 'ret', 'rnc', 'rnz', 'rm', 'rp', 'rpe', 'rpo', 'rz', 'ral', 'rar', 'rlc', 'rrc', 'sbb', 'sbi', 'shld', 'sphl', 'sta', 'stax', 'stc', 'sub', 'sui', 'xchg', 'xra', 'xri', 'xthl', 'org'}
        registers = {'a', 'b', 'c', 'd', 'e', 'h', 'l', 'm', 'sp', 'psw', 'bc', 'de', 'hl'}
        line_counters = {}
        
        for tok in self.app.debugger.tokens:
            name = tok['name']
            val = tok['value']
            raw = tok['raw']
            line = tok['pos'].line
            
            tag = None
            if name == 'COMMENT': tag = 'syntax_comment'
            elif name == 'STRING': tag = 'syntax_string'
            elif name == 'LABEL': tag = 'syntax_label'
            elif name == 'NUMBER': tag = 'syntax_number'
            elif name == 'ID':
                lower_val = val.lower()
                if lower_val in instructions: tag = 'syntax_instruction'
                elif lower_val in registers: tag = 'syntax_register'
                    
            if tag:
                if line not in line_counters:
                    line_counters[line] = 0
                
                line_text = self.code_text.get(f"{line}.0", f"{line}.end")
                start_col = line_text.find(raw, line_counters[line])
                if start_col != -1:
                    end_col = start_col + len(raw)
                    self.code_text.tag_add(tag, f"{line}.{start_col}", f"{line}.{end_col}")
                    line_counters[line] = end_col

    def on_text_scroll(self, *args):
        self.scrollbar.set(*args)
        self.update_gutter()

    def update_gutter(self, event=None):
        self.gutter_canvas.delete("all")
        for bp in self.app.debugger.breakpoints:
            info = self.code_text.dlineinfo(f"{bp}.0")
            if info:
                x, y, w, h, base = info
                cy = y + h // 2
                self.gutter_canvas.create_oval(4, cy - 4, 12, cy + 4, fill="#e51400", outline="#a00000")

    def on_text_modified(self, event):
        if self.code_text.edit_modified():
            self.app.debugger.is_dirty = True
            if self.app.debugger.running:
                self.app.on_stop()
            self.clear_execution_highlight()
            
            if self.app.compile_code(quiet=False):
                self.app.update_ui()
                self.app.set_status_ready()
                
            self.highlight_syntax()
            self.after_idle(self.update_gutter)
                
            self.code_text.edit_modified(False)
            self.app.update_button_states()

    def on_toggle_breakpoint(self, event):
        index = self.code_text.index(f"@{event.x},{event.y}")
        line_num = int(index.split('.')[0])
        self.toggle_breakpoint_ui(line_num)
        return "break"

    def on_gutter_click(self, event):
        index = self.code_text.index(f"@0,{event.y}")
        line_num = int(index.split('.')[0])
        self.toggle_breakpoint_ui(line_num)

    def toggle_breakpoint_ui(self, line_num):
        if self.app.debugger.is_dirty:
            self.app.compile_code(quiet=True)
            
        if self.app.debugger.toggle_breakpoint(line_num):
            if line_num in self.app.debugger.breakpoints:
                self.code_text.tag_add("breakpoint", f"{line_num}.0", f"{line_num}.0 lineend")
            else:
                self.code_text.tag_remove("breakpoint", f"{line_num}.0", f"{line_num}.0 lineend")
            self.update_gutter()
        else:
            self.app.set_status_fail("Breakpoints can only be set on executable commands.")