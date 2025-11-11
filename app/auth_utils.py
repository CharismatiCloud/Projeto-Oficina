from passlib.context import CryptContext
from fastapi import Request, HTTPException
from starlette import status
from app.database import SessionLocal
from app.database_models import User           

# Configura o algoritmo de hashing (bcrypt é o recomendado)
pwd_context = CryptContext(schemes=["scrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha pura corresponde ao hash salvo."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Gera um hash para a senha pura."""
    return pwd_context.hash(password)

def create_admin_user_if_not_exists():
    """Cria o usuário 'admin' padrão se ele não existir (versão SQLAlchemy)."""
    
    # 1. Cria uma sessão (como no seu exemplo)
    db = SessionLocal()
    
    try:
        # 2. Verifica se o usuário "admin" existe (como no seu exemplo)
        admin_user = db.query(User).filter(User.username == "admin").first()
        
        if admin_user is None:
            # 3. Se não existir, cria o novo usuário (como no seu exemplo)
            admin_hash = get_password_hash("admin")
            new_admin = User(
                username="admin",
                password_hash=admin_hash,
                full_name="Administrador do Sistema"
            )
            db.add(new_admin)
            db.commit() # Salva no banco
            print("Usuário 'admin' padrão criado com sucesso.")
        else:
            print("Usuário 'admin' já existe.")
            
    finally:
        # 4. Fecha a sessão (como no seu exemplo)
        db.close()

# --- FUNÇÃO MOVIDA PARA CÁ ---
def get_current_user(request: Request):
    """Verifica se o usuário está na sessão. Se não, redireciona para o login."""
    username = request.session.get("user")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            # CORREÇÃO: Converta o objeto URL para string
            headers={"Location": str(request.url_for("login_form"))} 
        )
    return username