from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import re
import datetime
import os
import platform
import psutil

app = FastAPI()

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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

LIBRARY_HARDWARE_REQUIREMENTS = {
    "tensorflow": {"CPU": "Intel i5/i7 or AMD Ryzen 5/7", "RAM": "8GB (16GB recommended)", "GPU": "NVIDIA GTX 1050+"},
    "torch": {"CPU": "Intel i5/i7 or AMD Ryzen 5/7", "RAM": "8GB (16GB recommended)", "GPU": "NVIDIA GTX 1060+"},
    "opencv": {"CPU": "Intel Core 2 Duo or higher", "RAM": "2GB (4GB recommended)", "GPU": "Not required"},
    "numpy": {"CPU": "Any modern processor", "RAM": "2GB minimum"},
    "pandas": {"CPU": "Any modern processor", "RAM": "4GB minimum"},
}

# ✅ Extract dependencies from Python code
def extract_dependencies(file_content):
    return list(set(re.findall(r'^(?:import|from) (\w+)', file_content, re.MULTILINE)))

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
<<<<<<< HEAD:main.py
    return filename.endswith((".pt", ".bin", ".h5", ".onnx", ".pb",".ipynb"))
=======
    return filename.endswith((".pt", ".bin", ".h5", ".onnx", ".pb", ".ipynb"))

# ✅ Get hardware requirements
def get_hardware_requirements(libraries):
    return {lib: LIBRARY_HARDWARE_REQUIREMENTS.get(lib, {"CPU": "Unknown", "RAM": "Unknown", "GPU": "Unknown"}) for lib in libraries}

# ✅ Get system hardware specs
def get_system_specs():
    return {
        "CPU": platform.processor(),
        "RAM": f"{round(psutil.virtual_memory().total / (1024**3))} GB",
        "GPU": "N/A (GPU detection requires additional libraries)"
    }
>>>>>>> 5c74bb5fb79523de12a1a37316df5794ea3f3078:backend/main.py

# ✅ Upload & Process File
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        file_text = content.decode("utf-8", errors="ignore")
        
        dependencies = extract_dependencies(file_text) if not is_model_file(file.filename) else []
        model_name = os.path.splitext(file.filename)[0]
        author = determine_author(dependencies, model_name)
        hardware_requirements = get_hardware_requirements(dependencies)
        system_specs = get_system_specs()
        
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
                "HardwareRequirements": hardware_requirements,
                "SystemSpecs": system_specs,
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
