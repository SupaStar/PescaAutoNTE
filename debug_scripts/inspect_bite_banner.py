import cv2
import numpy as np
import os

ARTIFACT_DIR = r"C:\Users\obedn\.gemini\antigravity\brain\5e49abb0-9c31-44d9-b45d-8e33d9035125"
img_waiting_path = os.path.join(ARTIFACT_DIR, "media__1780929594225.png")
img_bite_path = os.path.join(ARTIFACT_DIR, "media__1780929628165.png")

img_waiting = cv2.imread(img_waiting_path)
img_bite = cv2.imread(img_bite_path)

# Let's inspect the top-middle region where the black bubble banner appears.
# In a 1024x428 image:
# Y: [70, 110] (about 300 to 450 in 3440x1440)
# X: [320, 700] (about 1100 to 2340 in 3440x1440)
y1, y2 = 70, 115
x1, x2 = 320, 700

crop_wait = img_waiting[y1:y2, x1:x2]
crop_bite = img_bite[y1:y2, x1:x2]

# Save the crops for visual confirmation
cv2.imwrite("crop_bite_wait.png", crop_wait)
cv2.imwrite("crop_bite_active.png", crop_bite)

# The banner has a very dark background (BGR around [10, 10, 10]) and bright white text.
# Let's check the percentage of very dark pixels (BGR < 25) in this region.
dark_wait = np.sum(np.all(crop_wait < 25, axis=-1))
dark_bite = np.sum(np.all(crop_bite < 25, axis=-1))

# Let's also check for bright white text pixels (gray value > 220)
gray_wait = cv2.cvtColor(crop_wait, cv2.COLOR_BGR2GRAY)
gray_bite = cv2.cvtColor(crop_bite, cv2.COLOR_BGR2GRAY)
white_wait = np.sum(gray_wait > 220)
white_bite = np.sum(gray_bite > 220)

print(f"Waiting screenshot ROI Y:[{y1}, {y2}] X:[{x1}, {x2}]:")
print(f"  Dark pixels: {dark_wait} | White text pixels: {white_wait}")
print(f"Bite screenshot ROI Y:[{y1}, {y2}] X:[{x1}, {x2}]:")
print(f"  Dark pixels: {dark_bite} | White text pixels: {white_bite}")

# A simple rule: if dark pixels > 4000 and white text pixels > 200 -> Banner active!
# Let's check total pixels in crop: (115-70) * (700-320) = 45 * 380 = 17100 pixels.
print(f"Total ROI pixels: {crop_wait.shape[0] * crop_wait.shape[1]}")
