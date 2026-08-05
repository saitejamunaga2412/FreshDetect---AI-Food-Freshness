from fastapi import APIRouter, Depends, HTTPException, status
from app.core.database import get_db
from app.api.deps import get_current_admin_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/stats")
async def get_admin_stats(db = Depends(get_db), current_user: dict = Depends(get_current_admin_user)):
    try:
        users_count = await db.users.count_documents({})
        retailers_count = await db.users.count_documents({"role": "Retailer"})
        consumers_count = await db.users.count_documents({"role": "Consumer"})
        
        batches_count = await db.inventory_batches.count_documents({})
        kb_count = await db.knowledge_base.count_documents({})
        scans_count = await db.scan_history.count_documents({})
        
        return {
            "total_users": users_count,
            "total_retailers": retailers_count,
            "total_consumers": consumers_count,
            "total_inventory_batches": batches_count,
            "total_knowledge_base_items": kb_count,
            "total_ai_predictions": scans_count
        }
    except Exception as e:
        logger.error(f"Failed to fetch admin stats: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch statistics")

@router.get("/users")
async def get_all_users(db = Depends(get_db), current_user: dict = Depends(get_current_admin_user)):
    try:
        cursor = db.users.find({}, {"passwordHash": 0})
        users = await cursor.to_list(length=1000)
        
        for user in users:
            user["id"] = str(user.pop("_id"))
            
        return users
    except Exception as e:
        logger.error(f"Failed to fetch users: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to fetch users")
