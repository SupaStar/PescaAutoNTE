import cv2
import numpy as np
import os

ARTIFACT_DIR = r"C:\Users\obedn\.gemini\antigravity\brain\5e49abb0-9c31-44d9-b45d-8e33d9035125"
img_night_wait = os.path.join(ARTIFACT_DIR, "media__1780929594225.png") # Image 1
img_night_bite = os.path.join(ARTIFACT_DIR, "media__1780929628165.png") # Image 2
img_day_wait = os.path.join(ARTIFACT_DIR, "media__1780931283252.png")  # Image 5 (Daytime)

img1 = cv2.imread(img_night_wait)
img2 = cv2.imread(img_night_bite)
img5 = cv2.imread(img_day_wait)

# Let's crop the bottom right area.
# In a 1024x428 image, let's look at Y: [350, 420], X: [900, 1000]
y1, y2 = 350, 420
x1, x2 = 900, 1000

crop1 = img1[y1:y2, x1:x2]
crop2 = img2[y1:y2, x1:x2]
crop5 = img5[y1:y2, x1:x2]

cv2.imwrite("f_icon_night_wait.png", crop1)
cv2.imwrite("f_icon_night_bite.png", crop2)
cv2.imwrite("f_icon_day_wait.png", crop5)

print("Saved crops for F icon comparison.")
