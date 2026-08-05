from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.database import get_db
import jwt
from bson import ObjectId

security = HTTPBearer()

# Role Constants mapping
ROLE_CONSUMER = "Consumer"
ROLE_RETAIL_MANAGER = "Retail Manager"
ROLE_WAREHOUSE_OPERATOR = "Warehouse Operator"
ROLE_QUALITY_INSPECTOR = "Food Quality Inspector"
ROLE_ADMINISTRATOR = "Administrator"

# Backward compatibility with legacy roles
LEGACY_ROLE_MAP = {
    "Admin": ROLE_ADMINISTRATOR,
    "Administrator": ROLE_ADMINISTRATOR,
    "Retailer": ROLE_RETAIL_MANAGER,
    "Operator": ROLE_WAREHOUSE_OPERATOR,
    "Warehouse Operator": ROLE_WAREHOUSE_OPERATOR,
    "User": ROLE_CONSUMER,
    "Consumer": ROLE_CONSUMER
}

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db = Depends(get_db)):
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
        
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise credentials_exception
        
    # Standardize string ID
    user["id"] = str(user["_id"])
    
    # Map legacy roles to new roles dynamically
    if user.get("role") in LEGACY_ROLE_MAP:
        user["role"] = LEGACY_ROLE_MAP[user["role"]]
        
    return user

async def get_current_admin_user(current_user: dict = Depends(get_current_user)):
    if current_user.get("role") != ROLE_ADMINISTRATOR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges (Administrator required)"
        )
    return current_user

# All logged in users can be "Consumers" at a minimum
async def get_current_consumer_user(current_user: dict = Depends(get_current_user)):
    return current_user

async def require_inventory_view(current_user: dict = Depends(get_current_user)):
    allowed = [ROLE_RETAIL_MANAGER, ROLE_WAREHOUSE_OPERATOR, ROLE_QUALITY_INSPECTOR, ROLE_ADMINISTRATOR]
    if current_user.get("role") not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view inventory")
    return current_user

async def require_inventory_add_edit(current_user: dict = Depends(get_current_user)):
    allowed = [ROLE_ADMINISTRATOR]
    if current_user.get("role") not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify inventory (Administrator required)")
    return current_user

async def require_inventory_delete(current_user: dict = Depends(get_current_user)):
    allowed = [ROLE_ADMINISTRATOR]
    if current_user.get("role") not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete inventory (Administrator required)")
    return current_user

# Keep the old dependency named `get_current_retailer_user` for backward compat, but use the new logic
# In previous implementation this was used for general access to inventory/reports. We will map this to `require_inventory_view` or something similar depending on the endpoint.
# Actually, I'll update all endpoints to use the exact permission they need (view vs edit).
async def get_current_retailer_user(current_user: dict = Depends(get_current_user)):
    allowed = [ROLE_RETAIL_MANAGER, ROLE_WAREHOUSE_OPERATOR, ROLE_QUALITY_INSPECTOR, ROLE_ADMINISTRATOR]
    if current_user.get("role") not in allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Retail Manager or equivalent required")
    return current_user
