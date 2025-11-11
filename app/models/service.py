from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

# ----------------------------------------------------
# 1. ENUMERADOR DE STATUS
# Define os possíveis estados de um serviço.
# É importante que estes valores sejam usados no backend.
# ----------------------------------------------------
class ServiceStatus(str, Enum):
    """
    Status possíveis para um serviço na oficina.
    Os valores em caixa alta são usados para comparação no código.
    """
    PENDENTE = "PENDENTE"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDO = "CONCLUIDO"
    CANCELADO = "CANCELADO"
    
# ----------------------------------------------------
# 2. MODELO Pydantic para Serviço (Service)
# Define a estrutura de dados para um serviço.
# ----------------------------------------------------
class Service(BaseModel):
    """
    Representa um serviço realizado em um veículo.
    """
    id: Optional[int] = Field(None, description="Identificador único do serviço.")
    
    # Chave Estrangeira: ID do veículo relacionado
    vehicle_id: int = Field(..., description="ID do veículo ao qual o serviço pertence.")

    description: str = Field(..., description="Breve descrição do trabalho a ser realizado.")
    
    # Usamos date (apenas a data) em vez de datetime (data e hora)
    start_date: date = Field(..., description="Data de início ou agendamento do serviço (Formato YYYY-MM-DD).")
    
    # Campo para o custo do serviço.
    price: float = Field(..., ge=0.0, description="Preço total cobrado pelo serviço.")
    
    # Status do serviço, utilizando o enumerador definido acima
    status: ServiceStatus = Field(ServiceStatus.PENDENTE, description="Status atual do serviço.")
    
    # Observações adicionais sobre o serviço.
    notes: Optional[str] = Field(None, description="Notas ou observações adicionais sobre o serviço.")
