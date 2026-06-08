import cv2
import numpy as np
import os

ARTIFACT_DIR = r"C:\Users\obedn\.gemini\antigravity\brain\5e49abb0-9c31-44d9-b45d-8e33d9035125"
img_path = os.path.join(ARTIFACT_DIR, "media__1780929636448.png")

img = cv2.imread(img_path)
h, w, _ = img.shape
print(f"Loaded image {img_path} with shape {w}x{h}")

# Let's crop the top center region where we expect the progress bar
# On a 1024x428 image, top center is around Y: [10, 100], X: [300, 724]
crop = img[10:100, 300:724]
cv2.imwrite("top_center_crop.png", crop)
print("Saved top center crop to top_center_crop.png")

# Convert the crop to HSV to find the exact green color of the bar
crop_hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

# The green bar has a very bright neon green/cyan color.
# Let's find pixels where green is highly saturated and bright.
# Let's search for Hue between 40 and 80, Saturation > 150, Value > 150
lower_neon_green = np.array([40, 150, 150])
upper_neon_green = np.array([85, 255, 255])

mask = cv2.inRange(crop_hsv, lower_neon_green, upper_neon_green)
y_idx, x_idx = np.where(mask > 0)

if len(x_idx) > 0:
    min_x, max_x = np.min(x_idx), np.max(x_idx)
    min_y, max_y = np.min(y_idx), np.max(y_idx)
    print(f"Neon green pixels found in crop!")
    print(f"Local coordinates: Y: [{min_y}, {max_y}], X: [{min_x}, {max_x}]")
    print(f"Global coordinates: Y: [{10 + min_y}, {10 + max_y}], X: [{300 + min_x}, {300 + max_x}]")
    
    # Let's print the actual HSV and BGR values of some neon green pixels
    sample_y = min_y + (max_y - min_y) // 2
    sample_x = min_x + (max_x - min_x) // 2
    bgr_val = crop[sample_y, sample_x]
    hsv_val = crop_hsv[sample_y, sample_x]
    print(f"Sample pixel at local ({sample_x}, {sample_y}): BGR={bgr_val}, HSV={hsv_val}")
else:
    print("No neon green pixels found in the crop using the strict filter.")
    # Let's print out the HSV values of the middle row in the crop to see what colors are there
    mid_y = crop.shape[0] // 2
    print(f"HSV values along the middle row (Y={mid_y}) of the crop:")
    for x in range(0, crop.shape[1], 20):
        print(f"X={x}: BGR={crop[mid_y, x]}, HSV={crop_hsv[mid_y, x]}")
