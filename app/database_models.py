from sqlalchemy import Column, Integer, String, Float, ForeignKey, TEXT
from sqlalchemy.orm import relationship
from .database import Base # Importa o 'Base' que acabamos de criar

# 1. Modelo de Tabela para Usuários
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))

# 2. Modelo de Tabela para Clientes
class Client(Base):
    __tablename__ = "clients"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    phone = Column(String(50))
    email = Column(String(255), unique=True, index=True)

    # Relacionamento: Um Cliente tem muitos Veículos
    vehicles = relationship("Vehicle", back_populates="owner", cascade="all, delete-orphan")

# 3. Modelo de Tabela para Veículos
class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(Integer, primary_key=True, autoincrement=True)
    model = Column(String(100), nullable=False)
    plate = Column(String(20), unique=True, nullable=False, index=True)
    color = Column(String(50))
    year = Column(Integer)
    observations = Column(TEXT)
    image_url = Column(String(500))
    
    # Chave Estrangeira
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)

    # Relacionamentos
    owner = relationship("Client", back_populates="vehicles")
    services = relationship("Service", back_populates="vehicle", cascade="all, delete-orphan")

# 4. Modelo de Tabela para Serviços
class Service(Base):
    __tablename__ = "services"
    id = Column(Integer, primary_key=True, autoincrement=True)
    description = Column(String(500), nullable=False)
    start_date = Column(String(20), nullable=False)
    status = Column(String(50), nullable=False) # (Ex: "Pendente", "Concluído")
    price = Column(Float, default=0.0)
    notes = Column(TEXT)

    # Chave Estrangeira
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=False)

    # Relacionamento
    vehicle = relationship("Vehicle", back_populates="services")