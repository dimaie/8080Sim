# SAP-3 Processor Project Context

## Overview
This project is an FPGA implementation of the SAP-3 (Simple As Possible 3) processor, which is an educational implementation of the Intel 8080 Instruction Set Architecture. 
The design uses a shared 16-bit internal data bus with multiplexed component access.
The hardware is based on the OneChipBook laptop. `OneChipBook12-TechRef.pdf` is available for all hardware-related questions.

## Verilog Coding Standards
- **Standard:** Use standard Verilog-2001 syntax. Do not use SystemVerilog specific features unless explicitly requested.
- **Sequential Logic:** Always use non-blocking assignments (`<=`) inside `always @(posedge clk)` blocks.
- **Combinational Logic:** Always use blocking assignments (`=`) inside `always @(*)` blocks. Default all outputs to a known state (e.g., `0`) at the top of combinational blocks to prevent latch inference.
- **Constants:** Use `localparam` for state definitions, opcodes, and bit-positions. Name them using `UPPER_CASE`.

## Naming Conventions
- `*_we`: Write Enable signals (active high).
- `*_oe`: Output Enable signals (active high, used for driving the shared bus).
- `*_sel`: Select signals for multiplexers.
- `clk`: System clock.
- `rst`: Internal reset (active-high).

## Memory Map
- `0x0000` - `0x0DF3`: 3572 Bytes Program ROM
- `0x0DF4` - `0x1FFF`: Unused
- `0x2000` - `0x3FFF`: 8KB Program RAM
- `0x4000` - `0x5DFF`: 7680 Bytes Video Graphics RAM (256x240 monochrome, Read/Write)
- `0x5E00` - `0x9FFF`: Unused
- `0xA000` - `0xA77F`: 1920 Bytes Video Text RAM (64x30 text mode, Write-Only)
- `0xA780` - `0xAFFF`: Unused
- `0xB000` - `0xB7FF`: 2KB Video Font RAM (8x8 character fonts, 256 chars, Write-Only)
- `0xC001`: Video Ink Color Register
- `0xC002`: Video Background Color Register
- `0xC003`: Cursor X Position Register (0-63)
- `0xC004`: Cursor Y Position Register (0-29)
- `0xC005`: Cursor Style Register (0=Hidden, 1=Half Blinking, 2=Full Blinking, 3=Full Solid)
- `0xC006`: Video Graphics Ink Color Register

## Architecture Notes
- The external board reset (`RESET_N`) is active-low, but it is inverted to an active-high `rst` signal at the top level (`Computer1CB12-1_Top.v`). All sub-modules should assume `rst` is active-high.
- Memory is initialized from a `program.hex` hex file.
- The ALU evaluates arithmetic/logic operations on the positive clock edge but updates processor flags (Z, C, P, S) on the negative clock edge.
- Video Mixer Logic: The VGA display pipeline reads both Text and Graphics RAM simultaneously. Text pixels are overlaid transparently on top of graphics pixels, eliminating the need for a dedicated video mode register.

## System Monitor (ROM) Specification
A ROM-based system monitor program is being developed gradually to provide basic debugging, execution, and API functionalities.

### C-Compiler ROM API (Jump Table)
The monitor provides a stable API for compiled C programs or user assembly routines. Arguments are passed via the hardware stack (Right-to-Left, 16-bit per argument, Caller Cleanup). Return values are placed in the `HL` register pair (or `L` for 8-bit returns).

- `0x0010`: `void print_char(int c)` - Prints a character to Text RAM and advances the hardware cursor.
- `0x0013`: `int read_key()` - Blocks and returns the ASCII value of the next key pressed.
- `0x0016`: `void clear_screen(int layer)` - Clears the screen (layer: 0 = both, 1 = text, 2 = graphics).
- `0x0019`: `void print_char_xy(int c, int x, int y)` - Draws a character directly to specific Text RAM coordinates (X: 0-63, Y: 0-29).
- `0x001C`: `int read_char_xy(int x, int y)` - Reads the character currently at the specified Text RAM coordinates (X: 0-63, Y: 0-29).
- `0x001F`: `int read_pixel_xy(int x, int y)` - Reads the pixel state (0 or 1) at the specified Graphics RAM coordinates (X: 0-255, Y: 0-239).
- `0x0022`: `int check_key(void)` - Non-blocking check of the PS/2 keyboard. Returns the scan code, or 0 if empty.

### Monitor Commands
- `Dxxxx[,yyyy]` - **Dump Memory:** Displays the memory contents starting at hex address `xxxx`. If `yyyy` is provided, dumps the range up to `yyyy`.
- `Mxxxx` - **Modify Memory:** Displays the current byte at hex address `xxxx` and prompts for input. If a valid hex value is entered, writes it to the address. If empty/invalid, leaves the cell unmodified.
- `X` - **Examine/Modify Registers:** Iterates through the CPU registers one by one, displaying their current values and prompting for new input to overwrite them.
- `R` - **Receive Data:** Accepts binary data via the COM-port (UART RX) and loads it directly into memory. (Detailed protocol specification pending).
- `Gxxxx` - **Go:** Transfers execution control (jumps) to the program located at hex address `xxxx`.
