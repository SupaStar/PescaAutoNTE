import cv2
import numpy as np
import os

ARTIFACT_DIR = r"C:\Users\obedn\.gemini\antigravity\brain\5e49abb0-9c31-44d9-b45d-8e33d9035125"
img_path = os.path.join(ARTIFACT_DIR, "media__1780929628165.png")

img = cv2.imread(img_path)
y1, y2 = 350, 420
x1, x2 = 900, 1000
crop = img[y1:y2, x1:x2]

hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
lower_blue = np.array([100, 100, 100])
upper_blue = np.array([125, 255, 255])
mask = cv2.inRange(hsv, lower_blue, upper_blue)

y_indices, x_indices = np.where(mask > 0)

if len(x_indices) > 0:
    min_x, max_x = np.min(x_indices), np.max(x_indices)
    min_y, max_y = np.min(y_indices), np.max(y_indices)
    print(f"Blue pixels found in crop:")
    print(f"  X-range: [{min_x}, {max_x}] | Center X: {(min_x + max_x) / 2}")
    print(f"  Y-range: [{min_y}, {max_y}] | Center Y: {(min_y + max_y) / 2}")
else:
    print("No blue pixels found.")
