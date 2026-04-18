import unittest

from src.parser import Parser, ParseError
from src.assembler import Assembler, AssemblyError
from src.sim8080 import CPU8080


def runProg(progText, maxSteps=50000):
    p = Parser()
    asm = Assembler()
    sourceLines = p.parse(progText)
    mem, labelToAddr = asm.assemble(sourceLines)

    def memoryTo(addr, value):
        mem[addr] = value
        
    def memoryAt(addr):
        return mem[addr]

    CPU8080.init(memoryTo, memoryAt)
    CPU8080.set('pc', 0)

    for _ in range(maxSteps):
        CPU8080.steps(1)
        if CPU8080.status().halted:
            break

    return CPU8080.status(), mem, labelToAddr


class TestParseErrors(unittest.TestCase):
    def expectParseError(self, code, messageMatchRegex, posMatchFunc):
        with self.assertRaises(ParseError) as cm:
            runProg(code)
        self.assertRegex(cm.exception.args[0], messageMatchRegex)
        self.assertTrue(posMatchFunc(cm.exception.pos), f"pos mismatch, got {cm.exception.pos}")

    def test_token_error(self):
        self.expectParseError(
            'mvi a, %%%',
            r'invalid token',
            lambda pos: pos.line == 1
        )

    def test_parse_error(self):
        self.expectParseError(
            '\nmvi a, :',
            r'want arg',
            lambda pos: pos.line == 2
        )


class TestAssemblyError(unittest.TestCase):
    def expectAssemblyError(self, code, messageMatchRegex, posMatchFunc):
        with self.assertRaises(AssemblyError) as cm:
            runProg(code)
        self.assertRegex(cm.exception.args[0], messageMatchRegex)
        self.assertTrue(posMatchFunc(cm.exception.pos), f"pos mismatch, got {cm.exception.pos}")

    def test_assembly_error(self):
        self.expectAssemblyError(
            '\nmvi a',
            r'want 2 args for mvi',
            lambda pos: pos.line == 2
        )


class TestSim(unittest.TestCase):
    def test_movadd(self):
        state, mem, _ = runProg("""
          mvi b, 12h
          mvi a, 23h
          add b
          hlt
        """)
        self.assertTrue(state.halted)
        self.assertEqual(state.a, 0x35)

    def test_movsub(self):
        state, mem, _ = runProg("""
          mvi a, 20
          mvi b, 5

          sub b
          sbi 7
          hlt
        """)
        self.assertTrue(state.halted)
        self.assertEqual(state.a, 8)

    def test_jzlabel(self):
        state, mem, _ = runProg("""
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
        """)
        self.assertTrue(state.halted)
        self.assertEqual(state.c, 20)

    def test_jnzlabel(self):
        state, mem, _ = runProg("""
          mvi a, 2h
          dcr a
          jz YesZero
          jnz NoZero

        YesZero:
          mvi c, 20
          hlt

        NoZero:
          mvi c, 50
          hlt
        """)
        self.assertTrue(state.halted)
        self.assertEqual(state.c, 50)

    def test_stack(self):
        state, mem, _ = runProg("""
          mvi a, 20
          mvi b, 30
          push bc
          mvi b, 50
          add b
          pop bc
          add b
          hlt
        """)
        self.assertTrue(state.halted)
        self.assertEqual(state.a, 100)

    def test_labels_to_addr(self):
        state, mem, labelToAddr = runProg("""
        Start:
              mvi a, 50       ; 2 bytes each
              mvi b, 20
              mvi c, 100
              jmp Uno         ; 3 bytes
        Tres: add b           ; 1 bytes for add/hlt each
              hlt
        Uno:  jmp Dos
              add c
        Dos:  jmp Tres
              add c
        """)
        self.assertTrue(state.halted)
        self.assertEqual(labelToAddr.get('Start'), 0)
        self.assertEqual(labelToAddr.get('Tres'), 9)
        self.assertEqual(labelToAddr.get('Uno'), 11)
        self.assertEqual(labelToAddr.get('Dos'), 15)

    def test_chainjmp(self):
        state, mem, _ = runProg("""
              mvi a, 50
              mvi b, 20
              mvi c, 100
              jmp Uno
        Tres: add b
              hlt
        Uno:  jmp Dos
              add c
        Dos:  jmp Tres
              add c
        """)
        self.assertTrue(state.halted)
        self.assertEqual(state.a, 70)

    def test_callret(self):
        state, mem, _ = runProg("""
          mvi b, 35
          mvi c, 22
          call Sub
          hlt

            ; This subroutine adds b into c, and clobbers a.
        Sub:
          mov a, b
          add c
          mov c, a
          ret
        """)
        self.assertTrue(state.halted)
        self.assertEqual(state.c, 57)

    def test_loadadd16bit(self):
        state, mem, _ = runProg("""
          lxi hl, 1234h
          lxi bc, 4567h
          dad bc
          hlt
        """)
        self.assertTrue(state.halted)
        self.assertEqual(state.h, 0x57)
        self.assertEqual(state.l, 0x9b)

    def test_movindirect(self):
        state, mem, _ = runProg("""
          lxi hl, myArray
          mov b, m
          inr l
          mov c m
          hlt

        myArray:
          db 10, 20
        """)
        self.assertTrue(state.halted)
        self.assertEqual(state.b, 10)
        self.assertEqual(state.c, 20)

    def test_movindirect_store(self):
        state, mem, _ = runProg("""
          lxi hl, myArray
          mvi m, 33
          mvi a, 55
          lda myArray
          hlt

        myArray:
          db 00
        """)
        self.assertTrue(state.halted)
        self.assertEqual(state.a, 33)

    def test_lda_sta(self):
        state, mem, _ = runProg("""
          lda myArray
          mov c, a
          mvi a, 99
          sta myArray

          mvi a, 0
          lda myArray
          hlt
        myArray:
          db 33
        """)
        self.assertTrue(state.halted)
        self.assertEqual(state.c, 33)
        self.assertEqual(state.a, 99)

    def test_array_dw(self):
        state, mem, labelToAddr = runProg("""
          hlt

        myArray:
          dw 2030h, 5060h
        """)
        self.assertTrue(state.halted)
        arrAddr = labelToAddr.get('myArray')
        self.assertEqual(mem[arrAddr], 0x30)
        self.assertEqual(mem[arrAddr+1], 0x20)
        self.assertEqual(mem[arrAddr+2], 0x60)
        self.assertEqual(mem[arrAddr+3], 0x50)

    def test_mult(self):
        state, mem, _ = runProg("""
                mvi b, 44
                mvi c, 55
                call Multiply
                hlt

    ; multiplies b by c, puts result in hl
    Multiply:   push psw            ; save registers
                push bc

                mvi h, 00h
                mvi l, 00h

                mov a,b          ; the multiplier goes in a
                cpi 00h          ; if it's 0, we're finished
                jz AllDone

                mvi b,00h

    MultLoop:   dad bc
                dcr a
                jnz MultLoop

    AllDone:    pop  bc
                pop psw
                ret
        """)
        self.assertTrue(state.halted)
        self.assertEqual(state.h * 256 + state.l, 44 * 55)

    def test_adduparray(self):
        state, mem, _ = runProg("""
          ; The sum will be accumulated into d
          mvi d, 0
          lxi bc, myArray

          ; Each iteration: load next item from myArray
          ; (until finding 0) into a. Then do d <- d+a.
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
          db 10, 20, 30, 10h, 20h, 0
        """)
        self.assertTrue(state.halted)
        self.assertEqual(state.d, 108)

    def test_adduparray_count(self):
        state, mem, _ = runProg("""
          ; The sum will be accumulated into a
          mvi a, 0
          lxi hl, myArray

          ; c is the counter
          mvi c, 5

        Loop:
          add m
          inr l
          dcr c
          jz Done
          jmp Loop

        Done:
          hlt

        myArray:
          db 10, 20, 30, 10h, 21h
        """)
        self.assertTrue(state.halted)
        self.assertEqual(state.a, 109)

    def test_adduparray_string_count(self):
        state, mem, _ = runProg("""
          ; The sum will be accumulated into a
          mvi a, 0
          lxi hl, myArray

          ; c is the counter
          mvi c, 3

        Loop:
          add m
          inr l
          dcr c
          jz Done
          jmp Loop

        Done:
          hlt

        myArray:
          db 'ABC'
        """)
        self.assertTrue(state.halted)
        self.assertEqual(state.a, 65 + 66 + 67)

    def test_pchl(self):
        state, mem, _ = runProg("""
            lxi hl, There
            pchl
            mvi a, 20
            hlt

    There:  mvi a, 30
            hlt
          """)
        self.assertTrue(state.halted)
        self.assertEqual(state.a, 30)

    def test_cond_call_cnz_yes(self):
        state, mem, _ = runProg("""
            mvi b, 5
            mvi a, 2
            dcr a
            cnz BAdder
            hlt

            ; This function increments b
        BAdder:
            inr b
            ret
          """)
        self.assertTrue(state.halted)
        self.assertEqual(state.b, 6)

    def test_cond_call_cnz_no(self):
        state, mem, _ = runProg("""
            mvi b, 5
            mvi a, 1
            dcr a
            cnz BAdder
            hlt

            ; This function increments b
        BAdder:
            inr b
            ret
          """)
        self.assertTrue(state.halted)
        self.assertEqual(state.b, 5)

    def test_cond_ret_rz_first(self):
        state, mem, _ = runProg("""
            mvi b, 1
            call BRet
            hlt

        BRet:
            mvi c, 10
            dcr b
            rz
            mvi c, 20
            dcr b
            rz
            mvi c, 99
            hlt
          """)
        self.assertTrue(state.halted)
        self.assertEqual(state.c, 10)

    def test_cond_ret_rz_second(self):
        state, mem, _ = runProg("""
            mvi b, 2
            call BRet
            hlt

        BRet:
            mvi c, 10
            dcr b
            rz
            mvi c, 20
            dcr b
            rz
            mvi c, 99
            hlt
          """)
        self.assertTrue(state.halted)
        self.assertEqual(state.c, 20)

    def test_bitwise_and(self):
        state, mem, _ = runProg("""
           mvi a, 11111111b
           mvi b, 11101110b
           ani 11111101b
           ana b
           hlt
          """)
        self.assertTrue(state.halted)
        self.assertEqual(state.a, 0b11101100)

    def test_bitwise_or(self):
        state, mem, _ = runProg("""
           mvi a, 10000001b
           mvi b, 10101010b
           ori 100b
           ora b
           hlt
          """)
        self.assertTrue(state.halted)
        self.assertEqual(state.a, 0b10101111)

    def test_bitwise_xor(self):
        state, mem, _ = runProg("""
           mvi a, 10000001b
           mvi b, 11111111b
           xra b
           xri 00111100b
           hlt
          """)
        self.assertTrue(state.halted)
        self.assertEqual(state.a, 0b01000010)

    def test_bitwise_rotate(self):
        state, mem, _ = runProg("""
           mvi a, 11101110b
           rlc
           mov b, a
           mvi a, 11101110b
           rrc
           hlt
          """)
        self.assertTrue(state.halted)
        self.assertEqual(state.a, 0b01110111)
        self.assertEqual(state.b, 0b11011101)

    def test_xchg(self):
        state, mem, _ = runProg("""
          lxi hl, 1234h
          lxi de, 4567h
          xchg
          hlt
          """)
        self.assertTrue(state.halted)
        self.assertEqual(state.h, 0x45)
        self.assertEqual(state.l, 0x67)
        self.assertEqual(state.d, 0x12)
        self.assertEqual(state.e, 0x34)

    def test_rp_single_char_ref(self):
        state, mem, _ = runProg("""
          lxi h, 1234h
          lxi d, 4567h
          lxi b, abcdh
          hlt
          """)
        self.assertTrue(state.halted)
        self.assertEqual(state.h, 0x12)
        self.assertEqual(state.l, 0x34)
        self.assertEqual(state.d, 0x45)
        self.assertEqual(state.e, 0x67)
        self.assertEqual(state.b, 0xab)
        self.assertEqual(state.c, 0xcd)

    def test_inx(self):
        state, mem, _ = runProg("""
          lxi hl, 12ffh
          inx hl
          hlt
          """)
        self.assertTrue(state.halted)
        self.assertEqual(state.h, 0x13)
        self.assertEqual(state.l, 0x00)

    def test_dcx(self):
        state, mem, _ = runProg("""
          lxi de, 2200h
          dcx de
          hlt
          """)
        self.assertTrue(state.halted)
        self.assertEqual(state.d, 0x21)
        self.assertEqual(state.e, 0xff)

    def test_memcpy(self):
        state, mem, labelToAddr = runProg("""
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
        """)
        self.assertTrue(state.halted)
        target_addr = labelToAddr.get('TargetArray')
        self.assertEqual(mem[target_addr], 0x11)
        self.assertEqual(mem[target_addr + 1], 0x22)
        self.assertEqual(mem[target_addr + 2], 0x33)
        self.assertEqual(mem[target_addr + 3], 0x44)
        self.assertEqual(mem[target_addr + 4], 0x55)

    def test_subroutine_pass_arg_pointer(self):
        state, mem, labelToAddr = runProg("""
          lxi h, plist
          call ADSUB

          lxi h, list2
          call ADSUB
          hlt

        plist: db 6, 8, 0
        list2: db 10, 35, 0

        ADSUB:
          mov a, m
          inx h
          mov b, m
          add b
          inx h
          mov m, a
          ret
        """)
        self.assertTrue(state.halted)
        plist = labelToAddr.get('plist')
        list2 = labelToAddr.get('list2')

        self.assertEqual(mem[plist + 2], 6 + 8)
        self.assertEqual(mem[list2 + 2], 10 + 35)

    def test_capitalize_string(self):
        state, mem, labelToAddr = runProg("""
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
        """)
        self.assertTrue(state.halted)
        str_addr = labelToAddr.get('str')

        s = ''
        for i in range(str_addr, str_addr + 14):
            s += chr(mem[i])
            
        self.assertEqual(s, 'HELLO, FRIENDS')


if __name__ == '__main__':
    unittest.main()