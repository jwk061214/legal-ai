from pydantic import BaseModel
from typing import Dict, Optional

class InterpretationRequest(BaseModel):
    text: str

class InterpretationResponse(BaseModel):
    result: str
    terms: Optional[Dict[str, str]] = None