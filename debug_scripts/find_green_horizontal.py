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

# Define a clean HSV range for the green bar
# Based on the sample: HSV=[ 84 190 160 ]
# Let's use Hue: 75 to 90, Saturation: 120 to 255, Value: 100 to 255
lower_green = np.array([75, 120, 100])
upper_green = np.array([90, 255, 255])

mask_green = cv2.inRange(hsv, lower_green, upper_green)

# Sum up green pixels vertically for each X column
column_counts = np.sum(mask_green > 0, axis=0)

print("Green pixel counts per X column in the crop:")
active_columns = []
for x, count in enumerate(column_counts):
    if count > 0:
        print(f"Local X={x} (Global X={x1+x}): {count} green pixels")
        active_columns.append(x)

if active_columns:
    print(f"\nActive green columns span: local X [{min(active_columns)}, {max(active_columns)}]")
    # Find contiguous blocks
    print("Contiguous green blocks:")
    start = active_columns[0]
    for i in range(1, len(active_columns)):
        if active_columns[i] != active_columns[i-1] + 1:
            print(f"Block: local X [{start}, {active_columns[i-1]}] (Width: {active_columns[i-1] - start + 1} px)")
            start = active_columns[i]
    print(f"Block: local X [{start}, {active_columns[-1]}] (Width: {active_columns[-1] - start + 1} px)")
else:
    print("No green columns found with this range.")
