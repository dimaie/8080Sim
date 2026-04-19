from parser import Parser
from assembler import Assembler
from sim8080 import CPU8080

def main():
    # A small 8080 assembly program
    code = """
        mvi a, 10
        add a
        hlt
    """
    
    p = Parser()
    asm = Assembler()
    
    lines = p.parse(code)
    mem, labels = asm.assemble(lines)
    
    print("Assembly successful!")
    print("Memory (first 5 bytes):", [hex(b) for b in mem[:5]])

    # -----------------------------------------------
    # Connect the memory layout and execute the code!
    # -----------------------------------------------
    def mem_write(addr, value): mem[addr] = value
    def mem_read(addr): return mem[addr]
        
    CPU8080.init(mem_write, mem_read)
    CPU8080.set('pc', 0)
    
    CPU8080.steps(10)  # We will execute at most 10 cycles, until halted
    print("\nFinal CPU Status:\n", CPU8080.status())

if __name__ == "__main__":
    main()