import sys
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# --- LÓGICA DE CAMINHO ---
# (Garante que o banco seja criado na raiz do projeto)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS) 
else:
    BASE_DIR = Path(".") 

DB_FILE = BASE_DIR / "oficina.db"
# -------------------------

# 1. Engine de Conexão (como no seu exemplo)
# A string de conexão aponta para o nosso arquivo de banco
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_FILE}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    # 'check_same_thread' é necessário apenas para SQLite
    connect_args={"check_same_thread": False} 
)

# 2. Fábrica de Sessões (como no seu exemplo)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 3. Base Declarativa (como no seu exemplo)
# Nossas classes de modelo herdarão desta
Base = declarative_base()

# --- Função helper para obter a sessão ---
def get_db():
    """Função helper para gerenciar a sessão do banco de dados."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()