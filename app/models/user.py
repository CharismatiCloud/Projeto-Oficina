from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: int
    username: str
    password_hash: str # NUNCA guardamos a senha pura
    full_name: Optional[str] = None