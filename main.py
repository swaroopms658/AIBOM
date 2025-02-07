from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import re

app = FastAPI()

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Adjust if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Function to extract libraries from Python file
def extract_python_libraries(file_content):
    imports = re.findall(r"^(?:import|from) (\w+)", file_content, re.MULTILINE)
    unique_imports = list(set(imports))  # Remove duplicates
    return {"libraries": unique_imports}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        if not file:
            raise HTTPException(status_code=400, detail="No file uploaded")

        content = await file.read()
        content_str = content.decode("utf-8")  # Decode file content
        
        # DEBUG: Print file details in backend console
        print(f"Received file: {file.filename}, Size: {len(content)} bytes")

        if file.filename.endswith(".py"):
            extracted_data = extract_python_libraries(content_str)
        else:
            extracted_data = {"error": "Unsupported file type"}

        return extracted_data

    except Exception as e:
        print("Error processing file:", str(e))
        raise HTTPException(status_code=500, detail="File processing failed")

