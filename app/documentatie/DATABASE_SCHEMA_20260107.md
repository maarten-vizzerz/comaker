# Comaker - Database Schema Documentatie

> **BELANGRIJKSTE DOCUMENT** - Gebruik dit als referentie bij ELKE database aanpassing!
> 
> **Laatste update:** 8 januari 2025
> **Database:** SQLite (development) / PostgreSQL (production)

---

## 📋 Inhoudsopgave

1. [Naamgevingsconventies](#naamgevingsconventies)
2. [Database Modellen](#database-modellen)
3. [Relaties tussen Tabellen](#relaties-tussen-tabellen)
4. [Enum Types](#enum-types)
5. [Versiebeheer (Historie)](#versiebeheer-historie)
6. [Seed Data Structuur](#seed-data-structuur)

---

## 🎯 Naamgevingsconventies

### **Belangrijkste Regels:**

```python
# ✅ CORRECT
project_nummer      # underscore tussen woorden
projectleider_id    # compound woorden aan elkaar, dan _id
created_at         # timestamps altijd _at
leverancier_id     # Nederlandse woorden, geen vertaling

# ❌ FOUT
projectNummer      # geen camelCase
project_leider_id  # geen spatie tussen compound woorden  
createdAt          # gebruik Nederlandse conventies
supplier_id        # gebruik Nederlandse termen
```

### **Standaard Velden:**

Elk model met versiebeheer heeft:
```python
id = Column(String, primary_key=True)           # Format: "prj_a1b2c3d4"
created_at = Column(DateTime(timezone=True))    # Automatisch bij create
updated_at = Column(DateTime(timezone=True))    # Automatisch bij update
versie_nummer = Column(Integer, default=1)      # Voor historie tracking
```

### **ID Formaten:**

```python
"usr_" + 8 hex chars  # Users:        usr_a1b2c3d4
"prj_" + 8 hex chars  # Projects:     prj_x9y8z7w6
"con_" + 8 hex chars  # Contracts:    con_m5n4o3p2
"lev_" + 8 hex chars  # Leveranciers: lev_q7r6s5t4
uuid.uuid4()          # Andere:       full UUID
```

---

## 📊 Database Modellen

### **1. Users** (`users`)

```python
# app/models/user.py

__tablename__ = "users"

# Primary Key
id: String                          # Format: usr_12345678

# Basic Info
email: String                       # Unique, indexed
hashed_password: String             # Bcrypt hash
name: String
role: UserRole (Enum)               # Zie Enum Types
is_active: Boolean = True
avatar: String | None               # Avatar URL/path

# Leverancier Link
leverancier_id: String | None       # FK → leveranciers.id
                                    # Alleen gevuld als role=LEVERANCIER

# Timestamps & Versioning
versie_nummer: Integer = 1
created_at: DateTime
updated_at: DateTime | None

# Relationships
leverancier: Leverancier            # back_populates="users"
```

**Belangrijke Notes:**
- Email is unique constraint
- `leverancier_id` is alleen gevuld voor users met `role=LEVERANCIER`
- Interne medewerkers hebben `leverancier_id=None`

---

### **2. Leveranciers** (`leveranciers`)

```python
# app/models/leverancier.py

__tablename__ = "leveranciers"

# Primary Key
id: String                          # Format: lev_12345678

# Basis Info
naam: String                        # Bedrijfsnaam
kvk_nummer: String | None           # KVK nummer (optioneel maar meestal aanwezig)
btw_nummer: String | None           # BTW nummer
type: LeverancierType (Enum)        # BOUW, INSTALLATIE, etc.
status: LeverancierStatus (Enum)    # ACTIEF, INACTIEF, etc.

# Contact Info
contactpersoon: String | None       # Naam contactpersoon
email: String | None
telefoon: String | None
mobiel: String | None
website: String | None

# Adres (aparte velden, GEEN embedded object!)
adres_straat: String | None
adres_huisnummer: String | None
adres_postcode: String | None
adres_plaats: String | None
adres_land: String = "Nederland"

# Bank Info
iban: String | None
bank_naam: String | None

# Metadata
rating: Float | None                # 0.0 - 5.0
notities: Text | None
is_actief: Boolean = True

# Timestamps & Versioning
versie_nummer: Integer = 1
created_at: DateTime
updated_at: DateTime | None

# Relationships
users: List[User]                   # back_populates="leverancier"
contracts: List[Contract]           # back_populates="leverancier"
projectfases: List[ProjectFase]     # back_populates="leverancier"

# Computed Property
@property
def volledig_adres() -> str:
    # Combinatie van adres velden
```

**Belangrijke Notes:**
- Adres is GEEN nested object - gebruik individuele velden
- `volledig_adres` is een computed property, geen database veld
- `rating` is optioneel en kan None zijn

---

### **3. Projects** (`projects`)

```python
# app/models/project.py

__tablename__ = "projects"

# Primary Key
id: String                          # Format: prj_12345678

# Basis Info
project_nummer: String              # Unique, bijvoorbeeld "PRJ-001"
naam: String
beschrijving: Text | None
status: ProjectStatus (Enum)        # CONCEPT, IN_UITVOERING, etc.

# Financieel
budget_totaal: Numeric(15, 2)       # Total budget in euro's
budget_besteed: Numeric(15, 2) = 0  # Besteed bedrag

# Planning
start_datum: Date | None
eind_datum: Date | None

# Verantwoordelijken
projectleider_id: String            # FK → users.id (role=PROJECTLEIDER)

# Timestamps & Versioning
versie_nummer: Integer = 1
created_at: DateTime
updated_at: DateTime | None

# Relationships
projectleider: User                 # Foreign key user
contracts: List[Contract]           # back_populates="project"
projectfases: List[ProjectFase]     # back_populates="project"

# Computed Properties
@property
def budget_percentage() -> float:
    # Berekent (besteed / totaal) * 100
```

**Belangrijke Notes:**
- `project_nummer` heeft unique constraint
- `budget_totaal` en `budget_besteed` zijn Numeric (geen Float!)
- `budget_percentage` is computed, niet opgeslagen

---

### **4. Contracts** (`contracts`)

```python
# app/models/contract.py

__tablename__ = "contracts"

# Primary Key
id: String                          # Format: con_12345678

# Basis Info
contract_nummer: String             # Unique, bijvoorbeeld "CON-2025-001"
naam: String
beschrijving: Text | None
type: ContractType (Enum)           # AANNEMING, DIENSTVERLENING, etc.
status: ContractStatus (Enum)       # CONCEPT, GETEKEND, etc.

# Financieel
contract_bedrag: Numeric(15, 2)     # Contract waarde
gefactureerd_bedrag: Numeric(15, 2) = 0  # Al gefactureerd

# Planning
start_datum: Date | None
eind_datum: Date | None
getekend_datum: Date | None         # Wanneer getekend

# Foreign Keys
project_id: String                  # FK → projects.id
leverancier_id: String              # FK → leveranciers.id

# Metadata
is_actief: Boolean = True
bijlagen: Text | None               # JSON of comma-separated paths

# Timestamps & Versioning
versie_nummer: Integer = 1
created_at: DateTime
updated_at: DateTime | None

# Relationships
project: Project                    # back_populates="contracts"
leverancier: Leverancier           # back_populates="contracts"

# Computed Properties
@property
def restant_bedrag() -> Decimal:
    # contract_bedrag - gefactureerd_bedrag

@property
def gefactureerd_percentage() -> float:
    # (gefactureerd / contract) * 100
```

**Belangrijke Notes:**
- `contract_nummer` heeft unique constraint
- Alle bedragen zijn Numeric(15, 2)
- `restant_bedrag` en `gefactureerd_percentage` zijn computed

---

### **5. ProjectFases** (`projectfases`)

```python
# app/models/projectfase.py

__tablename__ = "projectfases"

# Primary Key
id: String                          # Full UUID (geen prefix!)

# Basis Info
fase_nummer: Integer                # 1, 2, 3, etc.
naam: String                        # "Sloop", "Bouw", etc.
beschrijving: Text | None
status: ProjectFaseStatus (Enum)    # NIET_GESTART, IN_UITVOERING, etc.

# Planning
geplande_start_datum: Date | None
geplande_eind_datum: Date | None
werkelijke_start_datum: Date | None
werkelijke_eind_datum: Date | None

# Foreign Keys
project_id: String                  # FK → projects.id
verantwoordelijke_id: String        # FK → users.id
leverancier_id: String | None       # FK → leveranciers.id (kan None zijn)

# Timestamps & Versioning
versie_nummer: Integer = 1
created_at: DateTime
updated_at: DateTime | None

# Relationships
project: Project                    # back_populates="projectfases"
verantwoordelijke: User             # User die verantwoordelijk is
leverancier: Leverancier | None     # Gekoppelde leverancier
documenten: List[ProjectFaseDocument]      # back_populates="fase"
commentaren: List[ProjectFaseCommentaar]   # back_populates="fase"
```

**Belangrijke Notes:**
- ID is VOLLEDIG UUID (geen "pf_" prefix!)
- `leverancier_id` kan None zijn (interne fase zonder leverancier)
- Leveranciers zien ALLEEN fases waar `leverancier_id = hun_leverancier_id`

---

### **6. ProjectFaseDocument** (`projectfase_documenten`)

```python
# app/models/projectfase.py

__tablename__ = "projectfase_documenten"

# Primary Key
id: String                          # Full UUID

# Document Info
naam: String                        # Display naam
beschrijving: Text | None
type: DocumentType (Enum)           # OFFERTE, TEKENING, etc.

# Bestand Info
bestandsnaam: String                # Originele filename
bestandstype: String                # pdf, docx, dwg, etc.
bestandsgrootte: Integer            # In bytes

# Opslag
opslag_type: String = "local"       # local, s3, etc.
opslag_pad: String                  # Path of S3 key

# Versie & Status
versie: String = "1.0"              # Versie nummer van document
is_definitief: Boolean = False      # Is dit de definitieve versie?

# Toegang & Rechten
zichtbaar_voor_leverancier: Boolean = True  # BELANGRIJK voor leverancier toegang!
geupload_door_id: String            # FK → users.id

# Foreign Key
fase_id: String                     # FK → projectfases.id

# Timestamps
created_at: DateTime
updated_at: DateTime | None

# Relationships
fase: ProjectFase                   # back_populates="documenten"
geupload_door: User
```

**Belangrijke Notes:**
- `zichtbaar_voor_leverancier` bepaalt of leverancier document kan zien
- Interne documenten hebben `zichtbaar_voor_leverancier=False`
- `bestandsgrootte` in bytes
- `versie` is STRING, niet Integer!

---

### **7. ProjectFaseCommentaar** (`projectfase_commentaren`)

```python
# app/models/projectfase.py

__tablename__ = "projectfase_commentaren"

# Primary Key
id: String                          # Full UUID

# Commentaar Info
type: CommentaarType (Enum)         # MEDEWERKER, COMAKER
status: CommentaarStatus (Enum)     # CONCEPT, GEPUBLICEERD
onderwerp: String | None            # Optioneel onderwerp
bericht: Text                       # Daadwerkelijke commentaar

# Foreign Keys
fase_id: String                     # FK → projectfases.id
auteur_id: String                   # FK → users.id
leverancier_id: String | None       # FK → leveranciers.id (als type=COMAKER)

# Timestamps
gepubliceerd_op: DateTime | None    # Wanneer gepubliceerd
created_at: DateTime
updated_at: DateTime | None

# Relationships
fase: ProjectFase                   # back_populates="commentaren"
auteur: User
leverancier: Leverancier | None     # Alleen als type=COMAKER
```

**Belangrijke Notes:**
- Type MEDEWERKER: interne communicatie (leverancier ziet niet)
- Type COMAKER: zichtbaar voor leverancier
- `leverancier_id` alleen gevuld bij COMAKER type
- `gepubliceerd_op` bepaalt wanneer zichtbaar

---

### **8. HistorieRecord** (`historie_records`)

```python
# app/models/historie.py

__tablename__ = "historie_records"

# Primary Key
id: String                          # Full UUID

# Tracking Info
tabel_naam: String                  # Naam van de tabel (bijv. "projects")
record_id: String                   # ID van het record
versie_nummer: Integer              # Versie nummer

# Actie Info
actie: String                       # "create", "update", "delete"
gewijzigd_door_id: String | None    # FK → users.id
gewijzigd_op: DateTime              # Timestamp van wijziging

# Data Snapshots (JSON)
data_voor: Text | None              # JSON van oude data (bij update/delete)
data_na: Text | None                # JSON van nieuwe data (bij create/update)

# Metadata
opmerking: String | None            # Optionele opmerking bij wijziging

# Relationships
gewijzigd_door: User | None
```

**Belangrijke Notes:**
- Automatisch gevuld via SQLAlchemy events
- `data_voor` en `data_na` zijn JSON strings
- Gebruikt voor audit trail en rollback functionaliteit

---

## 🔗 Relaties tussen Tabellen

### **User Relations:**

```python
User
├── leverancier (Many-to-One → Leverancier)
│   # user.leverancier_id → leveranciers.id
│   # Alleen voor role=LEVERANCIER
│
├── projecten_als_leider (One-to-Many → Project)
│   # projects.projectleider_id → users.id
│
├── fase_verantwoordelijkheden (One-to-Many → ProjectFase)
│   # projectfases.verantwoordelijke_id → users.id
│
├── geupload_documenten (One-to-Many → ProjectFaseDocument)
│   # projectfase_documenten.geupload_door_id → users.id
│
└── commentaren (One-to-Many → ProjectFaseCommentaar)
    # projectfase_commentaren.auteur_id → users.id
```

### **Leverancier Relations:**

```python
Leverancier
├── users (One-to-Many → User)
│   # users.leverancier_id → leveranciers.id
│
├── contracts (One-to-Many → Contract)
│   # contracts.leverancier_id → leveranciers.id
│
├── projectfases (One-to-Many → ProjectFase)
│   # projectfases.leverancier_id → leveranciers.id
│
└── commentaren (One-to-Many → ProjectFaseCommentaar)
    # projectfase_commentaren.leverancier_id → leveranciers.id
```

### **Project Relations:**

```python
Project
├── projectleider (Many-to-One → User)
│   # projects.projectleider_id → users.id
│
├── contracts (One-to-Many → Contract)
│   # contracts.project_id → projects.id
│
└── projectfases (One-to-Many → ProjectFase)
    # projectfases.project_id → projects.id
```

### **ProjectFase Relations:**

```python
ProjectFase
├── project (Many-to-One → Project)
│   # projectfases.project_id → projects.id
│
├── verantwoordelijke (Many-to-One → User)
│   # projectfases.verantwoordelijke_id → users.id
│
├── leverancier (Many-to-One → Leverancier) [OPTIONAL]
│   # projectfases.leverancier_id → leveranciers.id
│
├── documenten (One-to-Many → ProjectFaseDocument)
│   # projectfase_documenten.fase_id → projectfases.id
│
└── commentaren (One-to-Many → ProjectFaseCommentaar)
    # projectfase_commentaren.fase_id → projectfases.id
```

---

## 🎭 Enum Types

### **UserRole**

```python
class UserRole(str, enum.Enum):
    BEHEERDER = "beheerder"                      # Full access
    PROJECTLEIDER = "projectleider"              # Project management
    CONTROLEUR = "controleur"                    # Quality control
    ADMINISTRATIEF_MEDEWERKER = "administratief_medewerker"  # Admin tasks
    LEVERANCIER = "leverancier"                  # Supplier (external)
    READ_ONLY = "read_only"                      # View only
```

### **LeverancierType**

```python
class LeverancierType(str, enum.Enum):
    BOUW = "bouw"                                # Construction
    INSTALLATIE = "installatie"                  # Installation
    SCHILDERWERK = "schilderwerk"               # Painting
    ELEKTRA = "elektra"                          # Electrical
    LOODGIETER = "loodgieter"                    # Plumbing
    ANDERS = "anders"                            # Other
```

### **LeverancierStatus**

```python
class LeverancierStatus(str, enum.Enum):
    ACTIEF = "actief"                            # Active
    INACTIEF = "inactief"                        # Inactive
    GEBLOKKEERD = "geblokkeerd"                  # Blocked
```

### **ProjectStatus**

```python
class ProjectStatus(str, enum.Enum):
    CONCEPT = "concept"                          # Draft
    GOEDGEKEURD = "goedgekeurd"                 # Approved
    IN_UITVOERING = "in_uitvoering"             # In progress
    AFGEROND = "afgerond"                        # Completed
    GEANNULEERD = "geannuleerd"                 # Cancelled
```

### **ContractStatus**

```python
class ContractStatus(str, enum.Enum):
    CONCEPT = "concept"                          # Draft
    VERZONDEN = "verzonden"                      # Sent
    GETEKEND = "getekend"                        # Signed
    ACTIEF = "actief"                            # Active
    AFGEROND = "afgerond"                        # Completed
    GEANNULEERD = "geannuleerd"                 # Cancelled
```

### **ContractType**

```python
class ContractType(str, enum.Enum):
    AANNEMING = "aanneming"                      # General contracting
    DIENSTVERLENING = "dienstverlening"         # Services
    LEVERING = "levering"                        # Supply
    ONDERHOUD = "onderhoud"                      # Maintenance
    ANDERS = "anders"                            # Other
```

### **ProjectFaseStatus**

```python
class ProjectFaseStatus(str, enum.Enum):
    NIET_GESTART = "niet_gestart"               # Not started
    IN_VOORBEREIDING = "in_voorbereiding"       # In preparation
    IN_UITVOERING = "in_uitvoering"             # In progress
    OPGESCHORT = "opgeschort"                    # Suspended
    AFGEROND = "afgerond"                        # Completed
    GEANNULEERD = "geannuleerd"                 # Cancelled
```

### **DocumentType**

```python
class DocumentType(str, enum.Enum):
    OFFERTE = "offerte"                          # Quote
    CONTRACT = "contract"                        # Contract
    FACTUUR = "factuur"                          # Invoice
    TEKENING = "tekening"                        # Drawing
    FOTO = "foto"                                # Photo
    RAPPORT = "rapport"                          # Report
    ANDERS = "anders"                            # Other
```

### **CommentaarType**

```python
class CommentaarType(str, enum.Enum):
    MEDEWERKER = "medewerker"                   # Internal only
    COMAKER = "comaker"                          # Visible to supplier
```

### **CommentaarStatus**

```python
class CommentaarStatus(str, enum.Enum):
    CONCEPT = "concept"                          # Draft
    GEPUBLICEERD = "gepubliceerd"               # Published
```

---

## 🕐 Versiebeheer (Historie)

### **Hoe het werkt:**

1. **Automatisch tracking** via SQLAlchemy events
2. Elk model met `versie_nummer` krijgt historie
3. Bij elke wijziging wordt `HistorieRecord` aangemaakt

### **Models met versiebeheer:**

- ✅ User
- ✅ Leverancier
- ✅ Project
- ✅ Contract
- ✅ ProjectFase
- ❌ ProjectFaseDocument (geen versiebeheer)
- ❌ ProjectFaseCommentaar (geen versiebeheer)

### **HistorieContext gebruiken:**

```python
from app.models.historie_setup import HistorieContext

# SET context VOOR update
HistorieContext.set_user_id(current_user.id)
HistorieContext.set_opmerking("Project budget verhoogd")

# Do update
project.budget_totaal = 500000
db.commit()

# CLEAR context NA commit
HistorieContext.clear()
```

### **Historie disablen (bijv. bij seeding):**

```python
from app.models.historie_setup import disable_historie_tracking, enable_historie_tracking

disable_historie_tracking(db)
# ... bulk inserts ...
enable_historie_tracking(db)
```

---

## 🌱 Seed Data Structuur

### **Test Users (6 stuks):**

```python
# Interne users (leverancier_id = None)
projectleider@comaker.cloud     # Role: PROJECTLEIDER
beheerder@comaker.cloud         # Role: BEHEERDER
controleur@comaker.cloud        # Role: CONTROLEUR
admin@comaker.cloud             # Role: ADMINISTRATIEF_MEDEWERKER

# Leverancier users (leverancier_id = gekoppeld)
jan@debouwer.nl                 # Role: LEVERANCIER, leverancier_id = bouwbedrijf
maria@installatietech.nl        # Role: LEVERANCIER, leverancier_id = installatietech

# ALL passwords: Test1234!
```

### **Leveranciers (2 stuks):**

```python
# Bouwbedrijf de Bouwer BV
{
    "id": "lev_xxxxxxxx",
    "naam": "Bouwbedrijf de Bouwer BV",
    "type": LeverancierType.BOUW,
    "kvk_nummer": "12345678",
    "email": "info@debouwer.nl"
}

# InstallatieTech Solutions
{
    "id": "lev_yyyyyyyy",
    "naam": "InstallatieTech Solutions",
    "type": LeverancierType.INSTALLATIE,
    "kvk_nummer": "87654321",
    "email": "contact@installatietech.nl"
}
```

### **Project (1 stuks):**

```python
{
    "id": "prj_zzzzzzzz",
    "project_nummer": "PRJ-001",
    "naam": "Renovatie Kantoorpand Centrum",
    "status": ProjectStatus.IN_UITVOERING,
    "projectleider_id": user_projectleider.id,
    "budget_totaal": 250000.00
}
```

### **Contract (1 stuks):**

```python
{
    "id": "con_aaaaaaaa",
    "contract_nummer": "CON-2025-001",
    "naam": "Bouwcontract Renovatie",
    "type": ContractType.AANNEMING,
    "status": ContractStatus.GETEKEND,
    "project_id": project.id,
    "leverancier_id": leverancier_bouwbedrijf.id,
    "contract_bedrag": 180000.00
}
```

### **ProjectFases (5 stuks):**

```python
1. Sloop (AFGEROND) → leverancier: bouwbedrijf
2. Bouw (IN_UITVOERING) → leverancier: bouwbedrijf
3. Dakwerk (IN_UITVOERING) → leverancier: bouwbedrijf
4. Installatie (IN_VOORBEREIDING) → leverancier: installatietech
5. Afwerking (NIET_GESTART) → leverancier: bouwbedrijf
```

### **Access Matrix:**

```
User                          | Ziet fases
-----------------------------|------------------
projectleider@comaker.cloud  | Alle 5 fases
beheerder@comaker.cloud      | Alle 5 fases
controleur@comaker.cloud     | Alle 5 fases
admin@comaker.cloud          | Alle 5 fases
jan@debouwer.nl             | Fases 1, 2, 3, 5 (bouwbedrijf)
maria@installatietech.nl    | Fase 4 (installatietech)
```

---

## ✅ Checklist voor Database Wijzigingen

Wanneer je database aanpassingen maakt:

- [ ] Gebruik EXACTE veldnamen uit dit document
- [ ] Check of relaties correct zijn (FK namen kloppen)
- [ ] Gebruik juiste ID formaten (prj_, usr_, lev_, etc.)
- [ ] Timestamps: `created_at` en `updated_at` (niet createdAt!)
- [ ] Enums: gebruik waarden zoals in dit document
- [ ] Computed properties NIET in database opslaan
- [ ] Versiebeheer: voeg `versie_nummer` toe als nodig
- [ ] Test met seed data uit `init_db.py`

---

## 🚨 Veel Voorkomende Fouten

### **❌ FOUT:**
```python
# Verkeerde veldnamen
project.project_leider_id      # Spatie in compound woord
project.projectNummer          # CamelCase
contract.supplier_id           # Engels ipv Nederlands
user.createdAt                # CamelCase timestamp

# Verkeerde enum waarden
status = "active"              # Moet "actief" zijn
type = "construction"          # Moet "bouw" zijn

# ID formaten
id = str(uuid.uuid4())         # Voor users moet prj_ prefix!
```

### **✅ CORRECT:**
```python
# Juiste veldnamen
project.projectleider_id       # Compound aan elkaar
project.project_nummer         # Underscore tussen woorden
contract.leverancier_id        # Nederlands
user.created_at               # Underscore timestamp

# Juiste enum waarden
status = LeverancierStatus.ACTIEF
type = LeverancierType.BOUW

# Juiste ID formaten
id = f"prj_{uuid.uuid4().hex[:8]}"  # Voor projects
id = str(uuid.uuid4())               # Voor fases/documenten
```

---

## 📝 Samenvatting Belangrijkste Punten

1. **Veldnamen:** Altijd underscore, Nederlandse termen
2. **IDs:** Prefix voor hoofdmodellen (prj_, usr_, etc.), UUID voor rest
3. **Enums:** Gebruik Nederlandse waarden zoals in dit document
4. **Relaties:** Check FK namen exact (projectleider_id, niet project_leider_id)
5. **Timestamps:** Altijd `created_at` en `updated_at`
6. **Computed:** Properties zoals `budget_percentage` NIET in DB
7. **Versiebeheer:** Modellen met `versie_nummer` krijgen historie
8. **Leverancier toegang:** Fase moet `leverancier_id` matchen met user's `leverancier_id`

---

**Dit document is de single source of truth voor de database structuur.**

Bij twijfel: kijk hier EERST voordat je code schrijft! 🎯
