from fastapi import FastAPI
from typing import Optional
from config import AI_BOM

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Welcome to AI BoM API"}

@app.get("/bom")
def get_bom(category: Optional[str] = None):
    """Fetch AI BoM. Filter by category if provided."""
    if category and category.lower() in AI_BOM:
        return {category: AI_BOM[category.lower()]}
    return AI_BOM

@app.get("/bom/{component}")
def get_component(component: str):
    """Fetch details of a specific AI component."""
    for category, items in AI_BOM.items():
        for item in items:
            if item["name"].lower() == component.lower():
                return item
    return {"error": "Component not found"}

# Run using: uvicorn app:app --reload
