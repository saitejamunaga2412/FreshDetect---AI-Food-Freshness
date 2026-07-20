import cv2
import numpy as np

def assess_freshness(image_bytes):
    """
    Analyzes an image and returns a freshness score (0-100) and status.
    This is a heuristic-based engine simulating a trained ML model.
    """
    try:
        # Convert bytes to numpy array then to OpenCV image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return {"error": "Invalid image data"}
            
        # 1. Convert to HSV color space for better analysis
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        
        # 2. Calculate brightness and saturation
        brightness = np.mean(hsv_img[:, :, 2])
        saturation = np.mean(hsv_img[:, :, 1])
        
        # 3. Detect "dark spots" (potential spoilage/bruising)
        # Convert to grayscale and threshold to find dark regions
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Focus on the center of the image to avoid background shadows
        h, w = gray.shape
        center_gray = gray[int(h*0.2):int(h*0.8), int(w*0.2):int(w*0.8)]
        
        # Threshold for severe rot/spoilage (intensity < 30) instead of just shadows
        _, dark_mask = cv2.threshold(center_gray, 30, 255, cv2.THRESH_BINARY_INV)
        
        # Calculate percentage of dark spots relative to the center
        total_pixels = center_gray.size
        dark_pixels = cv2.countNonZero(dark_mask)
        dark_ratio = (dark_pixels / total_pixels) * 100
        
        # 4. Calculate Freshness Score
        # Base score starts at 100.
        score = 100
        
        # Gentle penalty for dark spots (assuming some might just be shadows)
        if dark_ratio > 1:
            penalty = min(dark_ratio * 2, 40) # Cap penalty at 40
            score -= penalty
            
        # Penalty for low saturation (faded colors usually mean less fresh)
        if saturation < 80:
            score -= (80 - saturation) * 0.3
            
        score = max(10, min(100, round(score)))
        
        # 5. Determine Status
        status = "Fresh"
        if score < 50:
            status = "Spoiled"
        elif score < 75:
            status = "Expiring Soon"
            
        # 6. Simulate AI Confidence based on image clarity (variance of Laplacian)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        confidence = min(99.9, max(60.0, 60 + (laplacian_var / 50)))
        
        return {
            "score": int(score),
            "status": status,
            "confidence": round(confidence, 1),
            "metrics": {
                "dark_spot_ratio": round(dark_ratio, 2),
                "brightness": round(brightness, 2),
                "saturation": round(saturation, 2)
            }
        }
        
    except Exception as e:
        return {"error": str(e)}
