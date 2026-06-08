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
    
    # Let's find the center of the F-icon circle.
    # Typically, the circular button is centered in the crop.
    # Let's find coordinates of the mask
    y_indices, x_indices = np.where(mask > 0)
    
    print(f"\n--- Analysis for {label} ---")
    print(f"Total blue pixels: {len(x_indices)}")
    
    if len(x_indices) > 0:
        # Center of the crop is: width / 2 = 50
        # Let's count pixels on the left half (X < 50) and right half (X >= 50)
        left_half = np.sum(x_indices < 50)
        right_half = np.sum(x_indices >= 50)
        
        print(f"  Left Half (X < 50):  {left_half}")
        print(f"  Right Half (X >= 50): {right_half}")
        
        # We can also divide into top and bottom halves (Y < 35 vs Y >= 35)
        top_half = np.sum(y_indices < 35)
        bottom_half = np.sum(y_indices >= 35)
        print(f"  Top Half (Y < 35):    {top_half}")
        print(f"  Bottom Half (Y >= 35): {bottom_half}")
        
        # Bite trigger condition: both left and right halves have at least 40 pixels,
        # and both top and bottom halves have at least 40 pixels.
        is_bite = (left_half >= 40) and (right_half >= 40) and (top_half >= 40) and (bottom_half >= 40)
        print(f"  Bite detected by quadrant check: {is_bite}")
    else:
        print("  No blue pixels detected.")

analyze_distribution(crop_nw, "Night Waiting")
analyze_distribution(crop_dw, "Day Waiting")
analyze_distribution(crop_nb, "Night Bite")
