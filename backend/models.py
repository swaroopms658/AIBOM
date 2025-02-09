from pydantic import BaseModel
from typing import List

class BoMItem(BaseModel):
    name: str
    spec: str
    purpose: str

class BoMCategory(BaseModel):
    category: str
    items: List[BoMItem]
