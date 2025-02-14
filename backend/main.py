from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import requests
import json
import os
import platform
import psutil
import ast
import re
import importlib
import pkg_resources
import importlib.metadata
import zipfile
from io import BytesIO

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

# ✅ Enhanced dependency version extraction
def extract_dependency_versions(file_content, filename):
    versions = {}
    
    # Check requirements.txt
    if filename == "requirements.txt":
        lines = file_content.splitlines()
        for line in lines:
            # Handle different requirement formats
            # Examples: package==1.0.0, package>=1.0.0, package~=1.0.0
            match = re.match(r"([a-zA-Z0-9_\-]+)(?:[=~><]+)([0-9][0-9\.\-]*[0-9])", line.strip())
            if match:
                package, version = match.groups()
                versions[package] = version
    
    # Check pyproject.toml
    elif filename == "pyproject.toml":
        # Handle both dependencies and dev-dependencies sections
        dependency_patterns = [
            r'dependencies\s*=\s*\[(.*?)\]',
            r'dependencies\s*=\s*{(.*?)}',
            r'([a-zA-Z0-9_\-]+)\s*=\s*["\']([0-9][0-9\.\-]*[0-9])["\']'
        ]
        
        for pattern in dependency_patterns:
            matches = re.finditer(pattern, file_content, re.DOTALL)
            for match in matches:
                if len(match.groups()) == 2:
                    package, version = match.groups()
                    versions[package.strip()] = version.strip()

    # Extract versions from imported packages
    for dep in extract_from_python_code(file_content):
        try:
            # Try multiple methods to get version
            version = None
            
            # Method 1: Try importing and checking __version__
            try:
                module = importlib.import_module(dep)
                version = getattr(module, "__version__", None)
                if not version:
                    version = getattr(module, "VERSION", None)
                if not version:
                    version = getattr(module, "version", None)
            except Exception:
                pass
            
            # Method 2: Try pkg_resources
            if version is None:
                try:
                    dist = pkg_resources.get_distribution(dep)
                    version = dist.version
                except Exception:
                    pass
            
            # Method 3: Try importlib.metadata (Python 3.8+)
            if version is None:
                try:
                    version = importlib.metadata.version(dep)
                except Exception:
                    pass
            
            # Method 4: Try pip list
            if version is None:
                try:
                    import subprocess
                    result = subprocess.run(['pip', 'show', dep], capture_output=True, text=True)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if line.startswith('Version:'):
                                version = line.split('Version:')[1].strip()
                                break
                except Exception:
                    pass

            # Store the version if we found it
            if version:
                versions[dep] = version
            else:
                versions[dep] = "Unknown"
            
        except Exception as e:
            print(f"❌ Error getting version for {dep}: {e}")
            versions[dep] = "Unknown"
    
    return versions

# ✅ Get system hardware specs
def get_system_specs():
    specs = {
        "CPU": platform.processor(),
        "RAM": f"{round(psutil.virtual_memory().total / (1024**3))} GB",
        "OS": f"{platform.system()} {platform.release()}",
        "Python": platform.python_version(),
        "GPU": "N/A"
    }
    
    # Try to detect GPU if possible
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

# ✅ Get latest version from PyPI
def get_latest_version(package_name):
    try:
        response = requests.get(
            f"https://pypi.org/pypi/{package_name}/json",
            timeout=10
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
            "LatestVersion": latest_version
        }
    return version_details

# ✅ Process ZIP content
def process_zip_content(zip_content):
    dependencies = set()
    licenses = set()
    used_versions = {}
    
    with zipfile.ZipFile(BytesIO(zip_content)) as zip_file:
        for file_info in zip_file.filelist:
            if file_info.filename.endswith(('.py', '.ipynb', 'requirements.txt', 'pyproject.toml')):
                try:
                    # Read the file content from the ZIP
                    file_content = zip_file.read(file_info.filename)
                    try:
                        file_content_str = file_content.decode('utf-8')
                    except UnicodeDecodeError:
                        file_content_str = file_content.decode('ISO-8859-1')
                    
                    # Extract dependencies and licenses
                    deps = extract_dependencies(file_content_str, file_info.filename)
                    dependencies.update(deps)
                    licenses.update(extract_licenses(file_content_str))
                    
                    # Extract versions
                    versions = extract_dependency_versions(file_content_str, file_info.filename)
                    used_versions.update(versions)
                except Exception as e:
                    print(f"❌ Error processing {file_info.filename} in ZIP: {e}")
                    continue
    
    return list(dependencies), list(licenses), used_versions

# ✅ Upload & Process File
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        
        # Read file content
        file_content = await file.read()
        
        # Check if the file is a ZIP
        if file.filename.endswith('.zip'):
            dependencies, licenses, used_versions = process_zip_content(file_content)
        else:
            # Try decoding with UTF-8, fallback to ISO-8859-1 if it fails
            try:
                file_content_str = file_content.decode("utf-8")
            except UnicodeDecodeError:
                file_content_str = file_content.decode("ISO-8859-1")

            # Extract dependencies, licenses, and versions for single file
            dependencies = extract_dependencies(file_content_str, file.filename)
            licenses = extract_licenses(file_content_str)
            used_versions = extract_dependency_versions(file_content_str, file.filename)

        # Save the file locally
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Get version details and system specs
        version_details = check_versions(dependencies, used_versions)
        system_specs = get_system_specs()

        return {
            "message": "File processed successfully",
            "data": {
                "ModelDetails": {
                    "Name": file.filename,
                    "Version": "1.0",
                    "Licenses": licenses,
                    "Libraries": dependencies,
                    "VersionDetails": version_details,
                    "SystemSpecs": system_specs,
                    "Source": "Local Upload"
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

# Add a health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

print(os.path.exists("C:\\Users\\Sriram\\Downloads\\downloaded (1).json"))