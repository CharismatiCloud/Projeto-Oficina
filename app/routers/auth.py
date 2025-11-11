import sys
from pathlib import Path
from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from starlette.responses import RedirectResponse
from starlette import status

# --- NOVAS IMPORTAÇÕES DO BANCO ---
from app.database import SessionLocal  # Importa o criador de sessão
from app.database_models import User   # Importa o modelo da tabela Users
# ----------------------------------

from app.auth_utils import verify_password
# (Não precisamos mais do FAKE_USER_DB, então foi removido)

router = APIRouter(tags=["auth"])

# --- LÓGICA DE TEMPLATES (sem alteração) ---
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS) 
else:
    BASE_DIR = Path(".") 
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates") 
# -----------------------------------------------------------------

# --- ROTA 1: MOSTRAR O FORMULÁRIO DE LOGIN (sem alteração) ---
@router.get("/login", name="login_form")
def login_form(request: Request):
    """Exibe o formulário de login."""
    if "user" in request.session:
        return RedirectResponse(url="/clients", status_code=status.HTTP_303_SEE_OTHER)
        
    return templates.TemplateResponse(
        "auth/login.html", 
        {"request": request, "title": "Login"}
    )

# --- ROTA 2: PROCESSAR O LOGIN (MODIFICADA) ---
@router.post("/login", name="login_process")
def login_process(request: Request, username: str = Form(...), password: str = Form(...)):
    """Processa os dados de login usando o banco de dados SQLAlchemy."""
    
    # 1. Cria uma sessão com o banco
    db = SessionLocal()
    
    try:
        # 2. Busca o usuário no banco de dados (substitui o FAKE_USER_DB)
        user = db.query(User).filter(User.username == username).first()

        # 3. Verifica a senha (mesma lógica de antes)
        if user and verify_password(password, user.password_hash):
            # Se sim, salva na sessão
            request.session["user"] = user.username
            return RedirectResponse(url="/clients", status_code=status.HTTP_303_SEE_OTHER)
        
        # 4. Se falhar, recarrega o login com erro
        return templates.TemplateResponse(
            "auth/login.html", 
            {
                "request": request, 
                "title": "Login",
                "error": "Usuário ou senha inválidos."
            }
        )
    finally:
        # 5. Fecha a sessão, não importa o que aconteça
        db.close()

# --- ROTA 3: LOGOUT (sem alteração) ---
@router.get("/logout", name="logout")
def logout(request: Request):
    """Limpa a sessão do usuário."""
    request.session.clear()
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)