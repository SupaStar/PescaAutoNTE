import time
import json
import os

class AdaptiveController:
    """
    Adaptive self-tuning PD controller for the fishing minigame.
    Instead of continuous press/release, it pulses key inputs.
    It adjusts the proportional gain (Kp) online by detecting sluggish response or oscillation.
    Saves and loads its learned gains to/from a local JSON file (ai_config.json).
    """
    def __init__(self, base_pulse=0.04, initial_kp=1.0, initial_kd=0.15):
        self.base_pulse = base_pulse  # Unit of pulse duration (seconds)
        self.initial_kp = initial_kp
        self.initial_kd = initial_kd
        
        self.kp = initial_kp
        self.kd = initial_kd
        
        # Tracking states
        self.last_error_norm = 0.0
        self.last_side = None
        self.consecutive_side_frames = 0
        self.last_cross_time = time.time()
        
        # Load learned configuration from disk if available
        self.load_config()
        
    def load_config(self):
        """Loads the saved Kp baseline from the local config file."""
        config_path = "ai_config.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    data = json.load(f)
                    val = float(data.get("initial_kp", self.initial_kp))
                    # Clamp to safe boundaries
                    self.initial_kp = max(0.4, min(3.5, val))
                    self.kp = self.initial_kp
            except Exception:
                pass  # Fall back to default if file is corrupt or unreadable

    def save_config(self):
        """Saves the learned Kp baseline to the local config file."""
        config_path = "ai_config.json"
        # Update our long-term baseline initial_kp towards the currently learned kp
        # Uses exponential smoothing: 80% baseline, 20% newly learned value
        self.initial_kp = 0.8 * self.initial_kp + 0.2 * self.kp
        self.initial_kp = max(0.4, min(3.5, self.initial_kp))
        
        try:
            with open(config_path, "w") as f:
                json.dump({"initial_kp": self.initial_kp}, f, indent=4)
        except Exception:
            pass  # Fail silently if cannot write to disk

    def reset(self):
        """Resets transient state variables for a new minigame session."""
        self.last_error_norm = 0.0
        self.last_side = None
        self.consecutive_side_frames = 0
        self.last_cross_time = time.time()
        
        # Save learned parameters to disk
        self.save_config()
        
        # Revert Kp slightly towards baseline so it doesn't carry over extreme values
        self.kp = (self.kp + self.initial_kp) / 2.0
        
    def update(self, ind_x, green_start, green_end):
        """
        Processes current game frame coordinates and determines steering actions.
        Returns:
            steer_key (str or None): 'a', 'd', or None.
            pulse_duration (float): How long the key should be pressed.
            log_msg (str or None): Message highlighting AI learning adjustments.
        """
        green_center = (green_start + green_end) / 2.0
        # Avoid division by zero
        green_half_width = max(1.0, (green_end - green_start) / 2.0)
        
        # Normalized error: -1.0 is left edge of green bar, +1.0 is right edge of green bar
        error_norm = (ind_x - green_center) / green_half_width
        
        # Derivative of error (rate of change)
        error_diff = error_norm - self.last_error_norm
        self.last_error_norm = error_norm
        
        current_time = time.time()
        log_msg = None
        
        # 1. Determine direction to steer
        # If we are to the left of the center (negative error_norm), we steer right ('d')
        # If we are to the right of the center (positive error_norm), we steer left ('a')
        # We apply a small deadband of +/- 0.15 (15% from center) to prevent unnecessary small inputs
        if error_norm < -0.15:
            direction = 'right'
            steer_key = 'd'
        elif error_norm > 0.15:
            direction = 'left'
            steer_key = 'a'
        else:
            direction = 'none'
            steer_key = None
            
        # 2. Online Adaptation (Learning)
        if steer_key is not None:
            # We only track side change when we are actively steering and outside the green zone
            if abs(error_norm) > 1.0:
                if self.last_side is None:
                    self.last_side = direction
                    self.consecutive_side_frames = 1
                    self.last_cross_time = current_time
                elif self.last_side != direction:
                    # Side changed (crossed center) -> Check for oscillation
                    time_since_cross = current_time - self.last_cross_time
                    if time_since_cross < 0.8:  # Crossed and overshot quickly (within 800ms)
                        old_kp = self.kp
                        self.kp = max(0.4, self.kp * 0.80)  # Reduce Kp by 20%
                        log_msg = f"[Adaptive AI] Oscillation detected (overshot in {time_since_cross:.2f}s). Damping Kp: {old_kp:.2f} -> {self.kp:.2f}"
                    
                    self.last_side = direction
                    self.consecutive_side_frames = 1
                    self.last_cross_time = current_time
                else:
                    # Same side -> Check for sluggish response
                    self.consecutive_side_frames += 1
                    if self.consecutive_side_frames >= 6:
                        old_kp = self.kp
                        self.kp = min(3.5, self.kp * 1.15)  # Increase Kp by 15%
                        log_msg = f"[Adaptive AI] Sluggish response (stuck on {direction}). Increasing Kp: {old_kp:.2f} -> {self.kp:.2f}"
                        self.consecutive_side_frames = 0
            else:
                self.consecutive_side_frames = 0
        else:
            self.consecutive_side_frames = 0
            
        # 3. Calculate Pulse Duration
        if steer_key is not None:
            # Proportional contribution
            control_output = abs(error_norm) * self.kp
            
            # Derivative damping contribution:
            # If indicator is already moving towards the green center, reduce steering to avoid overshoot.
            is_moving_to_center = (error_norm < 0 and error_diff > 0) or (error_norm > 0 and error_diff < 0)
            if is_moving_to_center:
                control_output -= abs(error_diff) * self.kd
                
            # Clamp the control output to a minimum of 0.1 to guarantee some steering effect
            control_output = max(0.1, control_output)
            
            # Translate control output to key press duration
            pulse_duration = self.base_pulse * control_output
            
            # Clamp the pulse duration (max 180ms) to ensure the loop releases keys to take new screenshots
            pulse_duration = min(0.18, pulse_duration)
        else:
            pulse_duration = 0.0
            
        return steer_key, pulse_duration, log_msg
