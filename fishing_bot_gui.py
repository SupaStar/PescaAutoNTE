import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import queue
import time
import cv2
import numpy as np
import mss
from PIL import Image, ImageTk
import sys
import os
import re

# Import our refactored bot logic and default configs
from fishing_bot import FishingBot, BAR_REF, F_ICON_REF, SUCCESS_REF

# Queue for thread-safe communication between Bot Thread and Tkinter Main Thread
gui_queue = queue.Queue()

# Global states
bot_thread = None
bot_instance = None
window_rect = None  # (left, top, right, bottom)
window_title = "None"
crop_window = None  # Handle to the calibration window if open

# Styling Colors (Tokyo Night Dark Theme)
BG_MAIN = "#1A1B26"
BG_CARD = "#24283B"
BG_CONSOLE = "#16161E"
TEXT_PRIMARY = "#C0CAF5"
TEXT_SECONDARY = "#A9B1D6"
TEXT_MUTED = "#565F89"
ACCENT_BLUE = "#7AA2F7"
ACCENT_GREEN = "#41A67C"
ACCENT_GREEN_HOVER = "#2CF6B3"
ACCENT_RED = "#F7768E"
ACCENT_RED_HOVER = "#FF5F56"
ACCENT_CYAN = "#00ADB5"
ACCENT_CYAN_HOVER = "#89DDFF"
ACCENT_YELLOW = "#E0AF68"

def find_game_window(exclude_hwnd=None):
    """
    Uses Windows user32 APIs via ctypes to search for active window
    containing Neverness to Everness or NTE.
    """
    import ctypes
    from ctypes import wintypes

    EnumWindows = ctypes.windll.user32.EnumWindows
    EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
    GetWindowText = ctypes.windll.user32.GetWindowTextW
    GetWindowTextLength = ctypes.windll.user32.GetWindowTextLengthW
    IsWindowVisible = ctypes.windll.user32.IsWindowVisible
    GetWindowRect = ctypes.windll.user32.GetWindowRect
    
    found = []

    def foreach_window(hwnd, lParam):
        if exclude_hwnd and hwnd == exclude_hwnd:
            return True
            
        if IsWindowVisible(hwnd):
            length = GetWindowTextLength(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                GetWindowText(hwnd, buff, length + 1)
                title = buff.value
                title_lower = title.lower()
                
                # Exclude this tool's GUI or shell wrappers to avoid self-targeting
                if "auto-fisher" in title_lower or "fishing_bot" in title_lower or "powershell" in title_lower or "cmd.exe" in title_lower:
                    return True
                
                # Check for game title indicators using word boundaries for "nte"
                if "neverness" in title_lower or "everness" in title_lower or re.search(r'\bnte\b', title_lower):
                    rect = wintypes.RECT()
                    GetWindowRect(hwnd, ctypes.byref(rect))
                    found.append((hwnd, title, (rect.left, rect.top, rect.right, rect.bottom)))
        return True

    EnumWindows(EnumWindowsProc(foreach_window), 0)
    return found


class FishingBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Neverness to Everness (NTE) Auto-Fisher (Adaptive AI)")
        self.root.geometry("880x740")
        self.root.configure(bg=BG_MAIN)
        self.root.resizable(True, True)

        # Apply basic style modifications
        self.setup_styles()

        # Build GUI layouts
        self.create_header_panel()
        self.create_main_content()
        self.create_log_panel()

        # Setup periodic queue checking
        self.root.after(100, self.process_queue)
        
        # Auto-detect game window on startup
        self.detect_window(silent=True)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background=BG_MAIN, foreground=TEXT_PRIMARY)
        style.configure("TFrame", background=BG_MAIN)
        style.configure("Card.TFrame", background=BG_CARD, relief="flat")
        style.configure("TLabel", background=BG_MAIN, foreground=TEXT_PRIMARY, font=("Segoe UI", 10))
        style.configure("Card.TLabel", background=BG_CARD, foreground=TEXT_PRIMARY, font=("Segoe UI", 10))
        style.configure("Header.TLabel", background=BG_MAIN, foreground=ACCENT_BLUE, font=("Segoe UI", 16, "bold"))
        style.configure("Sub.TLabel", background=BG_MAIN, foreground=TEXT_MUTED, font=("Segoe UI", 9, "italic"))

    def create_header_panel(self):
        # Header Container
        header_frame = ttk.Frame(self.root, padding=(20, 15, 20, 10))
        header_frame.pack(fill="x")

        # Title Label
        title_label = ttk.Label(header_frame, text="NEVERNESS TO EVERNESS AUTO-FISHER", style="Header.TLabel")
        title_label.pack(side="left")

        # Subtitle
        sub_label = ttk.Label(header_frame, text="Enhanced with Adaptive AI Controller", style="Sub.TLabel")
        sub_label.pack(side="left", padx=15, pady=5)

        # Window detection status block
        self.win_status_var = tk.StringVar(value="Game Window: Not Detected")
        self.win_status_label = tk.Label(
            header_frame, 
            textvariable=self.win_status_var, 
            font=("Segoe UI", 10, "bold"), 
            bg=BG_MAIN, 
            fg=ACCENT_RED
        )
        self.win_status_label.pack(side="right")

    def create_main_content(self):
        # Container
        content_frame = ttk.Frame(self.root, padding=(20, 5, 20, 10))
        content_frame.pack(fill="both", expand=False)

        # Left Column: Configuration & Actions
        left_col = ttk.Frame(content_frame)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Action Buttons Card
        btn_card = ttk.Frame(left_col, style="Card.TFrame", padding=15)
        btn_card.pack(fill="x", pady=(0, 10))

        card_title = tk.Label(btn_card, text="BOT CONTROLS", font=("Segoe UI", 10, "bold"), bg=BG_CARD, fg=ACCENT_BLUE)
        card_title.pack(anchor="w", pady=(0, 10))

        # Start Button
        self.btn_start = tk.Button(
            btn_card, text="▶ START BOT", font=("Segoe UI", 10, "bold"),
            bg=ACCENT_GREEN, fg="white", activebackground=ACCENT_GREEN_HOVER, activeforeground="white",
            bd=0, relief="flat", padx=15, pady=8, cursor="hand2", command=self.start_bot
        )
        self.btn_start.pack(fill="x", pady=4)
        self.bind_hover(self.btn_start, ACCENT_GREEN, ACCENT_GREEN_HOVER)

        # Pause / Resume Button
        self.btn_pause = tk.Button(
            btn_card, text="⏸ PAUSE BOT", font=("Segoe UI", 10, "bold"),
            bg=ACCENT_YELLOW, fg="white", activebackground="#F1C40F", activeforeground="white",
            bd=0, relief="flat", padx=15, pady=8, cursor="hand2", command=self.pause_bot, state="disabled"
        )
        self.btn_pause.pack(fill="x", pady=4)

        # Stop Button
        self.btn_stop = tk.Button(
            btn_card, text="⏹ STOP BOT", font=("Segoe UI", 10, "bold"),
            bg=ACCENT_RED, fg="white", activebackground=ACCENT_RED_HOVER, activeforeground="white",
            bd=0, relief="flat", padx=15, pady=8, cursor="hand2", command=self.stop_bot, state="disabled"
        )
        self.btn_stop.pack(fill="x", pady=4)
        self.bind_hover(self.btn_stop, ACCENT_RED, ACCENT_RED_HOVER)

        # Secondary utilities row
        utils_row = ttk.Frame(btn_card)
        utils_row.pack(fill="x", pady=(8, 0))
        utils_row.configure(style="Card.TFrame")

        self.btn_detect = tk.Button(
            utils_row, text="🔍 Detect Window", font=("Segoe UI", 9),
            bg=BG_MAIN, fg=TEXT_PRIMARY, activebackground=BG_CONSOLE, activeforeground=TEXT_PRIMARY,
            bd=1, relief="solid", highlightthickness=0, cursor="hand2", command=self.detect_window
        )
        self.btn_detect.pack(side="left", fill="x", expand=True, padx=(0, 4))

        self.btn_test_crop = tk.Button(
            utils_row, text="📸 Test Crop & Calibration", font=("Segoe UI", 9, "bold"),
            bg=ACCENT_CYAN, fg="white", activebackground=ACCENT_CYAN_HOVER, activeforeground="white",
            bd=0, relief="flat", cursor="hand2", command=self.test_crop_popup
        )
        self.btn_test_crop.pack(side="right", fill="x", expand=True, padx=(4, 0))
        self.bind_hover(self.btn_test_crop, ACCENT_CYAN, ACCENT_CYAN_HOVER)

        # Settings Card
        settings_card = ttk.Frame(left_col, style="Card.TFrame", padding=15)
        settings_card.pack(fill="both", expand=True)

        card_title2 = tk.Label(settings_card, text="CALIBRATION & KEYBINDINGS", font=("Segoe UI", 10, "bold"), bg=BG_CARD, fg=ACCENT_BLUE)
        card_title2.pack(anchor="w", pady=(0, 10))

        # Grid for configurations
        grid_frame = ttk.Frame(settings_card)
        grid_frame.pack(fill="x")
        grid_frame.configure(style="Card.TFrame")

        # Window Coords labels
        tk.Label(grid_frame, text="Window Coords:", bg=BG_CARD, fg=TEXT_SECONDARY).grid(row=0, column=0, sticky="w", pady=3)
        self.lbl_coords = tk.Label(grid_frame, text="Not detected", bg=BG_CARD, fg=TEXT_PRIMARY, font=("Consolas", 9))
        self.lbl_coords.grid(row=0, column=1, sticky="w", padx=10, pady=3)

        # Keyboard entries
        tk.Label(grid_frame, text="Key Cast/Reel:", bg=BG_CARD, fg=TEXT_SECONDARY).grid(row=1, column=0, sticky="w", pady=3)
        self.ent_cast = ttk.Entry(grid_frame, width=8)
        self.ent_cast.insert(0, "f")
        self.ent_cast.grid(row=1, column=1, sticky="w", padx=10, pady=3)

        tk.Label(grid_frame, text="Key Close UI (ESC):", bg=BG_CARD, fg=TEXT_SECONDARY).grid(row=2, column=0, sticky="w", pady=3)
        self.ent_close = ttk.Entry(grid_frame, width=8)
        self.ent_close.insert(0, "esc")
        self.ent_close.grid(row=2, column=1, sticky="w", padx=10, pady=3)

        tk.Label(grid_frame, text="Key Steer Left:", bg=BG_CARD, fg=TEXT_SECONDARY).grid(row=3, column=0, sticky="w", pady=3)
        self.ent_left = ttk.Entry(grid_frame, width=8)
        self.ent_left.insert(0, "a")
        self.ent_left.grid(row=3, column=1, sticky="w", padx=10, pady=3)

        tk.Label(grid_frame, text="Key Steer Right:", bg=BG_CARD, fg=TEXT_SECONDARY).grid(row=4, column=0, sticky="w", pady=3)
        self.ent_right = ttk.Entry(grid_frame, width=8)
        self.ent_right.insert(0, "d")
        self.ent_right.grid(row=4, column=1, sticky="w", padx=10, pady=3)

        # AI params divider
        ttk.Separator(grid_frame, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=10)

        # Adaptive AI params
        tk.Label(grid_frame, text="Base Pulse Duration (s):", bg=BG_CARD, fg=TEXT_SECONDARY).grid(row=6, column=0, sticky="w", pady=3)
        self.ent_base_pulse = ttk.Entry(grid_frame, width=8)
        self.ent_base_pulse.insert(0, "0.04")
        self.ent_base_pulse.grid(row=6, column=1, sticky="w", padx=10, pady=3)

        tk.Label(grid_frame, text="Initial Gain (Kp):", bg=BG_CARD, fg=TEXT_SECONDARY).grid(row=7, column=0, sticky="w", pady=3)
        self.ent_kp = ttk.Entry(grid_frame, width=8)
        self.ent_kp.insert(0, "1.0")
        self.ent_kp.grid(row=7, column=1, sticky="w", padx=10, pady=3)

        # Right Column: Live Dashboard
        right_col = ttk.Frame(content_frame)
        right_col.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Dashboard Card
        dash_card = ttk.Frame(right_col, style="Card.TFrame", padding=15)
        dash_card.pack(fill="both", expand=True)

        card_title3 = tk.Label(dash_card, text="LIVE MONITOR", font=("Segoe UI", 10, "bold"), bg=BG_CARD, fg=ACCENT_BLUE)
        card_title3.pack(anchor="w", pady=(0, 15))

        # State label
        state_container = ttk.Frame(dash_card, style="Card.TFrame")
        state_container.pack(fill="x", pady=5)
        tk.Label(state_container, text="Current State:", font=("Segoe UI", 10), bg=BG_CARD, fg=TEXT_SECONDARY).pack(side="left")
        self.lbl_bot_state = tk.Label(state_container, text="IDLE", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=TEXT_MUTED)
        self.lbl_bot_state.pack(side="right")

        # Stats widgets
        stats_frame = ttk.Frame(dash_card, style="Card.TFrame")
        stats_frame.pack(fill="both", expand=True, pady=10)

        # Caught stats
        self.lbl_caught = tk.Label(
            stats_frame, text="FISH CAUGHT\n0", font=("Segoe UI", 14, "bold"),
            bg="#2A3042", fg="#2ECC71", padx=15, pady=15, width=15, relief="flat"
        )
        self.lbl_caught.pack(side="left", fill="both", expand=True, padx=(0, 5), pady=5)

        # Lost stats
        self.lbl_lost = tk.Label(
            stats_frame, text="FISH ESCAPED\n0", font=("Segoe UI", 14, "bold"),
            bg="#2A3042", fg=ACCENT_RED, padx=15, pady=15, width=15, relief="flat"
        )
        self.lbl_lost.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=5)

        # Current AI Steering parameter card
        ai_frame = ttk.Frame(dash_card, style="Card.TFrame")
        ai_frame.pack(fill="x", pady=(10, 0))
        
        tk.Label(ai_frame, text="Adaptive Steer Gain (Kp):", font=("Segoe UI", 10), bg=BG_CARD, fg=TEXT_SECONDARY).pack(side="left")
        self.lbl_ai_kp = tk.Label(ai_frame, text="1.00", font=("Consolas", 14, "bold"), bg=BG_CARD, fg=ACCENT_CYAN)
        self.lbl_ai_kp.pack(side="right")

    def create_log_panel(self):
        # Console Log Panel
        log_frame = ttk.Frame(self.root, padding=(20, 10, 20, 20))
        log_frame.pack(fill="both", expand=True)

        log_lbl = tk.Label(log_frame, text="BOT CONSOLE LOGS", font=("Segoe UI", 10, "bold"), bg=BG_MAIN, fg=ACCENT_BLUE)
        log_lbl.pack(anchor="w", pady=(0, 5))

        self.txt_logs = scrolledtext.ScrolledText(
            log_frame, 
            bg=BG_CONSOLE, 
            fg=TEXT_PRIMARY, 
            insertbackground=TEXT_PRIMARY,
            font=("Consolas", 9), 
            bd=0, 
            padx=10, 
            pady=10
        )
        self.txt_logs.pack(fill="both", expand=True)
        self.append_log("[System] GUI Started successfully. Waiting for commands...")

    def bind_hover(self, widget, normal_bg, hover_bg):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg))

    def append_log(self, text):
        self.txt_logs.configure(state="normal")
        self.txt_logs.insert(tk.END, text + "\n")
        self.txt_logs.see(tk.END)
        self.txt_logs.configure(state="disabled")

    def detect_window(self, silent=False):
        global window_rect, window_title
        try:
            exclude_hwnd = self.root.winfo_id()
        except Exception:
            exclude_hwnd = None
        windows = find_game_window(exclude_hwnd)
        if windows:
            # Prefer the exact match, or take the first matching window
            hwnd, title, rect = windows[0]
            window_rect = rect
            window_title = title
            
            width = rect[2] - rect[0]
            height = rect[3] - rect[1]
            
            self.win_status_var.set(f"Game Detected: {width}x{height}")
            self.win_status_label.config(fg="#2ECC71") # Green
            
            self.lbl_coords.config(text=f"[{rect[0]}, {rect[1]}] -> [{rect[2]}, {rect[3]}] ({width}x{height})")
            self.append_log(f"[System] Located window: '{title}' at screen coordinates {rect}")
            
            if bot_instance:
                bot_instance.update_rois(window_rect)
        else:
            window_rect = None
            window_title = "None"
            self.win_status_var.set("Game Window: NOT DETECTED")
            self.win_status_label.config(fg=ACCENT_RED)
            self.lbl_coords.config(text="Not detected")
            if not silent:
                self.append_log("[System Error] Could not find Neverness to Everness window. Make sure the game is running!")
                messagebox.showwarning(
                    "Window Not Found", 
                    "Could not locate Neverness to Everness window.\n"
                    "Make sure the game is running in windowed or borderless mode."
                )

    def start_bot(self):
        global bot_thread, bot_instance, window_rect
        if bot_instance and bot_instance.running and bot_thread and bot_thread.is_alive():
            # Bot is already running, perhaps just paused. Resume it
            if not bot_instance.active:
                bot_instance.toggle_bot()
                self.btn_pause.config(text="⏸ PAUSE BOT", state="normal")
            return

        # Re-detect window to make sure coordinates are fresh
        self.detect_window(silent=True)
        if not window_rect:
            ans = messagebox.askyesno(
                "Game Window Not Found",
                "Neverness to Everness window was not detected.\n"
                "Would you like to run the bot targeting the absolute primary screen (Full Screen mode) instead?"
            )
            if not ans:
                return
            self.append_log("[System] Starting bot targeting absolute screen coordinates (no offset)...")
        else:
            self.append_log(f"[System] Starting bot targeting window offset: {window_rect}")

        # Set configs from inputs
        import fishing_bot as fb
        fb.KEY_CAST_REEL = self.ent_cast.get()
        fb.KEY_CLOSE_SCREEN = self.ent_close.get()
        fb.KEY_STEER_LEFT = self.ent_left.get()
        fb.KEY_STEER_RIGHT = self.ent_right.get()

        # Instantiate bot core
        bot_instance = FishingBot(
            window_rect=window_rect,
            log_callback=lambda msg: gui_queue.put(('log', msg)),
            status_callback=lambda st: gui_queue.put(('status', st)),
            stats_callback=lambda c, l: gui_queue.put(('stats', (c, l)))
        )
        
        # Apply AI params
        try:
            bot_instance.controller.base_pulse = float(self.ent_base_pulse.get())
            bot_instance.controller.kp = float(self.ent_kp.get())
            bot_instance.controller.initial_kp = float(self.ent_kp.get())
            self.lbl_ai_kp.config(text=f"{bot_instance.controller.kp:.2f}")
        except ValueError:
            self.append_log("[Warning] Invalid AI gain values. Using defaults.")

        # Thread setup
        bot_instance.running = True
        bot_instance.toggle_bot()  # Sets active=True and sets state to CAST_ROD
        bot_thread = threading.Thread(target=bot_instance.run, daemon=True)
        bot_thread.start()

        # Update controls
        self.btn_start.config(state="disabled", bg=BG_CARD, fg=TEXT_MUTED)
        self.btn_pause.config(text="⏸ PAUSE BOT", state="normal")
        self.btn_stop.config(state="normal")
        self.lbl_bot_state.config(text="CAST_ROD", fg="#2ECC71")

    def pause_bot(self):
        global bot_instance
        if bot_instance:
            bot_instance.toggle_bot()
            if bot_instance.active:
                self.btn_pause.config(text="⏸ PAUSE BOT")
                self.lbl_bot_state.config(text=bot_instance.state, fg="#2ECC71")
            else:
                self.btn_pause.config(text="▶ RESUME BOT")
                self.lbl_bot_state.config(text="PAUSED (IDLE)", fg=ACCENT_YELLOW)

    def stop_bot(self):
        global bot_instance, bot_thread
        if bot_instance:
            self.append_log("[System] Stopping bot thread...")
            bot_instance.running = False
            bot_instance.active = False
            bot_instance.inputs.release_all()
            
        # Re-enable Start button
        self.btn_start.config(state="normal", bg=ACCENT_GREEN, fg="white")
        self.btn_pause.config(text="⏸ PAUSE BOT", state="disabled")
        self.btn_stop.config(state="disabled")
        self.lbl_bot_state.config(text="IDLE", fg=TEXT_MUTED)
        self.append_log("[System] Bot thread stopped successfully.")

    def process_queue(self):
        """Processes messages sent by the bot thread in a thread-safe manner."""
        while not gui_queue.empty():
            try:
                msg_type, data = gui_queue.get_nowait()
                if msg_type == 'log':
                    # Parse log for adaptive AI events to update Kp label
                    if "[Adaptive AI]" in data:
                        # Extract the float value of Kp
                        try:
                            parts = data.split("Kp:")
                            if len(parts) > 1:
                                kp_val = float(parts[1].split()[0].strip())
                                self.lbl_ai_kp.config(text=f"{kp_val:.2f}")
                        except Exception:
                            pass
                    self.append_log(data)
                elif msg_type == 'status':
                    self.lbl_bot_state.config(text=data)
                    if data == "FISHING_MINIGAME":
                        self.lbl_bot_state.config(fg="#E0AF68")
                        # Reset Kp display on interface
                        if bot_instance:
                            self.lbl_ai_kp.config(text=f"{bot_instance.controller.kp:.2f}")
                    elif data == "WAITING_FOR_BITE":
                        self.lbl_bot_state.config(fg=ACCENT_BLUE)
                    elif data == "CAST_ROD":
                        self.lbl_bot_state.config(fg="#2ECC71")
                    else:
                        self.lbl_bot_state.config(fg=TEXT_MUTED)
                elif msg_type == 'stats':
                    caught, lost = data
                    self.lbl_caught.config(text=f"FISH CAUGHT\n{caught}")
                    self.lbl_lost.config(text=f"FISH ESCAPED\n{lost}")
            except queue.Empty:
                break
        
        # Recurse
        self.root.after(100, self.process_queue)

    def test_crop_popup(self):
        """
        Grabs a screenshot of the current game bounds and opens a secondary
        window with live crops of the regions (F-Icon, Bar, Success Banner)
        to calibrate offline.
        """
        global window_rect, crop_window
        self.detect_window(silent=True)
        
        # Use full primary screen coordinates if window is not detected
        if not window_rect:
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                w_rect = (0, 0, monitor["width"], monitor["height"])
        else:
            w_rect = window_rect
            
        left, top, right, bottom = w_rect
        width = right - left
        height = bottom - top

        # Setup reference crops
        # Create a temp instance of bot to utilize its scaling methods
        temp_bot = FishingBot(window_rect=w_rect)
        
        with mss.mss() as sct:
            # Capture the entire window/screen bounds
            monitor = {"top": top, "left": left, "width": width, "height": height}
            try:
                screenshot = sct.grab(monitor)
            except Exception as e:
                self.append_log(f"[System Error] Screenshot capture failed: {e}")
                messagebox.showerror("Capture Error", f"Failed to grab screen: {e}")
                return
                
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)

            # Scale crops relative to actual image
            bar_crop = temp_bot.process_screenshot(sct, temp_bot.roi_bar)
            f_crop = temp_bot.process_screenshot(sct, temp_bot.roi_f_icon)
            success_crop = temp_bot.process_screenshot(sct, temp_bot.roi_success)

        # Let's perform analysis on these crops to show feedback
        # 1. F-icon analysis
        hsv_f = cv2.cvtColor(f_crop, cv2.COLOR_BGR2HSV)
        lower_blue = np.array([100, 100, 100])
        upper_blue = np.array([125, 255, 255])
        mask_blue = cv2.inRange(hsv_f, lower_blue, upper_blue)
        y_indices, x_indices = np.where(mask_blue > 0)
        
        bite_analysis = "No blue pixels found."
        ring_complete = "NO"
        if len(x_indices) > 0:
            cx, cy = 67, 35
            l_h = np.sum(x_indices < cx)
            r_h = np.sum(x_indices >= cx)
            t_h = np.sum(y_indices < cy)
            b_h = np.sum(y_indices >= cy)
            bite_analysis = f"Blue Px: L={l_h}, R={r_h}, T={t_h}, B={b_h}"
            if (l_h >= 35) and (r_h >= 35) and (t_h >= 35) and (b_h >= 35):
                ring_complete = "YES (Bite Ready!)"
            else:
                ring_complete = "NO (Partial/Waiting)"

        # 2. Minigame Bar analysis
        hsv_b = cv2.cvtColor(bar_crop, cv2.COLOR_BGR2HSV)
        lower_green = np.array([75, 120, 100])
        upper_green = np.array([90, 255, 255])
        mask_green = cv2.inRange(hsv_b, lower_green, upper_green)
        y_g, x_g = np.where(mask_green > 0)
        
        green_found = "NO"
        green_bounds = "N/A"
        annotated_bar = bar_crop.copy()
        if len(x_g) > 0:
            green_found = "YES"
            g_start, g_end = np.min(x_g), np.max(x_g)
            green_bounds = f"{g_start} to {g_end}"
            # Draw green boundaries on display image
            cv2.line(annotated_bar, (g_start, 0), (g_start, bar_crop.shape[0]), (0, 255, 0), 2)
            cv2.line(annotated_bar, (g_end, 0), (g_end, bar_crop.shape[0]), (0, 255, 0), 2)

        # Indicator analysis
        detected_ind_x = []
        for x in range(50, 310):
            col_matches = 0
            for y in range(11, 19):
                h, s, v = hsv_b[y, x]
                is_yellow = (15 <= h <= 35) and (40 <= s <= 255) and (150 <= v <= 255)
                is_white = (s < 40) and (v > 220)
                if is_yellow or is_white:
                    col_matches += 1
            if col_matches >= 3:
                detected_ind_x.append(x)
        
        ind_found = "NO"
        ind_pos = "N/A"
        if detected_ind_x:
            ind_found = "YES"
            ind_x = int(np.median(detected_ind_x))
            ind_pos = f"X = {ind_x}"
            # Draw red circle at indicator
            cv2.circle(annotated_bar, (ind_x, 15), 4, (0, 0, 255), -1)

        # 3. Success Banner Analysis
        gray_s = cv2.cvtColor(success_crop, cv2.COLOR_BGR2GRAY)
        white_pixels = np.sum(gray_s > 200)
        success_detected = "YES" if white_pixels > 200 else "NO"

        # Create pop-up window
        if crop_window and tk.Toplevel.winfo_exists(crop_window):
            crop_window.destroy()
            
        crop_window = tk.Toplevel(self.root)
        crop_window.title("Visual Calibration Preview")
        crop_window.geometry("500x520")
        crop_window.configure(bg=BG_CARD)
        
        # Prevent window garbage collection for images
        crop_window.images = []

        tk.Label(crop_window, text="CALIBRATION CROPS", font=("Segoe UI", 12, "bold"), bg=BG_CARD, fg=ACCENT_BLUE).pack(pady=10)

        # 1. F-Icon Section
        f_frame = ttk.LabelFrame(crop_window, text="F-Button Detector ROI", padding=5)
        f_frame.pack(fill="x", padx=15, pady=5)
        
        f_photo = self.cv2_to_photo(f_crop)
        crop_window.images.append(f_photo)
        tk.Label(f_frame, image=f_photo).pack(side="left", padx=10)
        
        f_text = f"Blue quadrant analysis:\n{bite_analysis}\nRing Completed: {ring_complete}"
        tk.Label(f_frame, text=f_text, justify="left", font=("Segoe UI", 9)).pack(side="left", padx=10)

        # 2. Minigame Bar Section
        bar_frame = ttk.LabelFrame(crop_window, text="Progress Bar ROI (Steering Target)", padding=5)
        bar_frame.pack(fill="x", padx=15, pady=5)
        
        bar_photo = self.cv2_to_photo(annotated_bar)
        crop_window.images.append(bar_photo)
        tk.Label(bar_frame, image=bar_photo).pack(side="top", pady=5)
        
        bar_text = f"Green Zone Detected: {green_found} (Bounds: {green_bounds})\nIndicator Found: {ind_found} ({ind_pos})"
        tk.Label(bar_frame, text=bar_text, justify="center", font=("Segoe UI", 9)).pack(side="top", pady=5)

        # 3. Success Banner Section
        success_frame = ttk.LabelFrame(crop_window, text="Success Screen Banner ROI", padding=5)
        success_frame.pack(fill="x", padx=15, pady=5)
        
        success_photo = self.cv2_to_photo(success_crop)
        crop_window.images.append(success_photo)
        tk.Label(success_frame, image=success_photo).pack(side="left", padx=10)
        
        success_text = f"White Pixels (Threshold > 200): {white_pixels}\nSuccess Detected: {success_detected}"
        tk.Label(success_frame, text=success_text, justify="left", font=("Segoe UI", 9)).pack(side="left", padx=10)

        # Close button
        tk.Button(
            crop_window, text="Close Preview", bg=BG_MAIN, fg=TEXT_PRIMARY, bd=1, relief="solid",
            cursor="hand2", command=crop_window.destroy, padx=15, pady=5
        ).pack(pady=15)

    def cv2_to_photo(self, cv_img):
        """Converts BGR OpenCV image to ImageTk PhotoImage."""
        rgb_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        # Scale up slightly for preview visibility if very small
        h, w = rgb_img.shape[:2]
        if h < 80:
            scale = 2.0
            rgb_img = cv2.resize(rgb_img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_NEAREST)
        pil_img = Image.fromarray(rgb_img)
        return ImageTk.PhotoImage(pil_img)


if __name__ == "__main__":
    # Ensure executing as administrator check (optional warning)
    import ctypes
    is_admin = False
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        pass
        
    root = tk.Tk()
    gui = FishingBotGUI(root)
    
    if not is_admin:
        gui.append_log("[WARNING] The script is not running as ADMINISTRATOR.")
        gui.append_log("Keyboard input simulation may fail inside the game window!")
        
    root.mainloop()
