import cv2
import numpy as np
import os

# Paths to the screenshot images
ARTIFACT_DIR = r"C:\Users\obedn\.gemini\antigravity\brain\5e49abb0-9c31-44d9-b45d-8e33d9035125"
img_waiting = os.path.join(ARTIFACT_DIR, "media__1780929594225.png") # Image 1
img_bite = os.path.join(ARTIFACT_DIR, "media__1780929628165.png")    # Image 2
img_minigame = os.path.join(ARTIFACT_DIR, "media__1780929636448.png")# Image 3
img_success = os.path.join(ARTIFACT_DIR, "media__1780929648605.png") # Image 4

def analyze_minigame(image_path):
    print(f"\n--- Analyzing Minigame: {image_path} ---")
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not load minigame image.")
        return
    
    h, w, _ = img.shape
    print(f"Image resolution: {w}x{h}")
    
    # We suspect the minigame bar is near the top center. Let's crop X: [1000, 2440], Y: [50, 250]
    # Let's search the whole image first for green pixels to locate it exactly.
    # Convert to HSV
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Green/cyan color range for the green zone
    # In HSV, Green is roughly H: 35-85, S: 50-255, V: 50-255
    # Let's make it broad to see what we find
    lower_green = np.array([35, 50, 50])
    upper_green = np.array([90, 255, 255])
    
    mask_green = cv2.inRange(hsv, lower_green, upper_green)
    
    # Find coordinates of all green pixels
    y_indices, x_indices = np.where(mask_green > 0)
    
    if len(x_indices) > 0:
        min_x, max_x = np.min(x_indices), np.max(x_indices)
        min_y, max_y = np.min(y_indices), np.max(y_indices)
        print(f"Green zone pixels found! Y-range: [{min_y}, {max_y}], X-range: [{min_x}, {max_x}]")
        
        # Crop the progress bar region based on green zone findings (with some padding)
        crop_y1 = max(0, min_y - 20)
        crop_y2 = min(h, max_y + 20)
        crop_x1 = max(0, min_x - 100)
        crop_x2 = min(w, max_x + 100)
        print(f"Recommended Progress Bar ROI: Y: [{crop_y1}, {crop_y2}], X: [{crop_x1}, {crop_x2}]")
        
        # Analyze the white line in this cropped region
        # Convert crop to grayscale and threshold it for bright white pixels
        crop_gray = cv2.cvtColor(img[crop_y1:crop_y2, crop_x1:crop_x2], cv2.COLOR_BGR2GRAY)
        _, mask_white = cv2.threshold(crop_gray, 240, 255, cv2.THRESH_BINARY)
        
        # Let's find white line X position in the crop
        white_y, white_x = np.where(mask_white > 0)
        if len(white_x) > 0:
            # Group x coordinates to find the white line (usually it's a vertical line, so x coords will be clustered)
            median_white_x = int(np.median(white_x))
            actual_white_x = crop_x1 + median_white_x
            print(f"White line detected at X = {actual_white_x} (local X in crop: {median_white_x})")
            
            # Find the green zone's horizontal center in the crop
            # We filter green pixels in the crop
            crop_hsv = hsv[crop_y1:crop_y2, crop_x1:crop_x2]
            crop_mask_green = cv2.inRange(crop_hsv, lower_green, upper_green)
            green_y, green_x = np.where(crop_mask_green > 0)
            if len(green_x) > 0:
                min_green_x = np.min(green_x)
                max_green_x = np.max(green_x)
                mean_green_x = int(np.mean(green_x))
                print(f"Green zone in crop: local X-range [{min_green_x}, {max_green_x}], center: {mean_green_x}")
                print(f"Global Green zone: X-range [{crop_x1 + min_green_x}, {crop_x1 + max_green_x}], center: {crop_x1 + mean_green_x}")
                
                # Decision check:
                if median_white_x < min_green_x:
                    print("Action: White line is to the LEFT of green zone -> Press D")
                elif median_white_x > max_green_x:
                    print("Action: White line is to the RIGHT of green zone -> Press A")
                else:
                    print("Action: White line is INSIDE the green zone -> Release keys")
        else:
            print("Warning: White line not detected in the cropped ROI.")
            
        # Let's save the cropped ROI image for inspection
        cv2.imwrite("roi_progress_bar.png", img[crop_y1:crop_y2, crop_x1:crop_x2])
        print("Saved cropped progress bar ROI to 'roi_progress_bar.png'")
    else:
        print("Error: No green pixels found in the image. Check if HSV thresholds or image are correct.")

def analyze_bite_banner(image_path):
    print(f"\n--- Analyzing Bite Banner: {image_path} ---")
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not load bite image.")
        return
    
    h, w, _ = img.shape
    
    # The banner "¡Hay un pez en el anzuelo!..." is in the top-middle area.
    # Let's search around Y: [250, 450], X: [1000, 2440]
    # The banner has a very distinct dark background (almost black) with white/red text.
    # Let's print the average color of this region or look for the banner's specific features.
    # In Image 2, there is a text banner. Let's crop a potential banner region and save it.
    # Let's crop Y: [300, 420], X: [1100, 2340]
    y1, y2 = 300, 420
    x1, x2 = 1100, 2340
    crop = img[y1:y2, x1:x2]
    cv2.imwrite("roi_bite_banner.png", crop)
    print("Saved crop 'roi_bite_banner.png'")
    
    # We can detect the banner by checking if the average color of the banner region is dark,
    # but has a significant amount of white text in the center.
    # Let's convert to gray and see the histogram of the crop
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    white_pixels = np.sum(gray > 220)
    print(f"Number of white text pixels (>220 gray) in banner ROI: {white_pixels}")
    
    # Let's compare with the waiting image (Image 1) in the same ROI
    img_wait = cv2.imread(img_waiting)
    if img_wait is not None:
        crop_wait = img_wait[y1:y2, x1:x2]
        gray_wait = cv2.cvtColor(crop_wait, cv2.COLOR_BGR2GRAY)
        white_pixels_wait = np.sum(gray_wait > 220)
        print(f"Number of white text pixels (>220 gray) in waiting image (same ROI): {white_pixels_wait}")
        print(f"Difference ratio: {white_pixels / (white_pixels_wait + 1):.2f}")

def analyze_success_screen(image_path):
    print(f"\n--- Analyzing Success Screen: {image_path} ---")
    img = cv2.imread(image_path)
    if img is None:
        print("Error: Could not load success image.")
        return
    
    h, w, _ = img.shape
    
    # The success screen has "Presiona en un área vacía para cerrar" at the bottom center.
    # Let's crop the bottom center area.
    # Y: [1300, 1420], X: [1300, 2140]
    y1, y2 = 1300, 1420
    x1, x2 = 1300, 2140
    crop = img[y1:y2, x1:x2]
    cv2.imwrite("roi_success_text.png", crop)
    print("Saved crop 'roi_success_text.png'")
    
    # Check white pixels
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    white_pixels = np.sum(gray > 200)
    print(f"Number of white pixels (>200 gray) in success text ROI: {white_pixels}")
    
    # Let's check with the waiting image in the same ROI
    img_wait = cv2.imread(img_waiting)
    if img_wait is not None:
        crop_wait = img_wait[y1:y2, x1:x2]
        gray_wait = cv2.cvtColor(crop_wait, cv2.COLOR_BGR2GRAY)
        white_pixels_wait = np.sum(gray_wait > 200)
        print(f"Number of white pixels (>200 gray) in waiting image (same ROI): {white_pixels_wait}")
        print(f"Difference ratio: {white_pixels / (white_pixels_wait + 1):.2f}")

if __name__ == "__main__":
    analyze_minigame(img_minigame)
    analyze_bite_banner(img_bite)
    analyze_success_screen(img_success)
