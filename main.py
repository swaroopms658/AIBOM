from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import re
import datetime
import os

app = FastAPI()

# ✅ Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Ensure static directory exists
UPLOAD_DIR = "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ✅ Serve static files
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

# ✅ Known dependencies and models
KNOWN_DEVELOPERS = {
    "tensorflow": "Google",
    "torch": "Meta (Facebook)",
    "transformers": "Hugging Face",
    "numpy": "Community",
    "pandas": "Community",
}

KNOWN_MODELS = {
    "bert-base-uncased": "Hugging Face",
    "gpt-neo-125M": "EleutherAI",
    "resnet50": "Facebook AI",
    "mobilenet_v2": "Google",
    "gpt2": "OpenAI",
    "llama2": "Meta (Facebook)",
    "clip": "OpenAI",
}

# ✅ Extract dependencies from Python code
def extract_dependencies(file_content):
    return list(set(re.findall(r'^\s*(?:import|from) (\w+)', file_content, re.MULTILINE)))

# ✅ Determine author based on dependencies or model
def determine_author(dependencies, model_name=""):
    if model_name.lower() in KNOWN_MODELS:
        return KNOWN_MODELS[model_name.lower()]
    
    for lib in dependencies:
        if lib.lower() in KNOWN_DEVELOPERS:
            return KNOWN_DEVELOPERS[lib.lower()]
    
    return "Unknown"

# ✅ Check if the uploaded file is a pre-trained model
def is_model_file(filename):
    return filename.endswith((".pt", ".bin", ".h5", ".onnx", ".pb",".ipynb"))

# ✅ Upload & Process File
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        file_text = content.decode("utf-8", errors="ignore")  # Decode safely

        dependencies = extract_dependencies(file_text) if not is_model_file(file.filename) else []
        model_name = os.path.splitext(file.filename)[0]
        author = determine_author(dependencies, model_name)

        # ✅ Create JSON structure
        result = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "ModelDetails": {
                "Name": file.filename,
                "Version": "1.0",
                "Type": "Pre-trained Model" if is_model_file(file.filename) else "Software Model",
                "Author": author,
                "Licenses": ["MIT", "Apache-2.0"],
                "Libraries": dependencies,
                "Source": "Local Upload",
                "BOMGeneration": {
                    "Timestamp": datetime.datetime.utcnow().isoformat(),
                    "Method": "Automated Extraction",
                    "GeneratedBy": "FastAPI System"
                },
                "OtherReferences": [],
                "Tags": []
            }
        }

        # ✅ Save JSON file
        json_filename = f"{model_name}_bom.json"
        json_path = os.path.join(UPLOAD_DIR, json_filename)

        with open(json_path, "w") as json_file:
            json.dump(result, json_file, indent=4)

        return {
            "message": "File processed successfully",
            "data": result,
            "json_file": json_filename,
            "download_url": f"/static/{json_filename}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Endpoint to download JSON file
@app.get("/download-json/{filename}")
async def download_json(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/json", filename=filename)
    else:
        raise HTTPException(status_code=404, detail="File not found")
