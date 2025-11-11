import sys
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from starlette import status as status_codes 
from datetime import datetime

# --- IMPORTAÇÕES DO BANCO DE DADOS (SQLAlchemy) ---
from app.database import SessionLocal
# Importa os MODELOS DAS TABELAS
from app.database_models import Vehicle, Service
# --------------------------------------------------

# --- IMPORTAÇÕES DE MODELOS (PYDANTIC) ---
# Usamos o modelo Pydantic para validar o status
from app.models.service import ServiceStatus

# --- IMPORTAÇÃO DA FUNÇÃO DE AUTH ---
from app.auth_utils import get_current_user
# ------------------------------------
# (Os imports do FAKE_DB foram removidos)


# Importação necessária para o redirecionamento
from app.routers.vehicles import router as vehicles_router 

router = APIRouter(prefix="/services", tags=["services"])

# --- LÓGICA DE CAMINHO PARA PYINSTALLER (sem alteração) ---
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS) 
else:
    BASE_DIR = Path(".") 

templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates") 
# ----------------------------------------------------


# Rota 1: Exibir Formulário de Novo Serviço (MODIFICADA)
@router.get("/new/{vehicle_id}", name="new_service_form")
def new_service_form(request: Request, vehicle_id: int):
    username = get_current_user(request) # <--- PROTEGIDO
    
    db = SessionLocal()
    try:
        # Busca o veículo no banco de dados real
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Veículo não encontrado.")
    finally:
        db.close()
    
    # Passa as opções de status para o template
    status_options = [e.value for e in ServiceStatus]

    return templates.TemplateResponse(
        "services/new.html",
        {
            "request": request, 
            "title": f"Novo Serviço para {vehicle.model} ({vehicle.plate})", 
            "vehicle": vehicle,
            "status_options": status_options,
            "username": username # <-- Passa o usuário
        }
    )


# Rota 2: Processar Cadastro de Serviço (MODIFICADA)
@router.post("/", name="create_service")
def create_service(
    request: Request, # <--- 'request' ADICIONADO
    vehicle_id: int = Form(...),
    description: str = Form(...),
    status_str: str = Form(ServiceStatus.PENDENTE.value),
    price: float = Form(0.0),
    observations: Optional[str] = Form(None), # 'observations' do formulário
):
    get_current_user(request) # <--- PROTEGIDO
    
    db = SessionLocal()
    try:
        # 1. Verifica se o vehicle_id existe
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=400, detail="ID de Veículo inválido.")

        # 2. Valida o Enum de Status (como antes)
        try:
            status_enum = ServiceStatus(status_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Status inválido: {status_str}")

        # 3. Pega a data atual
        current_date_only = datetime.now().strftime("%Y-%m-%d")

        # 4. Cria o novo objeto Service
        # Nota: o campo no formulário é 'observations', mas no modelo é 'notes'
        new_service = Service(
            vehicle_id=vehicle_id,
            start_date=current_date_only, 
            description=description,
            status=status_enum.value, # Salva o valor da string (ex: "Pendente")
            price=price,
            notes=observations 
        )
        
        # 5. Adiciona e salva no banco
        db.add(new_service)
        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"Erro ao criar serviço: {e}")
        raise HTTPException(status_code=400, detail=f"Erro ao criar serviço: {e}")
    finally:
        db.close()

    # Redireciona de volta para a página de detalhes do veículo
    return RedirectResponse(
        vehicles_router.url_path_for("show_vehicle", vehicle_id=vehicle_id), 
        status_code=status_codes.HTTP_303_SEE_OTHER
    )