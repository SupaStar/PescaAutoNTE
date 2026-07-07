import cv2
import numpy as np
import os

ARTIFACT_DIR = r"C:\Users\obedn\.gemini\antigravity\brain\5e49abb0-9c31-44d9-b45d-8e33d9035125"
img_waiting = os.path.join(ARTIFACT_DIR, "media__1780929594225.png") # Image 1 (Night waiting)
img_bite = os.path.join(ARTIFACT_DIR, "media__1780929628165.png")    # Image 2 (Night bite)
img_minigame = os.path.join(ARTIFACT_DIR, "media__1780929636448.png")# Image 3 (Minigame)
img_success = os.path.join(ARTIFACT_DIR, "media__1780929648605.png") # Image 4 (Success screen)
img_day_wait = os.path.join(ARTIFACT_DIR, "media__1780931283252.png")  # Image 5 (Day waiting)

# Import the logic parameters from fishing_bot
from fishing_bot import F_ICON_REF, BAR_REF, SUCCESS_REF

def process_img(img, roi):
    """Processes image as if captured from screen."""
    # Crop using the reference ROI since test images are already 1024x428
    crop = img[roi["y1"]:roi["y2"], roi["x1"]:roi["x2"]]
    return crop

def check_bite_logic(crop):
    """Executes the exact bite detection logic from fishing_bot."""
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    lower_blue = np.array([100, 100, 100])
    upper_blue = np.array([125, 255, 255])
    mask_blue = cv2.inRange(hsv, lower_blue, upper_blue)
    
    y_indices, x_indices = np.where(mask_blue > 0)
    
    if len(x_indices) > 0:
        center_x = 67
        center_y = 35
        
        left_half = np.sum(x_indices < center_x)
        right_half = np.sum(x_indices >= center_x)
        top_half = np.sum(y_indices < center_y)
        bottom_half = np.sum(y_indices >= center_y)
        
        is_bite = (left_half >= 35) and (right_half >= 35) and (top_half >= 35) and (bottom_half >= 35)
        return is_bite, (left_half, right_half, top_half, bottom_half)
    else:
        return False, (0, 0, 0, 0)

def test_waiting_state():
    print("\n--- Test 1: Night Waiting Screen ---")
    img = cv2.imread(img_waiting)
    crop = process_img(img, F_ICON_REF)
    is_bite, (l, r, t, b) = check_bite_logic(crop)
    print(f"Blue ring counts -> L:{l}, R:{r}, T:{t}, B:{b}")
    print(f"Bite detected: {is_bite} (Expected: False)")
    assert not is_bite, "Failed: false positive bite detection on night waiting"

def test_day_waiting_state():
    print("\n--- Test 2: Day Waiting Screen (Partial blue arc) ---")
    img = cv2.imread(img_day_wait)
    crop = process_img(img, F_ICON_REF)
    is_bite, (l, r, t, b) = check_bite_logic(crop)
    print(f"Blue ring counts -> L:{l}, R:{r}, T:{t}, B:{b}")
    print(f"Bite detected: {is_bite} (Expected: False)")
    assert not is_bite, "Failed: false positive bite detection on day waiting"

def test_bite_state():
    print("\n--- Test 3: Night Bite Screen (Complete blue ring) ---")
    img = cv2.imread(img_bite)
    crop = process_img(img, F_ICON_REF)
    is_bite, (l, r, t, b) = check_bite_logic(crop)
    print(f"Blue ring counts -> L:{l}, R:{r}, T:{t}, B:{b}")
    print(f"Bite detected: {is_bite} (Expected: True)")
    assert is_bite, "Failed: false negative bite detection on bite screen"

def test_minigame_state():
    print("\n--- Test 4: Minigame Screen ---")
    img = cv2.imread(img_minigame)
    crop = process_img(img, BAR_REF)
    
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    
    # Green zone detection
    lower_green = np.array([75, 120, 100])
    upper_green = np.array([90, 255, 255])
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    y_g, x_g = np.where(mask_green > 0)
    
    print(f"Green zone detected: {len(x_g) > 0} (Expected: True)")
    assert len(x_g) > 0, "Failed: green zone not detected"
    
    green_start = np.min(x_g)
    green_end = np.max(x_g)
    print(f"Green zone range: [{green_start}, {green_end}]")
    
    # Indicator detection
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
            
    print(f"Indicator detected: {len(detected_ind_x) > 0} (Expected: True)")
    assert len(detected_ind_x) > 0, "Failed: indicator not detected"
    
    ind_x = int(np.median(detected_ind_x))
    print(f"Indicator position: X = {ind_x}")
    
    # Action decision
    if ind_x < green_start:
        action = "Press D (Pull Right)"
    elif ind_x > green_end:
        action = "Press A (Pull Left)"
    else:
        action = "Release both"
        
    print(f"Determined Action: {action} (Expected: Press A (Pull Left))")
    assert action == "Press A (Pull Left)", f"Failed: incorrect action: {action}"

def test_success_state():
    print("\n--- Test 5: Success Screen ---")
    img = cv2.imread(img_success)
    crop = process_img(img, SUCCESS_REF)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    white_pixels = np.sum(gray > 200)
    
    print(f"White pixels (>200): {white_pixels} (Threshold: >350)")
    is_success = white_pixels > 350
    print(f"Success detected: {is_success} (Expected: True)")
    assert is_success, "Failed: false negative success detection"

def test_success_on_waiting():
    print("\n--- Test 6: Success Check on Waiting Screen ---")
    img = cv2.imread(img_waiting)
    crop = process_img(img, SUCCESS_REF)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    white_pixels = np.sum(gray > 200)
    
    print(f"White pixels (>200): {white_pixels} (Threshold: >350)")
    is_success = white_pixels > 350
    print(f"Success detected: {is_success} (Expected: False)")
    assert not is_success, "Failed: false positive success detection"
def test_adaptive_controller():
    print("\n--- Test 7: Adaptive Controller Logic & Adaptation ---")
    
    # Isolate test from local config file
    config_path = "ai_config.json"
    temp_config_path = "ai_config.json.tmp"
    config_existed = os.path.exists(config_path)
    if config_existed:
        if os.path.exists(temp_config_path):
            os.remove(temp_config_path)
        os.rename(config_path, temp_config_path)
        
    try:
        from adaptive_controller import AdaptiveController
        ctrl = AdaptiveController(base_pulse=0.04, initial_kp=1.0, initial_kd=0.15)
        
        # Minigame stats: green bounds [100, 200], center 150, half-width 50
        # Scenario 1: Indicator is at 150 (perfectly centered)
        key, pulse, log = ctrl.update(150, 100, 200)
        print(f"Center check: Key={key}, Pulse={pulse}, Log={log}")
        assert key is None, "Failed: should not steer when centered"
        
        # Scenario 2: Indicator is far left at 50
        key, pulse, log = ctrl.update(50, 100, 200)
        print(f"Far left check: Key={key}, Pulse={pulse}, Log={log}")
        assert key == 'd', "Failed: should steer right when indicator is left"
        assert pulse > 0.04, f"Failed: pulse should be scaled higher than base pulse. Pulse={pulse}"
        
        # Scenario 3: Sluggish check (feed same far-left error 6 times to trigger Kp increase)
        for i in range(4):
            key, pulse, log = ctrl.update(50, 100, 200)
        # The 6th time should trigger Kp increase
        key, pulse, log = ctrl.update(50, 100, 200)
        print(f"Sluggish response check (after 6 frames): Key={key}, Pulse={pulse}, Log={log}")
        assert log is not None and "Increasing Kp" in log, f"Failed: should trigger Kp increase on sluggish response. Log={log}"
        assert ctrl.kp > 1.0, f"Failed: Kp should have increased. Kp={ctrl.kp}"
        
        # Scenario 4: Oscillation check (crossing side from left to right rapidly)
        # Let's say we cross to far right (250) and it's within 0.8s
        # Note: We need to set the side and cross times.
        # Let's call update with a right-side error
        key, pulse, log = ctrl.update(250, 100, 200)
        print(f"Oscillation check: Key={key}, Pulse={pulse}, Log={log}")
        assert log is not None and "Oscillation detected" in log, f"Failed: should trigger oscillation damping. Log={log}"
        assert ctrl.kp < 1.2, f"Failed: Kp should have decreased. Kp={ctrl.kp}"
        
        print("Adaptive Controller tests passed!")
    finally:
        # Restore original config file
        if os.path.exists(config_path):
            os.remove(config_path)
        if config_existed:
            os.rename(temp_config_path, config_path)


if __name__ == "__main__":
    try:
        test_waiting_state()
        test_day_waiting_state()
        test_bite_state()
        test_minigame_state()
        test_success_state()
        test_success_on_waiting()
        test_adaptive_controller()
        print("\n" + "="*40 + "\nALL TESTS PASSED SUCCESSFULLY!\n" + "="*40)
    except AssertionError as e:
        print(f"\nTEST FAILED: {e}")

