import re

MEMORY_SIZE = 64 * 1024


class AssemblyError(Exception):
    def __init__(self, message, pos):
        super().__init__(message)
        self.pos = pos

    def __str__(self):
        return f"Assembly error at {self.pos}: {self.args[0]}"


class Assembler:
    def __init__(self):
        self.memory = [0] * MEMORY_SIZE
        self.labelToAddr = {}
        self.labelToFixups = {}
        self.addrToLine = {}
        self.tracing = False

    def assemble(self, sourceLines):
        self._assembleInstructions(sourceLines)
        self._applyFixups()
        return self.memory, self.labelToAddr
        
    def setTracing(self, tracing):
        self.tracing = tracing
        
    def _assembleInstructions(self, sourceLines):
        curAddr = 0
        for sl in sourceLines:
            if sl['instr'] is not None and sl['instr'].lower() == 'org':
                self._expectArgsCount(sl, 1)
                curAddr = self._argImm(sl, sl['args'][0])

            if sl['label'] is not None:
                if sl['label'] in self.labelToAddr:
                    self._assemblyError(sl['pos'], f"duplicate label \"{sl['label']}\"")
                
                if self.tracing:
                    print(f"Setting label {sl['label']}=0x{curAddr:x}")
                
                self.labelToAddr[sl['label']] = curAddr

            if sl['instr'] is not None and sl['instr'].lower() != 'org':
                if sl['instr'].lower() not in ('db', 'dw'):
                    self.addrToLine[curAddr] = sl['pos'].line
                encoded = self._encodeInstruction(sl, curAddr)
                if self.tracing:
                    print(f"0x{curAddr:x} => {[hex(e) for e in encoded]}")
                
                for val in encoded:
                    self.memory[curAddr] = val
                    curAddr += 1

    def _applyFixups(self):
        for label, fixups in self.labelToFixups.items():
            addr = self.labelToAddr.get(label)
            if addr is None:
                user = fixups[0]
                self._assemblyError(user['pos'], f"label '{label}' used but not defined")
            
            addrLowByte = addr & 0xff
            addrHighByte = (addr >> 8) & 0xff
            
            for user in fixups:
                self.memory[user['addr'] + 1] = addrLowByte
                self.memory[user['addr'] + 2] = addrHighByte
                
                if self.tracing:
                    vals = [hex(v) for v in self.memory[user['addr'] : user['addr'] + 3]]
                    print(f"applied fixup at 0x{user['addr']:x}: {vals}")

    def _encodeInstruction(self, sl, curAddr):
        if self.tracing:
            print(f"assembling {sl}")
            
        instrName = sl['instr'].lower()
        
        if instrName == 'adc':
            self._expectArgsCount(sl, 1)
            r = self._argR(sl, sl['args'][0])
            return [0b10001000 | r]
        elif instrName == 'add':
            self._expectArgsCount(sl, 1)
            r = self._argR(sl, sl['args'][0])
            return [0b10000000 | r]
        elif instrName == 'aci':
            self._expectArgsCount(sl, 1)
            imm = self._argImm(sl, sl['args'][0])
            return [0b11001110, imm]
        elif instrName == 'adi':
            self._expectArgsCount(sl, 1)
            imm = self._argImm(sl, sl['args'][0])
            return [0b11000110, imm]
        elif instrName == 'ana':
            self._expectArgsCount(sl, 1)
            r = self._argR(sl, sl['args'][0])
            return [0b10100000 | r]
        elif instrName == 'ani':
            self._expectArgsCount(sl, 1)
            imm = self._argImm(sl, sl['args'][0])
            return [0b11100110, imm]
        elif instrName in ('call', 'cc', 'cnc', 'cnz', 'cm', 'cp', 'cpe', 'cpo', 'cz'):
            self._expectArgsCount(sl, 1)
            self._argLabel(sl, sl['args'][0], curAddr)
            if instrName == 'call':
                ie = 0b11001101
            else:
                ccc = instrName[1:]
                ie = 0b11000100 | (self._translateCCC(ccc, sl) << 3)
            return [ie, 0, 0]
        elif instrName == 'cma':
            self._expectArgsCount(sl, 0)
            return [0b00101111]
        elif instrName == 'cmc':
            self._expectArgsCount(sl, 0)
            return [0b00111111]
        elif instrName == 'cmp':
            self._expectArgsCount(sl, 1)
            r = self._argR(sl, sl['args'][0])
            return [0b10111000 | r]
        elif instrName == 'cpi':
            self._expectArgsCount(sl, 1)
            imm = self._argImm(sl, sl['args'][0])
            return [0b11111110, imm]
        elif instrName == 'dad':
            self._expectArgsCount(sl, 1)
            rp = self._argRP(sl, sl['args'][0])
            return [0b00001001 | (rp << 4)]
        elif instrName == 'db':
            if len(sl['args']) == 1 and isinstance(sl['args'][0], list):
                return [ord(c) for c in sl['args'][0]]
            else:
                return [self._argImm(sl, arg) for arg in sl['args']]
        elif instrName == 'dw':
            enc = []
            for arg in sl['args']:
                argEnc = self._argImm(sl, arg)
                enc.append(argEnc & 0xFF)
                enc.append((argEnc >> 8) & 0xFF)
            return enc
        elif instrName == 'dcr':
            self._expectArgsCount(sl, 1)
            r = self._argR(sl, sl['args'][0])
            return [0b00000101 | (r << 3)]
        elif instrName == 'dcx':
            self._expectArgsCount(sl, 1)
            rp = self._argRP(sl, sl['args'][0])
            return [0b00001011 | (rp << 4)]
        elif instrName == 'hlt':
            self._expectArgsCount(sl, 0)
            return [0b01110110]
        elif instrName == 'inr':
            self._expectArgsCount(sl, 1)
            r = self._argR(sl, sl['args'][0])
            return [0b00000100 | (r << 3)]
        elif instrName == 'inx':
            self._expectArgsCount(sl, 1)
            rp = self._argRP(sl, sl['args'][0])
            return [0b00000011 | (rp << 4)]
        elif instrName in ('jc', 'jm', 'jmp', 'jnc', 'jnz', 'jp', 'jpe', 'jpo', 'jz'):
            self._expectArgsCount(sl, 1)
            self._argLabel(sl, sl['args'][0], curAddr)
            if instrName == 'jmp':
                ie = 0b11000011
            else:
                ccc = instrName[1:]
                ie = 0b11000010 | (self._translateCCC(ccc, sl) << 3)
            return [ie, 0, 0]
        elif instrName == 'lda':
            self._expectArgsCount(sl, 1)
            num = self._argImmOrLabel(sl, sl['args'][0], curAddr)
            return [0b00111010, num & 0xff, (num >> 8) & 0xff]
        elif instrName == 'ldax':
            self._expectArgsCount(sl, 1)
            rp = self._argRP(sl, sl['args'][0])
            return [0b00001010 | (rp << 4)]
        elif instrName == 'lhld':
            self._expectArgsCount(sl, 1)
            num = self._argImmOrLabel(sl, sl['args'][1], curAddr)
            return [0b00101010, num & 0xff, (num >> 8) & 0xff]
        elif instrName == 'lxi':
            self._expectArgsCount(sl, 2)
            rp = self._argRP(sl, sl['args'][0])
            num = self._argImmOrLabel(sl, sl['args'][1], curAddr)
            return [0b00000001 | (rp << 4), num & 0xff, (num >> 8) & 0xff]
        elif instrName == 'mov':
            self._expectArgsCount(sl, 2)
            rd = self._argR(sl, sl['args'][0])
            rs = self._argR(sl, sl['args'][1])
            return [0b01000000 | (rd << 3) | rs]
        elif instrName == 'mvi':
            self._expectArgsCount(sl, 2)
            r = self._argR(sl, sl['args'][0])
            imm = self._argImm(sl, sl['args'][1])
            return [0b110 | (r << 3), imm]
        elif instrName == 'nop':
            self._expectArgsCount(sl, 0)
            return [0b00000000]
        elif instrName == 'ora':
            self._expectArgsCount(sl, 1)
            r = self._argR(sl, sl['args'][0])
            return [0b10110000 | r]
        elif instrName == 'ori':
            self._expectArgsCount(sl, 1)
            imm = self._argImm(sl, sl['args'][0])
            return [0b11110110, imm]
        elif instrName == 'pchl':
            self._expectArgsCount(sl, 0)
            return [0b11101001]
        elif instrName == 'pop':
            self._expectArgsCount(sl, 1)
            rp = self._argRP(sl, sl['args'][0])
            return [0b11000001 | (rp << 4)]
        elif instrName == 'push':
            self._expectArgsCount(sl, 1)
            rp = self._argRP(sl, sl['args'][0])
            return [0b11000101 | (rp << 4)]
        elif instrName in ('rc', 'ret', 'rnc', 'rnz', 'rm', 'rp', 'rpe', 'rpo', 'rz'):
            self._expectArgsCount(sl, 0)
            if instrName == 'ret':
                ie = 0b11001001
            else:
                ccc = instrName[1:]
                ie = 0b11000000 | (self._translateCCC(ccc, sl) << 3)
            return [ie]
        elif instrName == 'ral':
            self._expectArgsCount(sl, 0)
            return [0b00010111]
        elif instrName == 'rar':
            self._expectArgsCount(sl, 0)
            return [0b00011111]
        elif instrName == 'rlc':
            self._expectArgsCount(sl, 0)
            return [0b00000111]
        elif instrName == 'rrc':
            self._expectArgsCount(sl, 0)
            return [0b00001111]
        elif instrName == 'sbb':
            self._expectArgsCount(sl, 1)
            r = self._argR(sl, sl['args'][0])
            return [0b10011000 | r]
        elif instrName == 'sbi':
            self._expectArgsCount(sl, 1)
            imm = self._argImm(sl, sl['args'][0])
            return [0b11011110, imm]
        elif instrName == 'shld':
            self._expectArgsCount(sl, 1)
            num = self._argImmOrLabel(sl, sl['args'][1], curAddr)
            return [0b00100010, num & 0xff, (num >> 8) & 0xff]
        elif instrName == 'sphl':
            self._expectArgsCount(sl, 0)
            return [0b11111001]
        elif instrName == 'sta':
            self._expectArgsCount(sl, 1)
            num = self._argImmOrLabel(sl, sl['args'][0], curAddr)
            return [0b00110010, num & 0xff, (num >> 8) & 0xff]
        elif instrName == 'stax':
            self._expectArgsCount(sl, 1)
            rp = self._argRP(sl, sl['args'][0])
            return [0b00000010 | (rp << 4)]
        elif instrName == 'stc':
            self._expectArgsCount(sl, 0)
            return [0b00110111]
        elif instrName == 'sub':
            self._expectArgsCount(sl, 1)
            r = self._argR(sl, sl['args'][0])
            return [0b10010000 | r]
        elif instrName == 'sui':
            self._expectArgsCount(sl, 1)
            imm = self._argImm(sl, sl['args'][0])
            return [0b11010110, imm]
        elif instrName == 'xchg':
            self._expectArgsCount(sl, 0)
            return [0b11101011]
        elif instrName == 'xra':
            self._expectArgsCount(sl, 1)
            r = self._argR(sl, sl['args'][0])
            return [0b10101000 | r]
        elif instrName == 'xri':
            self._expectArgsCount(sl, 1)
            imm = self._argImm(sl, sl['args'][0])
            return [0b11101110, imm]
        elif instrName == 'xthl':
            self._expectArgsCount(sl, 0)
            return [0b11100011]
        else:
            self._assemblyError(sl['pos'], f"unknown instruction {sl['instr']}")
            return []

    def _expectArgsCount(self, sl, count):
        if len(sl['args']) != count:
            self._assemblyError(sl['pos'], f"want {count} args for {sl['instr']}; got {len(sl['args'])}")

    def _argRP(self, sl, arg):
        arg_lower = arg.lower()
        if arg_lower in ('bc', 'b'): return 0b00
        elif arg_lower in ('de', 'd'): return 0b01
        elif arg_lower in ('hl', 'h'): return 0b10
        elif arg_lower in ('sp', 'psw'): return 0b11
        else:
            self._assemblyError(sl['pos'], f"invalid register pair {arg}")

    def _argR(self, sl, arg):
        arg_lower = arg.lower()
        if arg_lower == 'a': return 0b111
        elif arg_lower == 'b': return 0b000
        elif arg_lower == 'c': return 0b001
        elif arg_lower == 'd': return 0b010
        elif arg_lower == 'e': return 0b011
        elif arg_lower == 'h': return 0b100
        elif arg_lower == 'l': return 0b101
        elif arg_lower == 'm': return 0b110
        else:
            self._assemblyError(sl['pos'], f"invalid register {arg}")

    def _argImm(self, sl, arg):
        n = self._parseNumber(arg)
        if n is None:
            self._assemblyError(sl['pos'], f"invalid immediate {arg}")
        return n

    def _argLabel(self, sl, arg, curAddr):
        if not re.match(r'^[a-zA-Z_][a-zA-Z_0-9]*', arg):
            self._assemblyError(sl['pos'], f"invalid label name {arg}")

        if arg not in self.labelToFixups:
            self.labelToFixups[arg] = [{'addr': curAddr, 'pos': sl['pos']}]
        else:
            self.labelToFixups[arg].append({'addr': curAddr, 'pos': sl['pos']})

        if self.tracing:
            print(f"fixups for '{arg}': {self.labelToFixups[arg]}")

    def _argImmOrLabel(self, sl, arg, curAddr):
        n = self._parseNumber(arg)
        if n is None:
            self._argLabel(sl, arg, curAddr)
            return 0
        return n

    def _parseNumber(self, n):
        n = n.lower()
        base = 10
        if n.endswith('h'):
            if not re.match(r'^[0-9a-f]+$', n[:-1]): return None
            n = n[:-1]
            base = 16
        elif n.endswith('b'):
            if not re.match(r'^[0-1]+$', n[:-1]): return None
            n = n[:-1]
            base = 2
        else:
            if not re.match(r'^[0-9]+$', n): return None
                
        try:
            return int(n, base)
        except ValueError:
            return None

    def _translateCCC(self, ccc, sl):
        if ccc == 'nz': return 0b000
        elif ccc == 'z':  return 0b001
        elif ccc == 'nc': return 0b010
        elif ccc == 'c':  return 0b011
        elif ccc == 'po': return 0b100
        elif ccc == 'pe': return 0b101
        elif ccc == 'p':  return 0b110
        elif ccc == 'm':  return 0b111
        else:
            self._assemblyError(sl['pos'], f"unknown CCC ending {ccc}")
            
    def _assemblyError(self, pos, msg):
        raise AssemblyError(msg, pos)