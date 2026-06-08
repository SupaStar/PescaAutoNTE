import cv2
import numpy as np
import os

ARTIFACT_DIR = r"C:\Users\obedn\.gemini\antigravity\brain\5e49abb0-9c31-44d9-b45d-8e33d9035125"
img_path = os.path.join(ARTIFACT_DIR, "media__1780929636448.png")

img = cv2.imread(img_path)
y1, y2 = 15, 60
x1, x2 = 350, 674
crop = img[y1:y2, x1:x2]
hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

# Channel Y bounds: local Y from 11 to 18
chan_y1, chan_y2 = 11, 18

print("Scanning channel for indicator (X: [50, 310])...")
detected_x = []

# Restrict horizontal search to avoid circular icons at the ends
for x in range(50, 310):
    col_matches = 0
    for y in range(chan_y1, chan_y2 + 1):
        h, s, v = hsv[y, x]
        # Check for yellow/orange: Hue 15-35, Saturation 40-255, Value 150-255
        is_yellow = (15 <= h <= 35) and (40 <= s <= 255) and (150 <= v <= 255)
        # Check for white: Saturation < 40, Value > 220
        is_white = (s < 40) and (v > 220)
        
        if is_yellow or is_white:
            col_matches += 1
            
    if col_matches >= 3:
        print(f"Detected indicator candidate at local X={x} (Global X={x1+x}) with {col_matches} matching pixels")
        detected_x.append(x)

if detected_x:
    median_x = int(np.median(detected_x))
    print(f"Final detected indicator X: local {median_x} (global {x1+median_x})")
else:
    print("Indicator NOT detected!")
