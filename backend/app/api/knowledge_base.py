from fastapi import APIRouter, Depends, HTTPException, status, Query
from app.core.database import get_db
from app.api.deps import get_current_admin_user, get_current_user
from app.models.inventory import FoodKnowledgeBaseCreate, FoodKnowledgeBaseOut
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("", response_model=list[FoodKnowledgeBaseOut])
async def get_knowledge_base_foods(db = Depends(get_db), current_user = Depends(get_current_user)):
    collection = db["knowledge_base"]
    foods = []
    async for food in collection.find():
        food["_id"] = str(food["_id"])
        foods.append(food)
    return foods

@router.post("", response_model=FoodKnowledgeBaseOut, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base_food(
    food_in: FoodKnowledgeBaseCreate,
    db = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    collection = db["knowledge_base"]
    
    # Ensure unique constraint on name
    existing = await collection.find_one({"name": {"$regex": f"^{food_in.name}$", "$options": "i"}})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Produce '{food_in.name}' already exists in the Knowledge Base."
        )
        
    food_dict = food_in.model_dump()
    
    # Ensure unique index exists
    await collection.create_index("name", unique=True)
    
    result = await collection.insert_one(food_dict)
    food_dict["_id"] = str(result.inserted_id)
    return food_dict

from bson import ObjectId

@router.put("/{id}", response_model=FoodKnowledgeBaseOut)
async def update_knowledge_base_food(
    id: str,
    food_in: FoodKnowledgeBaseCreate,
    db = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    collection = db["knowledge_base"]
    
    try:
        obj_id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")
        
    # Check duplicate name, ignoring self
    existing = await collection.find_one({"name": {"$regex": f"^{food_in.name}$", "$options": "i"}, "_id": {"$ne": obj_id}})
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Produce '{food_in.name}' already exists in the Knowledge Base."
        )
        
    food_dict = food_in.model_dump()
    result = await collection.update_one({"_id": obj_id}, {"$set": food_dict})
    
    if result.matched_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food item not found")
        
    food_dict["_id"] = str(obj_id)
    return food_dict

@router.delete("/{id}")
async def delete_knowledge_base_food(
    id: str,
    db = Depends(get_db),
    current_user: dict = Depends(get_current_admin_user)
):
    collection = db["knowledge_base"]
    try:
        obj_id = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid ID format")
        
    result = await collection.delete_one({"_id": obj_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Food item not found")
        
    return {"message": "Food item deleted successfully"}
