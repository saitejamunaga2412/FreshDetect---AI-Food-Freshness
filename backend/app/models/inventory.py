from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class FoodKnowledgeBaseCreate(BaseModel):
    name: str
    category: str
    ideal_temperature: float
    ideal_humidity: float
    shelf_life_days: int
    spoilage_symptoms: List[str] = []

class FoodKnowledgeBaseOut(FoodKnowledgeBaseCreate):
    id: str = Field(alias="_id")

class InventoryBatchCreate(BaseModel):
    batch_id: str
    fruit_name: str
    category: str
    quantity: int
    supplier: Optional[str] = None
    storage_location: str = "Room Temperature"
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    visual_condition: Optional[str] = None
    environment_score: Optional[float] = None
    overall_score: Optional[float] = None
    final_status: Optional[str] = None
    confidence: Optional[str] = None
    yolo_class: Optional[str] = None
    
    @field_validator('storage_location')
    @classmethod
    def location_must_be_allowed(cls, v):
        allowed = ['Room Temperature', 'Refrigerator', 'Freezer']
        if v not in allowed:
            raise ValueError('storage_location must be Room Temperature, Refrigerator, or Freezer')
        return v
    
    @field_validator('category')
    @classmethod
    def category_must_be_allowed(cls, v):
        allowed = ['Fruit', 'Vegetable', 'Fruits', 'Vegetables']
        if v.title() not in allowed:
            raise ValueError('Category must be Fruit or Vegetable')
        return v.title()
    
    @field_validator('quantity')
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('quantity must be greater than 0')
        return v

class InventoryBatchUpdate(BaseModel):
    quantity: Optional[int] = None
    is_active: Optional[bool] = None
    storage_location: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    
    @field_validator('storage_location')
    @classmethod
    def location_must_be_allowed(cls, v):
        if v is not None:
            allowed = ['Room Temperature', 'Refrigerator', 'Freezer']
            if v not in allowed:
                raise ValueError('storage_location must be Room Temperature, Refrigerator, or Freezer')
        return v
    
    @field_validator('quantity')
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v is not None and v <= 0:
            raise ValueError('quantity must be greater than 0')
        return v

class InventoryBatchOut(InventoryBatchCreate):
    id: str = Field(alias="_id")
    retailer_id: str
    received_date: datetime
    estimated_expiry_date: Optional[datetime] = None
    is_active: bool = True
    shelf_life_trend: str = "Stable"
    risk_forecast: str = "Low Risk"
    days_remaining: Optional[int] = None
    storage_recommendation: Optional[str] = None
    consumption_recommendation: Optional[str] = None
    inventory_rotation_recommendation: Optional[str] = None
    waste_reduction_recommendation: Optional[str] = None
    quality_improvement_recommendation: Optional[str] = None
    storage_compliance: str = "Compliant"
    storage_optimization: Optional[str] = None
    storage_duration: Optional[str] = None
    storage_history: list = []
