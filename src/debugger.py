from parser import Parser
from assembler import Assembler
from sim8080 import CPU8080


class Debugger:
    def __init__(self):
        self.memory = [0] * 65536
        self.original_memory = [0] * 65536
        self.breakpoints = set()
        self.addr_to_line = {}
        self.line_to_addr = {}
        self.label_to_addr = {}
        self.is_dirty = True
        self.running = False
        self.just_resumed = False
        self.last_modified_regs = set()
        self.last_modified_mem = set()
        self.tokens = []
        self.start_addr = 0
        self.last_compiled_chunks = []
        self.reset()

    def toggle_breakpoint(self, line_num):
        if line_num in self.line_to_addr:
            if line_num in self.breakpoints:
                self.breakpoints.remove(line_num)
            else:
                self.breakpoints.add(line_num)
            return True
        return False

    def compile(self, prog_text):
        p = Parser()
        asm = Assembler()
        try:
            source_lines = p.parse(prog_text)
            mem, label_to_addr = asm.assemble(source_lines)
            
            self.addr_to_line = asm.addrToLine
            self.line_to_addr = {line: addr for addr, line in self.addr_to_line.items()}
            self.label_to_addr = label_to_addr
            
            for chunk in self.last_compiled_chunks:
                for i in range(chunk['length']):
                    self.original_memory[chunk['addr'] + i] = 0
                    
            for chunk in asm.assembled_chunks:
                for i in range(chunk['length']):
                    self.original_memory[chunk['addr'] + i] = mem[chunk['addr'] + i]
                    
            self.last_compiled_chunks = asm.assembled_chunks
            
            if asm.assembled_chunks:
                self.start_addr = asm.assembled_chunks[0]['addr']
            else:
                self.start_addr = 0
                
            self.reset()
            self.is_dirty = False
            
            # Validate existing breakpoints
            self.breakpoints = {bp for bp in self.breakpoints if bp in self.line_to_addr}
        finally:
            self.tokens = p.tokens

    def reset(self):
        self.memory = list(self.original_memory)
        self.running = False
        self.just_resumed = False
        self.last_modified_regs.clear()
        self.last_modified_mem.clear()
        
        def mem_write_tracker(addr, value):
            if self.memory[addr] != value:
                self.memory[addr] = value
                self.last_modified_mem.add(addr)
        def mem_read(addr): return self.memory[addr]
            
        CPU8080.init(mem_write_tracker, mem_read)
        CPU8080.set('pc', self.start_addr)

    def set_register(self, reg, val):
        CPU8080.set(reg, val)

    def set_memory(self, addr, val):
        self.memory[addr] = val

    def step(self, track_registers=True):
        if CPU8080.status().halted:
            return False

        if track_registers:
            self.last_modified_mem.clear()
            self.last_modified_regs.clear()
            before_state = self.get_state().copy()

        CPU8080.steps(1)

        if track_registers:
            after_state = self.get_state()
            for reg in ['a', 'b', 'c', 'd', 'e', 'h', 'l', 'pc', 'sp', 'f', 'halted']:
                if before_state.get(reg) != after_state.get(reg):
                    self.last_modified_regs.add(reg)

        return True

    def run(self):
        self.running = True
        self.just_resumed = True

    def stop(self):
        self.running = False

    def execute_batch(self, batch_size=100):
        if not self.running:
            return False
            
        self.last_modified_mem.clear()
        self.last_modified_regs.clear()
            
        for _ in range(batch_size):
            state = CPU8080.status()
            if state.halted:
                self.stop()
                return False
                
            pc = state.pc
            if not self.just_resumed and pc in self.addr_to_line:
                is_breakpoint = self.addr_to_line[pc] in self.breakpoints
                is_modified = self.memory[pc] != self.original_memory[pc]
                if is_breakpoint or is_modified:
                    self.stop()
                    return False
            self.just_resumed = False
            self.step(track_registers=False)
            
        return self.running

    def get_state(self):
        return CPU8080.status()