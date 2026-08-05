import logging
import os
import uuid
import io
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile
from PIL import Image
from pydantic import BaseModel
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import UserCreate, UserOut, Token, UserUpdate
from datetime import datetime
from bson import ObjectId

logger = logging.getLogger(__name__)

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate, db=Depends(get_db)):
    users_collection = db["users"]
    
    existing_user = await users_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
        
    user_dict = user.model_dump()
    password = user_dict.pop("password")
    
    user_dict["passwordHash"] = get_password_hash(password)
    user_dict["createdAt"] = datetime.utcnow()
    user_dict["updatedAt"] = datetime.utcnow()
    
    if "role" not in user_dict or not user_dict["role"]:
        user_dict["role"] = "Consumer"
        
    result = await users_collection.insert_one(user_dict)
    
    return {"message": "User created successfully"}

@router.post("/login", response_model=Token)
async def login(login_req: LoginRequest, db=Depends(get_db)):
    users_collection = db["users"]
    
    user = await users_collection.find_one({"email": login_req.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    stored_hash = user.get("passwordHash")
    
    if not stored_hash or not verify_password(login_req.password, stored_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    access_token = create_access_token(
        subject=str(user["_id"])
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "token": access_token,
        "user": {
            "id": str(user["_id"]),
            "name": user.get("name", ""),
            "email": user["email"],
            "role": user.get("role", "Staff")
        }
    }



from app.api.deps import get_current_user

@router.get("/me", response_model=UserOut)
async def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user.get("role", "Staff"),
        "phone": current_user.get("phone"),
        "location": current_user.get("location"),
        "address": current_user.get("address"),
        "dob": current_user.get("dob"),
        "gender": current_user.get("gender"),
        "bio": current_user.get("bio"),
        "avatarImage": current_user.get("avatarImage")
    }

@router.put("/me", response_model=UserOut)
async def update_me(update_data: UserUpdate, current_user: dict = Depends(get_current_user), db=Depends(get_db)):
    users_collection = db["users"]
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if update_dict:
        update_dict["updatedAt"] = datetime.utcnow()
        await users_collection.update_one(
            {"_id": ObjectId(current_user["id"])},
            {"$set": update_dict}
        )
        
        # Fetch updated user
        updated_user = await users_collection.find_one({"_id": ObjectId(current_user["id"])})
        if updated_user:
            updated_user["id"] = str(updated_user["_id"])
            current_user = updated_user

    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "role": current_user.get("role", "Staff"),
        "phone": current_user.get("phone"),
        "location": current_user.get("location"),
        "address": current_user.get("address"),
        "dob": current_user.get("dob"),
        "gender": current_user.get("gender"),
        "bio": current_user.get("bio"),
        "avatarImage": current_user.get("avatarImage")
    }

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "uploads", "profile_pictures"))

@router.post("/profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    if file.content_type not in ["image/jpeg", "image/png", "image/webp", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Unsupported file format")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")

    try:
        image = Image.open(io.BytesIO(content))
        image.thumbnail((800, 800))
        filename = f"{uuid.uuid4()}.webp"
        filepath = os.path.join(UPLOAD_DIR, filename)
        
        # Save as WEBP for better compression
        image.save(filepath, format="WEBP", quality=85)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")
        
    url_path = f"/uploads/profile_pictures/{filename}"
    
    users_collection = db["users"]
    
    # Delete old avatar
    if current_user.get("avatarImage") and current_user["avatarImage"].startswith("/uploads/profile_pictures/"):
        old_file = os.path.basename(current_user["avatarImage"])
        old_path = os.path.join(UPLOAD_DIR, old_file)
        if os.path.exists(old_path):
            os.remove(old_path)

    await users_collection.update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": {"avatarImage": url_path, "updatedAt": datetime.utcnow()}}
    )

    return {"avatarImage": url_path}

@router.delete("/profile-picture")
async def remove_profile_picture(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db)
):
    users_collection = db["users"]
    
    # Delete old avatar
    if current_user.get("avatarImage") and current_user["avatarImage"].startswith("/uploads/profile_pictures/"):
        old_file = os.path.basename(current_user["avatarImage"])
        old_path = os.path.join(UPLOAD_DIR, old_file)
        if os.path.exists(old_path):
            os.remove(old_path)
            
    await users_collection.update_one(
        {"_id": ObjectId(current_user["id"])},
        {"$set": {"avatarImage": None, "updatedAt": datetime.utcnow()}}
    )
    
    return {"message": "Profile picture removed"}
