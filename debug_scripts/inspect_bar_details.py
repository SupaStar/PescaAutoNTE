import cv2
import numpy as np
import os

ARTIFACT_DIR = r"C:\Users\obedn\.gemini\antigravity\brain\5e49abb0-9c31-44d9-b45d-8e33d9035125"
img_path = os.path.join(ARTIFACT_DIR, "media__1780929636448.png")

img = cv2.imread(img_path)
h, w, _ = img.shape

# Let's crop a window around the bar.
# Y: 15 to 60, X: 350 to 674
y1, y2 = 15, 60
x1, x2 = 350, 674
crop = img[y1:y2, x1:x2]
cv2.imwrite("bar_crop.png", crop)

# Convert to HSV and grayscale
hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)

print("--- Green Zone Analysis ---")
# Let's search for green pixels using HSV Hue: [60, 95]
lower_green = np.array([60, 100, 100])
upper_green = np.array([95, 255, 255])
mask_green = cv2.inRange(hsv, lower_green, upper_green)
y_g, x_g = np.where(mask_green > 0)
if len(x_g) > 0:
    print(f"Green zone local X: [{np.min(x_g)}, {np.max(x_g)}], Y: [{np.min(y_g)}, {np.max(y_g)}]")
    print(f"Green zone global X: [{x1 + np.min(x_g)}, {x1 + np.max(x_g)}], Y: [{y1 + np.min(y_g)}, {y1 + np.max(y_g)}]")
else:
    print("No green pixels found.")

print("\n--- White Line Analysis ---")
# The white line is bright. Let's find pixels in the crop that are very bright white.
# We'll use gray threshold > 240
_, mask_white = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
y_w, x_w = np.where(mask_white > 0)
if len(x_w) > 0:
    print(f"White pixels local X: [{np.min(x_w)}, {np.max(x_w)}], Y: [{np.min(y_w)}, {np.max(y_w)}]")
    print(f"White pixels global X: [{x1 + np.min(x_w)}, {x1 + np.max(x_w)}], Y: [{y1 + np.min(y_w)}, {y1 + np.max(y_w)}]")
    # Let's print out the X coordinates of the white pixels to see the shape
    unique_x = np.unique(x_w)
    print("Unique local X coordinates of white pixels:", unique_x)
else:
    print("No white pixels found.")

print("\n--- Progress Bar Frame Analysis ---")
# The progress bar is a long horizontal line. It has a dark background and some border.
# Let's look at the gray values of a vertical slice to see where the bar background starts and ends.
# We will check the column at local X = 50 (which is global X = 400).
col_x = 50
print(f"Grayscale values at local X = {col_x} (global X = {x1 + col_x}) for local Y = 0 to {y2-y1}:")
for y in range(y2 - y1):
    print(f"local Y={y} (global Y={y1+y}): gray={gray[y, col_x]}, BGR={crop[y, col_x]}")
