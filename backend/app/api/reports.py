from fastapi import APIRouter, Depends, Query
from app.core.database import get_db
from app.api.deps import get_current_admin_user, get_current_consumer_user
from typing import Optional
from datetime import datetime
from app.api.inventory import apply_dynamic_recommendations
from app.api.notifications import get_notifications

router = APIRouter()

@router.get("")
async def generate_report(db = Depends(get_db), current_user = Depends(get_current_admin_user)):
    """
    Generates a basic report of all inventory items.
    Restricted to Admin users.
    Can be extended for PDF/Excel exports in the future.
    """
    # Fetch all items from all users
    items_cursor = db["fooditems"].find()
    items = await items_cursor.to_list(length=1000)
    
    total = len(items)
    spoiled = sum(1 for item in items if item.get("status") == "Spoiled")
    fresh = sum(1 for item in items if item.get("status") == "Fresh")
    warning = sum(1 for item in items if item.get("status") == "Warning")
    
    return {
        "success": True,
        "summary": {
            "totalItems": total,
            "freshItems": fresh,
            "warningItems": warning,
            "spoiledItems": spoiled
        },
        "data": [
            {
                "id": str(item["_id"]),
                "name": item.get("name"),
                "category": item.get("category"),
                "status": item.get("status"),
                "freshnessScore": item.get("freshnessScore"),
                "addedBy": str(item.get("addedBy"))
            } for item in items
        ]
    }

@router.get("/comprehensive")
async def generate_comprehensive_report(
    db = Depends(get_db), 
    current_user = Depends(get_current_consumer_user),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    storage_location: Optional[str] = None,
    risk_level: Optional[str] = None,
    freshness_status: Optional[str] = None
):
    query = {"retailer_id": current_user["id"], "is_active": True}
    
    # Time filter uses received_date or createdAt
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = datetime.fromisoformat(start_date.replace("Z", "+00:00")).replace(tzinfo=None)
        if end_date:
            date_filter["$lte"] = datetime.fromisoformat(end_date.replace("Z", "+00:00")).replace(tzinfo=None)
        query["received_date"] = date_filter

    if category:
        query["category"] = category
    if storage_location:
        query["storage_location"] = storage_location
        
    batches_cursor = db["inventory_batches"].find(query)
    raw_batches = await batches_cursor.to_list(length=1000)
    
    processed_batches = []
    for b in raw_batches:
        processed_batches.append(apply_dynamic_recommendations(b))
        
    # In-memory filtering for computed fields
    filtered_batches = []
    for b in processed_batches:
        keep = True
        if risk_level and b.get("risk_forecast") != risk_level:
            keep = False
        
        # Determine freshness status based on days_remaining
        days = b.get("days_remaining")
        f_status = "Fresh"
        if days is not None:
            if days <= 0:
                f_status = "Spoiled"
            elif days <= 3:
                f_status = "Warning"
                
        if freshness_status and f_status != freshness_status:
            keep = False
            
        if keep:
            b["freshness_status"] = f_status # Assign for frontend use
            b["_id"] = str(b["_id"])
            filtered_batches.append(b)

    # 1. Inventory Summary
    inv_summary = {
        "total_items": len(filtered_batches),
        "total_quantity": sum(b.get("quantity", 0) for b in filtered_batches),
        "categories": {}
    }
    for b in filtered_batches:
        cat = b.get("category", "Unknown")
        inv_summary["categories"][cat] = inv_summary["categories"].get(cat, 0) + 1
        
    # 2. Freshness Summary
    fresh_summary = {"Fresh": 0, "Warning": 0, "Spoiled": 0}
    for b in filtered_batches:
        fresh_summary[b.get("freshness_status", "Fresh")] += 1
        
    # 3. Shelf-Life Summary
    sl_summary = {"Expired": 0, "Near_Expiry": 0, "Stable": 0}
    for b in filtered_batches:
        d = b.get("days_remaining")
        if d is not None:
            if d <= 0: sl_summary["Expired"] += 1
            elif d <= 3: sl_summary["Near_Expiry"] += 1
            else: sl_summary["Stable"] += 1

    # 4. Storage Compliance Report
    storage_summary = {"Compliant": 0, "Warning": 0, "Non-Compliant": 0}
    for b in filtered_batches:
        comp = b.get("storage_compliance", "Compliant")
        storage_summary[comp] = storage_summary.get(comp, 0) + 1
        
    # 5. Recommendation Summary
    rec_summary = {}
    for b in filtered_batches:
        sr = b.get("storage_recommendation")
        if sr: rec_summary[sr] = rec_summary.get(sr, 0) + 1
        
    # 6. Notifications (Filter the user's notifications based on related_batch in filtered)
    all_notifs = await get_notifications(db, current_user)
    valid_batch_ids = {b.get("batch_id") for b in filtered_batches}
    filtered_notifs = [n for n in all_notifs if n.get("related_batch") in valid_batch_ids or not n.get("related_batch")]
    
    notif_summary = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
    for n in filtered_notifs:
        notif_summary[n.get("severity")] += 1
        
    # 7. Batch History
    history_report = []
    for b in filtered_batches:
        for hist in b.get("storage_history", []):
            history_report.append({
                "batch_id": b.get("batch_id"),
                "fruit_name": b.get("fruit_name"),
                "field": hist.get("field"),
                "previous": hist.get("previous"),
                "new": hist.get("new"),
                "timestamp": hist.get("timestamp"),
                "user": hist.get("user")
            })

    # Sort history descending
    history_report.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return {
        "success": True,
        "summary": {
            "inventory": inv_summary,
            "freshness": fresh_summary,
            "shelf_life": sl_summary,
            "storage": storage_summary,
            "recommendations": rec_summary,
            "notifications": notif_summary
        },
        "data": {
            "batches": filtered_batches,
            "notifications": filtered_notifs,
            "history": history_report[:100] # Cap history
        }
    }
