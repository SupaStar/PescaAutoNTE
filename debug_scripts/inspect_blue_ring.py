import cv2
import numpy as np
import os

ARTIFACT_DIR = r"C:\Users\obedn\.gemini\antigravity\brain\5e49abb0-9c31-44d9-b45d-8e33d9035125"
img_night_wait = cv2.imread(os.path.join(ARTIFACT_DIR, "media__1780929594225.png"))
img_night_bite = cv2.imread(os.path.join(ARTIFACT_DIR, "media__1780929628165.png"))
img_day_wait = cv2.imread(os.path.join(ARTIFACT_DIR, "media__1780931283252.png"))

# Crop coordinates in 1024x428 space
y1, y2 = 350, 420
x1, x2 = 900, 1000

crop_nw = img_night_wait[y1:y2, x1:x2]
crop_nb = img_night_bite[y1:y2, x1:x2]
crop_dw = img_day_wait[y1:y2, x1:x2]

# Let's convert them to HSV
hsv_nw = cv2.cvtColor(crop_nw, cv2.COLOR_BGR2HSV)
hsv_nb = cv2.cvtColor(crop_nb, cv2.COLOR_BGR2HSV)
hsv_dw = cv2.cvtColor(crop_dw, cv2.COLOR_BGR2HSV)

# Define HSV range for the bright blue color
# Bright blue is typically Hue: 100 to 125, Saturation: 100 to 255, Value: 100 to 255
lower_blue = np.array([100, 100, 100])
upper_blue = np.array([125, 255, 255])

mask_nw = cv2.inRange(hsv_nw, lower_blue, upper_blue)
mask_nb = cv2.inRange(hsv_nb, lower_blue, upper_blue)
mask_dw = cv2.inRange(hsv_dw, lower_blue, upper_blue)

blue_nw = np.sum(mask_nw > 0)
blue_nb = np.sum(mask_nb > 0)
blue_dw = np.sum(mask_dw > 0)

print(f"Blue pixels count in F-icon region:")
print(f"  Night Waiting: {blue_nw}")
print(f"  Day Waiting:   {blue_dw}")
print(f"  Night Bite:    {blue_nb}")

# Let's save the masks for visual inspection of what is being matched
cv2.imwrite("blue_mask_night_wait.png", mask_nw)
cv2.imwrite("blue_mask_night_bite.png", mask_nb)
cv2.imwrite("blue_mask_day_wait.png", mask_dw)
print("Saved masks to files.")
