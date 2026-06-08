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

y_inspect = 19
print(f"Values along local Y = {y_inspect} (global Y = {y1 + y_inspect}) from local X = 130 to 190:")
for x in range(130, 190):
    print(f"Local X={x} (Global X={x1+x}): gray={gray[y_inspect, x]}, BGR={crop[y_inspect, x]}")
