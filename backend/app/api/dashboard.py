from fastapi import APIRouter, Depends
from app.core.database import get_db
from app.api.deps import get_current_consumer_user
from bson import ObjectId
from datetime import datetime, timedelta

router = APIRouter()

@router.get("")
async def get_dashboard_stats(db = Depends(get_db), current_user = Depends(get_current_consumer_user)):
    user_id = ObjectId(current_user["_id"])
    now = datetime.utcnow()
    
    # Basic counts
    total_items = await db["fooditems"].count_documents({"addedBy": user_id})
    fresh_items = await db["fooditems"].count_documents({"addedBy": user_id, "status": "Fresh"})
    warning_items = await db["fooditems"].count_documents({"addedBy": user_id, "status": "Warning"})
    spoiled_items = await db["fooditems"].count_documents({"addedBy": user_id, "status": "Spoiled"})
    
    # Near expiry (within 3 days)
    three_days_from_now = now + timedelta(days=3)
    near_expiry_items = await db["fooditems"].count_documents({
        "addedBy": user_id,
        "expiryDate": {"$gt": now, "$lte": three_days_from_now}
    })
    
    # Aggregations for averages and insights
    pipeline = [
        {"$match": {"addedBy": user_id}},
        {"$group": {
            "_id": None,
            "avgFreshness": {"$avg": "$freshnessScore"}
        }}
    ]
    avg_freshness_cursor = db["fooditems"].aggregate(pipeline)
    avg_freshness_list = await avg_freshness_cursor.to_list(length=1)
    avg_freshness = round(avg_freshness_list[0]["avgFreshness"], 1) if avg_freshness_list else 0.0

    # Weekly trend
    seven_days_ago = now - timedelta(days=7)
    trend_pipeline = [
        {"$match": {"addedBy": user_id, "createdAt": {"$gte": seven_days_ago}}},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$createdAt"}},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    weekly_trend_cursor = db["fooditems"].aggregate(trend_pipeline)
    weekly_trend = await weekly_trend_cursor.to_list(length=7)

    # Most scanned produce
    produce_pipeline = [
        {"$match": {"addedBy": user_id}},
        {"$group": {
            "_id": "$name",
            "count": {"$sum": 1}
        }},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    produce_cursor = db["fooditems"].aggregate(produce_pipeline)
    top_produce = await produce_cursor.to_list(length=5)

    # Recent activity
    recent_cursor = db["fooditems"].find({"addedBy": user_id}).sort("createdAt", -1).limit(5)
    recent_activity = []
    for item in await recent_cursor.to_list(length=5):
        recent_activity.append({
            "id": str(item["_id"]),
            "name": item.get("name"),
            "freshnessScore": item.get("freshnessScore"),
            "status": item.get("status"),
            "createdAt": item.get("createdAt")
        })

    health_score = 0
    if total_items > 0:
        health_score = round(((fresh_items + warning_items) / total_items) * 100, 1)

    return {
        "total": total_items,
        "fresh": fresh_items,
        "warning": warning_items,
        "spoiled": spoiled_items,
        "nearExpiry": near_expiry_items,
        "avgFreshness": avg_freshness,
        "healthScore": health_score,
        "weeklyTrend": weekly_trend,
        "topProduce": top_produce,
        "recentActivity": recent_activity
    }
