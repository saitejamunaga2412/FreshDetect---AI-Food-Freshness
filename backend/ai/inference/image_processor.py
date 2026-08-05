import cv2
import numpy as np
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageProcessor:
    """
    Handles image preprocessing such as resize, normalize, noise reduction, and validation.
    """
    def __init__(self, target_size=(640, 640)):
        self.target_size = target_size

    def validate_image(self, image_path: str) -> bool:
        """Check if image exists and is readable."""
        if not os.path.exists(image_path):
            logger.error(f"Image not found: {image_path}")
            return False
        return True

    def load_image(self, image_path: str) -> np.ndarray:
        """Load image from path."""
        if not self.validate_image(image_path):
            raise FileNotFoundError(f"Cannot load image: {image_path}")
        
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Failed to read image (might be corrupted): {image_path}")
        return image

    def preprocess_for_freshness(self, image: np.ndarray) -> np.ndarray:
        """Apply noise reduction and standard sizing for visual analysis."""
        # Resize
        resized = cv2.resize(image, self.target_size)
        # Noise reduction using Gaussian Blur
        blurred = cv2.GaussianBlur(resized, (5, 5), 0)
        return blurred
