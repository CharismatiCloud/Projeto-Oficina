# Projeto Oficina

Sistema de cadastro e controle de veículos, clientes e serviços de uma oficina mecânica, construído com FastAPI e SQLAlchemy.

## Requisitos

- Python 3.11+
- pip

## Como rodar o projeto

### 1. Extraia o projeto

Extraia o `.zip` em uma pasta de sua preferência.

> O projeto já vem com uma pasta `venv/` e as pastas `dist/`/`build/` (sobras de uma build antiga feita com PyInstaller). Elas não são necessárias para rodar via Python e podem ser ignoradas ou apagadas.

### 2. Crie um ambiente virtual novo

Não reaproveite a pasta `venv/` que já vem no projeto — ela foi criada em outro computador (aponta para um caminho específico de outra máquina) e está incompleta.

Abra o terminal na pasta do projeto e rode:

```bash
python -m venv venv
```

### 3. Ative o ambiente virtual

No **cmd**:

```bash
.\venv\Scripts\activate.bat
```

No **PowerShell**:

```bash
.\venv\Scripts\Activate.ps1
```

Você vai ver `(venv)` aparecer no início da linha do terminal, confirmando que está ativo.

### 4. Instale as dependências

```bash
pip install -r requirements.txt
pip install passlib itsdangerous
```

> `passlib` e `itsdangerous` são usados pelo projeto (hash de senha no login e sessão de usuário), mas não estão listados no `requirements.txt`, por isso precisam ser instalados à parte.

### 5. Rode o projeto

Com o ambiente virtual ainda ativo:

```bash
python main.py
```

Isso sobe o servidor em `http://127.0.0.1:8000`.

Alternativa equivalente (recarrega sozinho a cada alteração no código, útil durante o desenvolvimento):

```bash
uvicorn main:app --reload
```

### 6. Acesse no navegador

Abra [http://127.0.0.1:8000](http://127.0.0.1:8000). Você será redirecionado para a tela de login.

**Credenciais padrão:**

- **Usuário:** `admin`
- **Senha:** `admin`

Essas credenciais são criadas automaticamente na primeira vez que o app roda, caso ainda não exista um usuário administrador no banco (`oficina.db`, que já vem com dados no projeto).

## Estrutura do projeto

```
Projeto-Oficina-main/
├── main.py                  # Ponto de entrada da aplicação FastAPI
├── requirements.txt         # Dependências do projeto
├── oficina.db                # Banco de dados SQLite
└── app/
    ├── routers/              # Rotas (clientes, veículos, serviços, autenticação)
    ├── models/                # Modelos de dados
    ├── helpers/               # Funções auxiliares
    ├── static/                # Arquivos estáticos (CSS, JS)
    ├── templates/             # Templates HTML (Jinja2)
    ├── uploads/                # Arquivos enviados pelos usuários
    ├── database.py            # Configuração do banco de dados
    ├── database_models.py     # Modelos SQLAlchemy
    └── auth_utils.py          # Utilitários de autenticação
```
