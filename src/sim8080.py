class CPUState(dict):
    """A dictionary that also allows attribute access (state.a, state.pc, etc.)"""
    def __getattr__(self, name):
        if name in self:
            return self[name]
        raise AttributeError(f"No such attribute: {name}")
    
    def __setattr__(self, name, value):
        self[name] = value


class CPU8080:
    _mem_read = None
    _mem_write = None
    _io_read = None
    _io_write = None
    _state = None
    _t = 0
    
    # Mapping integer codes 0-7 to register names. 6 is 'M' (Memory access via HL)
    _reg_names = ['b', 'c', 'd', 'e', 'h', 'l', 'm', 'a']

    @classmethod
    def init(cls, memoryTo, memoryAt, io_read=None, io_write=None):
        cls._mem_write = memoryTo
        cls._mem_read = memoryAt
        cls._io_read = io_read if io_read else lambda port: 0
        cls._io_write = io_write if io_write else lambda port, val: None
        cls._state = CPUState({
            'a': 0, 'b': 0, 'c': 0, 'd': 0, 'e': 0, 'h': 0, 'l': 0,
            'pc': 0, 'sp': 0, 'f': 2, 'halted': False
        })
        cls._t = 0

    @classmethod
    def set(cls, reg_name, value):
        reg_name = reg_name.lower()
        if reg_name in cls._state:
            cls._state[reg_name] = value

    @classmethod
    def status(cls):
        return CPUState(cls._state)

    @classmethod
    def T(cls):
        return cls._t

    @classmethod
    def steps(cls, num_steps):
        for _ in range(num_steps):
            if cls._state['halted']:
                return
            
            pc = cls._state['pc']
            op = cls._mem_read(pc)
            cls._state['pc'] = (pc + 1) & 0xFFFF
            
            # Simplified T-state increment (always +4 for simulation output consistency)
            cls._t += 4
            
            # === Instruction Decode & Execute ===
            if op == 0x00:
                pass # NOP
            elif op == 0x76:
                cls._state['halted'] = True # HLT
            elif (op & 0xC0) == 0x40: # MOV r1, r2
                dst = (op >> 3) & 7
                src = op & 7
                cls._set_reg(dst, cls._get_reg(src))
            elif (op & 0xC0) == 0x80: # ALU A, r
                alu_op = (op >> 3) & 7
                val = cls._get_reg(op & 7)
                cls._do_alu(alu_op, val)
            elif (op & 0xC7) == 0xC6: # ALU A, imm
                alu_op = (op >> 3) & 7
                val = cls._fetch_byte()
                cls._do_alu(alu_op, val)
            elif (op & 0xC7) == 0x06: # MVI r, imm
                dst = (op >> 3) & 7
                val = cls._fetch_byte()
                cls._set_reg(dst, val)
            elif (op & 0xC7) == 0x04: # INR r
                r = (op >> 3) & 7
                val = (cls._get_reg(r) + 1) & 0xFF
                cls._set_reg(r, val)
                cls._set_zsp(val)
            elif (op & 0xC7) == 0x05: # DCR r
                r = (op >> 3) & 7
                val = (cls._get_reg(r) - 1) & 0xFF
                cls._set_reg(r, val)
                cls._set_zsp(val)
            elif (op & 0xCF) == 0x01: # LXI rp, d16
                rp = (op >> 4) & 3
                val = cls._fetch_word()
                cls._set_rp(rp, val)
            elif (op & 0xCF) == 0x03: # INX rp
                rp = (op >> 4) & 3
                val = (cls._get_rp(rp) + 1) & 0xFFFF
                cls._set_rp(rp, val)
            elif (op & 0xCF) == 0x0B: # DCX rp
                rp = (op >> 4) & 3
                val = (cls._get_rp(rp) - 1) & 0xFFFF
                cls._set_rp(rp, val)
            elif (op & 0xCF) == 0x09: # DAD rp
                rp = (op >> 4) & 3
                hl = cls._get_rp(2)
                val = cls._get_rp(rp)
                res = hl + val
                cls._set_rp(2, res & 0xFFFF)
                cls._set_cy(res > 0xFFFF)
            elif op == 0x3A: # LDA
                addr = cls._fetch_word()
                cls._state['a'] = cls._mem_read(addr)
            elif op == 0x32: # STA
                addr = cls._fetch_word()
                cls._mem_write(addr, cls._state['a'])
            elif op == 0x2A: # LHLD
                addr = cls._fetch_word()
                cls._state['l'] = cls._mem_read(addr)
                cls._state['h'] = cls._mem_read((addr + 1) & 0xFFFF)
            elif op == 0x22: # SHLD
                addr = cls._fetch_word()
                cls._mem_write(addr, cls._state['l'])
                cls._mem_write((addr + 1) & 0xFFFF, cls._state['h'])
            elif op == 0x0A: # LDAX B
                addr = cls._get_rp(0)
                cls._state['a'] = cls._mem_read(addr)
            elif op == 0x1A: # LDAX D
                addr = cls._get_rp(1)
                cls._state['a'] = cls._mem_read(addr)
            elif op == 0x02: # STAX B
                addr = cls._get_rp(0)
                cls._mem_write(addr, cls._state['a'])
            elif op == 0x12: # STAX D
                addr = cls._get_rp(1)
                cls._mem_write(addr, cls._state['a'])
            elif (op & 0xCF) == 0xC5: # PUSH rp
                rp = (op >> 4) & 3
                val = cls._get_rp(rp, sp_is_psw=True)
                cls._push(val)
            elif (op & 0xCF) == 0xC1: # POP rp
                rp = (op >> 4) & 3
                val = cls._pop()
                cls._set_rp(rp, val, sp_is_psw=True)
            elif op == 0xC3: # JMP
                addr = cls._fetch_word()
                cls._state['pc'] = addr
            elif (op & 0xC7) == 0xC2: # Jccc
                ccc = (op >> 3) & 7
                addr = cls._fetch_word()
                if cls._check_cond(ccc):
                    cls._state['pc'] = addr
            elif op == 0xCD: # CALL
                addr = cls._fetch_word()
                cls._push(cls._state['pc'])
                cls._state['pc'] = addr
            elif (op & 0xC7) == 0xC4: # Cccc
                ccc = (op >> 3) & 7
                addr = cls._fetch_word()
                if cls._check_cond(ccc):
                    cls._push(cls._state['pc'])
                    cls._state['pc'] = addr
            elif op == 0xC9: # RET
                cls._state['pc'] = cls._pop()
            elif (op & 0xC7) == 0xC0: # Rccc
                ccc = (op >> 3) & 7
                if cls._check_cond(ccc):
                    cls._state['pc'] = cls._pop()
            elif op == 0xEB: # XCHG
                h, l = cls._state['h'], cls._state['l']
                d, e = cls._state['d'], cls._state['e']
                cls._state['h'], cls._state['l'] = d, e
                cls._state['d'], cls._state['e'] = h, l
            elif op == 0xE9: # PCHL
                cls._state['pc'] = (cls._state['h'] << 8) | cls._state['l']
            elif op == 0xF9: # SPHL
                cls._state['sp'] = (cls._state['h'] << 8) | cls._state['l']
            elif op == 0xE3: # XTHL
                sp = cls._state['sp']
                lo = cls._mem_read(sp)
                hi = cls._mem_read((sp + 1) & 0xFFFF)
                cls._mem_write(sp, cls._state['l'])
                cls._mem_write((sp + 1) & 0xFFFF, cls._state['h'])
                cls._state['l'] = lo
                cls._state['h'] = hi
            elif op == 0x2F: # CMA
                cls._state['a'] = (~cls._state['a']) & 0xFF
            elif op == 0x3F: # CMC
                cls._state['f'] ^= 1
            elif op == 0x37: # STC
                cls._state['f'] |= 1
            elif op == 0x07: # RLC
                a = cls._state['a']
                cy = (a >> 7) & 1
                cls._state['a'] = ((a << 1) | cy) & 0xFF
                cls._set_cy(cy)
            elif op == 0x0F: # RRC
                a = cls._state['a']
                cy = a & 1
                cls._state['a'] = ((a >> 1) | (cy << 7)) & 0xFF
                cls._set_cy(cy)
            elif op == 0x17: # RAL
                a = cls._state['a']
                cy = cls._get_cy()
                new_cy = (a >> 7) & 1
                cls._state['a'] = ((a << 1) | cy) & 0xFF
                cls._set_cy(new_cy)
            elif op == 0x1F: # RAR
                a = cls._state['a']
                cy = cls._get_cy()
                new_cy = a & 1
                cls._state['a'] = ((a >> 1) | (cy << 7)) & 0xFF
                cls._set_cy(new_cy)
            elif op == 0xDB: # IN port
                port = cls._fetch_byte()
                cls._state['a'] = cls._io_read(port)
            elif op == 0xD3: # OUT port
                port = cls._fetch_byte()
                cls._io_write(port, cls._state['a'])

    # === Helpers ===
    @classmethod
    def _fetch_byte(cls):
        pc = cls._state['pc']
        val = cls._mem_read(pc)
        cls._state['pc'] = (pc + 1) & 0xFFFF
        return val

    @classmethod
    def _fetch_word(cls):
        return cls._fetch_byte() | (cls._fetch_byte() << 8)

    @classmethod
    def _get_reg(cls, r):
        if r == 6:
            return cls._mem_read((cls._state['h'] << 8) | cls._state['l'])
        return cls._state[cls._reg_names[r]]
        
    @classmethod
    def _set_reg(cls, r, val):
        if r == 6:
            cls._mem_write((cls._state['h'] << 8) | cls._state['l'], val & 0xFF)
        else:
            cls._state[cls._reg_names[r]] = val & 0xFF

    @classmethod
    def _get_rp(cls, rp, sp_is_psw=False):
        if rp == 0: return (cls._state['b'] << 8) | cls._state['c']
        elif rp == 1: return (cls._state['d'] << 8) | cls._state['e']
        elif rp == 2: return (cls._state['h'] << 8) | cls._state['l']
        elif rp == 3: return (cls._state['a'] << 8) | cls._state['f'] if sp_is_psw else cls._state['sp']
            
    @classmethod
    def _set_rp(cls, rp, val, sp_is_psw=False):
        if rp == 0: cls._state['b'], cls._state['c'] = (val >> 8) & 0xFF, val & 0xFF
        elif rp == 1: cls._state['d'], cls._state['e'] = (val >> 8) & 0xFF, val & 0xFF
        elif rp == 2: cls._state['h'], cls._state['l'] = (val >> 8) & 0xFF, val & 0xFF
        elif rp == 3:
            if sp_is_psw:
                cls._state['a'], cls._state['f'] = (val >> 8) & 0xFF, (val & 0xFF) | 2
            else:
                cls._state['sp'] = val & 0xFFFF

    @classmethod
    def _push(cls, val):
        sp = cls._state['sp']
        cls._mem_write((sp - 1) & 0xFFFF, (val >> 8) & 0xFF)
        cls._mem_write((sp - 2) & 0xFFFF, val & 0xFF)
        cls._state['sp'] = (sp - 2) & 0xFFFF

    @classmethod
    def _pop(cls):
        sp = cls._state['sp']
        cls._state['sp'] = (sp + 2) & 0xFFFF
        return cls._mem_read(sp) | (cls._mem_read((sp + 1) & 0xFFFF) << 8)

    @classmethod
    def _do_alu(cls, alu_op, val):
        a = cls._state['a']
        cy = cls._get_cy()
        
        if alu_op == 0: res = a + val # ADD
        elif alu_op == 1: res = a + val + cy # ADC
        elif alu_op == 2: res = a - val # SUB
        elif alu_op == 3: res = a - val - cy # SBB
        elif alu_op == 4: res = a & val # ANA
        elif alu_op == 5: res = a ^ val # XRA
        elif alu_op == 6: res = a | val # ORA
        elif alu_op == 7: res = a - val # CMP
        
        if alu_op not in (7,): cls._state['a'] = res & 0xFF
        cls._set_zsp(res)
        if alu_op in (0, 1): cls._set_cy(res > 0xFF)
        elif alu_op in (2, 3, 7): cls._set_cy(res < 0)
        elif alu_op in (4, 5, 6): cls._set_cy(False)

    @classmethod
    def _set_zsp(cls, val):
        val &= 0xFF
        cls._state['f'] = (cls._state['f'] & ~(0b11000100)) | \
                          ((val >> 7) << 7) | \
                          ((1 if val == 0 else 0) << 6) | \
                          ((1 if bin(val).count('1') % 2 == 0 else 0) << 2)
                          
    @classmethod
    def _get_cy(cls): return cls._state['f'] & 1

    @classmethod
    def _set_cy(cls, cy): cls._state['f'] = (cls._state['f'] & ~1) | (1 if cy else 0)

    @classmethod
    def _check_cond(cls, ccc):
        f = cls._state['f']
        return [not (f & 0x40), bool(f & 0x40), not (f & 0x01), bool(f & 0x01),
                not (f & 0x04), bool(f & 0x04), not (f & 0x80), bool(f & 0x80)][ccc]