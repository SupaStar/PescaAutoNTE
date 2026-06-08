import cv2
import numpy as np
import os

ARTIFACT_DIR = r"C:\Users\obedn\.gemini\antigravity\brain\5e49abb0-9c31-44d9-b45d-8e33d9035125"
img_path = os.path.join(ARTIFACT_DIR, "media__1780929636448.png")

img = cv2.imread(img_path)
y1, y2 = 15, 60
x1, x2 = 350, 674
crop = img[y1:y2, x1:x2]
gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

# Inspect Y = 19 (which is global Y = 34)
y_inspect = 19
print(f"Grayscale values at local Y = {y_inspect} (global Y = {y1 + y_inspect}):")
for x in range(crop.shape[1]):
    val = gray[y_inspect, x]
    # Only print values that are reasonably bright to find the line
    if val > 150:
        print(f"Local X={x} (Global X={x1+x}): gray={val}, BGR={crop[y_inspect, x]}")
