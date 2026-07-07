import cv2
import numpy as np
import mss
import time
import pydirectinput
import keyboard
import sys
import math
import random
import os
import json

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
F_ICON_REF = {"x1": 917, "y1": 350, "x2": 1017, "y2": 420}
# Success Screen crop ROI
SUCCESS_REF = {"x1": 380, "y1": 385, "x2": 640, "y2": 420}

def load_config():
    global BAR_REF, F_ICON_REF, SUCCESS_REF
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                data = json.load(f)
                if "BAR_REF" in data: BAR_REF = data["BAR_REF"]
                if "F_ICON_REF" in data: F_ICON_REF = data["F_ICON_REF"]
                if "SUCCESS_REF" in data: SUCCESS_REF = data["SUCCESS_REF"]
        except Exception as e:
            print(f"[Error] Failed to load config.json: {e}")

def save_config():
    data = {
        "BAR_REF": BAR_REF,
        "F_ICON_REF": F_ICON_REF,
        "SUCCESS_REF": SUCCESS_REF
    }
    try:
        with open("config.json", "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"[Error] Failed to save config.json: {e}")

load_config()


class SimpleNeuralNetwork:
    """A basic 3-layer Feedforward Neural Network for the agent."""
    def __init__(self, input_size=3, hidden_size=5, output_size=3, weights=None):
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.output_size = output_size
        
        if weights is not None:
            self.weights1 = weights[0].copy()
            self.bias1 = weights[1].copy()
            self.weights2 = weights[2].copy()
            self.bias2 = weights[3].copy()
        else:
            # Initialize random weights and biases
            self.weights1 = [[random.uniform(-1, 1) for _ in range(hidden_size)] for _ in range(input_size)]
            self.bias1 = [random.uniform(-1, 1) for _ in range(hidden_size)]
            self.weights2 = [[random.uniform(-1, 1) for _ in range(output_size)] for _ in range(hidden_size)]
            self.bias2 = [random.uniform(-1, 1) for _ in range(output_size)]
            
    def to_dict(self):
        return {
            "weights1": self.weights1,
            "bias1": self.bias1,
            "weights2": self.weights2,
            "bias2": self.bias2
        }

    def from_dict(self, data):
        self.weights1 = data["weights1"]
        self.bias1 = data["bias1"]
        self.weights2 = data["weights2"]
        self.bias2 = data["bias2"]
            
    def feed_forward(self, inputs):
        # Hidden layer
        hidden = []
        for j in range(self.hidden_size):
            val = sum(inputs[i] * self.weights1[i][j] for i in range(self.input_size)) + self.bias1[j]
            # Tanh activation function
            hidden.append(math.tanh(val))
            
        # Output layer
        outputs = []
        for k in range(self.output_size):
            val = sum(hidden[j] * self.weights2[j][k] for j in range(self.hidden_size)) + self.bias2[k]
            outputs.append(val)  # Linear output, will take argmax
            
        return outputs

    def get_genome(self):
        """Flattens the network weights and biases into a single list."""
        genome = []
        for row in self.weights1:
            genome.extend(row)
        genome.extend(self.bias1)
        for row in self.weights2:
            genome.extend(row)
        genome.extend(self.bias2)
        return genome

    def set_genome(self, genome):
        """Reconstructs the network weights from a flat list."""
        idx = 0
        for i in range(self.input_size):
            for j in range(self.hidden_size):
                self.weights1[i][j] = genome[idx]
                idx += 1
        for j in range(self.hidden_size):
            self.bias1[j] = genome[idx]
            idx += 1
        for j in range(self.hidden_size):
            for k in range(self.output_size):
                self.weights2[j][k] = genome[idx]
                idx += 1
        for k in range(self.output_size):
            self.bias2[k] = genome[idx]
            idx += 1


class InputController:
    """Manages key states to prevent spamming keyDown and keyUp commands."""
    def __init__(self):
        self.keys = {KEY_STEER_LEFT: False, KEY_STEER_RIGHT: False}

    def press(self, key, duration=0.08):
        pydirectinput.keyDown(key)
        time.sleep(duration)
        pydirectinput.keyUp(key)

    def click_safe_area(self, window_rect):
        """Clicks a safe area (top-left) to close screens that don't accept ESC."""
        if window_rect:
            x = window_rect[0] + 100
            y = window_rect[1] + 100
            pydirectinput.click(x=int(x), y=int(y))
        else:
            pydirectinput.click(100, 100)

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
    def __init__(self, window_rect=None, log_callback=None, status_callback=None, stats_callback=None, steering_mode="Adaptive PD"):
        self.inputs = InputController()
        self.active = False
        self.running = True
        self.state = "IDLE"
        self.consecutive_no_minigame = 0
        self.last_state_change = time.time()
        
        self.log_callback = log_callback
        self.status_callback = status_callback
        self.stats_callback = stats_callback
        self.caught_count = 0
        self.lost_count = 0
        
        self.steering_mode = steering_mode  # "Adaptive PD" or "Neural Network (Trained)"
        self.nn = None
        
        # Initialize adaptive AI controller
        from adaptive_controller import AdaptiveController
        self.controller = AdaptiveController()
        
        # Velocity and timing state tracking for NN inputs
        self.last_sim_x = None
        self.last_sim_target_x = None
        self.last_update_time = None
        
        # Coordinates and ROI setup
        self.window_rect = window_rect
        self.update_rois(window_rect)

    def log(self, message):
        """Helper to print logs or send them to a GUI callback."""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)

    def update_rois(self, window_rect):
        """Updates ROIs from global references based on the provided window_rect"""
        self.window_rect = window_rect
        if window_rect:
            left, top, right, bottom = window_rect
            width = right - left
            height = bottom - top
            
            # Re-scale from references
            self.roi_bar = self._scale_roi_with_offset(BAR_REF, left, top, width, height)
            self.roi_f_icon = self._scale_roi_with_offset(F_ICON_REF, left, top, width, height)
            self.roi_success = self._scale_roi_with_offset(SUCCESS_REF, left, top, width, height)
        else:
            self.roi_bar = self._scale_roi(BAR_REF)
            self.roi_f_icon = self._scale_roi(F_ICON_REF)
            self.roi_success = self._scale_roi(SUCCESS_REF)

    def _scale_roi(self, ref_roi):
        """Scales reference ROI coordinates to native screen resolution."""
        x1 = int(ref_roi["x1"] * SCREEN_W / REF_W)
        y1 = int(ref_roi["y1"] * SCREEN_H / REF_H)
        x2 = int(ref_roi["x2"] * SCREEN_W / REF_W)
        y2 = int(ref_roi["y2"] * SCREEN_H / REF_H)
        
        ref_w = ref_roi["x2"] - ref_roi["x1"]
        ref_h = ref_roi["y2"] - ref_roi["y1"]
        
        return {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "ref_w": ref_w, "ref_h": ref_h}

    def _scale_roi_with_offset(self, ref_roi, offset_x, offset_y, width, height):
        """Scales reference ROI coordinates to a window rect offset."""
        x1 = offset_x + int(ref_roi["x1"] * width / REF_W)
        y1 = offset_y + int(ref_roi["y1"] * height / REF_H)
        x2 = offset_x + int(ref_roi["x2"] * width / REF_W)
        y2 = offset_y + int(ref_roi["y2"] * height / REF_H)
        
        ref_w = ref_roi["x2"] - ref_roi["x1"]
        ref_h = ref_roi["y2"] - ref_roi["y1"]
        
        return {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "ref_w": ref_w, "ref_h": ref_h}

    def toggle_bot(self):
        self.active = not self.active
        self.inputs.release_all()
        if self.active:
            self.log("\n>>> BOT STARTED! Standing at a fishing spot. <<<")
            self.log("Waiting 1 second for you to focus the game window...")
            time.sleep(1.0)
            self.set_state("CAST_ROD")
        else:
            self.log("\n>>> BOT PAUSED! <<<")
            self.set_state("IDLE")

    def set_state(self, new_state):
        if self.state != new_state:
            self.log(f"State transition: {self.state} -> {new_state}")
            self.state = new_state
            self.last_state_change = time.time()
            if self.status_callback:
                self.status_callback(new_state)
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

    def load_nn(self):
        if os.path.exists("ai_neural_net.json"):
            try:
                with open("ai_neural_net.json", "r") as f:
                    data = json.load(f)
                nn = SimpleNeuralNetwork()
                nn.from_dict(data)
                self.log("[System] Loaded Neural Network weights from 'ai_neural_net.json' successfully.")
                return nn
            except Exception as e:
                self.log(f"[Error] Failed to load neural network weights: {e}")
        else:
            self.log("[Error] 'ai_neural_net.json' not found! Train the AI first using the simulator.")
        return None

    def run(self):
        if self.steering_mode == "Neural Network (Trained)":
            self.nn = self.load_nn()
            if self.nn is None:
                self.log("[Warning] Falling back to Adaptive PD steering.")
                self.steering_mode = "Adaptive PD"

        self.log("=" * 60)
        self.log("          NTE AUTOMATIC FISHING BOT (ADAPTIVE AI)")
        self.log("=" * 60)
        self.log("Instructions:")
        if self.window_rect:
            self.log(f"  Game window coordinates detected: {self.window_rect}")
        else:
            self.log(f"  Run the game in {SCREEN_W}x{SCREEN_H} borderless/windowed mode.")
        self.log("  Position your character at a fishing spot.")
        self.log("  Run this script as ADMINISTRATOR.")
        self.log(f"  Press [{HOTKEY_TOGGLE.upper()}] to Start / Pause the bot.")
        self.log(f"  Press [{HOTKEY_EXIT.upper()}] to Stop the bot and exit.")
        self.log("=" * 60)
        self.log("Status: WAITING FOR START...")

        # If not running inside GUI thread, handle hotkeys
        if not self.log_callback:
            keyboard.add_hotkey(HOTKEY_TOGGLE, self.toggle_bot)
        
        # Main execution loop
        with mss.mss() as sct:
            fps_time = time.time()
            fps_count = 0
            
            # If running in GUI, we handle termination externally, otherwise check hotkey
            while self.running and (self.log_callback or not keyboard.is_pressed(HOTKEY_EXIT)):
                # Calculate processing FPS
                fps_count += 1
                if time.time() - fps_time >= 2.0:
                    fps = fps_count / (time.time() - fps_time)
                    if self.active and not self.log_callback:
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
                    
                    if white_pixels > 300:
                        self.log(f"\n[Warning] Victory screen is still open (White px: {white_pixels})! Pressing ESC and clicking...")
                        self.inputs.press(KEY_CLOSE_SCREEN)
                        self.inputs.click_safe_area(self.window_rect)
                        time.sleep(2.0)  # Wait for it to close
                        continue  # Skip casting and re-evaluate on the next iteration
                        
                    self.log("Casting rod... (pressing F)")
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
                    
                    # Check quadrant distribution around the white hook icon to verify it's a complete ring
                    if len(x_indices) > 0:
                        # Find the white hook icon to use as center
                        gray_f = cv2.cvtColor(f_crop, cv2.COLOR_BGR2GRAY)
                        wy, wx = np.where(gray_f > 200)
                        if len(wx) > 5:
                            center_x = int(np.median(wx))
                            center_y = int(np.median(wy))
                        else:
                            center_x, center_y = 50, 35
                            
                        left_half = np.sum(x_indices < center_x)
                        right_half = np.sum(x_indices >= center_x)
                        top_half = np.sum(y_indices < center_y)
                        bottom_half = np.sum(y_indices >= center_y)
                        
                        # A complete circle will have high counts in all 4 quadrants (at least 75 px each)
                        if (left_half >= 75) and (right_half >= 75) and (top_half >= 75) and (bottom_half >= 75):
                            self.log(f"\n[BITE DETECTED!] F-icon blue ring complete. (L:{left_half}, R:{right_half}, T:{top_half}, B:{bottom_half})")
                            self.inputs.press(KEY_CAST_REEL)
                            self.controller.reset()  # Reset adaptive AI controller for a new fish
                            self.last_sim_x = None
                            self.last_sim_target_x = None
                            self.last_update_time = None
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
                            self.log("\nMinigame UI disappeared. Checking success...")
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
                        
                        if self.steering_mode == "Neural Network (Trained)" and self.nn is not None:
                            # Neural Network Steering Mode
                            current_time = time.time()
                            # Convert coordinates to simulator's normalized 0-100 system
                            sim_x = (ind_x - 50.0) / 260.0 * 100.0
                            green_center = (green_start + green_end) / 2.0
                            sim_target_x = (green_center - 50.0) / 260.0 * 100.0
                            
                            if self.last_update_time is not None and current_time > self.last_update_time:
                                dt = current_time - self.last_update_time
                                dt = max(0.005, min(0.1, dt))
                                v = (sim_x - self.last_sim_x) / dt
                                target_v = (sim_target_x - self.last_sim_target_x) / dt
                            else:
                                v = 0.0
                                target_v = 0.0
                                
                            self.last_sim_x = sim_x
                            self.last_sim_target_x = sim_target_x
                            self.last_update_time = current_time
                            
                            # Clamp velocities
                            v = max(-30.0, min(30.0, v))
                            target_v = max(-30.0, min(30.0, target_v))
                            
                            # Normalize inputs for the feed forward
                            relative_error = (sim_x - sim_target_x) / 50.0
                            norm_v = v / 15.0
                            norm_target_v = target_v / 15.0
                            
                            inputs = [relative_error, norm_v, norm_target_v]
                            outputs = self.nn.feed_forward(inputs)
                            
                            # Output action selection
                            act_idx = outputs.index(max(outputs))
                            if act_idx == 0:
                                steer_key = 'a'
                            elif act_idx == 1:
                                steer_key = 'd'
                            else:
                                steer_key = None
                                
                            # Apply actions continuously
                            if steer_key == 'a':
                                self.inputs.set_key(KEY_STEER_RIGHT, False)
                                self.inputs.set_key(KEY_STEER_LEFT, True)
                            elif steer_key == 'd':
                                self.inputs.set_key(KEY_STEER_LEFT, False)
                                self.inputs.set_key(KEY_STEER_RIGHT, True)
                            else:
                                self.inputs.set_key(KEY_STEER_LEFT, False)
                                self.inputs.set_key(KEY_STEER_RIGHT, False)
                        else:
                            # Adaptive PD Steering Mode (default)
                            steer_key, pulse_duration, ai_log = self.controller.update(ind_x, green_start, green_end)
                            if ai_log:
                                self.log(ai_log)
                                
                            # Apply pulsed key command
                            if steer_key == 'd':
                                self.inputs.set_key(KEY_STEER_LEFT, False)
                                self.inputs.set_key(KEY_STEER_RIGHT, True)
                                if pulse_duration > 0:
                                    time.sleep(pulse_duration)
                                    self.inputs.set_key(KEY_STEER_RIGHT, False)
                            elif steer_key == 'a':
                                self.inputs.set_key(KEY_STEER_RIGHT, False)
                                self.inputs.set_key(KEY_STEER_LEFT, True)
                                if pulse_duration > 0:
                                    time.sleep(pulse_duration)
                                    self.inputs.set_key(KEY_STEER_LEFT, False)
                            else:
                                self.inputs.set_key(KEY_STEER_LEFT, False)
                                self.inputs.set_key(KEY_STEER_RIGHT, False)
                    else:
                        # Indicator not found -> Release keys to avoid drift
                        self.inputs.set_key(KEY_STEER_LEFT, False)
                        self.inputs.set_key(KEY_STEER_RIGHT, False)
                        self.last_update_time = None

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
                        
                        if white_pixels > 300:
                            success_detected = True
                            self.caught_count += 1
                            self.log(f"\n[FISH CAUGHT!] Victory screen detected! (White px: {white_pixels}) | Total caught: {self.caught_count}")
                            if self.stats_callback:
                                self.stats_callback(self.caught_count, self.lost_count)
                            break
                        time.sleep(0.1)
                        
                    if success_detected:
                        self.log(f"Closing victory screen... (pressing {KEY_CLOSE_SCREEN.upper()} and clicking)")
                        self.inputs.press(KEY_CLOSE_SCREEN)
                        self.inputs.click_safe_area(self.window_rect)
                        time.sleep(4.5)  # Wait for screen close animation to complete
                    else:
                        self.lost_count += 1
                        self.log(f"\n[FISH ESCAPED / NOT SUCCESSFUL] (Victory screen did not appear) | Total lost: {self.lost_count}")
                        if self.stats_callback:
                            self.stats_callback(self.caught_count, self.lost_count)
                        time.sleep(1.0)
                        
                    self.set_state("CAST_ROD")

                # Throttle processing loop slightly to reduce CPU usage
                time.sleep(0.01)

        self.inputs.release_all()
        self.log("\n>>> BOT TERMINATED SUCCESSFULLY! <<<")


if __name__ == "__main__":
    bot = FishingBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        print("\nScript interrupted manually.")
        bot.inputs.release_all()
        sys.exit(0)
