import cv2
import numpy as np
import os

ARTIFACT_DIR = r"C:\Users\obedn\.gemini\antigravity\brain\5e49abb0-9c31-44d9-b45d-8e33d9035125"
img_night_wait = cv2.imread(os.path.join(ARTIFACT_DIR, "media__1780929594225.png"))
img_night_bite = cv2.imread(os.path.join(ARTIFACT_DIR, "media__1780929628165.png"))
img_day_wait = cv2.imread(os.path.join(ARTIFACT_DIR, "media__1780931283252.png"))

y1, y2 = 350, 420
x1, x2 = 900, 1000

crop_nw = img_night_wait[y1:y2, x1:x2]
crop_nb = img_night_bite[y1:y2, x1:x2]
crop_dw = img_day_wait[y1:y2, x1:x2]

# HSV thresholds
lower_blue = np.array([100, 100, 100])
upper_blue = np.array([125, 255, 255])

def analyze_distribution(crop, label):
    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower_blue, upper_blue)
    
    y_indices, x_indices = np.where(mask > 0)
    
    print(f"\n--- Analysis for {label} ---")
    print(f"Total blue pixels: {len(x_indices)}")
    
    if len(x_indices) > 0:
        # Corrected Center
        center_x = 67
        center_y = 35
        
        left_half = np.sum(x_indices < center_x)
        right_half = np.sum(x_indices >= center_x)
        
        top_half = np.sum(y_indices < center_y)
        bottom_half = np.sum(y_indices >= center_y)
        
        print(f"  Left Half (X < 67):  {left_half}")
        print(f"  Right Half (X >= 67): {right_half}")
        print(f"  Top Half (Y < 35):    {top_half}")
        print(f"  Bottom Half (Y >= 35): {bottom_half}")
        
        # Bite trigger condition: at least 30 pixels in each half to ensure complete circle
        is_bite = (left_half >= 30) and (right_half >= 30) and (top_half >= 30) and (bottom_half >= 30)
        print(f"  Bite detected by quadrant check: {is_bite}")
    else:
        print("  No blue pixels detected.")

analyze_distribution(crop_nw, "Night Waiting")
analyze_distribution(crop_dw, "Day Waiting")
analyze_distribution(crop_nb, "Night Bite")
