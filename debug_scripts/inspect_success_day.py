import cv2
import numpy as np
import os

ARTIFACT_DIR = r"C:\Users\obedn\.gemini\antigravity\brain\5e49abb0-9c31-44d9-b45d-8e33d9035125"
img_night_success = os.path.join(ARTIFACT_DIR, "media__1780929648605.png") # Image 4 (Night success)
img_day_success = os.path.join(ARTIFACT_DIR, "media__1780931737839.png")   # Image 6 (Day success)

img4 = cv2.imread(img_night_success)
img6 = cv2.imread(img_day_success)

# Crop coordinates in 1024x428 space
y1, y2 = 385, 420
x1, x2 = 380, 640

crop4 = img4[y1:y2, x1:x2]
crop6 = img6[y1:y2, x1:x2]

cv2.imwrite("success_crop_night.png", crop4)
cv2.imwrite("success_crop_day.png", crop6)

gray4 = cv2.cvtColor(crop4, cv2.COLOR_BGR2GRAY)
gray6 = cv2.cvtColor(crop6, cv2.COLOR_BGR2GRAY)

white4 = np.sum(gray4 > 200)
white6 = np.sum(gray6 > 200)

print(f"White pixels (>200) in success crop:")
print(f"  Night Success: {white4}")
print(f"  Day Success:   {white6}")

# Let's also print the dimensions of the crop
print(f"Crop dimensions: {crop6.shape}")
