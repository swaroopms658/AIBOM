from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import os
import datetime
import platform
import psutil
import ast
import zipfile
import shutil

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

# ✅ Hardware requirements
LIBRARY_HARDWARE_REQUIREMENTS = {
    "tensorflow": {"CPU": "Intel i5/i7", "RAM": "8GB+", "GPU": "NVIDIA GTX 1050+"},
    "torch": {"CPU": "Intel i5/i7", "RAM": "8GB+", "GPU": "NVIDIA GTX 1060+"},
    "opencv": {"CPU": "Intel Core 2 Duo+", "RAM": "2GB+", "GPU": "Not required"},
    "numpy": {"CPU": "Any", "RAM": "2GB+"},
    "pandas": {"CPU": "Any", "RAM": "4GB+"},
    "transformers": {"CPU": "Intel i7+", "RAM": "16GB+", "GPU": "NVIDIA RTX 2060+"},
}

# ✅ Extract dependencies from Python code
def extract_from_python_code(code):
    try:
        tree = ast.parse(code)
        dependencies = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.add(node.module.split(".")[0])
        return dependencies
    except Exception as e:
        print(f"❌ Error extracting dependencies: {e}")
        return set()

# ✅ Extract licenses
def extract_licenses(file_content):
    possible_licenses = ["MIT", "Apache-2.0", "GPL", "BSD", "MPL", "LGPL"]
    return [license for license in possible_licenses if license in file_content]

# ✅ Extract dependencies based on file type
def extract_dependencies(file_content, filename):
    dependencies = set()
    try:
        if filename.endswith(".ipynb"):
            notebook_data = json.loads(file_content)
            for cell in notebook_data.get("cells", []):
                if cell.get("cell_type") == "code":
                    dependencies.update(extract_from_python_code("".join(cell.get("source", []))))
        else:
            dependencies.update(extract_from_python_code(file_content))
        return list(dependencies)
    except Exception as e:
        print(f"❌ Error extracting dependencies: {e}")
        return []

# ✅ Determine author
def determine_author(dependencies, model_name=""):
    if model_name.lower() in KNOWN_MODELS:
        return KNOWN_MODELS[model_name.lower()]
    for lib in dependencies:
        if lib.lower() in KNOWN_DEVELOPERS:
            return KNOWN_DEVELOPERS[lib.lower()]
    return "Unknown"

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

# ✅ Extract files from ZIP and process them
def process_zip_file(zip_path):
    extracted_dir = os.path.join(UPLOAD_DIR, "extracted_zip")
    
    if os.path.exists(extracted_dir):
        shutil.rmtree(extracted_dir)
    os.makedirs(extracted_dir)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extracted_dir)

    all_dependencies = set()
    all_licenses = set()

    for root, _, files in os.walk(extracted_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    file_content = f.read()
                    dependencies = extract_dependencies(file_content, file)
                    licenses = extract_licenses(file_content)
                    all_dependencies.update(dependencies)
                    all_licenses.update(licenses)
            except Exception as e:
                print(f"❌ Skipping file {file}: {e}")

    return list(all_dependencies), list(all_licenses)

# ✅ Upload & Process File
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        if file.filename.endswith(".zip"):
            dependencies, licenses = process_zip_file(file_path)
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                file_content = f.read()
            dependencies = extract_dependencies(file_content, file.filename)
            licenses = extract_licenses(file_content)

        model_name = os.path.splitext(file.filename)[0]
        author = determine_author(dependencies, model_name)
        hardware_requirements = get_hardware_requirements(dependencies)
        system_specs = get_system_specs()

        result = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "ModelDetails": {
                "Name": file.filename,
                "Version": "1.0",
                "Type": "ZIP Archive" if file.filename.endswith(".zip") else "Software Model",
                "Author": author,
                "Licenses": licenses,
                "Libraries": dependencies,
                "HardwareRequirements": hardware_requirements,
                "SystemSpecs": system_specs,
                "Source": "Local Upload",
                "BOMGeneration": {
                    "Timestamp": datetime.datetime.utcnow().isoformat(),
                    "Method": "Automated Extraction",
                    "GeneratedBy": "FastAPI System"
                }
            }
        }

        json_file_path = os.path.join(UPLOAD_DIR, "downloaded.json")
        with open(json_file_path, "w", encoding="utf-8") as json_file:
            json.dump(result, json_file, indent=4)

        return {"message": "File processed successfully", "data": result}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Endpoint to Download JSON
@app.get("/download-json")
async def download_json():
    json_file_path = os.path.join(UPLOAD_DIR, "downloaded.json")
    if not os.path.exists(json_file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(json_file_path, media_type="application/json", filename="downloaded.json")
