import cv2
import numpy as np
import mss
import time
import pydirectinput
import keyboard
import sys

# --- CONFIGURATION ---
# The script will automatically scale the detection regions based on these dimensions.
# Set this to the resolution of your game window.
SCREEN_W = 3440
SCREEN_H = 1440

# Reference resolution on which coordinates were measured
REF_W = 1024
REF_H = 428

# Key bindings
KEY_CAST_REEL = 'f'
KEY_CLOSE_SCREEN = 'esc'  # Can be 'f' or 'esc'
KEY_STEER_LEFT = 'a'
KEY_STEER_RIGHT = 'd'

# Hotkeys (Global)
HOTKEY_TOGGLE = 'f9'
HOTKEY_EXIT = 'f10'

# Fail-safe configurations for PyDirectInput
pydirectinput.FAILSAFE = True
pydirectinput.PAUSE = 0.01

# --- REFERENCE REGIONS OF INTEREST (ROI) in 1024x428 space ---
# Progress Bar crop ROI
BAR_REF = {"x1": 350, "y1": 15, "x2": 674, "y2": 60}
# F-icon button crop ROI (detecting the blue ring)
F_ICON_REF = {"x1": 900, "y1": 350, "x2": 1000, "y2": 420}
# Success Screen crop ROI
SUCCESS_REF = {"x1": 380, "y1": 385, "x2": 640, "y2": 420}


class InputController:
    """Manages key states to prevent spamming keyDown and keyUp commands."""
    def __init__(self):
        self.keys = {KEY_STEER_LEFT: False, KEY_STEER_RIGHT: False}

    def press(self, key):
        pydirectinput.press(key)

    def set_key(self, key, press_down):
        if key not in self.keys:
            return
        
        if press_down and not self.keys[key]:
            pydirectinput.keyDown(key)
            self.keys[key] = True
        elif not press_down and self.keys[key]:
            pydirectinput.keyUp(key)
            self.keys[key] = False

    def release_all(self):
        for key in list(self.keys.keys()):
            if self.keys[key]:
                pydirectinput.keyUp(key)
                self.keys[key] = False


class FishingBot:
    def __init__(self):
        self.inputs = InputController()
        self.active = False
        self.state = "IDLE"
        self.consecutive_no_minigame = 0
        self.last_state_change = time.time()
        
        # Calculate native screen ROIs
        self.roi_bar = self._scale_roi(BAR_REF)
        self.roi_f_icon = self._scale_roi(F_ICON_REF)
        self.roi_success = self._scale_roi(SUCCESS_REF)

    def _scale_roi(self, ref_roi):
        """Scales reference ROI coordinates to native screen resolution."""
        x1 = int(ref_roi["x1"] * SCREEN_W / REF_W)
        y1 = int(ref_roi["y1"] * SCREEN_H / REF_H)
        x2 = int(ref_roi["x2"] * SCREEN_W / REF_W)
        y2 = int(ref_roi["y2"] * SCREEN_H / REF_H)
        
        # Width and height at reference resolution
        ref_w = ref_roi["x2"] - ref_roi["x1"]
        ref_h = ref_roi["y2"] - ref_roi["y1"]
        
        return {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "ref_w": ref_w, "ref_h": ref_h}

    def toggle_bot(self):
        self.active = not self.active
        self.inputs.release_all()
        if self.active:
            print("\n>>> BOT STARTED! Standing at a fishing spot. <<<")
            self.set_state("CAST_ROD")
        else:
            print("\n>>> BOT PAUSED! <<<")
            self.set_state("IDLE")

    def set_state(self, new_state):
        if self.state != new_state:
            print(f"State transition: {self.state} -> {new_state}")
            self.state = new_state
            self.last_state_change = time.time()
            if new_state == "IDLE":
                self.inputs.release_all()

    def process_screenshot(self, sct, roi):
        """Captures a specific ROI from the screen and resizes it to its reference resolution."""
        monitor = {"top": roi["y1"], "left": roi["x1"], "width": roi["x2"] - roi["x1"], "height": roi["y2"] - roi["y1"]}
        screenshot = sct.grab(monitor)
        
        # Convert to numpy array
        img = np.array(screenshot)
        # Convert BGRA to BGR
        img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        
        # Resize to reference width/height for normalized template checks
        resized = cv2.resize(img, (roi["ref_w"], roi["ref_h"]), interpolation=cv2.INTER_LINEAR)
        return resized

    def run(self):
        print("=" * 60)
        print("          NTE AUTOMATIC FISHING BOT (3440x1440)")
        print("=" * 60)
        print(f"Instructions:")
        print(f"  1. Run the game in {SCREEN_W}x{SCREEN_H} borderless/windowed mode.")
        print(f"  2. Position your character at a fishing spot.")
        print(f"  3. Run this script as ADMINISTRATOR.")
        print(f"  4. Press [{HOTKEY_TOGGLE.upper()}] to Start / Pause the bot.")
        print(f"  5. Press [{HOTKEY_EXIT.upper()}] to Stop the bot and exit.")
        print("=" * 60)
        print("Status: WAITING FOR START...")

        keyboard.add_hotkey(HOTKEY_TOGGLE, self.toggle_bot)
        
        # Main execution loop
        with mss.mss() as sct:
            fps_time = time.time()
            fps_count = 0
            
            while not keyboard.is_pressed(HOTKEY_EXIT):
                # Calculate processing FPS
                fps_count += 1
                if time.time() - fps_time >= 2.0:
                    fps = fps_count / (time.time() - fps_time)
                    if self.active:
                        print(f"[Bot Active] Current State: {self.state} | Processing FPS: {fps:.1f}", end='\r')
                    fps_count = 0
                    fps_time = time.time()

                if not self.active:
                    time.sleep(0.1)
                    continue

                # --- STATE MACHINE ---
                
                if self.state == "CAST_ROD":
                    # Safety check: Verify the victory screen is actually closed before casting
                    success_crop = self.process_screenshot(sct, self.roi_success)
                    gray = cv2.cvtColor(success_crop, cv2.COLOR_BGR2GRAY)
                    white_pixels = np.sum(gray > 200)
                    
                    if white_pixels > 200:
                        print(f"\n[Warning] Victory screen is still open (White px: {white_pixels})! Pressing ESC again...")
                        self.inputs.press(KEY_CLOSE_SCREEN)
                        time.sleep(2.0)  # Wait for it to close
                        continue  # Skip casting and re-evaluate on the next iteration
                        
                    print("Casting rod... (pressing F)")
                    self.inputs.press(KEY_CAST_REEL)
                    time.sleep(1.5)  # Wait for cast animation
                    self.set_state("WAITING_FOR_BITE")

                elif self.state == "WAITING_FOR_BITE":
                    # Capture F-icon ROI
                    f_crop = self.process_screenshot(sct, self.roi_f_icon)
                    
                    # Convert to HSV
                    hsv = cv2.cvtColor(f_crop, cv2.COLOR_BGR2HSV)
                    
                    # Mask blue pixels (Hue: 100 to 125, Saturation: 100 to 255, Value: 100 to 255)
                    lower_blue = np.array([100, 100, 100])
                    upper_blue = np.array([125, 255, 255])
                    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
                    
                    y_indices, x_indices = np.where(mask_blue > 0)
                    
                    # Check quadrant distribution around center (67, 35) to verify it's a complete ring
                    if len(x_indices) > 0:
                        center_x = 67
                        center_y = 35
                        
                        left_half = np.sum(x_indices < center_x)
                        right_half = np.sum(x_indices >= center_x)
                        top_half = np.sum(y_indices < center_y)
                        bottom_half = np.sum(y_indices >= center_y)
                        
                        # A complete circle will have high counts in all 4 quadrants (at least 35 px each)
                        if (left_half >= 35) and (right_half >= 35) and (top_half >= 35) and (bottom_half >= 35):
                            print(f"\n[BITE DETECTED!] F-icon blue ring complete. (L:{left_half}, R:{right_half}, T:{top_half}, B:{bottom_half})")
                            self.inputs.press(KEY_CAST_REEL)
                            self.set_state("FISHING_MINIGAME")
                            self.consecutive_no_minigame = 0
                            time.sleep(0.5)  # Wait for minigame UI to load

                elif self.state == "FISHING_MINIGAME":
                    # Capture progress bar ROI
                    bar_crop = self.process_screenshot(sct, self.roi_bar)
                    
                    # Convert to HSV and grayscale
                    hsv = cv2.cvtColor(bar_crop, cv2.COLOR_BGR2HSV)
                    
                    # 1. Detect Green Zone bounds
                    lower_green = np.array([75, 120, 100])
                    upper_green = np.array([90, 255, 255])
                    mask_green = cv2.inRange(hsv, lower_green, upper_green)
                    y_g, x_g = np.where(mask_green > 0)
                    
                    # If green zone is not detected, we count frames.
                    # If it's missing for too long, the minigame is over.
                    if len(x_g) == 0:
                        self.consecutive_no_minigame += 1
                        if self.consecutive_no_minigame > 8:
                            print("\nMinigame UI disappeared. Checking success...")
                            self.inputs.release_all()
                            self.set_state("CHECK_SUCCESS")
                        continue
                    
                    # Green zone boundaries
                    self.consecutive_no_minigame = 0
                    green_start = np.min(x_g)
                    green_end = np.max(x_g)
                    
                    # 2. Detect Indicator position
                    # We scan only within the active horizontal channel Y: [11, 18], X: [50, 310]
                    detected_ind_x = []
                    for x in range(50, 310):
                        col_matches = 0
                        for y in range(11, 19):
                            h, s, v = hsv[y, x]
                            is_yellow = (15 <= h <= 35) and (40 <= s <= 255) and (150 <= v <= 255)
                            is_white = (s < 40) and (v > 220)
                            if is_yellow or is_white:
                                col_matches += 1
                        if col_matches >= 3:
                            detected_ind_x.append(x)
                            
                    # 3. Decision making
                    if detected_ind_x:
                        ind_x = int(np.median(detected_ind_x))
                        
                        # Check where indicator is relative to the green bar
                        if ind_x < green_start:
                            # Too far left -> Pull right (Press D, release A)
                            self.inputs.set_key(KEY_STEER_LEFT, False)
                            self.inputs.set_key(KEY_STEER_RIGHT, True)
                        elif ind_x > green_end:
                            # Too far right -> Pull left (Press A, release D)
                            self.inputs.set_key(KEY_STEER_RIGHT, False)
                            self.inputs.set_key(KEY_STEER_LEFT, True)
                        else:
                            # Inside green zone -> Release both keys to float
                            self.inputs.set_key(KEY_STEER_LEFT, False)
                            self.inputs.set_key(KEY_STEER_RIGHT, False)
                    else:
                        # Indicator not found -> Release keys to avoid random pulling
                        self.inputs.set_key(KEY_STEER_LEFT, False)
                        self.inputs.set_key(KEY_STEER_RIGHT, False)

                elif self.state == "CHECK_SUCCESS":
                    self.inputs.release_all()
                    
                    # Wait for screen transition and poll for the victory screen for up to 4.0 seconds
                    success_detected = False
                    start_check = time.time()
                    
                    while time.time() - start_check < 4.0:
                        # Capture success screen text ROI
                        success_crop = self.process_screenshot(sct, self.roi_success)
                        gray = cv2.cvtColor(success_crop, cv2.COLOR_BGR2GRAY)
                        white_pixels = np.sum(gray > 200)
                        
                        if white_pixels > 200:
                            success_detected = True
                            print(f"\n[FISH CAUGHT!] Victory screen detected! (White px: {white_pixels})")
                            break
                        time.sleep(0.1)
                        
                    if success_detected:
                        print(f"Closing victory screen... (pressing {KEY_CLOSE_SCREEN.upper()})")
                        self.inputs.press(KEY_CLOSE_SCREEN)
                        time.sleep(4.5)  # Wait for screen close animation to complete
                    else:
                        print("\n[FISH ESCAPED / NOT SUCCESSFUL] (Victory screen did not appear)")
                        time.sleep(1.0)
                        
                    self.set_state("CAST_ROD")

                # Throttle processing loop slightly to reduce CPU usage
                time.sleep(0.01)

        self.inputs.release_all()
        print("\n>>> BOT TERMINATED SUCCESSFULLY! <<<")


if __name__ == "__main__":
    bot = FishingBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\nScript interrupted manually.")
        bot.inputs.release_all()
        sys.exit(0)
