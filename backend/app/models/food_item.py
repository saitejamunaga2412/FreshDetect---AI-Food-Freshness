from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class FoodItemBase(BaseModel):
    name: str
    category: str
    uploadDate: Optional[datetime] = None
    expiryDate: datetime
    freshnessScore: float = 100
    status: str = "Fresh"
    imageURL: Optional[str] = None
    scanId: Optional[str] = None
    addedBy: str

class FoodItemCreate(BaseModel):
    name: str
    category: str
    expiryDate: datetime
    freshnessScore: float = 100
    status: str = "Fresh"
    imageURL: Optional[str] = None
    scanId: Optional[str] = None
    visual_condition: Optional[str] = None
    environment_score: Optional[float] = None
    overall_score: Optional[float] = None
    final_status: Optional[str] = None
    confidence: Optional[str] = None
    yolo_class: Optional[str] = None

class FoodItemOut(FoodItemBase):
    id: str
    createdAt: datetime
    updatedAt: datetime
    
    class Config:
        populate_by_name = True
