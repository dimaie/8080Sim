import threading
import time
import tkinter as tk
import os
from .base_plugin import BasePlugin

def rgb332_to_rgb(val):
    """Converts 8-bit RGB332 color to a 3-byte RGB sequence."""
    return bytes([(val >> 5) * 36, ((val >> 2) & 7) * 36, (val & 3) * 85])

class CustomComputerPlugin(BasePlugin):
    name = "Custom 8080 Computer (Display)"

    def __init__(self, app):
        super().__init__(app)
        self.running = False
        self.thread = None
        self.window = None
        self.canvas = None
        self.img_id = None
        self.photo_img = None
        
        self.last_hash = 0
        self.frame_cnt = 0
        self._lut_cache = {}
        self.reg_labels = {}
        self.color_swatches = {}
        
    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._scan_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def on_reset(self):
        # Inject default colors so the simulated screen isn't completely black on black
        mem = self.app.debugger.memory
        orig = self.app.debugger.original_memory
        
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Load Program ROM
        self._load_hex(os.path.join(plugin_dir, "program.hex"), 0x0000)
        
        # Load Font ROM
        font_path = os.path.join(plugin_dir, "fon_rom.hex")
        if not os.path.exists(font_path):
            font_path = os.path.join(plugin_dir, "font_rom.hex") # fallback
        self._load_hex(font_path, 0xB000)
        
        mem[0xC001] = orig[0xC001] = 0xFF # Text Ink = White
        mem[0xC002] = orig[0xC002] = 0x00 # Background = Black
        mem[0xC006] = orig[0xC006] = 0xFF # Gfx Ink = White
        self.last_hash = 0

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
        self.window.attributes("-topmost", True)
        self.window.protocol("WM_DELETE_WINDOW", self.hide_window)

        # Left Panel: 640x480 Display
        disp_frame = tk.Frame(self.window, width=640, height=480, bg="black")
        disp_frame.pack(side=tk.LEFT)
        disp_frame.pack_propagate(False)
        
        self.canvas = tk.Canvas(disp_frame, width=640, height=480, bg="black", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Right Panel: Registers
        reg_frame = tk.Frame(self.window, width=240, height=480, padx=15, pady=15)
        reg_frame.pack(side=tk.LEFT, fill=tk.BOTH)
        
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
