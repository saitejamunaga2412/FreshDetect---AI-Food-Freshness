from fastapi import APIRouter
from app.core.database import get_db

router = APIRouter()

@router.get("")
async def get_health():
    db = get_db()
    
    # 1. Check MongoDB
    mongo_status = True
    try:
        await db.command("ping")
    except Exception as e:
        mongo_status = f"False: {str(e)}"

    # 2. Check YOLO
    yolo_status = True
    try:
        from app.api.scanner import yolo_detector
        if getattr(yolo_detector, 'model', None) is None:
            yolo_status = "False: YOLO model weights not loaded into memory"
    except Exception as e:
        yolo_status = f"False: YOLO import error - {str(e)}"

    # 3. Check ML Model (Freshness)
    ml_status = True
    try:
        from app.api.scanner import freshness_predictor
        if getattr(freshness_predictor, 'model', None) is None:
            ml_status = "False: ML .pkl model file not loaded into memory"
    except Exception as e:
        ml_status = f"False: Freshness Predictor import error - {str(e)}"

    # 4. Check FoodKeeper Dataset
    foodkeeper_status = True
    try:
        from app.api.scanner import foodkeeper_service
        if getattr(foodkeeper_service, '_dataset', None) is None:
            foodkeeper_status = "False: FoodKeeper CSV dataset not loaded into memory"
    except Exception as e:
        foodkeeper_status = f"False: FoodKeeper import error - {str(e)}"

    # Determine overall status
    is_healthy = all(x is True for x in [mongo_status, yolo_status, ml_status, foodkeeper_status])

    return {
        "status": "healthy" if is_healthy else "degraded",
        "fastapi": True,
        "mongodb": mongo_status,
        "yolo_loaded": yolo_status,
        "freshness_model_loaded": ml_status,
        "foodkeeper_loaded": foodkeeper_status,
        "version": "1.0.0"
    }
