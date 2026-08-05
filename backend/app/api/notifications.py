from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.api.deps import get_current_consumer_user
from bson import ObjectId
from datetime import datetime, timedelta
import uuid
from app.api.inventory import apply_dynamic_recommendations

router = APIRouter()

@router.get("")
async def get_notifications(db=Depends(get_db), current_user=Depends(get_current_consumer_user)):
    user_id = ObjectId(current_user["_id"])
    notifications = []
    
    # We only process Retailer/Admin roles as they have inventory_batches
    role = current_user.get("role", "")
    if role not in ["Retailer", "Admin", "Retail Manager", "Administrator", "Warehouse Operator", "Food Quality Inspector"]:
        return []
        
    batches_cursor = db["inventory_batches"].find({"retailer_id": current_user["id"], "is_active": True})
    batches_raw = await batches_cursor.to_list(length=1000)
    
    now = datetime.utcnow()
    one_day_ago = now - timedelta(days=1)
    
    for b_raw in batches_raw:
        # Generate dynamic data first
        b = apply_dynamic_recommendations(b_raw)
        
        batch_id = b.get("batch_id")
        fruit_name = b.get("fruit_name")
        days_rem = b.get("days_remaining")
        risk = b.get("risk_forecast")
        trend = b.get("shelf_life_trend")
        qty = b.get("quantity", 0)
        compliance = b.get("storage_compliance")
        temp = b.get("temperature")
        hum = b.get("humidity")
        loc = b.get("storage_location")
        
        def add_notif(n_type, severity, title, message, rec=None, ts=now):
            notifications.append({
                "id": str(uuid.uuid4()),
                "type": n_type,
                "severity": severity,
                "title": title,
                "message": message,
                "timestamp": ts.isoformat(),
                "related_batch": batch_id,
                "recommendation": rec
            })

        # --- 1. Freshness Alerts ---
        if trend == "Decreasing rapidly":
            add_notif("Freshness Alert", "WARNING", "Freshness Dropping Rapidly", 
                      f"{fruit_name} (Batch {batch_id}) freshness is dropping rapidly.", 
                      b.get("quality_improvement_recommendation"))
                      
        # --- 2. Shelf-Life Warnings ---
        if days_rem is not None:
            if days_rem == 3:
                add_notif("Shelf-Life Warning", "WARNING", "3 Days Remaining", 
                          f"{fruit_name} expires in 3 days.", 
                          b.get("consumption_recommendation"))
            elif days_rem == 1:
                add_notif("Shelf-Life Warning", "CRITICAL", "1 Day Remaining", 
                          f"{fruit_name} expires tomorrow.", 
                          b.get("consumption_recommendation"))
            elif days_rem == 0 and risk != "Expired":
                add_notif("Shelf-Life Warning", "CRITICAL", "Expires Today", 
                          f"{fruit_name} expires today.", 
                          b.get("consumption_recommendation"))

        # --- 3. Spoilage Notifications ---
        if risk == "High Risk":
            add_notif("Spoilage Notification", "CRITICAL", "High Spoilage Risk", 
                      f"{fruit_name} is at high risk of spoilage.", 
                      b.get("waste_reduction_recommendation"))
        elif risk == "Expired" or days_rem == 0:
            add_notif("Spoilage Notification", "CRITICAL", "Expired Product", 
                      f"{fruit_name} has expired.", 
                      b.get("waste_reduction_recommendation"))

        # --- 4. Storage Alerts ---
        if compliance == "Non-Compliant":
            add_notif("Storage Alert", "CRITICAL", "Non-Compliant Storage", 
                      f"{fruit_name} storage is Non-Compliant.", 
                      b.get("storage_recommendation"))
        elif compliance == "Warning":
            add_notif("Storage Alert", "WARNING", "Storage Warning", 
                      f"{fruit_name} storage conditions are suboptimal.", 
                      b.get("storage_optimization"))
                      
        if loc == "Refrigerator" and temp is not None and temp > 5.0:
            add_notif("Storage Alert", "WARNING", "Temperature Warning", 
                      f"Temperature ({temp}°C) is too high for {fruit_name}.", 
                      "Reduce Temperature")
                      
        if loc == "Refrigerator" and hum is not None and hum < 50.0:
            add_notif("Storage Alert", "WARNING", "Humidity Warning", 
                      f"Humidity ({hum}%) is too low for {fruit_name}.", 
                      "Improve Humidity")

        # --- 5. Inventory Alerts ---
        if qty > 0 and qty < 10:
            add_notif("Inventory Alert", "WARNING", "Low Stock Detected", 
                      f"Low stock for {fruit_name} (only {qty} left).", 
                      "Restock Soon")
        if risk == "Expired":
            add_notif("Inventory Alert", "CRITICAL", "Batch Expired", 
                      f"Batch {batch_id} has expired and should be removed.", 
                      b.get("inventory_rotation_recommendation"))
        elif days_rem is not None and days_rem > 0 and days_rem <= 3:
            add_notif("Inventory Alert", "WARNING", "Batch Near Expiry", 
                      f"Batch {batch_id} is near expiry.", 
                      b.get("inventory_rotation_recommendation"))

        # --- 6. Platform Notifications ---
        # Look through history for events in the last 24h
        history = b.get("storage_history", [])
        for event in history:
            try:
                event_time = datetime.fromisoformat(event.get("timestamp"))
                if event_time > one_day_ago:
                    field = event.get("field")
                    if field == "Initialization":
                        add_notif("Platform Notification", "INFO", "Inventory Batch Added", 
                                  f"New batch {batch_id} ({fruit_name}) added to inventory.", ts=event_time)
                    elif field == "storage_location":
                        add_notif("Platform Notification", "INFO", "Storage Location Changed", 
                                  f"Location for batch {batch_id} changed from {event.get('previous')} to {event.get('new')}.", ts=event_time)
                    elif field in ["temperature", "humidity"]:
                        add_notif("Platform Notification", "INFO", "Storage Conditions Updated", 
                                  f"{field.capitalize()} updated for batch {batch_id}.", ts=event_time)
                    else:
                        add_notif("Platform Notification", "INFO", "Inventory Batch Updated", 
                                  f"Batch {batch_id} updated.", ts=event_time)
            except:
                pass

    # Sort notifications by timestamp descending (newest first)
    notifications.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return notifications
