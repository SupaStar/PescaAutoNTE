import cv2
import numpy as np
import os

ARTIFACT_DIR = r"C:\Users\obedn\.gemini\antigravity\brain\5e49abb0-9c31-44d9-b45d-8e33d9035125"
img_waiting_path = os.path.join(ARTIFACT_DIR, "media__1780929594225.png")
img_success_path = os.path.join(ARTIFACT_DIR, "media__1780929648605.png")

img_waiting = cv2.imread(img_waiting_path)
img_success = cv2.imread(img_success_path)

# Crop bottom center area for 1024x428 image
# Y: [385, 420], X: [380, 640]
y1, y2 = 385, 420
x1, x2 = 380, 640

crop_wait = img_waiting[y1:y2, x1:x2]
crop_succ = img_success[y1:y2, x1:x2]

# Save crops
cv2.imwrite("crop_success_wait.png", crop_wait)
cv2.imwrite("crop_success_active.png", crop_succ)

# Convert to gray
gray_wait = cv2.cvtColor(crop_wait, cv2.COLOR_BGR2GRAY)
gray_succ = cv2.cvtColor(crop_succ, cv2.COLOR_BGR2GRAY)

# Check for bright white text pixels (gray > 200)
white_wait = np.sum(gray_wait > 200)
white_succ = np.sum(gray_succ > 200)

print(f"Waiting screenshot success ROI Y:[{y1}, {y2}] X:[{x1}, {x2}]:")
print(f"  White pixels (>200): {white_wait}")
print(f"Success screenshot success ROI Y:[{y1}, {y2}] X:[{x1}, {x2}]:")
print(f"  White pixels (>200): {white_succ}")
print(f"Total ROI pixels: {crop_wait.shape[0] * crop_wait.shape[1]}")
