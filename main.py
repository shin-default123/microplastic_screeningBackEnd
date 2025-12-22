# main.py - Updated version
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
from PIL import Image
import numpy as np
import io
import math
import os

app = FastAPI(title="Microplastics AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load YOLO model ONCE
try:
    model = YOLO("best.pt")
    print("✅ Model loaded successfully")
except Exception as e:
    print(f"❌ Error loading model: {e}")
    model = None

# Set MICRONS_PER_PIXEL directly (no .env needed)
MICRONS_PER_PIXEL = 5.0  # Default value, adjust as needed

SIZE_CATEGORIES = {
    'nanoplastic': (0, 1),
    'small': (1, 100),
    'medium': (100, 1000),
    'large': (1000, 5000),
}

def classify_microplastic_size(width_µm, height_µm):
    diagonal_µm = math.sqrt(width_µm**2 + height_µm**2)
    
    for category, (min_size, max_size) in SIZE_CATEGORIES.items():
        if min_size <= diagonal_µm < max_size:
            return category, diagonal_µm
    
    return 'large', diagonal_µm

@app.get("/")
def root():
    return {"status": "Microplastics AI Backend Running", "model_loaded": model is not None}

@app.get("/health")
def health_check():
    return {"status": "healthy", "model": "loaded" if model else "not loaded"}

@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    if model is None:
        return {"error": "Model not loaded"}
    
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img_array = np.array(image)
    img_height, img_width = img_array.shape[:2]

    results = model(img_array, conf=0.4)

    detections = []
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            x = x1
            y = y1
            width = x2 - x1
            height = y2 - y1
            
            bbox = [float(x), float(y), float(width), float(height)]
            width_µm = width * MICRONS_PER_PIXEL
            height_µm = height * MICRONS_PER_PIXEL
            
            cls_id = int(box.cls[0])
            label = model.names[cls_id] if hasattr(model, 'names') else "microplastic"
            
            size_category = None
            diagonal_µm = None
            
            if label.lower() == "microplastic":
                size_category, diagonal_µm = classify_microplastic_size(width_µm, height_µm)
            
            detection_data = {
                "label": label,
                "confidence": float(box.conf[0]),
                "bbox": bbox,
                "width_px": float(width),
                "height_px": float(height),
            }
            
            if label.lower() == "microplastic":
                detection_data.update({
                    "size_category": size_category,
                    "width_µm": round(float(width_µm), 2),
                    "height_µm": round(float(height_µm), 2),
                    "diagonal_µm": round(float(diagonal_µm), 2) if diagonal_µm else None,
                })
            
            detections.append(detection_data)

    size_counts = {key: 0 for key in SIZE_CATEGORIES.keys()}
    
    for detection in detections:
        if detection['label'].lower() == 'microplastic' and 'size_category' in detection:
            size_category = detection['size_category']
            if size_category in size_counts:
                size_counts[size_category] += 1
    
    return {
        "count": len(detections),
        "detections": detections,
        "image_size": [img_width, img_height],
        "size_counts": size_counts,
        "calibration_info": {
            "microns_per_pixel": MICRONS_PER_PIXEL,
            "field_of_view_µm": [
                round(img_width * MICRONS_PER_PIXEL, 2),
                round(img_height * MICRONS_PER_PIXEL, 2)
            ]
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)