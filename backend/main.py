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
from uuid import uuid4
from datetime import datetime

app = FastAPI()

# ✅ Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific domains if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Ensure static directory exists
UPLOAD_DIR = "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ✅ Serve static files
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

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

# ✅ Extract dependencies based on file type
def extract_dependencies(file_content, filename):
    dependencies = set()
    try:
        if filename.endswith(".ipynb"):
            notebook_data = json.loads(file_content)
            for cell in notebook_data.get("cells", []):
                if cell.get("cell_type") == "code":
                    dependencies.update(
                        extract_from_python_code("".join(cell.get("source", [])))
                    )
        else:
            dependencies.update(extract_from_python_code(file_content))
        return list(dependencies)
    except Exception as e:
        print(f"❌ Error extracting dependencies: {e}")
        return []

# ✅ Get system hardware specs
def get_system_specs():
    return {
        "CPU": platform.processor(),
        "RAM": f"{round(psutil.virtual_memory().total / (1024**3))} GB",
        "OS": f"{platform.system()} {platform.release()}",
        "Python": platform.python_version(),
        "GPU": "N/A"  # Placeholder, can be improved with GPU detection
    }

# ✅ Get latest version from PyPI
def get_latest_version(package_name):
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json", timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data["info"].get("version", "Unknown")
    except Exception as e:
        print(f"❌ Error fetching version for {package_name}: {e}")
    return "Unknown"

# ✅ Check versions
def check_versions(dependencies):
    version_details = {}
    for dep in dependencies:
        latest_version = get_latest_version(dep)
        version_details[dep] = {"Version": latest_version}
    return version_details

# ✅ Upload & Process File
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        file_text = file_content.decode("utf-8", errors="ignore")  # ✅ Decode file content
        
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as f:
            f.write(file_content)

        dependencies = extract_dependencies(file_text, file.filename)
        version_details = check_versions(dependencies)
        system_specs = get_system_specs()

        # ✅ Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()

        # ✅ Create CycloneDX BOM
        bom_filename = f"bom_{file.filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        bom_path = os.path.join(UPLOAD_DIR, bom_filename)
        cyclonedx_bom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "serialNumber": f"urn:uuid:{uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "component": {
                    "type": "application",
                    "bom-ref": str(uuid4()),
                    "name": file.filename,
                    "version": "1.0",
                    "hashes": [{"alg": "SHA-256", "content": file_hash}]
                },
                "properties": [
                    {"name": "system.cpu", "value": system_specs["CPU"]},
                    {"name": "system.ram", "value": system_specs["RAM"]},
                    {"name": "system.os", "value": system_specs["OS"]},
                    {"name": "system.python", "value": system_specs["Python"]}
                ]
            },
            "components": [
                {"name": dep, "version": version_details[dep].get("Version", "Unknown")}
                for dep in dependencies
            ],
        }
        with open(bom_path, 'w') as f:
            json.dump(cyclonedx_bom, f, indent=2)

        return {"message": "File processed successfully", "filename": bom_filename, "data": cyclonedx_bom}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating BOM: {str(e)}")

# ✅ Download BOM file
@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(UPLOAD_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type='application/json', filename=filename)
