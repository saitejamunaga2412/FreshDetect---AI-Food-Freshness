# FreshDetect AI - Intelligent Food Freshness Monitoring Platform

FreshDetect AI is a comprehensive full-stack application that leverages YOLO computer vision, environmental data, and the USDA FoodKeeper dataset to accurately predict the freshness and shelf-life of food items.

---

## 🌟 Features
- **Object Detection:** Identifies fruits/vegetables using a custom-trained YOLOv8 model.
- **Freshness Classification:** Scores visual condition (Fresh vs. Rotten) using a MobileNetV3 CNN.
- **Environmental Analysis:** Uses an XGBoost model to evaluate ambient temperature and humidity for storage condition scoring.
- **Knowledge Base Integration:** Relies on the USDA FoodKeeper dataset to provide absolute limits for shelf-life based on USDA guidelines.
- **Inventory Management:** Automatically tracks and manages your food inventory by saving predictions to MongoDB.
- **Modern UI:** Responsive, glassmorphism-themed React dashboard for scanning and inventory tracking.

---

## 📁 Folder Structure

```text
FreshDetect AI/
├── backend/                   # Complete Python backend
│   ├── ai/                    # YOLO & CNN Models, Training Scripts
│   ├── app/                   # FastAPI application
│   │   ├── api/               # FastAPI Routers (auth, scanner, inventory)
│   │   ├── core/              # Config & Database connection
│   │   ├── models/            # Pydantic Schemas
│   │   └── services/          # YOLO, ML, FoodKeeper singletons
│   ├── dataset/               # USDA FoodKeeper Dataset
│   ├── models/                # Trained AI models (.pkl, .pth)
│   ├── scripts/               # Utility & verify scripts
│   ├── tests/                 # Backend tests
│   ├── weights/               # YOLO Weights (.pt)
│   ├── main.py                # FastAPI entry point
│   ├── requirements.txt       # Python dependencies
│   └── uploads/               # Temporary uploaded files
└── frontend/                  # React / Vite frontend
    ├── src/
    │   ├── components/        # React UI elements
    │   ├── pages/             # Dashboard, Scanner, Profile, etc.
    │   └── assets/            # UI static assets
    ├── package.json           # Frontend dependencies
    └── index.css              # Global Glassmorphism Themes
```

---

## 🏗️ Architecture

### Backend Architecture
Built with FastAPI, the backend handles image uploads, executes AI inference pipelines, interacts with the MongoDB database, and serves data to the frontend via RESTful APIs.

### Frontend Architecture
A React-based single-page application built with Vite. Uses modern hooks, glassmorphism styling, and context for state management. It communicates with the FastAPI backend over HTTP.

### AI Pipeline & Models Used
The system relies on a multi-stage AI pipeline to determine the overall freshness and shelf-life of food items.

1. **Object Detection (YOLOv8)**
   - **Model**: `backend/weights/yolov8n.pt` / `best.pt`
   - **Role**: Identifies the fruit/vegetable in the camera feed and extracts the tightest bounding box to crop the image, removing background noise.

2. **Visual Freshness CNN (MobileNetV3)**
   - **Model**: `backend/models/freshness_classifier.pth`
   - **Role**: A binary classifier trained on the `Freshness44` dataset to score the cropped fruit purely on its visual condition (Fresh vs. Rotten).

3. **Environmental Analysis (XGBoost)**
   - **Model**: `backend/models/freshness_model.pkl`
   - **Role**: Evaluates the ambient temperature and humidity to generate a storage condition score.

4. **Fusion Engine**
   - The orchestrator weights the predictions from all three models:
     - Visual Condition: 40%
     - Environmental Condition: 25%
     - Shelf-Life Limit: 20%
     - Product Age: 15%
   - The system outputs a normalized freshness score (0-100) and categorizes the item as `Fresh`, `Good`, `Acceptable`, `Near Spoilage`, or `Spoiled`.

### Dataset Details
**Knowledge Base (FoodKeeper)**
- **Dataset Path**: `backend/dataset/processed/foodkeeper_fruits_vegetables.csv`
- **Role**: Provides absolute limits for shelf-life (Pantry, Fridge, Freezer) based on USDA guidelines. Loaded as a singleton `pandas` DataFrame during startup.

---

## 🚀 Installation & Deployment

### Prerequisites
- Node.js (v18+)
- Python 3.10+
- MongoDB 6.0+ (Local or Atlas)
- CUDA 11.8+ (Optional, Required for AI Training)

### 1. Backend Setup
Navigate to the `backend` directory:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 2. Frontend Setup
Navigate to the `frontend` directory:
```bash
cd frontend
npm install
```

### 3. Database Initialization
Ensure MongoDB is running locally on port `27017` or update `MONGODB_URI` to point to an Atlas cluster. No migrations are needed; collections are created dynamically upon insertion.

---

## ⚙️ Configuration & Environment Variables

### Backend (`backend/.env`)
Create a `.env` file in the `backend/` directory:
```env
MONGODB_URI=mongodb://127.0.0.1:27017/freshdetect
JWT_SECRET=your_secure_64_character_hex_string
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=43200
UPLOAD_DIR=uploads
```

### Frontend (`frontend/.env`)
Create a `.env` file in the `frontend/` directory (if using Vite):
```env
VITE_API_URL=http://127.0.0.1:8000
```
*(If using Next.js, use `NEXT_PUBLIC_API_URL=http://localhost:8000`)*

---

## 🔌 API Documentation
- `POST /api/auth/login` - Authenticate users via JWT
- `GET /api/health` - Runtime verification of DB, FastAPI, and AI Models
- `POST /api/scanner/scan` - Accepts `multipart/form-data` images (max 10MB) for YOLO detection.
- `GET /api/inventory` - Retrieve user's tracked food inventory.

---

## 📖 Usage Instructions

### Running the Application

1. **Start the FastAPI Backend**:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```
   *The backend will boot up on `http://127.0.0.1:8000`.*

2. **Start the Frontend Development Server**:
   ```bash
   cd frontend
   npm run dev
   ```
   *The frontend will be available at `http://localhost:5173` (or port 3000 depending on the framework).*

### Production AI Training (Optional)
The project ships with pre-trained models. However, to retrain the Visual Freshness CNN on the full `Freshness44` dataset:
1. Ensure a CUDA GPU is available.
2. Run `python backend/ai/training/train_freshness.py`.
3. The script will automatically export `freshness_classifier.pth` and `freshness_classifier.onnx` into `backend/models/`.
