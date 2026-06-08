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

lower_green = np.array([60, 100, 100])
upper_green = np.array([95, 255, 255])
mask_green = cv2.inRange(hsv, lower_green, upper_green)

y_g, x_g = np.where(mask_green > 0)
print(f"Total green pixels found: {len(x_g)}")
# Print first 50 green pixels
for i in range(min(50, len(x_g))):
    x, y = x_g[i], y_g[i]
    print(f"Local X={x}, Y={y} | Global X={x1+x}, Y={y1+y} | BGR={crop[y, x]}, HSV={hsv[y, x]}")
