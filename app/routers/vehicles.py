import sys
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, Form, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from starlette import status
import io
import openpyxl 
from datetime import datetime
# Adiciona 'joinedload' para otimizar queries com 'join'
from sqlalchemy.orm import joinedload

# --- IMPORTAÇÕES DO BANCO DE DADOS (SQLAlchemy) ---
from app.database import SessionLocal
# Importa os MODELOS DAS TABELAS
from app.database_models import Client, Vehicle, Service
# --------------------------------------------------

# --- IMPORTAÇÃO DA FUNÇÃO DE AUTH ---
from app.auth_utils import get_current_user
# ------------------------------------


router = APIRouter(prefix="/vehicles", tags=["vehicles"])

# --- LÓGICA DE CAMINHO PARA PYINSTALLER (sem alteração) ---
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS) 
else:
    BASE_DIR = Path(".") 

templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates") 
UPLOAD_DIR = Path("app/uploads/vehicles")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# ----------------------------------------------------

# --- ROTAS PROTEGIDAS E MIGRADAS ---

@router.get("/new/{client_id}", name="new_vehicle_form") 
def new_vehicle_form_for_client(request: Request, client_id: int):
    username = get_current_user(request)
    
    db = SessionLocal()
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    finally:
        db.close()
    
    empty_vehicle = {
        "id": None, "client_id": client_id, "model": "", "plate": "",
        "color": "", "year": None, "observations": "", "image_url": None
    }
    
    return templates.TemplateResponse(
        "vehicles/new.html",
        {
            "request": request, 
            "title": f"Novo Veículo para {client.name}", 
            "client": client,
            "vehicle": empty_vehicle,
            "username": username
        }
    )

@router.get("/new", name="new_vehicle_general") 
def new_vehicle_form_general(request: Request):
    username = get_current_user(request)
    
    db = SessionLocal()
    try:
        clients_list = db.query(Client).order_by(Client.name).all()
    finally:
        db.close()
        
    empty_vehicle = {
        "id": None, "client_id": None, "model": "", "plate": "",
        "color": "", "year": None, "observations": "", "image_url": None
    }
    
    return templates.TemplateResponse(
        "vehicles/new.html",
        {
            "request": request, 
            "title": "Novo Veículo", 
            "clients": clients_list,
            "vehicle": empty_vehicle,
            "username": username
        }
    )

@router.get("/", name="list_vehicles")
def list_vehicles(request: Request):
    username = get_current_user(request)
    
    db = SessionLocal()
    try:
        vehicles_data = db.query(Vehicle).options(
            joinedload(Vehicle.owner)
        ).order_by(Vehicle.model).all()
    finally:
        db.close()
        
    return templates.TemplateResponse(
        "vehicles/list.html",
        {
            "request": request, 
            "vehicles": vehicles_data, 
            "title": "Lista de Veículos",
            "username": username
        }
    )

# ⬇️⬇️ FUNÇÃO ATUALIZADA ⬇️⬇️
@router.post("/", name="create_vehicle")
async def create_vehicle(
    request: Request,
    client_id: int = Form(...),
    model: str = Form(...),
    plate: str = Form(...),
    color: str = Form(...),
    year: int = Form(...), 
    observations: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None)
):
    get_current_user(request)
    
    # Padroniza a placa para a verificação
    plate_str = plate.upper().strip()
    
    db = SessionLocal()
    try:
        # --- VERIFICAÇÃO DE DUPLICIDADE ---
        existing_vehicle = db.query(Vehicle).filter(Vehicle.plate == plate_str).first()
        if existing_vehicle:
            # A PLACA JÁ EXISTE! Recarrega o formulário com uma mensagem de erro.
            clients_list = db.query(Client).order_by(Client.name).all()
            
            # Recria o "vehicle" com os dados que o usuário digitou
            form_data_error = {
                "client_id": client_id, "model": model, "plate": plate,
                "color": color, "year": year, "observations": observations
            }
            
            return templates.TemplateResponse(
                "vehicles/new.html",
                {
                    "request": request, 
                    "title": "Novo Veículo", 
                    "clients": clients_list,
                    "vehicle": form_data_error, # Devolve os dados digitados
                    "username": request.session.get("user"),
                    "error": f"A placa '{plate_str}' já está cadastrada." # O ALERTA!
                }
            )
        # --- FIM DA VERIFICAÇÃO ---

        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=400, detail="ID de Cliente inválido.")
        
        new_vehicle = Vehicle(
            client_id=client_id, model=model, plate=plate_str,
            color=color, year=year, observations=observations, image_url=None
        )
        
        db.add(new_vehicle)
        db.commit()
        db.refresh(new_vehicle)

        image_url = None
        if photo and photo.filename:
            safe_filename = f"{new_vehicle.id}_{Path(photo.filename).name}" 
            file_path = UPLOAD_DIR / safe_filename
            try:
                with file_path.open("wb") as buffer:
                    shutil.copyfileobj(photo.file, buffer)
                image_url = f"/uploads/vehicles/{safe_filename}"
                new_vehicle.image_url = image_url
                db.commit()
            except Exception as e:
                print(f"Erro ao salvar a foto: {e}")
            finally:
                await photo.close()
                
    except Exception as e:
        db.rollback()
        print(f"Erro ao criar veículo: {e}")
        # Esta é a linha que está a causar o seu erro 400
        raise HTTPException(status_code=400, detail=f"Erro ao criar veículo: {e}")
    finally:
        db.close()

    return RedirectResponse(
        router.url_path_for("list_vehicles"),
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.get("/{vehicle_id}/edit", name="edit_vehicle_form")
def edit_vehicle_form(request: Request, vehicle_id: int):
    username = get_current_user(request)
    
    db = SessionLocal()
    try:
        vehicle = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle:
            raise HTTPException(status_code=404, detail="Veículo não encontrado")
        
        clients_list = db.query(Client).order_by(Client.name).all()
    finally:
        db.close()
    
    return templates.TemplateResponse(
        "vehicles/new.html", # Reutiliza o template de criação
        {
            "request": request, 
            "vehicle": vehicle, 
            "title": f"Editar Veículo: {vehicle.plate}", 
            "clients": clients_list,
            "username": username
        }
    )

# ⬇️⬇️ FUNÇÃO ATUALIZADA ⬇️⬇️
@router.post("/{vehicle_id}/update", name="update_vehicle")
async def update_vehicle(
    request: Request,
    vehicle_id: int,
    client_id: int = Form(...),
    model: str = Form(...),
    plate: str = Form(...),
    color: str = Form(...),
    year: int = Form(...), 
    observations: Optional[str] = Form(None),
    photo: Optional[UploadFile] = File(None)
):
    get_current_user(request)
    
    # Padroniza a placa
    plate_str = plate.upper().strip()
    
    db = SessionLocal()
    try:
        # --- VERIFICAÇÃO DE DUPLICIDADE (PARA UPDATE) ---
        existing_vehicle = db.query(Vehicle).filter(Vehicle.plate == plate_str).first()
        
        # Se a placa existe E o ID é diferente do veículo que estamos editando
        if existing_vehicle and existing_vehicle.id != vehicle_id:
            # A PLACA JÁ EXISTE EM OUTRO CARRO!
            
            clients_list = db.query(Client).order_by(Client.name).all()
            
            # Busca o veículo que o usuário tentava editar
            vehicle_data_error = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
            # Retorna o erro, mas mantém os dados que o usuário tentou salvar
            vehicle_data_error.plate = plate_str 
            
            return templates.TemplateResponse(
                "vehicles/new.html",
                {
                    "request": request, 
                    "vehicle": vehicle_data_error, 
                    "title": f"Editar Veículo: {vehicle_data_error.plate}", 
                    "clients": clients_list,
                    "username": request.session.get("user"),
                    "error": f"A placa '{plate_str}' já está cadastrada em outro veículo." # O ALERTA!
                }
            )
        # --- FIM DA VERIFICAÇÃO ---
        
        vehicle_to_update = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle_to_update:
            raise HTTPException(status_code=404, detail="Veículo não encontrado")
        
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            raise HTTPException(status_code=400, detail="ID de Cliente inválido.")
            
        image_url = vehicle_to_update.image_url 
        if photo and photo.filename:
            safe_filename = f"{vehicle_id}_{Path(photo.filename).name}"
            file_path = UPLOAD_DIR / safe_filename
            try:
                with file_path.open("wb") as buffer:
                    shutil.copyfileobj(photo.file, buffer)
                image_url = f"/uploads/vehicles/{safe_filename}"
            except Exception as e:
                print(f"Erro ao salvar a nova foto: {e}")
            finally:
                await photo.close()
                
        vehicle_to_update.client_id = client_id
        vehicle_to_update.model = model
        vehicle_to_update.plate = plate_str # Salva a placa padronizada
        vehicle_to_update.color = color
        vehicle_to_update.year = year
        vehicle_to_update.observations = observations
        vehicle_to_update.image_url = image_url
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erro ao atualizar veículo: {e}")
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar veículo: {e}")
    finally:
        db.close()

    return RedirectResponse(
        router.url_path_for("show_vehicle", vehicle_id=vehicle_id),
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.get("/{vehicle_id}", name="show_vehicle")
def show_vehicle(request: Request, vehicle_id: int):
    username = get_current_user(request)
    
    db = SessionLocal()
    try:
        vehicle = db.query(Vehicle).options(
            joinedload(Vehicle.owner),
            joinedload(Vehicle.services)
        ).filter(Vehicle.id == vehicle_id).first()
        
        if not vehicle:
            raise HTTPException(status_code=404, detail="Veículo não encontrado")

        client = vehicle.owner
        services_list = vehicle.services
        
    finally:
        db.close()

    return templates.TemplateResponse(
        "vehicles/show.html",
        {
            "request": request, 
            "vehicle": vehicle, 
            "client": client,
            "services": services_list,
            "title": f"Detalhes: {vehicle.plate}",
            "username": username
        }
    )

@router.post("/{vehicle_id}/delete", name="delete_vehicle")
def delete_vehicle(
    request: Request,
    vehicle_id: int
):
    get_current_user(request)
    
    db = SessionLocal()
    try:
        vehicle_to_delete = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
        if not vehicle_to_delete:
            raise HTTPException(status_code=404, detail="Veículo não encontrado")
        
        db.delete(vehicle_to_delete)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erro ao deletar veículo: {e}")
    finally:
        db.close()
    
    return RedirectResponse(
        router.url_path_for("list_vehicles"),
        status_code=status.HTTP_303_SEE_OTHER
    )

@router.post("/import", name="import_vehicles")
async def import_vehicles(
    request: Request,
    excel_file: UploadFile = File(...)
):
    get_current_user(request)
    
    if not excel_file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Arquivo inválido.")

    db = SessionLocal()
    imported_count = 0
    try:
        in_memory_file = io.BytesIO(await excel_file.read())
        workbook = openpyxl.load_workbook(in_memory_file)
        sheet = workbook.active
        rows = list(sheet.iter_rows(min_row=2, values_only=True))
        
        valid_client_ids = {row.id for row in db.query(Client.id).all()}
        
        vehicles_to_add = []
        for row in rows:
            if len(row) < 4 or not row[0]: continue
            try:
                client_id = int(row[0])
            except (ValueError, TypeError):
                continue
                
            if client_id not in valid_client_ids:
                continue 
            
            plate = str(row[2]).upper() if row[2] else f"S/PLACA-{imported_count}"
            
            new_vehicle = Vehicle(
                client_id=client_id,
                model=str(row[1]) if row[1] else "N/A",
                plate=plate,
                color=str(row[3]) if row[3] else "N/A",
                year=int(row[4]) if len(row) > 4 and row[4] and str(row[4]).isdigit() else 2000,
                observations=str(row[5]) if len(row) > 5 and row[5] else None,
                image_url=str(row[6]) if len(row) > 6 and row[6] else None
            )
            vehicles_to_add.append(new_vehicle)
            imported_count += 1
        
        if vehicles_to_add:
            db.bulk_save_objects(vehicles_to_add)
            db.commit()
            
        return RedirectResponse(
            router.url_path_for("list_vehicles"),
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"X-Import-Success": str(imported_count)}
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro no processamento do arquivo: {e}")
    finally:
        db.close()