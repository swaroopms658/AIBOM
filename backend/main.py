from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import json
import os
import platform
import psutil
import ast
import requests
import hashlib
import zipfile
import shutil
from datetime import datetime
import subprocess
import re
import importlib.util
#import pkg_resources

app = FastAPI()

# --- CORS and Static Files ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = r"C:\Users\darsh\Downloads\upload"
EXTRACT_DIR = r"C:\Users\darsh\Downloads\extracted"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXTRACT_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

def extract_from_python_code(code: str) -> set:
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
        print(f"Error extracting dependencies: {e}")
        return set()

def extract_licenses(file_content: str) -> list:
    possible_licenses = ["MIT", "Apache-2.0", "GPL", "BSD", "MPL", "LGPL"]
    return [lic for lic in possible_licenses if lic in file_content]

def extract_dependencies(file_content: str, filename: str) -> list:
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
        print(f"Error extracting dependencies: {e}")
        return []

def get_system_specs() -> dict:
    specs = {
        "CPU": platform.processor(),
        "RAM": f"{round(psutil.virtual_memory().total / (1024**3))} GB",
        "OS": f"{platform.system()} {platform.release()}",
        "Python": platform.python_version(),
        "GPU": "N/A"
    }
    try:
        import torch
        if torch.cuda.is_available():
            specs["GPU"] = torch.cuda.get_device_name(0)
    except ImportError:
        try:
            import tensorflow as tf
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                specs["GPU"] = f"Found {len(gpus)} GPU(s)"
        except ImportError:
            pass
    return specs

def get_latest_version(package_name: str) -> str:
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data["info"].get("version", "Unknown")
    except Exception as e:
        print(f"Error fetching version for {package_name}: {e}")
    return "Unknown"

def check_versions(dependencies: list) -> dict:
    version_details = {}
    for dep in dependencies:
        latest_version = get_latest_version(dep)
        version_details[dep] = {"Version": latest_version}
    return version_details

def extract_zip(file_path: str) -> str:
    extracted_folder = os.path.join(EXTRACT_DIR, os.path.splitext(os.path.basename(file_path))[0])
    if os.path.exists(extracted_folder):
        shutil.rmtree(extracted_folder)
    os.makedirs(extracted_folder, exist_ok=True)
    try:
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            zip_ref.extractall(extracted_folder)
        return extracted_folder
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Invalid ZIP file")

def process_extracted_files(extracted_folder: str) -> list:
    dependencies = set()
    for root, _, files in os.walk(extracted_folder):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    file_content = f.read()
                    dependencies.update(extract_dependencies(file_content, file))
            except Exception as e:
                print(f"Skipping {file}: {e}")
    return list(dependencies)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        file_text = file_content.decode("utf-8", errors="ignore")
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(file_content)

        if file.filename.endswith(".zip"):
            extracted_folder = extract_zip(file_path)
            dependencies = process_extracted_files(extracted_folder)
        else:
            dependencies = extract_dependencies(file_text, file.filename)

        licenses = extract_licenses(file_text)
        version_details = check_versions(dependencies)
        system_specs = get_system_specs()

        bom_filename = f"bom_{file.filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        bom_path = os.path.join(UPLOAD_DIR, bom_filename)
        cyclonedx_bom = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "ModelDetails": {
                "Name": file.filename,
                "Version": "1.0",
                "Licenses": licenses,
                "Libraries": dependencies,
                "VersionDetails": version_details,
                "SystemSpecs": system_specs,
                "Source": "Local Upload",
                "BOMGeneration": {
                    "Timestamp": datetime.utcnow().isoformat(),
                    "Method": "Automated Extraction",
                    "GeneratedBy": "FastAPI System"
                }
            }
        }
        with open(bom_path, "w") as f:
            json.dump(cyclonedx_bom, f, indent=2)

        return {"message": "File processed successfully", "filename": bom_filename, "data": cyclonedx_bom}
    except Exception as e:
        print(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating BOM: {str(e)}")

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/json", filename=filename)

# Model scan by file path endpoint
@app.post("/scan-model-path")
async def scan_model_path(payload: dict):
    file_path = payload.get("file_path")
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        command = ["modelscan", "-p", file_path]
        result = subprocess.run(command, capture_output=True, text=True)
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        # Check if stdout is not empty even if returncode is non-zero
        if result.returncode != 0 and not result.stdout.strip():
            raise HTTPException(status_code=500, detail=f"Model scan failed: {result.stderr}")
        return {"message": "Model scan completed", "scanOutput": result.stdout}
    except Exception as e:
        print(f"Error scanning model file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error scanning model file: {str(e)}")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
