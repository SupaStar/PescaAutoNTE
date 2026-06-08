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

print("Color profile of column X=162 (Indicator):")
for y in range(10, 35):
    print(f"Local Y={y} (Global Y={y1+y}): BGR={crop[y, 162]}, HSV={hsv[y, 162]}")
