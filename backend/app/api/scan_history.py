from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.database import get_db
from app.api.deps import get_current_consumer_user
from bson import ObjectId
from typing import List, Optional
import math

router = APIRouter()

@router.get("")
async def get_scan_history(
    current_user: dict = Depends(get_current_consumer_user),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    food_type: Optional[str] = None
):
    db = get_db()
    skip = (page - 1) * limit
    
    query = {"user_id": current_user["id"]}
    if food_type and food_type != "All":
        query["food_type"] = food_type
        
    sort_dir = -1 if order == "desc" else 1
    sort_field = sort_by
    
    total = await db.scan_history.count_documents(query)
    
    cursor = db.scan_history.find(query).sort(sort_field, sort_dir).skip(skip).limit(limit)
    scans = await cursor.to_list(length=limit)
    
    # Format for JSON
    for scan in scans:
        scan["_id"] = str(scan["_id"])
        
    return {
        "scans": scans,
        "total": total,
        "page": page,
        "pages": math.ceil(total / limit)
    }

@router.delete("/{scan_id}")
async def delete_scan(scan_id: str, current_user: dict = Depends(get_current_consumer_user)):
    db = get_db()
    
    try:
        obj_id = ObjectId(scan_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid scan ID")
        
    result = await db.scan_history.delete_one({"_id": obj_id, "user_id": current_user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Scan not found or not authorized")
        
    return {"message": "Scan deleted successfully"}
