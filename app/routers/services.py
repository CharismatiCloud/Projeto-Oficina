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
# Em app/routers/services.py
# (No topo do arquivo, garanta que todas estas importações existem)
from fastapi import APIRouter, Request, Form, HTTPException, Depends
from starlette.responses import RedirectResponse
from starlette import status as status_codes 
# ... (outras importações) ...


# ... (Suas rotas new_service_form e create_service já estão aqui) ...


# Rota 3: Exibir Formulário de EDIÇÃO de Serviço
@router.get("/{service_id}/edit", name="edit_service_form")
def edit_service_form(request: Request, service_id: int):
    username = get_current_user(request)
    
    db = SessionLocal()
    try:
        service = db.query(Service).filter(Service.id == service_id).first()
        if not service:
            raise HTTPException(status_code=404, detail="Serviço não encontrado.")
            
        status_options = [e.value for e in ServiceStatus]
        
    finally:
        db.close()

    return templates.TemplateResponse(
        "services/edit.html",
        {
            "request": request, 
            "title": f"Editar Serviço: {service.description}", 
            "service": service,
            "status_options": status_options,
            "username": username
        }
    )

# Rota 4: Processar ATUALIZAÇÃO de Serviço
@router.post("/{service_id}/update", name="update_service")
def update_service(
    request: Request,
    service_id: int,
    description: str = Form(...),
    status_str: str = Form(...),
    price: float = Form(0.0),
    observations: Optional[str] = Form(None),
):
    get_current_user(request)
    
    db = SessionLocal()
    try:
        # 1. Busca o serviço existente
        service_to_update = db.query(Service).filter(Service.id == service_id).first()
        if not service_to_update:
            raise HTTPException(status_code=404, detail="Serviço não encontrado.")
            
        # 2. Valida o Status
        try:
            status_enum = ServiceStatus(status_str)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Status inválido: {status_str}")

        # 3. Atualiza os campos
        service_to_update.description = description
        service_to_update.status = status_enum.value
        service_to_update.price = price
        service_to_update.notes = observations
        
        # 4. Salva no banco
        db.commit()
        
        # Pega o vehicle_id para o redirecionamento
        vehicle_id = service_to_update.vehicle_id
        
    except Exception as e:
        db.rollback()
        print(f"Erro ao atualizar serviço: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar serviço: {e}")
    finally:
        db.close()

    # Redireciona de volta para a página do veículo
    return RedirectResponse(
        vehicles_router.url_path_for("show_vehicle", vehicle_id=vehicle_id), 
        status_code=status_codes.HTTP_303_SEE_OTHER
    )

# Rota 5: DELETAR Serviço
@router.post("/{service_id}/delete", name="delete_service")
def delete_service(
    request: Request,
    service_id: int
):
    get_current_user(request)
    
    db = SessionLocal()
    try:
        service_to_delete = db.query(Service).filter(Service.id == service_id).first()
        if not service_to_delete:
            raise HTTPException(status_code=404, detail="Serviço não encontrado.")
        
        # Pega o vehicle_id ANTES de deletar, para saber para onde voltar
        vehicle_id = service_to_delete.vehicle_id
        
        db.delete(service_to_delete)
        db.commit()
        
    except Exception as e:
        db.rollback()
        print(f"Erro ao deletar serviço: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao deletar serviço: {e}")
    finally:
        db.close()
    
    return RedirectResponse(
        vehicles_router.url_path_for("show_vehicle", vehicle_id=vehicle_id), 
        status_code=status_codes.HTTP_303_SEE_OTHER
    )