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

_, mask_white = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
y_w, x_w = np.where(mask_white > 0)

print("List of all white pixels (local coordinates inside crop):")
for x, y in zip(x_w, y_w):
    # Print local x, y and global x, y
    print(f"Local X={x}, Y={y} | Global X={x1+x}, Y={y1+y} | Gray value = {gray[y, x]}")
