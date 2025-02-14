from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Set, List, Dict, Any, Optional
import json
import os
import datetime
import platform
import psutil
import ast
import zipfile
import shutil
import requests
import subprocess
import sys  # Import sys for standard library modules
from pathlib import Path

app = FastAPI(title="Model Analysis API")

# Constants
UPLOAD_DIR = Path("static")
EXTRACTED_DIR = UPLOAD_DIR / "extracted_zip"
TRIVY_REPORT_PATH = UPLOAD_DIR / "trivy_report.json"
POSSIBLE_LICENSES = ["MIT", "Apache-2.0", "GPL", "BSD", "MPL", "LGPL"]  # Make it a constant

# Create directories
UPLOAD_DIR.mkdir(exist_ok=True)
EXTRACTED_DIR.mkdir(exist_ok=True)

# CORS and static files configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

# Known dependencies and models (Consider loading from config files for maintainability)
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

# Standard library modules (Calculate once for efficiency)
STANDARD_LIBRARY_MODULES = set(sys.builtin_module_names)

# ✅ Extract dependencies from Python code
def extract_from_python_code(code: str) -> Set[str]:
    """Extracts imported library names from Python code."""
    dependencies: Set[str] = set()
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                dependencies.add(node.module.split(".")[0])
    except SyntaxError as e:
        print(f"SyntaxError in code: {e}") # Keep print for syntax errors as they are code issues
    except Exception as e:
        print(f"Error extracting dependencies: {e}") # Keep print for other extraction errors
    return dependencies

# ✅ Extract licenses
def extract_licenses(file_content: str) -> List[str]:
    """Extracts potential licenses by keyword matching."""
    return [license for license in POSSIBLE_LICENSES if license in file_content]

# ✅ Extract dependencies based on file type
def extract_dependencies_from_file(file_content: str, filename: str) -> List[str]:
    """Extracts dependencies based on file type (e.g., Python, Notebook)."""
    dependencies: Set[str] = set()
    try:
        if filename.endswith(".ipynb"):
            notebook_data = json.loads(file_content)
            for cell in notebook_data.get("cells", []):
                if cell.get("cell_type") == "code":
                    dependencies.update(
                        extract_from_python_code("".join(cell.get("source", [])))
                    )
        else: # Assumes other files are Python code
            dependencies.update(extract_from_python_code(file_content))
        return list(dependencies)
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError processing {filename}: {e}")
        return []
    except Exception as e:
        print(f"Error extracting dependencies from {filename}: {e}")
        return []

# ✅ Determine author
def determine_author(dependencies: List[str], model_name: str = "") -> str:
    """Determines the author based on known dependencies and model names."""
    model_name_lower = model_name.lower()
    if model_name_lower in KNOWN_MODELS:
        return KNOWN_MODELS[model_name_lower]
    for lib in dependencies:
        lib_lower = lib.lower()
        if lib_lower in KNOWN_DEVELOPERS:
            return KNOWN_DEVELOPERS[lib_lower]
    return "Community"  # Default to Community if author is unknown

# ✅ System Specifications
def get_system_specs() -> Dict[str, str]:
    """Retrieves system hardware specifications."""
    return {
        "CPU": platform.processor() or "Unknown",
        "RAM": f"{round(psutil.virtual_memory().total / (1024**3))} GB",
        "GPU": "N/A (GPU detection requires additional libraries)",
        "OS": f"{platform.system()} {platform.release()}",
    }

# ✅ Correct Aliases and Typos
def correct_aliases(dependencies: Set[str]) -> List[str]:
    """Corrects common aliases and typos in dependency names."""
    corrections = {
        "maths": "math",
        "sklearn": "scikit-learn",
        "skimage": "scikit-image", # Example correction
    }
    corrected = set()
    for dep in dependencies:
        corrected.add(corrections.get(dep, dep))
    return list(corrected)

# ✅ Trivy Scan
def trivy_scan(file_path: Path) -> Dict[str, Any]:
    """Runs a Trivy scan on the given file path."""
    trivy_output = TRIVY_REPORT_PATH
    try:
        subprocess.run(
            ["trivy", "fs", "--format", "json", "--output", str(trivy_output), str(file_path)],
            check=True,
            capture_output=True,  # Capture output for debugging
            text=True, # Ensure text output
        )
        if trivy_output.exists():
            with open(trivy_output, "r") as report:
                return json.load(report)
        else:
            return {"error": "Trivy report was not generated."} # Indicate report not found
    except FileNotFoundError:
        return {"error": "Trivy command not found. Please ensure Trivy is installed and in your PATH."}
    except subprocess.CalledProcessError as e:
        return {"error": f"Trivy scan failed with exit code {e.returncode}: {e.stderr or e.stdout}"} # Include stderr/stdout
    except Exception as e:
        return {"error": f"Error running Trivy scan: {e}"}
    finally:
        if trivy_output.exists(): # Clean up trivy report after each scan
            os.remove(trivy_output)

# ✅ NVD Scan (Placeholder)
def nvd_scan(dependencies: List[str]) -> Dict[str, str]:
    """Placeholder for NVD scan functionality."""
    nvd_results = {}
    for dep in dependencies:
        nvd_results[dep] = "NVD scan result placeholder (N/A)" # Indicate placeholder
    return nvd_results

# ✅ Process ZIP file
def process_zip_file(zip_path: Path) -> tuple[List[str], List[str]]:
    """Extracts and processes files from a ZIP archive to find dependencies and licenses."""
    if EXTRACTED_DIR.exists():
        shutil.rmtree(EXTRACTED_DIR) # Clean up previous extraction
    EXTRACTED_DIR.mkdir(exist_ok=True)

    all_dependencies: Set[str] = set()
    all_licenses: Set[str] = set()

    try:
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(EXTRACTED_DIR)

        for root, _, files in os.walk(EXTRACTED_DIR):
            for file in files:
                file_path = Path(root) / file
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        file_content = f.read()
                        dependencies = extract_dependencies_from_file(file_content, file)
                        licenses = extract_licenses(file_content)
                        all_dependencies.update(dependencies)
                        all_licenses.update(licenses)
                except Exception as e: # Catch file reading errors within zip
                    print(f"Skipping file {file} due to error: {e}")
    except zipfile.BadZipFile:
        raise ValueError("Invalid ZIP file.") # Specific exception for zip errors
    except Exception as e: # General zip processing errors
        raise Exception(f"Error processing ZIP file: {e}")
    finally:
        shutil.rmtree(EXTRACTED_DIR, ignore_errors=True) # Ensure cleanup even if errors occur

    return list(all_dependencies), list(all_licenses)


# ✅ Upload & Process File
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Endpoint to upload and process a file for model analysis."""
    try:
        file_path = UPLOAD_DIR / file.filename
        file_path.write_bytes(await file.read())

        if file.filename.endswith(".zip"):
            try:
                dependencies, licenses = process_zip_file(file_path)
                file_type_description = "ZIP Archive" # More descriptive type
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e)) # Bad request for zip errors
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e)) # Server error for zip processing
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                file_content = f.read()
            dependencies = extract_dependencies_from_file(file_content, file.filename)
            licenses = extract_licenses(file_content)
            file_type_description = "Software Model" # More descriptive type

        corrected_dependencies = correct_aliases(set(dependencies)) # Correct after extraction
        filtered_dependencies = [
            dep for dep in corrected_dependencies if dep not in STANDARD_LIBRARY_MODULES
        ]
        author = determine_author(filtered_dependencies, Path(file.filename).stem)
        system_specs = get_system_specs()
        # version_details = check_versions(filtered_dependencies) # Version check removed for now
        trivy_results = trivy_scan(file_path) # Run Trivy Scan
        nvd_results = nvd_scan(filtered_dependencies) # NVD Scan Placeholder

        result = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "ModelDetails": {
                "Name": file.filename,
                "Version": "1.0",
                "Type": file_type_description,
                "Author": author,
                "Licenses": licenses,
                "Libraries": filtered_dependencies,
                # "VersionDetails": version_details, # Removed version details for now
                "SystemSpecs": system_specs,
                "Source": "Local Upload",
                "BOMGeneration": {
                    "Timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(), # UTC timestamp
                    "Method": "Automated Extraction",
                    "GeneratedBy": "FastAPI System",
                },
            },
            "SecurityScans": {
                "Trivy": trivy_results,
                "NVD": nvd_results,
            },
        }

        output_path = UPLOAD_DIR / "downloaded.json"
        output_path.write_text(json.dumps(result, indent=4))

        return {"message": "File processed successfully", "data": result}

    except HTTPException as http_e: # Re-raise HTTP Exceptions
        raise http_e
    except Exception as e: # Catch all other exceptions and return 500
        raise HTTPException(status_code=500, detail=f"File processing failed: {e}")