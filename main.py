from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import re
import datetime
import os
import nbformat  # ✅ To handle Jupyter Notebook (.ipynb) files

app = FastAPI()

# ✅ Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Change this if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Known library maintainers
KNOWN_DEVELOPERS = {
    "tensorflow": "Google",
    "torch": "Meta (Facebook)",
    "transformers": "Hugging Face",
    "numpy": "Community",
    "pandas": "Community",
    "scipy": "Community",
    "sklearn": "Community",
    "matplotlib": "Community",
}

# ✅ Function to extract dependencies from Python or Jupyter Notebook files
def extract_dependencies(file_content, filename):
    dependencies = set()

    if filename.endswith(".ipynb"):  # If it's a Jupyter Notebook
        try:
            notebook = nbformat.reads(file_content, as_version=4)
            for cell in notebook.cells:
                if cell.cell_type == "code":
                    matches = re.findall(r'^\s*(?:import|from) (\w+)', cell.source, re.MULTILINE)
                    dependencies.update(matches)
        except Exception as e:
            print("Notebook Parsing Error:", e)
    else:  # If it's a Python script
        dependencies.update(re.findall(r'^\s*(?:import|from) (\w+)', file_content, re.MULTILINE))

    return list(dependencies)

# ✅ Function to determine author based on dependencies
def determine_author(dependencies):
    for lib in dependencies:
        if lib.lower() in KNOWN_DEVELOPERS:
            return KNOWN_DEVELOPERS[lib.lower()]
    return "Unknown"

# ✅ Upload & Process Code File
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        file_text = content.decode("utf-8")

        # Extract dependencies (supports both .py and .ipynb files)
        dependencies = extract_dependencies(file_text, file.filename)
        print("Extracted Dependencies:", dependencies)  # Debugging

        # Determine the author
        author = determine_author(dependencies)
        print("Determined Author:", author)  # Debugging

        # ✅ Create JSON structure matching your schema
        result = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "ModelDetails": {
                "Name": file.filename,
                "Version": "1.0",
                "Type": "Software Model",
                "Author": author,
                "Licenses": ["MIT", "Apache-2.0"],
                "Libraries": dependencies,
                "Source": "Local Upload",
                "BOMGeneration": {
                    "Timestamp": datetime.datetime.utcnow().isoformat(),
                    "Method": "Automated Extraction",
                    "GeneratedBy": "FastAPI System"
                },
            }
        }

        # ✅ Save JSON file
        json_filename = file.filename.replace(".py", "_bom.json").replace(".ipynb", "_bom.json")
        json_path = os.path.join("static", json_filename)

        os.makedirs("static", exist_ok=True)  # Ensure 'static' folder exists
        with open(json_path, "w") as json_file:
            json.dump(result, json_file, indent=4)

        return {"message": "File processed successfully", "data": result, "json_file": json_filename}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ✅ Endpoint to serve JSON files
@app.get("/static/{json_filename}")
async def get_json_file(json_filename: str):
    file_path = os.path.join("static", json_filename)
    if os.path.exists(file_path):
        return {"json_file": file_path}
    else:
        raise HTTPException(status_code=404, detail="File not found")
