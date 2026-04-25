import threading
import time
import tkinter as tk
from tkinter import messagebox
import os
from .base_plugin import BasePlugin
from sim8080 import CPU8080

PS2_MAP = {
    'a': 0x1C, 'b': 0x32, 'c': 0x21, 'd': 0x23, 'e': 0x24, 'f': 0x2B,
    'g': 0x34, 'h': 0x33, 'i': 0x43, 'j': 0x3B, 'k': 0x42, 'l': 0x4B,
    'm': 0x3A, 'n': 0x31, 'o': 0x44, 'p': 0x4D, 'q': 0x15, 'r': 0x2D,
    's': 0x1B, 't': 0x2C, 'u': 0x3C, 'v': 0x2A, 'w': 0x1D, 'x': 0x22,
    'y': 0x35, 'z': 0x1A,
    'A': 0x1C, 'B': 0x32, 'C': 0x21, 'D': 0x23, 'E': 0x24, 'F': 0x2B,
    'G': 0x34, 'H': 0x33, 'I': 0x43, 'J': 0x3B, 'K': 0x42, 'L': 0x4B,
    'M': 0x3A, 'N': 0x31, 'O': 0x44, 'P': 0x4D, 'Q': 0x15, 'R': 0x2D,
    'S': 0x1B, 'T': 0x2C, 'U': 0x3C, 'V': 0x2A, 'W': 0x1D, 'X': 0x22,
    'Y': 0x35, 'Z': 0x1A,
    '0': 0x45, '1': 0x16, '2': 0x1E, '3': 0x26, '4': 0x25, '5': 0x2E,
    '6': 0x36, '7': 0x3D, '8': 0x3E, '9': 0x46,
    'exclam': 0x16, 'at': 0x1E, 'numbersign': 0x26, 'dollar': 0x25, 'percent': 0x2E,
    'asciicircum': 0x36, 'ampersand': 0x3D, 'asterisk': 0x3E, 'parenleft': 0x46, 'parenright': 0x45,
    'space': 0x29, 'Return': 0x5A, 'Escape': 0x76, 'BackSpace': 0x66, 'Tab': 0x0D,
    'Shift_L': 0x12, 'Shift_R': 0x59, 'Control_L': 0x14, 'Control_R': [0xE0, 0x14],
    'Alt_L': 0x11, 'Alt_R': [0xE0, 0x11],
    'comma': 0x41, 'less': 0x41, 'period': 0x49, 'greater': 0x49,
    'slash': 0x4A, 'question': 0x4A, 'semicolon': 0x4C, 'colon': 0x4C,
    'apostrophe': 0x52, 'quotedbl': 0x52, 'bracketleft': 0x54, 'braceleft': 0x54,
    'bracketright': 0x5B, 'braceright': 0x5B, 'backslash': 0x5D, 'bar': 0x5D,
    'minus': 0x4E, 'underscore': 0x4E, 'equal': 0x55, 'plus': 0x55,
    'grave': 0x0E, 'asciitilde': 0x0E,
    'Up': [0xE0, 0x75], 'Down': [0xE0, 0x72], 'Left': [0xE0, 0x6B], 'Right': [0xE0, 0x74]
}

def rgb332_to_rgb(val):
    """Converts 8-bit RGB332 color to a 3-byte RGB sequence."""
    return bytes([(val >> 5) * 36, ((val >> 2) & 7) * 36, (val & 3) * 85])

class CustomComputerPlugin(BasePlugin):
    name = "Custom 8080 Computer (Display)"
    MAGIC_RETURN = 0xDEAD

    def __init__(self, app):
        super().__init__(app)
        self.running = False
        self.thread = None
        self.cpu_thread = None
        self.window = None
        self.canvas = None
        self.img_id = None
        self.photo_img = None
        
        self.last_hash = 0
        self.frame_cnt = 0
        self._lut_cache = {}
        self.reg_labels = {}
        self.color_swatches = {}
        
        self.kb_queue = []
        self.kb_data = 0
        self.kb_ready = False
        self.pressed_keys = set()
        self.led_indicator = None
        self.is_launched = False
        self.autorun = False
        self.saved_monitor_state = None
        self.user_program_mode = True
        
    def is_user_program_mode(self, start_addr=None):
        return self.user_program_mode

    def start(self):
        if self.running: return
        
        # Explicitly ask the user for their intended debugging mode when the plugin is initialized
        self.user_program_mode = messagebox.askyesno(
            "Plugin Debug Mode",
            "Are you debugging a User Program?\n\n"
            "Yes (User Program): The Monitor ROM runs natively in the background. "
            "Execution automatically handles context-switching via the 'G' command.\n\n"
            "No (Monitor): The background thread is disabled. "
            "You can debug the monitor's startup and execution explicitly from the UI.",
            parent=self.app
        )
        
        self.running = True
        self.thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.thread.start()
        self.cpu_thread = threading.Thread(target=self._cpu_loop, daemon=True)
        self.cpu_thread.start()
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()
        if hasattr(self, 'cpu_thread') and self.cpu_thread:
            self.cpu_thread.join()
            
    def _cpu_loop(self):
        while self.running:
            if self.window and self.window.winfo_exists() and self.autorun and not self.app.debugger.running:
                if not CPU8080.status().halted:
                    CPU8080.steps(2000)
                time.sleep(0.001)
            else:
                time.sleep(0.05)

    def on_reset(self):
        user_mode = self.is_user_program_mode()
        self.autorun = user_mode
        
        mem = self.app.debugger.memory
        orig = self.app.debugger.original_memory
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        
        if user_mode:
            rom_path = os.path.join(plugin_dir, "program.hex")
            self._load_hex(rom_path, 0x0000)
        
        # Load Font ROM
        font_path = os.path.join(plugin_dir, "fon_rom.hex")
        if not os.path.exists(font_path):
            font_path = os.path.join(plugin_dir, "font_rom.hex") # fallback
        self._load_hex(font_path, 0xB000)
        
        mem[0xC001] = orig[0xC001] = 0xFF # Text Ink = White
        mem[0xC002] = orig[0xC002] = 0x00 # Background = Black
        mem[0xC003] = orig[0xC003] = 0x00 # Cursor X
        mem[0xC004] = orig[0xC004] = 0x00 # Cursor Y
        mem[0xC005] = orig[0xC005] = 0x02 # Cursor Style = Block
        mem[0xC006] = orig[0xC006] = 0xFF # Gfx Ink = White
        self.last_hash = 0

        if user_mode:
            CPU8080.set('pc', 0x0000)
        else:
            CPU8080.set('pc', self.app.debugger.start_addr)
        self.is_launched = False

        self.kb_queue.clear()
        self.kb_data = 0
        self.kb_ready = False
        self.pressed_keys.clear()
        
        orig_io_read = CPU8080._io_read
        if getattr(orig_io_read, "__name__", "") != "custom_io_read":
            def custom_io_read(port):
                if port == 0x00:
                    val = self.kb_data
                    self.kb_ready = False # Auto-clear on read
                    if self.kb_queue:
                        self.kb_queue.pop(0)
                    if self.kb_queue:
                        self.kb_data = self.kb_queue[0]
                        self.kb_ready = True
                    return val
                elif port == 0x01:
                    return 1 if self.kb_ready else 0
                return orig_io_read(port)
                
            CPU8080._io_read = custom_io_read

    def pre_execute(self):
        # Verification 1: Are we running in monitor mode or user program mode?
        if not self.user_program_mode:
            self.autorun = False
            return
            
        # Verification 2: Are we starting the debugging session, or continuing it?
        # If is_launched is True, we are continuing the session. We should not emulate 'G'.
        if self.is_launched:
            self.autorun = False
            return
            
        # If we reach here, we are STARTING a new debugging session in User Program mode.
        self.autorun = False
        self.is_launched = True
        
        # Emulate the Monitor's 'G' command context switch
        self.saved_monitor_state = CPU8080.status()
        
        CPU8080.set('sp', 0x3FFF)
        CPU8080._push(self.MAGIC_RETURN) # Push magic trap address
        CPU8080.set('pc', self.app.debugger.start_addr)

    def restore_context(self):
        if self.saved_monitor_state:
            for reg in ['a', 'b', 'c', 'd', 'e', 'h', 'l', 'pc', 'sp', 'f', 'halted']:
                CPU8080.set(reg, getattr(self.saved_monitor_state, reg))

    def _load_hex(self, filepath, current_addr):
        if not os.path.exists(filepath):
            return
            
        mem = self.app.debugger.memory
        orig = self.app.debugger.original_memory
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                
                # Check for standard Intel HEX format
                if line.startswith(':'):
                    try:
                        length = int(line[1:3], 16)
                        addr = int(line[3:7], 16)
                        rec_type = int(line[7:9], 16)
                        if rec_type == 0: # Data record
                            for i in range(length):
                                val = int(line[9+i*2 : 11+i*2], 16)
                                target_addr = current_addr + addr + i
                                if 0 <= target_addr <= 0xFFFF:
                                    mem[target_addr] = val
                                    orig[target_addr] = val
                    except ValueError:
                        pass
                    continue
                    
                line = line.split('//')[0].split(';')[0].strip()
                for token in line.split():
                    if token.startswith('@'):
                        current_addr = int(token[1:], 16)
                    else:
                        try:
                            val = int(token, 16)
                            if 0 <= current_addr <= 0xFFFF:
                                mem[current_addr] = val
                                orig[current_addr] = val
                                current_addr += 1
                        except ValueError:
                            pass

    def show_window(self):
        if self.window and self.window.winfo_exists():
            self.window.lift()
            return

        self.window = tk.Toplevel(self.app)
        self.window.title(self.name)
        self.window.geometry("880x480")
        self.window.resizable(False, False)
        self.window.transient(self.app)
        self.window.protocol("WM_DELETE_WINDOW", self.hide_window)
        
        self.window.bind("<KeyPress>", self.on_key_press) # Bind to window to catch keys
        self.window.bind("<KeyRelease>", self.on_key_release)

        # Left Panel: 640x480 Display
        disp_frame = tk.Frame(self.window, width=640, height=480, bg="black")
        disp_frame.pack(side=tk.LEFT)
        disp_frame.pack_propagate(False)
        
        self.canvas = tk.Canvas(disp_frame, width=640, height=480, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind to canvas as well, as it's the main interactive element
        self.canvas.bind("<KeyPress>", self.on_key_press)
        self.canvas.bind("<KeyRelease>", self.on_key_release)

        # Right Panel: Registers
        reg_frame = tk.Frame(self.window, width=240, height=480, padx=15, pady=15)
        reg_frame.pack(side=tk.LEFT, fill=tk.BOTH)
        
        # --- Keyboard LED Indicator ---
        led_frame = tk.Frame(reg_frame)
        led_frame.pack(fill=tk.X, pady=(0,15))
        tk.Label(led_frame, text="KB Input:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.led_indicator = tk.Label(led_frame, width=2, bg="#400000", relief="solid", borderwidth=1)
        self.led_indicator.pack(side=tk.LEFT, padx=5)
        
        tk.Label(reg_frame, text="MMIO Registers", font=("Arial", 12, "bold")).pack(anchor="w", pady=(0,10))
        
        regs = [
            (0xC001, "Text Ink"), (0xC002, "Background"), (0xC003, "Cursor X"),
            (0xC004, "Cursor Y"), (0xC005, "Cursor Style"), (0xC006, "Gfx Ink")
        ]
        
        for addr, name in regs:
            frame = tk.Frame(reg_frame)
            frame.pack(fill=tk.X, pady=4)
            tk.Label(frame, text=f"{addr:04X} {name}:", width=16, anchor="w").pack(side=tk.LEFT)
            var = tk.StringVar(value="00")
            self.reg_labels[addr] = var
            tk.Label(frame, textvariable=var, font=("Courier", 10, "bold"), fg="#0055cc").pack(side=tk.LEFT)
            
            if addr in (0xC001, 0xC002, 0xC006):
                swatch = tk.Label(frame, width=2, bg="black", relief="solid", borderwidth=1)
                swatch.pack(side=tk.LEFT, padx=(5, 0))
                self.color_swatches[addr] = swatch

    def hide_window(self):
        if self.window:
            self.window.destroy()
            self.window = None
            self.img_id = None

    def _get_lut(self, txt_ink, gfx_ink, bg):
        key = (txt_ink, gfx_ink, bg)
        if key in self._lut_cache: return self._lut_cache[key]
        
        t_rgb = rgb332_to_rgb(txt_ink)
        g_rgb = rgb332_to_rgb(gfx_ink)
        b_rgb = rgb332_to_rgb(bg)
        
        lut = []
        for font_byte in range(256):
            row_lut = []
            for gfx_halfbyte in range(16):
                pixels = bytearray()
                for i in range(8):
                    f_bit = (font_byte >> (7 - i)) & 1
                    g_bit = (gfx_halfbyte >> (3 - (i // 2))) & 1
                    if f_bit: pixels.extend(t_rgb)
                    elif g_bit: pixels.extend(g_rgb)
                    else: pixels.extend(b_rgb)
                row_lut.append(bytes(pixels))
            lut.append(row_lut)
        
        self._lut_cache[key] = lut
        return lut

    def _enqueue_scan_code(self, code_seq):
        if isinstance(code_seq, list):
            self.kb_queue.extend(code_seq)
        else:
            self.kb_queue.append(code_seq)
            
        if not self.kb_ready and self.kb_queue:
            self.kb_data = self.kb_queue[0]
            self.kb_ready = True

    def on_key_press(self, event):
        keysym = event.keysym
        if keysym == 'F5':
            self.app.on_reset()
            return
            
        if keysym in self.pressed_keys:
            return # Suppress OS typematic repeating
            
        code = PS2_MAP.get(keysym)
        if code:
            self.pressed_keys.add(keysym)
            self._enqueue_scan_code(code)
            
            # Flash the LED indicator
            if self.led_indicator and self.window and self.window.winfo_exists():
                self.led_indicator.config(bg="#00ff00") # Bright Green
                self.window.after(50, self.turn_off_led)

    def on_key_release(self, event):
        keysym = event.keysym
        if keysym in self.pressed_keys:
            self.pressed_keys.discard(keysym)
            
            code = PS2_MAP.get(keysym)
            if code:
                if isinstance(code, list):
                    break_code = [code[0], 0xF0, code[1]]
                    self._enqueue_scan_code(break_code)
                else:
                    self._enqueue_scan_code([0xF0, code])

    def turn_off_led(self):
        if self.led_indicator and self.window and self.window.winfo_exists():
            self.led_indicator.config(bg="#400000") # Dark Red

    def _scan_loop(self):
        while self.running:
            if self.window and self.window.winfo_exists():
                self._render_frame()
            time.sleep(0.05) # Cap at ~20 FPS so it won't tax CPU

    def _render_frame(self):
        mem = self.app.debugger.memory
        self.frame_cnt += 1
        blink_active = (self.frame_cnt // 10) % 2 != 0
        
        # Using native python hash on memory slices as a lightning-fast dirtiness check
        h = hash(bytes(mem[0x4000:0x6580])) ^ hash(bytes(mem[0xA000:0xA960])) ^ \
            hash(bytes(mem[0xB000:0xB800])) ^ hash(bytes(mem[0xC001:0xC007])) ^ hash(blink_active)
            
        if h == self.last_hash: return
        self.last_hash = h
        
        t_ink, bg, cur_x, cur_y, cur_style, g_ink = (mem[addr] for addr in range(0xC001, 0xC007))
        lut = self._get_lut(t_ink, g_ink, bg)
        
        # Start PPM P6 image builder (640x480 resolution)
        ppm_data = bytearray(b"P6\n640 480\n255\n")
        
        for y in range(240):
            txt_off = 0xA000 + (y // 8) * 80
            gfx_off = 0x4000 + y * 40
            font_line = y % 8
            
            # Replicating Verilog's cursor shape/blink XOR logic
            cur_shape_active = (cur_style == 2) or (cur_style == 1 and font_line >= 4)
            show_cursor_line = cur_shape_active and blink_active and (cur_style != 0) and (y // 8 == cur_y)
            
            line_bytes = bytearray()
            for x in range(40):
                g_byte = mem[gfx_off + x]
                char1 = mem[txt_off + x*2]
                char2 = mem[txt_off + x*2 + 1]
                
                f1 = mem[0xB000 + char1 * 8 + font_line]
                f2 = mem[0xB000 + char2 * 8 + font_line]
                
                if show_cursor_line:
                    if x*2 == cur_x: f1 ^= 0xFF
                    if x*2 + 1 == cur_x: f2 ^= 0xFF
                    
                line_bytes.extend(lut[f1][g_byte >> 4])
                line_bytes.extend(lut[f2][g_byte & 0x0F])
                
            ppm_data.extend(line_bytes)
            ppm_data.extend(line_bytes) # Double-scale Y directly into the output
            
        self.app.after_idle(self._update_ui, ppm_data, (t_ink, bg, cur_x, cur_y, cur_style, g_ink))
        
    def _update_ui(self, ppm_data, regs):
        if not self.window or not self.window.winfo_exists(): return
        
        self.photo_img = tk.PhotoImage(data=bytes(ppm_data))
        if self.img_id is None: self.img_id = self.canvas.create_image(0, 0, image=self.photo_img, anchor="nw")
        else: self.canvas.itemconfig(self.img_id, image=self.photo_img)
            
        for i, val in enumerate(regs):
            addr = 0xC001 + i
            self.reg_labels[addr].set(f"{val:02X}")
            if addr in self.color_swatches:
                r, g, b = rgb332_to_rgb(val)
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                self.color_swatches[addr].config(bg=hex_color)
