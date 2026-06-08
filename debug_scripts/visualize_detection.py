import cv2
import numpy as np
import os

ARTIFACT_DIR = r"C:\Users\obedn\.gemini\antigravity\brain\5e49abb0-9c31-44d9-b45d-8e33d9035125"
img_path = os.path.join(ARTIFACT_DIR, "media__1780929636448.png")

img = cv2.imread(img_path)
y1, y2 = 15, 60
x1, x2 = 350, 674
crop = img[y1:y2, x1:x2].copy()
hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

# Green detection
lower_green = np.array([75, 120, 100])
upper_green = np.array([90, 255, 255])
mask_green = cv2.inRange(hsv, lower_green, upper_green)
y_g, x_g = np.where(mask_green > 0)

# White detection (broad threshold)
_, mask_white = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
y_w, x_w = np.where(mask_white > 0)

# Draw green zone on crop (semi-transparent overlay)
overlay = crop.copy()
if len(x_g) > 0:
    min_x_g, max_x_g = np.min(x_g), np.max(x_g)
    cv2.rectangle(overlay, (min_x_g, 0), (max_x_g, crop.shape[0]), (0, 255, 0), -1)

# Draw white pixels as red dots
for x, y in zip(x_w, y_w):
    cv2.circle(overlay, (x, y), 1, (0, 0, 255), -1)

# Blend overlay
cv2.addWeighted(overlay, 0.5, crop, 0.5, 0, crop)

# Save annotated image
cv2.imwrite("annotated_crop.png", crop)
print("Saved annotated_crop.png")
