from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    session_id: str = Field(..., description="ID único de sesión / hilo de conversación")
    message: str = Field(..., min_length=1, description="Mensaje enviado por el usuario")

class QuoteSchema(BaseModel):
    id: str
    text: str
    author: str
    source: str
    themes: List[str]
    verified: bool

class CrisisResource(BaseModel):
    name: str = ""
    phone: str = ""
    hours: str = ""
    source_url: str = ""
    verified_at: str = "YYYY-MM-DD"

class CrisisResponseData(BaseModel):
    is_crisis: bool = False
    message: str = ""
    resources: List[CrisisResource] = []

class ChatResponse(BaseModel):
    session_id: str
    response: str
    quote: Optional[QuoteSchema] = None
    is_crisis: bool = False
    crisis_data: Optional[CrisisResponseData] = None

class ThreadCreateResponse(BaseModel):
    session_id: str
    created_at: str
