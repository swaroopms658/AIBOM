from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
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
import subprocess

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
    
    # Check requirements.txt
    if filename == "requirements.txt":
        lines = file_content.splitlines()
        for line in lines:
            match = re.match(r"([a-zA-Z0-9_\-]+)==([0-9\.]+)", line)
            if match:
                package, version = match.groups()
                versions[package] = version
    
    # Check pyproject.toml
    elif filename == "pyproject.toml":
        dependencies = re.findall(r"([a-zA-Z0-9_\-]+) ?= ?\"([0-9\.]+)\"", file_content)
        for package, version in dependencies:
            versions[package] = version
    
    # Extract versions from code
    for dep in extract_from_python_code(file_content):
        try:
            module = importlib.import_module(dep)
            version = getattr(module, "__version__", "Unknown")
            if version == "Unknown":
                version = pkg_resources.get_distribution(dep).version
            versions[dep] = version
        except Exception:
            versions[dep] = "Unknown"
    
    return versions

# ✅ Get system hardware specs
def get_system_specs():
    return {
        "CPU": platform.processor(),
        "RAM": f"{round(psutil.virtual_memory().total / (1024**3))} GB",
        "GPU": "N/A (GPU detection requires additional libraries)"
    }

# ✅ Get latest version from PyPI
def get_latest_version(package_name):
    try:
        response = requests.get(
            f"https://pypi.org/pypi/{package_name}/json", timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            return data["info"].get("version", "Unknown")
    except Exception as e:
        print(f"❌ Error fetching version for {package_name}: {e}")
    return "Unknown"

# ✅ Check versions
def check_versions(dependencies, used_versions):
    version_details = {}
    for dep in dependencies:
        latest_version = get_latest_version(dep)
        version_details[dep] = {
            "UsedVersion": used_versions.get(dep, "Unknown"),
            "LatestVersion": latest_version
        }
    return version_details

# ✅ Scan dependencies with Trivy
def scan_with_trivy(dependencies):
    results = {}
    for dep in dependencies:
        try:
            command = ["trivy", "fs", "--ignore-unfixed", "--severity", "CRITICAL,HIGH,MEDIUM", dep]
            output = subprocess.run(command, capture_output=True, text=True)
            
            if output.returncode == 0:
                results[dep] = output.stdout
            else:
                results[dep] = "No vulnerabilities found or error occurred."
        except Exception as e:
            results[dep] = f"Error scanning with Trivy: {e}"
    return results

# ✅ Fetch vulnerabilities from NVD
def fetch_vulnerabilities_from_nvd(dependencies):
    nvd_results = {}
    api_url = "https://services.nvd.nist.gov/rest/json/cves/1.0"
    for dep in dependencies:
        try:
            response = requests.get(f"{api_url}?keyword={dep}")
            if response.status_code == 200:
                nvd_data = response.json()
                nvd_results[dep] = nvd_data.get("result", {}).get("CVE_Items", [])
            else:
                nvd_results[dep] = "No vulnerabilities found or API error."
        except Exception as e:
            nvd_results[dep] = f"Error fetching from NVD: {e}"
    return nvd_results

# ✅ Upload & Process File
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    # Read file content
    file_content = await file.read()
    file_content_str = file_content.decode("utf-8")

    # Save the file locally
    with open(file_path, "wb") as f:
        f.write(file_content)

    # Extract dependencies, licenses, and versions correctly
    dependencies = extract_dependencies(file_content_str, file.filename)
    licenses = extract_licenses(file_content_str)
    used_versions = extract_dependency_versions(file_content_str, file.filename)
    
    version_details = check_versions(dependencies, used_versions)
    system_specs = get_system_specs()
    
    nvd_results = fetch_vulnerabilities_from_nvd(dependencies)
    trivy_results = scan_with_trivy(dependencies)

    return {"message": "File processed successfully", "data": {
        "ModelDetails": {
            "Name": file.filename,
            "Version": "1.0",
            "Licenses": licenses,
            "Libraries": dependencies,
            "VersionDetails": version_details,
            "VulnerabilityScan": {"NVD": nvd_results, "Trivy": trivy_results},
            "SystemSpecs": system_specs,
            "Source": "Local Upload"
        }
    }}

