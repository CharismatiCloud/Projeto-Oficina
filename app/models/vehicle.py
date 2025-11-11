from typing import Optional
from pydantic import BaseModel

class Vehicle(BaseModel):

    id: int
    client_id: int # Chave estrangeira para o Cliente
    model: str
    plate: str
    color: str
    year: int # <--- NOVO CAMPO ADICIONADO PARA O ANO
    observations: Optional[str] = None
    image_url: Optional[str] = None
