# Vastgoed Backend API

FastAPI backend voor de vastgoed proces- en contractbeheersing applicatie.

## 🚀 Wat is dit?

Een **moderne, snelle REST API** gebouwd met FastAPI die:
- ✅ JWT authenticatie biedt
- ✅ Automatische API documentatie genereert (Swagger)
- ✅ Type-safe is met Python type hints
- ✅ Async support heeft voor performance
- ✅ Makkelijk uit te breiden is

## 📋 Vereisten

- **Python 3.9+** (check: `python --version`)
- **pip** (Python package manager)
- **SQLite** (ingebouwd in Python) of PostgreSQL (optioneel)

## 🔧 Installatie in 5 Minuten

### Stap 1: Python Virtual Environment

```bash
# Maak virtual environment
python -m venv venv

# Activeer (Windows)
venv\Scripts\activate

# Activeer (Mac/Linux)
source venv/bin/activate
```

Je ziet nu `(venv)` voor je terminal prompt.

### Stap 2: Installeer Dependencies

```bash
pip install -r requirements.txt
```

Dit installeert FastAPI, SQLAlchemy, JWT libraries, etc.

### Stap 3: Environment Variables

```bash
# Kopieer .env.example naar .env
cp .env.example .env

# .env wordt automatisch gebruikt
```

De defaults zijn al goed voor development!

### Stap 4: Start de Server

```bash
python main.py
```

Of gebruik uvicorn direct:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

✨ **API draait nu op:** http://localhost:8000

## 🎯 Test de API

### 1. Open Swagger Documentatie

Ga naar: **http://localhost:8000/docs**

Je ziet nu een **interactieve API documentatie**! 🎉

### 2. Test Login

**Via Swagger UI:**
1. Klik op `POST /api/v1/auth/login`
2. Klik "Try it out"
3. Gebruik deze credentials:

```json
{
  "email": "test.projectleider@vastgoed.nl",
  "password": "Test1234!"
}
```

4. Klik "Execute"
5. Je krijgt een **access_token** terug!

**Via curl:**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test.projectleider@vastgoed.nl",
    "password": "Test1234!"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "id": "usr_12345678",
    "email": "test.projectleider@vastgoed.nl",
    "name": "Jan Jansen",
    "role": "projectleider",
    "is_active": true,
    "created_at": "2024-12-17T10:00:00Z"
  }
}
```

### 3. Test Protected Endpoint

**Via Swagger:**
1. Kopieer de `access_token` uit de login response
2. Klik op het groene "Authorize" slot icoon (rechts bovenaan)
3. Plak token en klik "Authorize"
4. Nu kun je alle protected endpoints gebruiken!
5. Test bijv. `GET /api/v1/auth/me`

**Via curl:**
```bash
# Vervang YOUR_TOKEN met de access_token
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔐 Test Accounts

De database wordt automatisch gevuld met deze test users:

| Email | Password | Role |
|-------|----------|------|
| test.projectleider@vastgoed.nl | Test1234! | Projectleider |
| test.beheerder@vastgoed.nl | Test1234! | Beheerder |
| test.controleur@vastgoed.nl | Test1234! | Controleur |
| test.admin@vastgoed.nl | Test1234! | Administratief Medewerker |

## 📁 Project Structuur

```
vastgoed-backend-api/
├── main.py                    # FastAPI app entry point
├── requirements.txt           # Python dependencies
├── .env                       # Environment variables
├── vastgoed.db               # SQLite database (auto-created)
│
└── app/
    ├── api/
    │   ├── api.py            # Main API router
    │   └── endpoints/
    │       ├── auth.py       # Login, refresh, me
    │       ├── projects.py   # Projects endpoints (dummy data)
    │       └── reports.py    # Dashboard KPIs (dummy data)
    │
    ├── core/
    │   ├── config.py         # Settings (from .env)
    │   ├── security.py       # JWT + password hashing
    │   └── deps.py           # Authentication dependency
    │
    ├── db/
    │   ├── session.py        # Database connection
    │   └── init_db.py        # Create tables + seed data
    │
    ├── models/
    │   └── user.py           # User SQLAlchemy model
    │
    └── schemas/
        └── user.py           # Pydantic validation schemas
```

## 🔄 Hoe het Werkt

### 1. Login Flow

```
Client                    Backend                   Database
  |                          |                          |
  |-- POST /auth/login ----->|                          |
  |    (email, password)     |                          |
  |                          |-- Find user by email --->|
  |                          |<---- User data ----------|
  |                          |                          |
  |                          |-- Verify password        |
  |                          |                          |
  |                          |-- Create JWT tokens      |
  |                          |                          |
  |<-- Return tokens --------|                          |
  |    + user object         |                          |
```

### 2. Protected Endpoint

```
Client                    Backend                   Database
  |                          |                          |
  |-- GET /projects -------->|                          |
  |   Header:                |                          |
  |   Authorization: Bearer  |                          |
  |   eyJhbGci...            |                          |
  |                          |-- Decode JWT token       |
  |                          |                          |
  |                          |-- Verify signature       |
  |                          |                          |
  |                          |-- Extract user_id        |
  |                          |                          |
  |                          |-- Get user from DB ----->|
  |                          |<---- User data ----------|
  |                          |                          |
  |                          |-- Return projects        |
  |<-- Response -------------|                          |
```

### 3. JWT Token

Tokens bevatten:
```json
{
  "sub": "usr_12345678",    // User ID
  "type": "access",         // access of refresh
  "exp": 1702850400         // Expiration timestamp
}
```

Tokens zijn **signed** met SECRET_KEY → kan niet worden vervalst!

## 🛠️ Development

### Database Resetten

```bash
# Verwijder database
rm vastgoed.db

# Start server opnieuw - database wordt opnieuw aangemaakt
python main.py
```

### Nieuwe Endpoint Toevoegen

**1. Maak endpoint file:**
```python
# app/api/endpoints/contracts.py
from fastapi import APIRouter, Depends
from app.core.deps import get_current_user

router = APIRouter(tags=["Contracts"])

@router.get("/contracts")
def list_contracts(current_user = Depends(get_current_user)):
    return {"success": True, "data": []}
```

**2. Voeg toe aan main router:**
```python
# app/api/api.py
from app.api.endpoints import contracts

api_router.include_router(contracts.router, tags=["contracts"])
```

**3. Klaar!** Endpoint is nu beschikbaar op `/api/v1/contracts`

### Database Model Toevoegen

```python
# app/models/project.py
from sqlalchemy import Column, String, Integer, ForeignKey
from app.db.session import Base

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(String, primary_key=True)
    naam = Column(String, nullable=False)
    project_nummer = Column(String, unique=True)
    vestiging_id = Column(Integer, ForeignKey("vestigingen.id"))
    # ... meer velden
```

Don't forget to import in `init_db.py`!

### Pydantic Schema Toevoegen

```python
# app/schemas/project.py
from pydantic import BaseModel
from typing import Optional

class ProjectCreate(BaseModel):
    naam: str
    project_nummer: str
    vestiging_id: int
    budget: float

class ProjectResponse(BaseModel):
    id: str
    naam: str
    project_nummer: str
    
    class Config:
        from_attributes = True  # Was orm_mode in Pydantic v1
```

## 🚀 Van Dummy Data naar Echte Database

Op dit moment gebruiken de endpoints **dummy data**. Hier is hoe je echte database queries toevoegt:

### Voorbeeld: Projects Endpoint

**Nu (dummy):**
```python
@router.get("/projects")
def list_projects():
    return {"success": True, "data": [{"id": "prj_001", "naam": "Test"}]}
```

**Straks (database):**
```python
from app.models.project import Project

@router.get("/projects")
def list_projects(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # Query database
    projects = db.query(Project).filter(
        Project.projectleider_id == current_user.id
    ).limit(25).all()
    
    return {
        "success": True,
        "data": [ProjectResponse.model_validate(p) for p in projects]
    }
```

## 📊 Database Opties

### SQLite (Default - Makkelijk)

Al geconfigureerd! Geen setup nodig.
- ✅ Geen installatie nodig
- ✅ Perfect voor development
- ⚠️  Niet voor production met veel users

### PostgreSQL (Production)

**Stap 1: Installeer PostgreSQL**
```bash
# Mac (met Homebrew)
brew install postgresql

# Ubuntu/Debian
sudo apt-get install postgresql

# Windows
# Download installer van postgresql.org
```

**Stap 2: Maak database**
```bash
createdb vastgoed
```

**Stap 3: Update .env**
```
DATABASE_URL=postgresql://username:password@localhost/vastgoed
```

**Stap 4: Restart server**
```bash
python main.py
```

Done! SQLAlchemy maakt automatisch de tabellen.

## 🔒 Security Tips

### Development
- ✅ SECRET_KEY is random
- ✅ Passwords zijn gehashed (bcrypt)
- ✅ JWT tokens expiren
- ✅ CORS is ingesteld

### Production
- [ ] Gebruik sterke SECRET_KEY (genereer nieuwe!)
- [ ] Gebruik HTTPS (niet HTTP)
- [ ] Gebruik PostgreSQL (niet SQLite)
- [ ] Beperk ALLOWED_ORIGINS tot je frontend domain
- [ ] Enable rate limiting (bijv. slowapi)
- [ ] Monitor logs

## 📚 FastAPI Concepten

### Dependency Injection

FastAPI gebruikt **Depends()** voor herbruikbare logic:

```python
# Zonder dependency
@router.get("/projects")
def list_projects():
    db = SessionLocal()  # Handmatig database
    user = decode_token()  # Handmatig auth
    # ... logic

# Met dependency
@router.get("/projects")
def list_projects(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # db en user zijn automatisch!
```

### Path Parameters

```python
@router.get("/projects/{project_id}")
def get_project(project_id: str):
    # project_id komt uit URL
    pass
```

### Query Parameters

```python
@router.get("/projects")
def list_projects(page: int = 1, limit: int = 25):
    # page en limit komen uit ?page=1&limit=25
    pass
```

### Request Body

```python
class ProjectCreate(BaseModel):
    naam: str
    budget: float

@router.post("/projects")
def create_project(project: ProjectCreate):
    # project is automatisch gevalideerd!
    print(project.naam)
```

## 🧪 Testing

```bash
# Installeer test dependencies (al in requirements.txt)
pip install pytest httpx

# Run tests
pytest
```

**Voorbeeld test:**
```python
# tests/test_auth.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_login():
    response = client.post("/api/v1/auth/login", json={
        "email": "test.projectleider@vastgoed.nl",
        "password": "Test1234!"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
```

## 🔗 Connect met Vue Frontend

**Frontend moet wijzen naar:**
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

**Backend heeft CORS ingesteld voor:**
```
http://localhost:3000
http://localhost:5173
```

Als je Vue app op een andere poort draait, voeg die toe in `.env`:
```
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:5174
```

## 📖 Documentatie Links

- **FastAPI:** https://fastapi.tiangolo.com/
- **SQLAlchemy:** https://docs.sqlalchemy.org/
- **Pydantic:** https://docs.pydantic.dev/
- **JWT:** https://jwt.io/

## ❓ Veelgestelde Vragen

**Q: Ik krijg "ModuleNotFoundError"**
A: Activeer je virtual environment: `source venv/bin/activate` (Mac/Linux) of `venv\Scripts\activate` (Windows)

**Q: Ik krijg "Address already in use"**
A: Poort 8000 is al in gebruik. Stop andere processen of gebruik een andere poort: `uvicorn main:app --port 8001`

**Q: Database errors na code wijzigingen**
A: Reset de database: `rm vastgoed.db` en restart

**Q: Hoe test ik met Postman/Insomnia?**
A:
1. POST naar `http://localhost:8000/api/v1/auth/login`
2. Copy `access_token` uit response
3. Voor protected routes: Header `Authorization: Bearer YOUR_TOKEN`

**Q: Hoe deploy ik naar production?**
A: Zie deployment guides voor:
- **Heroku:** https://fastapi.tiangolo.com/deployment/heroku/
- **AWS:** https://fastapi.tiangolo.com/deployment/aws/
- **Docker:** https://fastapi.tiangolo.com/deployment/docker/

## 🎉 Je bent klaar!

Je hebt nu een **werkende backend API** met:
- ✅ Authentication (JWT)
- ✅ Database (SQLite)
- ✅ Auto-documentation (Swagger)
- ✅ Test users
- ✅ CORS configured
- ✅ Type-safe code

**Next steps:**
1. Test de API met Swagger UI
2. Connect je Vue frontend
3. Bouw echte database models voor Projects, Contracts, etc.
4. Vervang dummy data met database queries

Happy coding! 🚀
