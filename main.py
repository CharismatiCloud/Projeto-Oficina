import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse
from starlette import status as status_codes 
# --- Importações auxiliares ---
import sys 
from pathlib import Path
# -----------------------------

# --- Importação dos Roteadores ---
# BANCO DE DADOS
from app.database import engine, Base
from app.database_models import User, Client, Vehicle, Service
from app.auth_utils import create_admin_user_if_not_exists
#----------------------------------------------------------
from app.routers.clients import router as clients_router 
from app.routers.vehicles import router as vehicles_router
from app.routers.services import router as services_router
from app.routers import auth
# ---------------------------------

# Lógica para suportar PyInstaller e paths relativos
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS) 
else:
    BASE_DIR = Path(".") 
# -------------------------------------------------------------------------------


# Cria a instância principal do FastAPI
app = FastAPI(title="Oficina - Cadastro de Veículos")
Base.metadata.create_all(bind=engine)
create_admin_user_if_not_exists()

app.add_middleware(
    SessionMiddleware, 
    secret_key="sua-chave-secreta-muito-forte-aqui-123456",
    https_only=False # Em produção, considere True se tiver HTTPS
)

# Usa o BASE_DIR para montar os caminhos estáticos
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")
app.mount("/uploads", StaticFiles(directory=BASE_DIR / "app" / "uploads"), name="uploads")

# Inclui os roteadores (ordem não importa)
app.include_router(auth.router)
app.include_router(clients_router) 
app.include_router(vehicles_router)
app.include_router(services_router) 

# Rota de redirecionamento para a lista de veículos
@app.get("/", include_in_schema=False)
def redirect_to_list():
    # Garante que a rota de redirecionamento use a rota nomeada do roteador
    return RedirectResponse(
        url="/clients/",
        status_code=status_codes.HTTP_302_FOUND
    )

@app.get("/status")
def status(request: Request):
    return {
        "status": "ok",
        "host": request.client.host,
        "port": request.url.port or 80,
        "scheme": request.url.scheme,
        "path": request.url.path,
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
