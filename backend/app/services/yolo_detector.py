import os
import logging
from ultralytics import YOLO

logger = logging.getLogger(__name__)

class YoloDetector:
    """
    Responsible ONLY for detecting the food and identifying its name and type.
    Must NOT calculate freshness.
    """
    def __init__(self):
        # Models are located at weights/best.pt relative to project root
        self.model_path = os.path.abspath(os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "weights",
            "best.pt"
        ))
        
        logger.info(f"[YoloDetector] Loading model from absolute path: {self.model_path}")
        self.model = YOLO(self.model_path)
        
        num_classes = len(self.model.names)
        logger.info(f"[YoloDetector] Model loaded successfully. Number of classes: {num_classes}")
        logger.info(f"[YoloDetector] Model class names: {self.model.names}")
        
        # Simple mapping for food types. Extended to cover all model fruits/vegetables.
        self.fruit_classes = {'Apple', 'Banana', 'Grape', 'Orange', 'Pineapple', 'Watermelon', 'Mango', 'Guava', 'Jujube', 'Pomegranate', 'Strawberry'}
        self.vegetable_classes = {'Tomato', 'Potato', 'Carrot', 'Cucumber', 'Brinjal', 'Capsicum', 'Onion', 'Bellpepper'}
        
        # Configurable confidence threshold
        self.confidence_threshold = float(os.getenv("MIN_DETECTION_CONFIDENCE", "0.40"))
        logger.info(f"[YoloDetector] Using confidence threshold: {self.confidence_threshold}")

    def _normalize_class_name(self, raw_class_name: str) -> tuple[str, str]:
        # Example: "carrot_fresh" -> ("Carrot", "Fresh"), "apple_rotten" -> ("Apple", "Rotten")
        parts = raw_class_name.rsplit("_", 1)
        base_class = parts[0]
        visual_condition = parts[1].title() if len(parts) > 1 else "Unknown"
        
        # Title case to match backend sets: "carrot" -> "Carrot"
        normalized = base_class.title()
        
        # Synonyms and mapping fixes
        mapping = {
            "Bellpepper": "Capsicum"
        }
        return mapping.get(normalized, normalized), visual_condition

    def _get_food_type(self, food_name: str) -> str:
        if food_name in self.fruit_classes:
            return "Fruit"
        if food_name in self.vegetable_classes:
            return "Vegetable"
        return "Unknown"

    def detect(self, image_path: str) -> dict:
        """
        Detects food in the given image.
        Returns the highest confidence detection that passes the threshold and is supported.
        """
        logger.info(f"[YoloDetector] Starting inference on image size: {os.path.getsize(image_path)} bytes")
        results = self.model.predict(image_path, verbose=False)
        
        best_detection = None
        highest_conf = -1.0
        
        raw_detections = []
        filtered_detections = []

        for result in results:
            # Handle classification models
            if result.probs is not None:
                cls_id = int(result.probs.top1)
                conf = float(result.probs.top1conf)
                raw_food_name = self.model.names[cls_id]
                normalized_name, visual_condition = self._normalize_class_name(raw_food_name)
                food_type = self._get_food_type(normalized_name)
                bbox = [] # No bbox for classification
                
                det_info = {
                    "class_id": cls_id,
                    "raw_name": raw_food_name,
                    "normalized_name": normalized_name,
                    "visual_condition": visual_condition,
                    "confidence": round(conf, 4),
                    "food_type": food_type,
                    "bbox": bbox
                }
                raw_detections.append(det_info)
                
                reason = None
                if conf < self.confidence_threshold:
                    reason = f"Confidence {round(conf, 4)} is below threshold {self.confidence_threshold}"
                elif food_type == "Unknown":
                    reason = f"Class '{normalized_name}' is not in supported fruit/vegetable lists."
                
                if reason:
                    det_info["rejection_reason"] = reason
                    filtered_detections.append(det_info)
                else:
                    det_info["status"] = "Accepted"
                    highest_conf = conf
                    best_detection = {
                        "food_name": normalized_name,
                        "food_type": food_type,
                        "visual_condition": visual_condition,
                        "raw_name": raw_food_name,
                        "detection_confidence": round(conf, 4),
                        "bbox": bbox,
                        "raw_detections": raw_detections,
                        "filtered_detections": filtered_detections
                    }
            
            # Handle detection models (if fallback happens)
            elif result.boxes is not None:
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    raw_food_name = self.model.names[cls_id]
                    normalized_name, visual_condition = self._normalize_class_name(raw_food_name)
                    food_type = self._get_food_type(normalized_name)
                    bbox = [int(x) for x in box.xyxy[0].tolist()]
                    
                    det_info = {
                        "class_id": cls_id,
                        "raw_name": raw_food_name,
                        "normalized_name": normalized_name,
                        "visual_condition": visual_condition,
                        "confidence": round(conf, 4),
                        "food_type": food_type,
                        "bbox": bbox
                    }
                    raw_detections.append(det_info)
                    
                    reason = None
                    if conf < self.confidence_threshold:
                        reason = f"Confidence {round(conf, 4)} is below threshold {self.confidence_threshold}"
                    elif food_type == "Unknown":
                        reason = f"Class '{normalized_name}' is not in supported fruit/vegetable lists."
                    
                    if reason:
                        det_info["rejection_reason"] = reason
                        filtered_detections.append(det_info)
                    else:
                        det_info["status"] = "Accepted"
                        if conf > highest_conf:
                            highest_conf = conf
                            best_detection = {
                                "food_name": normalized_name,
                                "food_type": food_type,
                                "visual_condition": visual_condition,
                                "raw_name": raw_food_name,
                                "detection_confidence": round(conf, 4),
                                "bbox": bbox,
                                "raw_detections": raw_detections,
                                "filtered_detections": filtered_detections
                            }

        logger.info(f"[YoloDetector] Raw Detections: {len(raw_detections)} found. {raw_detections}")
        if filtered_detections:
            logger.info(f"[YoloDetector] Filtered Detections: {len(filtered_detections)} removed. {filtered_detections}")

        if best_detection:
            logger.info(f"[YoloDetector] Final Accepted Object: {best_detection['food_name']} with confidence {best_detection['detection_confidence']}")
        else:
            logger.warning("[YoloDetector] No valid objects passed filtering criteria.")

        # If no valid detection found, we can still return a dictionary with raw data for the scanner to format
        if not best_detection:
            return {
                "food_name": None,
                "raw_detections": raw_detections,
                "filtered_detections": filtered_detections
            }
            
        return best_detection
