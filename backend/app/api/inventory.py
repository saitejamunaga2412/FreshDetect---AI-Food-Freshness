from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.api.deps import get_current_user, require_inventory_view, require_inventory_add_edit, require_inventory_delete
from app.models.food_item import FoodItemCreate
from bson import ObjectId
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("")
async def get_inventory(db = Depends(get_db), current_user: dict = Depends(require_inventory_view)):
    try:
        items_cursor = db["fooditems"].find({"addedBy": ObjectId(current_user["_id"])}).sort("createdAt", -1)
        items = await items_cursor.to_list(length=100)
        
        # Format for frontend
        formatted_items = []
        for item in items:
            item["id"] = str(item["_id"])
            item["_id"] = str(item["_id"]) # Frontend might expect _id or id
            item["addedBy"] = {
                "_id": current_user["id"],
                "name": current_user["name"],
                "email": current_user["email"]
            }
            formatted_items.append(item)
            
        return formatted_items
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch inventory.")

@router.post("")
async def create_inventory_item(item: FoodItemCreate, db = Depends(get_db), current_user: dict = Depends(require_inventory_add_edit)):
    try:
        new_item = item.model_dump()
        new_item["addedBy"] = ObjectId(current_user["_id"])
        new_item["createdAt"] = datetime.utcnow()
        new_item["updatedAt"] = datetime.utcnow()
        
        result = await db["fooditems"].insert_one(new_item)
        new_item["_id"] = str(result.inserted_id)
        new_item["id"] = str(result.inserted_id)
        new_item["addedBy"] = {
            "_id": current_user["id"],
            "name": current_user["name"],
            "email": current_user["email"]
        }
        
        # Link to scan history if scanId is provided
        if item.scanId:
            try:
                scan_obj_id = ObjectId(item.scanId)
                await db["scan_history"].update_one(
                    {"_id": scan_obj_id, "user_id": current_user["id"]},
                    {"$set": {"is_saved_to_inventory": True, "inventory_id": str(result.inserted_id)}}
                )
            except Exception as ex:
                logger.error(f"Failed to link scan history: {ex}")
                
        return new_item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{item_id}")
async def update_inventory_item(item_id: str, item: FoodItemCreate, db = Depends(get_db), current_user: dict = Depends(require_inventory_add_edit)):
    try:
        if not ObjectId.is_valid(item_id):
            raise HTTPException(status_code=400, detail="Invalid item ID")
            
        update_data = item.model_dump(exclude_unset=True)
        update_data["updatedAt"] = datetime.utcnow()
        
        result = await db["fooditems"].update_one(
            {"_id": ObjectId(item_id), "addedBy": ObjectId(current_user["_id"])},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Item not found or unauthorized")
            
        return {"message": "Item updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{item_id}")
async def delete_inventory_item(item_id: str, db = Depends(get_db), current_user: dict = Depends(require_inventory_delete)):
    try:
        if not ObjectId.is_valid(item_id):
            raise HTTPException(status_code=400, detail="Invalid item ID")
            
        result = await db["fooditems"].delete_one(
            {"_id": ObjectId(item_id), "addedBy": ObjectId(current_user["_id"])}
        )
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Item not found or unauthorized")
            
        return {"message": "Item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# NEW RETAILER BATCH ENDPOINTS (Phase 5 & Shelf-Life)
# ---------------------------------------------------------
from app.models.inventory import InventoryBatchCreate, InventoryBatchOut, InventoryBatchUpdate
from typing import Optional
from app.services.foodkeeper_service import FoodKeeperService

def apply_dynamic_recommendations(batch: dict) -> dict:
    now = datetime.utcnow()
    
    # Base Recommendations
    batch["storage_recommendation"] = "Store at Room Temperature"
    batch["consumption_recommendation"] = "Safe to Store"
    batch["inventory_rotation_recommendation"] = "Rotate Stock"
    batch["waste_reduction_recommendation"] = "None"
    batch["quality_improvement_recommendation"] = "Improve Storage Conditions"
    
    # Shelf-Life Dynamic Calculations
    exp_date = batch.get("estimated_expiry_date")
    if exp_date:
        days_rem = (exp_date - now).days
        if days_rem < 0:
            batch["days_remaining"] = 0
            batch["risk_forecast"] = "Expired"
            batch["shelf_life_trend"] = "Expired"
            batch["consumption_recommendation"] = "Discard immediately"
            batch["inventory_rotation_recommendation"] = "Remove from active stock"
            batch["waste_reduction_recommendation"] = "Remove Expired Item"
        elif days_rem == 0:
            batch["days_remaining"] = 0
            batch["risk_forecast"] = "High Risk"
            batch["shelf_life_trend"] = "Decreasing rapidly"
            batch["consumption_recommendation"] = "Consume Today"
            batch["inventory_rotation_recommendation"] = "FEFO"
            batch["waste_reduction_recommendation"] = "Prioritize Consumption"
        elif days_rem <= 2:
            batch["days_remaining"] = days_rem
            batch["risk_forecast"] = "High Risk"
            batch["shelf_life_trend"] = "Decreasing rapidly"
            batch["consumption_recommendation"] = "Consume Within 2 Days"
            batch["inventory_rotation_recommendation"] = "Prioritize Batch"
            batch["waste_reduction_recommendation"] = "Donate Soon"
        elif days_rem <= 7:
            batch["days_remaining"] = days_rem
            batch["risk_forecast"] = "Medium Risk"
            batch["shelf_life_trend"] = "Decreasing"
            batch["consumption_recommendation"] = "Use Immediately"
            batch["inventory_rotation_recommendation"] = "Rotate Stock"
            batch["waste_reduction_recommendation"] = "Discount Product"
        else:
            batch["days_remaining"] = days_rem
            batch["risk_forecast"] = "Low Risk"
            batch["shelf_life_trend"] = "Stable"
            batch["consumption_recommendation"] = "Safe to Store"
            batch["inventory_rotation_recommendation"] = "Rotate Stock"
            batch["waste_reduction_recommendation"] = "None"
    else:
        batch["days_remaining"] = None
        batch["risk_forecast"] = "Unknown"
        batch["shelf_life_trend"] = "Unknown"
        
    # Storage Duration
    received_date = batch.get("received_date")
    if received_date:
        storage_dur_days = (now - received_date).days
        batch["storage_duration"] = f"{storage_dur_days} days"
    else:
        batch["storage_duration"] = "0 days"
        
    # Storage Compliance & Optimization
    batch["storage_compliance"] = "Compliant"
    batch["storage_optimization"] = "Storage conditions are optimal."
    
    fk_service = FoodKeeperService()
    fk_data = fk_service.lookup(batch.get("fruit_name"))
    if fk_data:
        optimal_area = fk_data.get("storage_area", "Room Temperature")
        current_loc = batch.get("storage_location", "Room Temperature")
        
        # Dynamic Storage Recommendation
        if optimal_area.lower() != current_loc.lower():
            batch["storage_recommendation"] = f"Move to {optimal_area}"
            batch["storage_compliance"] = "Warning"
            batch["storage_optimization"] = f"Consider moving to {optimal_area} to maximize shelf-life."
            
            # Extreme cases
            if current_loc == "Room Temperature" and optimal_area == "Refrigerator":
                batch["storage_compliance"] = "Non-Compliant"
                batch["storage_optimization"] = "Move to Refrigerator immediately to prevent rapid spoilage."
            elif current_loc == "Freezer" and optimal_area == "Refrigerator":
                batch["storage_compliance"] = "Warning"
                batch["storage_optimization"] = "Freezing may damage texture. Consider Refrigerator."
        else:
            if optimal_area == "Refrigerator" and batch.get("days_remaining") is not None and batch["days_remaining"] <= 2:
                batch["storage_recommendation"] = "Freeze Immediately"
            else:
                batch["storage_recommendation"] = f"Store at {optimal_area}"

        # Quality Improvement Recommendation based on temp/humidity
        temp = batch.get("temperature")
        hum = batch.get("humidity")
        
        qi_recs = []
        if current_loc == "Refrigerator" and temp is not None:
            if temp > 5.0:
                batch["storage_compliance"] = "Non-Compliant"
                batch["storage_optimization"] = "Reduce Refrigerator temperature below 5°C."
                qi_recs.append("Reduce Temperature")
        if current_loc == "Room Temperature" and temp is not None:
            if temp > 25.0:
                qi_recs.append("Reduce Temperature")
                
        if hum is not None:
            if hum < 50.0 and optimal_area == "Refrigerator":
                batch["storage_optimization"] = "Increase humidity to prevent wilting."
                qi_recs.append("Improve Humidity")
        
        if current_loc == "Room Temperature":
            qi_recs.append("Avoid Direct Sunlight")
            
        if qi_recs:
            batch["quality_improvement_recommendation"] = qi_recs[0]
        else:
            batch["quality_improvement_recommendation"] = "Improve Storage Conditions"

    return batch

@router.get("/batches", response_model=list[InventoryBatchOut])
async def get_inventory_batches(
    skip: int = 0, 
    limit: int = 20, 
    status: Optional[str] = None,
    fruit_name: Optional[str] = None,
    db = Depends(get_db), 
    current_user: dict = Depends(require_inventory_view)
):
    collection = db["inventory_batches"]
    
    # Ownership Check (IDOR prevention)
    query = {"retailer_id": current_user["id"], "is_active": True}
    
    if status == "archived":
        query["is_active"] = False
        
    if fruit_name:
        query["fruit_name"] = {"$regex": f"^{fruit_name}$", "$options": "i"}
        
    cursor = collection.find(query).skip(skip).limit(limit).sort("received_date", -1)
    
    now = datetime.utcnow()
    batches = []
    
    fk_service = FoodKeeperService()
    
    
    for batch in await cursor.to_list(length=limit):
        batch["_id"] = str(batch["_id"])
        batch = apply_dynamic_recommendations(batch)
        batches.append(batch)
        
    return batches
        


@router.post("/batches", response_model=InventoryBatchOut, status_code=201)
async def create_inventory_batch(
    batch_in: InventoryBatchCreate,
    db = Depends(get_db),
    current_user: dict = Depends(require_inventory_add_edit)
):
    collection = db["inventory_batches"]
    
    batch_dict = batch_in.model_dump()
    batch_dict["retailer_id"] = current_user["id"]
    batch_dict["received_date"] = datetime.utcnow()
    batch_dict["is_active"] = True
    batch_dict["storage_history"] = [{
        "timestamp": datetime.utcnow().isoformat(),
        "user": current_user.get("name", "Unknown"),
        "field": "Initialization",
        "previous": None,
        "new": f"Location: {batch_dict.get('storage_location')}, Temp: {batch_dict.get('temperature')}, Hum: {batch_dict.get('humidity')}"
    }]
    
    # Estimate Expiry Date from FoodKeeper dynamically
    fk_service = FoodKeeperService()
    fk_data = fk_service.lookup(batch_in.fruit_name)
    batch_dict["estimated_expiry_date"] = None
    days_to_add = None
    
    if fk_data and fk_data.get("shelf_life"):
        sl_dict = fk_data["shelf_life"]
        loc = batch_dict.get("storage_location", "Room Temperature").lower()
        key = "pantry" if "room" in loc else ("refrigerator" if "refriger" in loc else "freezer")
        
        sl_str = sl_dict.get(key)
        if sl_str:
            days_to_add = FoodKeeperService.parse_shelf_life_string(sl_str)
            
    if days_to_add is None:
        # Fallback to general Knowledge Base
        kb_item = await db["knowledge_base"].find_one({"name": {"$regex": f"^{batch_in.fruit_name}$", "$options": "i"}})
        if kb_item and kb_item.get("shelf_life_days"):
            days_to_add = kb_item["shelf_life_days"]
            
    if days_to_add is not None:
        from datetime import timedelta
        batch_dict["estimated_expiry_date"] = batch_dict["received_date"] + timedelta(days=days_to_add)
        
    result = await collection.insert_one(batch_dict)
    batch_dict["_id"] = str(result.inserted_id)
    return apply_dynamic_recommendations(batch_dict)

@router.patch("/batches/{batch_id}", response_model=InventoryBatchOut)
async def update_inventory_batch(
    batch_id: str,
    batch_in: InventoryBatchUpdate,
    db = Depends(get_db),
    current_user: dict = Depends(require_inventory_add_edit)
):
    collection = db["inventory_batches"]
    
    if not ObjectId.is_valid(batch_id):
        raise HTTPException(status_code=400, detail="Invalid batch ID")
        
    update_data = batch_in.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields provided for update")
        
        existing_batch = await collection.find_one({"_id": ObjectId(batch_id), "retailer_id": current_user["id"]})
        if existing_batch:
            # Handle Storage History Tracking
            history = list(existing_batch.get("storage_history", []))
            
            history_changed = False
            def add_history(field, prev, new_val):
                nonlocal history_changed
                if prev != new_val:
                    history.append({
                        "timestamp": datetime.utcnow().isoformat(),
                        "user": current_user.get("name", "Unknown"),
                        "field": field,
                        "previous": prev,
                        "new": new_val
                    })
                    history_changed = True
            
            loc_changed = False
            if "storage_location" in update_data:
                old_loc = existing_batch.get("storage_location")
                new_loc = update_data["storage_location"]
                if old_loc != new_loc:
                    add_history("storage_location", old_loc, new_loc)
                    loc_changed = True
                    
            if "temperature" in update_data:
                add_history("temperature", existing_batch.get("temperature"), update_data["temperature"])
            
            if "humidity" in update_data:
                add_history("humidity", existing_batch.get("humidity"), update_data["humidity"])
                
            if history_changed:
                update_data["storage_history"] = history
            
            # Recalculate Expiry if location changed
            if loc_changed:
                fk_service = FoodKeeperService()
                fk_data = fk_service.lookup(existing_batch.get("fruit_name", ""))
                days_to_add = None
            
            if fk_data and fk_data.get("shelf_life"):
                sl_dict = fk_data["shelf_life"]
                loc = update_data["storage_location"].lower()
                key = "pantry" if "room" in loc else ("refrigerator" if "refriger" in loc else "freezer")
                sl_str = sl_dict.get(key)
                if sl_str:
                    days_to_add = FoodKeeperService.parse_shelf_life_string(sl_str)
                    
            if days_to_add is None:
                # Fallback to general Knowledge Base
                kb_item = await db["knowledge_base"].find_one({"name": {"$regex": f"^{existing_batch.get('fruit_name', '')}$", "$options": "i"}})
                if kb_item and kb_item.get("shelf_life_days"):
                    days_to_add = kb_item["shelf_life_days"]
                    
            if days_to_add is not None:
                from datetime import timedelta
                rcv_date = existing_batch.get("received_date", datetime.utcnow())
                update_data["estimated_expiry_date"] = rcv_date + timedelta(days=days_to_add)

    # Strict Ownership Check in the query
    result = await collection.find_one_and_update(
        {"_id": ObjectId(batch_id), "retailer_id": current_user["id"]},
        {"$set": update_data},
        return_document=True
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Batch not found or unauthorized")
        
    result["_id"] = str(result["_id"])
    return apply_dynamic_recommendations(result)

@router.delete("/batches/{batch_id}", status_code=204)
async def delete_inventory_batch(
    batch_id: str,
    db = Depends(get_db),
    current_user: dict = Depends(require_inventory_delete)
):
    collection = db["inventory_batches"]
    
    if not ObjectId.is_valid(batch_id):
        raise HTTPException(status_code=400, detail="Invalid batch ID")
        
    # Soft Delete & Ownership Check
    result = await collection.update_one(
        {"_id": ObjectId(batch_id), "retailer_id": current_user["id"]},
        {"$set": {"is_active": False}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Batch not found or unauthorized")
    
    return None

@router.get("/stats")
async def get_inventory_stats(
    db = Depends(get_db),
    current_user: dict = Depends(require_inventory_view)
):
    collection = db["inventory_batches"]
    
    now = datetime.utcnow()
    near_expiry_threshold = now + __import__('datetime').timedelta(days=3)
    
    # Ownership Check
    query = {"retailer_id": current_user["id"], "is_active": True}
    
    batches = await collection.find(query).to_list(length=1000)
    
    total_items = 0
    fruits_count = 0
    vegetables_count = 0
    near_expiry_count = 0
    expired_count = 0
    low_stock_count = 0
    
    for b in batches:
        qty = b.get("quantity", 0)
        total_items += qty
        
        cat = b.get("category", "").lower()
        if "fruit" in cat:
            fruits_count += qty
        elif "veg" in cat:
            vegetables_count += qty
            
        if qty < 10:
            low_stock_count += 1
            
        if b.get("estimated_expiry_date"):
            exp = b["estimated_expiry_date"]
            if exp < now:
                expired_count += qty
            elif exp < near_expiry_threshold:
                near_expiry_count += qty
                
    healthy_items = total_items - expired_count - near_expiry_count
    healthy_percentage = (healthy_items / total_items * 100) if total_items > 0 else 100
    
    return {
        "total_items": total_items,
        "fruits_count": fruits_count,
        "vegetables_count": vegetables_count,
        "near_expiry_count": near_expiry_count,
        "expired_count": expired_count,
        "low_stock_count": low_stock_count,
        "healthy_percentage": round(healthy_percentage, 1)
    }
