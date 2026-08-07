import os
import uuid
import time
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from typing import Optional
from fastapi.concurrency import run_in_threadpool
import logging

logger = logging.getLogger(__name__)

from app.services.yolo_detector import YoloDetector
from app.services.freshness_predictor import FreshnessPredictor
from app.services.foodkeeper_service import FoodKeeperService
from app.services.freshness_classifier import VisualFreshnessClassifier
from PIL import Image

# --- Scoring Constants ---
VISUAL_WEIGHT = 0.40
ENVIRONMENT_WEIGHT = 0.25
SHELF_LIFE_WEIGHT = 0.20
PRODUCT_AGE_WEIGHT = 0.15

FRESH_THRESHOLD = 90
GOOD_THRESHOLD = 75
WARNING_THRESHOLD = 60
SPOILED_THRESHOLD = 40
# -------------------------

router = APIRouter()

# Initialize services
yolo_detector = YoloDetector()
freshness_predictor = FreshnessPredictor()
foodkeeper_service = FoodKeeperService()
visual_classifier = VisualFreshnessClassifier()

from app.core.config import settings

UPLOAD_DIR = settings.UPLOAD_DIR
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

from app.api.deps import get_current_consumer_user

@router.post("/scan")
async def scan_food(
    image: UploadFile = File(...), 
    temp: float = Form(...),
    humid: float = Form(...),
    current_user: dict = Depends(get_current_consumer_user)
):
    logger.info(f"Image received from user {current_user.get('id')}")
    # Validate file type using MIME and Extension
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if image.content_type not in allowed_types:
        logger.error(f"Validation failed: Unsupported image format {image.content_type}")
        raise HTTPException(status_code=400, detail="Unsupported image format")
        
    # Magic Number Validation (Pure Python)
    magic_bytes = await image.read(12)
    await image.seek(0)
    is_valid_magic = False
    if magic_bytes.startswith(b'\xff\xd8\xff'): # JPEG
        is_valid_magic = True
    elif magic_bytes.startswith(b'\x89PNG\r\n\x1a\n'): # PNG
        is_valid_magic = True
    elif magic_bytes[8:12] == b'WEBP': # WEBP
        is_valid_magic = True
        
    if not is_valid_magic:
        logger.error("Validation failed: Invalid file signature (Magic Numbers mismatch)")
        raise HTTPException(status_code=400, detail="Unsupported image format")

    # Validate file size (10 MB limit)
    image.file.seek(0, 2) # Seek to end
    file_size = image.file.tell()
    image.file.seek(0) # Seek back to beginning
    if file_size > 10 * 1024 * 1024:
        logger.error(f"Validation failed: Image too large ({file_size} bytes)")
        raise HTTPException(status_code=400, detail="Image too large")
        
    logger.info("Validation passed")
    
    # Save uploaded file
    file_ext = image.filename.split(".")[-1]
    filename = f"{int(time.time())}-{uuid.uuid4().hex[:6]}.{file_ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)

    try:
        await image.seek(0)
        with open(file_path, "wb") as buffer:
            buffer.write(await image.read())
            
        abs_file_path = os.path.abspath(file_path)
        
        # 1. YOLO Detect (Offloaded to threadpool to prevent event loop blocking)
        logger.info("YOLO started")
        detection = await run_in_threadpool(yolo_detector.detect, abs_file_path)
        logger.info("YOLO finished")
        
        if not detection or not detection.get("food_name"):
            raw_dets = detection.get("raw_detections", []) if detection else []
            filt_dets = detection.get("filtered_detections", []) if detection else []
            
            error_details = []
            if raw_dets:
                error_details.append(f"Raw detections: {[ { 'name': d['raw_name'], 'confidence': d['confidence'] } for d in raw_dets ]}")
            if filt_dets:
                reasons = [ d.get("rejection_reason") for d in filt_dets if "rejection_reason" in d ]
                error_details.append(f"Reason for rejection: {', '.join(reasons)}")
            
            if not error_details:
                error_details = ["No objects detected at all (empty detection)"]
                
            error_msg = f"No supported fruit or vegetable detected. {'; '.join(error_details)}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
            
        fruit_name = detection.get("food_name")
        detection_confidence = detection.get("detection_confidence")
        # 2. Knowledge Base Override & FoodKeeper Lookup
        from app.core.database import get_db
        db = get_db()
        
        kb_override = await db.knowledge_base.find_one({"name": {"$regex": f"^{fruit_name}$", "$options": "i"}})
        foodkeeper_data = foodkeeper_service.lookup(fruit_name)
        
        # Merge data. Priority: 1. KB Override, 2. FoodKeeper, 3. Defaults
        final_kb_data = None
        if foodkeeper_data:
            final_kb_data = foodkeeper_data.copy()
            logger.info(f"FoodKeeper lookup successful for: {fruit_name}")
        else:
            final_kb_data = {
                "name": fruit_name,
                "recommended_temperature": "Not Available",
                "recommended_humidity": "Not Available",
                "packaging_material": "Not Available",
                "storage_area": "Room Temperature",
                "shelf_life": {},
                "storage_instructions": "Not Available"
            }
            logger.info(f"FoodKeeper data not available for: {fruit_name}")

        if kb_override:
            logger.info(f"Applying Knowledge Base override for: {fruit_name}")
            if kb_override.get("ideal_temperature"):
                final_kb_data["recommended_temperature"] = f"{kb_override['ideal_temperature']} °C"
            if kb_override.get("ideal_humidity"):
                final_kb_data["recommended_humidity"] = f"{kb_override['ideal_humidity']} %"
            if kb_override.get("shelf_life_days"):
                loc = kb_override.get("category", "pantry").lower()
                key = "pantry" if "room" in loc else ("refrigerator" if "refriger" in loc else "freezer")
                final_kb_data["shelf_life"][key] = f"{kb_override['shelf_life_days']} Days"
            if kb_override.get("spoilage_symptoms"):
                final_kb_data["storage_instructions"] = "Spoilage Symptoms: " + ", ".join(kb_override["spoilage_symptoms"])
        # 3. Visual Freshness CNN (Crop and Predict)
        bbox = detection.get("bbox")
        try:
            with Image.open(abs_file_path) as img:
                if bbox and len(bbox) == 4:
                    cropped_img = img.crop((bbox[0], bbox[1], bbox[2], bbox[3]))
                else:
                    cropped_img = img
                cnn_result = visual_classifier.predict(cropped_img)
        except Exception as e:
            logger.error(f"Error cropping/classifying image: {e}")
            cnn_result = {"prediction": "Unknown", "confidence": 0.0}

        visual_condition = cnn_result.get("prediction", "Unknown")
        cnn_confidence = cnn_result.get("confidence", 0.0)
        logger.info(f"YOLO detected: {detection.get('raw_name')} with confidence {detection_confidence}")
        logger.info(f"CNN predicted: {visual_condition} with confidence {cnn_confidence}")

        # 4. Environmental ML Prediction
        # Convert food_name to capitalized for standard mapping (e.g. "Apple")
        fruit_name_capitalized = detection.get('food_name', 'Unknown').capitalize()
        freshness_result = freshness_predictor.predict(fruit_name_capitalized, temp, humid)
        freshness_probability = freshness_result.get("probability")
        
        # Weighted Scoring Model
        storage_score = int(freshness_probability * 100)
        shelf_life_score = 100 if final_kb_data and final_kb_data.get("shelf_life") else 50
        product_age_score = 100 # Defaulting to fresh age since no input is provided
        
        if visual_condition == "Fresh":
            visual_score = int(cnn_confidence * 100) if cnn_confidence > 0 else 100
        elif visual_condition == "Rotten":
            visual_score = 100 - (int(cnn_confidence * 100) if cnn_confidence > 0 else 100)
        else:
            visual_score = 50
            
        visual_score_text = visual_condition
        
        # Calculate overall score normalized over available 100% weight (40% visual + 60% others)
        total_available_weight = VISUAL_WEIGHT + ENVIRONMENT_WEIGHT + SHELF_LIFE_WEIGHT + PRODUCT_AGE_WEIGHT
        calculated_score = (visual_score * VISUAL_WEIGHT) + (storage_score * ENVIRONMENT_WEIGHT) + (shelf_life_score * SHELF_LIFE_WEIGHT) + (product_age_score * PRODUCT_AGE_WEIGHT)
        overall_score = int(calculated_score / total_available_weight)
        overall_score = max(0, min(100, overall_score))
        
        # 5-Tier Category Mapping
        if overall_score >= FRESH_THRESHOLD:
            freshness_category = "Fresh"
        elif overall_score >= GOOD_THRESHOLD:
            freshness_category = "Good"
        elif overall_score >= WARNING_THRESHOLD:
            freshness_category = "Acceptable"
        elif overall_score >= SPOILED_THRESHOLD:
            freshness_category = "Near Spoilage"
        else:
            freshness_category = "Spoiled"

        # Spoilage Reason Logic
        spoilage_reason = "None"
        if freshness_category in ["Near Spoilage", "Spoiled"]:
            if temp and temp > 25: spoilage_reason = "High storage temperature detected."
            elif humid and humid > 80: spoilage_reason = "Excessive humidity detected."
            else: spoilage_reason = "Sub-optimal humidity or temperature detected."

        # Final result structure
        result = {
            "fruit": fruit_name,
            "recommended_temperature": final_kb_data.get("recommended_temperature") if final_kb_data else "Not Available",
            "recommended_humidity": final_kb_data.get("recommended_humidity") if final_kb_data else "Not Available",
            "storage_area": final_kb_data.get("storage_area") if final_kb_data else "Not Available",
            "packaging_material": final_kb_data.get("packaging_material") if final_kb_data else "Not Available",
            "shelf_life": final_kb_data.get("shelf_life") if final_kb_data else "Not Available",
            "confidence": f"{round(detection_confidence * 100, 1)}%",
            "overall_score": overall_score,
            "freshness_category": freshness_category,
            "yolo_class": detection.get("raw_name"),
            "environment_score": storage_score,
            "segmented_image": detection.get("segmented_image_url"),
            "weighted_scores": {
                "visual_condition": visual_score_text,
                "storage": storage_score,
                "shelf_life": shelf_life_score,
                "product_age": product_age_score
            },
            "storage_instructions": final_kb_data.get("storage_instructions") if final_kb_data else "Not Available"
        }
        logger.info(f"Detected fruit: {fruit_name}")
        logger.info(f"Visual Condition: {visual_condition}")
        logger.info(f"Freshness probability: {freshness_probability}")
        logger.info(f"Predicted label: {freshness_result.get('prediction')}")
        logger.info(f"Threshold: overall_score >= 90 (Fresh), >= 75 (Good), >= 60 (Acceptable)")
        logger.info(f"Returned JSON: {result}")
        
        logger.info(f"API response generated successfully for {fruit_name}")
        from app.core.database import get_db
        from datetime import datetime
        db = get_db()
        
        scan_record = {
            "user_id": current_user["id"],
            "fruit": fruit_name,
            "detection_confidence": detection_confidence,
            "freshness_category": freshness_category,
            "overall_score": overall_score,
            "weighted_scores": result["weighted_scores"],
            "spoilage_reason": spoilage_reason,
            "shelf_life": result.get("shelf_life"),
            "storage_instructions": result.get("storage_instructions"),
            "image_url": f"/uploads/{filename}",
            "is_saved_to_inventory": False,
            "created_at": datetime.utcnow()
        }
        
        inserted_scan = await db.scan_history.insert_one(scan_record)
        scan_id = str(inserted_scan.inserted_id)

        # Return identical wrapper structure for frontend, with the new `result` payload inside
        return {
            "success": True,
            "message": "Prediction successful",
            "image": {
                "fileName": filename,
                "path": file_path,
            },
            "detections": [result],
            "result": result,
            "scanId": scan_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
