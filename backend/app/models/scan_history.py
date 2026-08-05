from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ScanHistoryBase(BaseModel):
    user_id: str
    food_name: str
    food_type: str
    freshness_score: float
    freshness_category: str
    detection_confidence: float
    spoilage_risk: str
    estimated_shelf_life: str
    recommendation: str
    image_url: str
    is_saved_to_inventory: bool = False
    inventory_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class ScanHistoryCreate(ScanHistoryBase):
    pass

class ScanHistoryResponse(ScanHistoryBase):
    id: str
