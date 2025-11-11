from typing import Optional
from pydantic import BaseModel

class Client(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str] = None