import os
import json
import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image
import logging

logger = logging.getLogger(__name__)

class VisualFreshnessClassifier:
    """
    Responsible ONLY for classifying visual freshness (Fresh vs Rotten) 
    from a cropped food image using MobileNetV3.
    """
    def __init__(self):
        self.model_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "ai",
            "models",
            "freshness",
            "freshness_classifier.pth"
        ))
        self.class_mapping_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "ai",
            "models",
            "freshness",
            "class_names.json"
        ))
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"[FreshnessClassifier] Loading model on {self.device}")
        
        # Initialize MobileNetV3-Small
        weights = models.MobileNet_V3_Small_Weights.DEFAULT
        self.model = models.mobilenet_v3_small(weights=weights)
        num_ftrs = self.model.classifier[3].in_features
        self.model.classifier[3] = nn.Linear(num_ftrs, 2)
        
        if os.path.exists(self.model_path):
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.model = self.model.to(self.device)
            self.model.eval()
            logger.info("[FreshnessClassifier] Model loaded successfully.")
        else:
            logger.warning(f"[FreshnessClassifier] Model not found at {self.model_path}")
            
        if os.path.exists(self.class_mapping_path):
            with open(self.class_mapping_path, "r") as f:
                self.class_mapping = json.load(f)
        else:
            self.class_mapping = {"0": "Fresh", "1": "Rotten"}
            
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def predict(self, image: Image.Image) -> dict:
        """
        Predicts Fresh or Rotten given a PIL Image crop.
        Returns a dict with 'prediction' and 'confidence'
        """
        if not os.path.exists(self.model_path):
            logger.error("Freshness model not available.")
            return {"prediction": "Unknown", "confidence": 0.0}
            
        try:
            image_tensor = self.transform(image.convert("RGB")).unsqueeze(0).to(self.device)
            with torch.no_grad():
                outputs = self.model(image_tensor)
                probs = torch.nn.functional.softmax(outputs, dim=1)
                confidence, predicted = torch.max(probs, 1)
                
            pred_class = self.class_mapping[str(predicted.item())]
            conf_val = confidence.item()
            
            logger.info(f"[FreshnessClassifier] Predicted: {pred_class} with confidence {conf_val:.4f}")
            return {
                "prediction": pred_class,
                "confidence": conf_val
            }
        except Exception as e:
            logger.error(f"[FreshnessClassifier] Error during prediction: {e}")
            return {"prediction": "Unknown", "confidence": 0.0}
