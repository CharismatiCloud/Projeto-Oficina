import sys
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from starlette import status

# --- IMPORTAÇÕES DO BANCO DE DADOS (SQLAlchemy) ---
from app.database import SessionLocal
# Importa os MODELOS DAS TABELAS (para query) e não os Pydantic
from app.database_models import Client, Vehicle, Service
# --------------------------------------------------

# --- IMPORTAÇÃO DA FUNÇÃO DE AUTH ---
from app.auth_utils import get_current_user
# ------------------------------------
# (Os imports do FAKE_DB foram removidos)

router = APIRouter(prefix="/clients", tags=["clients"])

# --- LÓGICA DE TEMPLATES (sem alteração) ---
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS) 
else:
    BASE_DIR = Path(".") 
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates") 
# ----------------------------------------------------


# Rota 1: Exibir Formulário de Novo Cliente (PROTEGIDA)
# (Esta rota não muda, pois só renderiza o template)
@router.get("/new", name="new_client_form")
def new_client_form(request: Request):
    username = get_current_user(request)
    return templates.TemplateResponse(
        "clients/new.html",
        {"request": request, "title": "Novo Cliente", "username": username}
    )

# Rota 2: Processar Cadastro de Cliente (MODIFICADA)
@router.post("/", name="create_client")
def create_client(
    request: Request,
    name: str = Form(...),
    phone: str = Form(...),
    email: Optional[str] = Form(None)
):
    get_current_user(request)
    
    # Cria o novo objeto Client do SQLAlchemy
    new_client = Client(name=name, phone=phone, email=email)
    
    db = SessionLocal()
    try:
        db.add(new_client) # Adiciona o objeto à sessão
        db.commit()        # Salva no banco de dados
    except Exception as e:
        db.rollback()
        # Tratar erro (ex: email duplicado)
        print(f"Erro ao criar cliente: {e}")
    finally:
        db.close()

    return RedirectResponse(
        router.url_path_for("list_clients"),
        status_code=status.HTTP_303_SEE_OTHER
    )

# Rota 3: Listar Clientes (MODIFICADA)
@router.get("/", name="list_clients")
def list_clients(request: Request):
    username = get_current_user(request)
    
    db = SessionLocal()
    try:
        # Substitui "list(FAKE_CLIENT_DB.values())"
        clients_list = db.query(Client).order_by(Client.name).all()
    finally:
        db.close()
    
    return templates.TemplateResponse(
        "clients/list.html",
        {
            "request": request, 
            "clients": clients_list, 
            "title": "Lista de Clientes",
            "username": username
        }
    )

# Rota 4: Exibir Detalhes de um Cliente (MODIFICADA)
@router.get("/{client_id}", name="show_client")
def show_client(request: Request, client_id: int):
    username = get_current_user(request)
    
    db = SessionLocal()
    try:
        # Busca o cliente (substitui FAKE_DB.get())
        # .first() retorna o primeiro resultado ou None
        client = db.query(Client).filter(Client.id == client_id).first()
        
        if not client:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        # Busca os veículos (a lógica é a mesma, só muda a fonte)
        # O SQLAlchemy já popula 'client.vehicles' por causa do 'relationship'
        # que definimos em 'database_models.py'
        vehicles_list = client.vehicles 
    
    finally:
        db.close()
    
    return templates.TemplateResponse(
        "clients/show.html",
        {
            "request": request, 
            "title": f"Detalhes do Cliente: {client.name}", 
            "client": client,
            "vehicles": vehicles_list,
            "username": username
        }
    )

# Rota 5: Exibir Formulário de Edição (MODIFICADA)
@router.get("/{client_id}/edit", name="edit_client_form")
def edit_client_form(request: Request, client_id: int):
    username = get_current_user(request)
    
    db = SessionLocal()
    try:
        client = db.query(Client).filter(Client.id == client_id).first()
        
        if not client:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
    finally:
        db.close()

    return templates.TemplateResponse(
        "clients/edit.html",
        {
            "request": request, 
            "client": client, 
            "title": f"Editar Cliente: {client.name}",
            "username": username
        }
    )

# Rota 6: Processar Atualização do Cliente (MODIFICADA)
@router.post("/{client_id}/update", name="update_client")
def update_client(
    request: Request,
    client_id: int,
    name: str = Form(...),
    phone: str = Form(...),
    email: Optional[str] = Form(None),
):
    get_current_user(request)
    
    db = SessionLocal()
    try:
        # 1. Busca o cliente existente
        client_to_update = db.query(Client).filter(Client.id == client_id).first()
        
        if not client_to_update:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")
        
        # 2. Atualiza os campos
        client_to_update.name = name
        client_to_update.phone = phone
        client_to_update.email = email
        
        # 3. Salva no banco
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erro ao atualizar cliente: {e}")
    finally:
        db.close()

    return RedirectResponse(
        router.url_path_for("show_client", client_id=client_id),
        status_code=status.HTTP_303_SEE_OTHER
    )


# Rota 7: Deletar Cliente (MODIFICADA)
@router.post("/{client_id}/delete", name="delete_client")
def delete_client(
    request: Request,
    client_id: int
):
    get_current_user(request)
    
    db = SessionLocal()
    try:
        # 1. Busca o cliente
        client_to_delete = db.query(Client).filter(Client.id == client_id).first()
        
        if not client_to_delete:
            raise HTTPException(status_code=404, detail="Cliente não encontrado")

        # 2. Deleta o cliente
        # Graças ao 'cascade="all, delete-orphan"' que definimos nos modelos,
        # o SQLAlchemy irá deletar automaticamente todos os Veículos e Serviços
        # relacionados a este cliente.
        db.delete(client_to_delete)
        
        # 3. Salva a mudança
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erro ao deletar cliente: {e}")
    finally:
        db.close()
    
    return RedirectResponse(
        router.url_path_for("list_clients"),
        status_code=status.HTTP_303_SEE_OTHER
    )