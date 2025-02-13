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
import requests
import re
import importlib.util
import sys

app = FastAPI()

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Ensure static directory exists
UPLOAD_DIR = "static"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ✅ Serve static files
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

# ✅ Aliases for common libraries
ALIASES = {
    "maths": "math",
    "sklearn": "scikit-learn"
}

# ✅ List of standard libraries
STANDARD_LIBRARIES = set(sys.builtin_module_names)

def is_standard_library(module_name):
    """Check if a module is a standard Python library"""
    if module_name in STANDARD_LIBRARIES:
        return True
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None and "site-packages" not in (spec.origin or "")
    except ModuleNotFoundError:
        return False


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
                    dependencies.update(
                        extract_from_python_code("".join(cell.get("source", [])))
                    )
        else:
            dependencies.update(extract_from_python_code(file_content))
        return list(dependencies)
    except Exception as e:
        print(f"❌ Error extracting dependencies: {e}")
        return []


# ✅ Extract dependency versions from requirements or pyproject.toml files
def extract_dependency_versions(file_content, filename):
    versions = {}
    if filename == "requirements.txt":
        lines = file_content.splitlines()
        for line in lines:
            match = re.match(r"([a-zA-Z0-9_\-]+)==([0-9\.]+)", line)
            if match:
                package, version = match.groups()
                versions[package] = version
    elif filename == "pyproject.toml":
        dependencies = re.findall(r"([a-zA-Z0-9_\-]+) ?= ?\"([0-9\.]+)\"", file_content)
        for package, version in dependencies:
            versions[package] = version
    return versions


# ✅ Get latest version from PyPI
def get_latest_version(package_name):
    try:
        response = requests.get(
            f"https://pypi.org/pypi/{package_name}/json", timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data["info"]["version"]
    except Exception as e:
        print(f"❌ Error fetching version for {package_name}: {e}")
    return "Unknown"


# ✅ Check versions
def check_versions(dependencies, used_versions):
    version_details = {}
    for dep in dependencies:
        # Map alias to correct name
        dep_name = ALIASES.get(dep, dep)

        # Skip standard libraries
        if is_standard_library(dep_name):
            version_details[dep] = {
                "UsedVersion": "Standard Library",
                "LatestVersion": "N/A"
            }
            continue
        
        # Get latest version from PyPI
        latest_version = get_latest_version(dep_name)
        version_details[dep] = {
            "UsedVersion": used_versions.get(dep, "Unknown"),
            "LatestVersion": latest_version if latest_version else "Unknown"
        }

    return version_details


# ✅ Process uploaded ZIP file
def process_zip_file(zip_path):
    extracted_dir = os.path.join(UPLOAD_DIR, "extracted_zip")

    if os.path.exists(extracted_dir):
        shutil.rmtree(extracted_dir)
    os.makedirs(extracted_dir)

    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extracted_dir)

    all_dependencies = set()
    all_licenses = set()
    all_versions = {}

    for root, _, files in os.walk(extracted_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    file_content = f.read()
                    dependencies = extract_dependencies(file_content, file)
                    versions = extract_dependency_versions(file_content, file)
                    licenses = extract_licenses(file_content)
                    all_dependencies.update(dependencies)
                    all_licenses.update(licenses)
                    all_versions.update(versions)
            except Exception as e:
                print(f"❌ Skipping file {file}: {e}")

    return list(all_dependencies), list(all_licenses), all_versions


# ✅ Upload & Process File
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    dependencies, licenses, used_versions = process_zip_file(file_path)
    version_details = check_versions(dependencies, used_versions)
    system_specs = {
        "CPU": platform.processor(),
        "RAM": f"{round(psutil.virtual_memory().total / (1024**3))} GB",
        "GPU": "N/A (GPU detection requires additional libraries)"
    }

    result = {
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
                "Timestamp": datetime.datetime.utcnow().isoformat(),
                "Method": "Automated Extraction",
                "GeneratedBy": "FastAPI System"
            }
        }
    }

    return {"message": "File processed successfully", "data": result}
