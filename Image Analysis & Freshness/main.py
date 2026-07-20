from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from engine import assess_freshness

app = FastAPI(title="FreshDetect AI Engine", version="1.0.0")

# Configure CORS so Node.js or React can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "FreshDetect Image Analysis Engine is running"}

@app.post("/api/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """
    Accepts an image file and returns the freshness analysis.
    """
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File provided is not an image")
        
    contents = await file.read()
    
    # Run the image through our computer vision engine
    analysis_result = assess_freshness(contents)
    
    if "error" in analysis_result:
        raise HTTPException(status_code=500, detail=analysis_result["error"])
        
    return {
        "filename": file.filename,
        "analysis": analysis_result
    }

if __name__ == "__main__":
    print("Starting FreshDetect AI Engine on port 8000...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
