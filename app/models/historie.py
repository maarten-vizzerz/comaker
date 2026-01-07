"""
HISTORIE & VERSIEBEHEER SYSTEEM
================================

Voor elke belangrijke tabel wordt een _historie tabel aangemaakt die:
- Alle wijzigingen bijhoudt
- Oude versies bewaart
- Wie, wat, wanneer tracked

AANPAK:
1. Basis HistorieMixin class
2. Historie models voor elke tabel
3. Automatische historie tracking via SQLAlchemy events
4. API endpoints om historie op te vragen

"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON, event
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func
from datetime import datetime, timezone
import json
from typing import Any, Dict

from app.db.session import Base


# ============================================================================
# BASE MIXIN VOOR HISTORIE
# ============================================================================

class HistorieMixin:
    """
    Mixin die historie tracking toevoegt aan een model
    
    Gebruik:
        class MyModel(Base, HistorieMixin):
            __tablename__ = "my_table"
            # ... rest of model
    """
    
    # Deze velden worden automatisch toegevoegd
    versie_nummer = Column(Integer, default=1, nullable=False)
    
    def increment_versie(self):
        """Verhoog versie nummer"""
        if self.versie_nummer is None:
            self.versie_nummer = 1
        else:
            self.versie_nummer += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model naar dictionary (voor historie opslag)"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            
            # Handle datetime
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            # Handle enums
            elif hasattr(value, 'value'):
                result[column.name] = value.value
            else:
                result[column.name] = value
        
        return result


# ============================================================================
# HISTORIE MODEL - GENERIEK
# ============================================================================

class HistorieRecord(Base):
    """
    Generieke historie tabel voor ALLE tabellen
    
    Dit is een centrale audit log waar alle wijzigingen worden opgeslagen.
    """
    __tablename__ = "historie_records"
    
    # Primary key
    id = Column(String, primary_key=True)
    
    # Welke tabel & record
    tabel_naam = Column(String, nullable=False, index=True)
    record_id = Column(String, nullable=False, index=True)
    
    # Versie info
    versie_nummer = Column(Integer, nullable=False)
    
    # Actie
    actie = Column(String, nullable=False)  # "create", "update", "delete"
    
    # Data snapshot (JSON)
    data_voor = Column(JSON, nullable=True)  # Oude waarden
    data_na = Column(JSON, nullable=True)    # Nieuwe waarden
    data_diff = Column(JSON, nullable=True)  # Alleen gewijzigde velden
    
    # Wie & wanneer
    gewijzigd_door_id = Column(String, ForeignKey('users.id'), nullable=True, index=True)
    gewijzigd_op = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Extra metadata
    ip_adres = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    opmerking = Column(Text, nullable=True)
    
    # Relationship
    gewijzigd_door = relationship("User", foreign_keys=[gewijzigd_door_id])
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<HistorieRecord {self.tabel_naam}:{self.record_id} v{self.versie_nummer}>"


# ============================================================================
# SPECIFIEKE HISTORIE TABELLEN (één per hoofdtabel)
# ============================================================================

class UserHistorie(Base):
    """Historie voor users tabel"""
    __tablename__ = "users_historie"
    
    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)
    versie_nummer = Column(Integer, nullable=False)
    
    # Snapshot van alle velden
    email = Column(String)
    name = Column(String)
    role = Column(String)
    is_active = Column(String)
    avatar = Column(String)
    
    # Meta
    gewijzigd_door_id = Column(String, ForeignKey('users.id'), nullable=True)
    gewijzigd_op = Column(DateTime(timezone=True), server_default=func.now())
    actie = Column(String)  # "create", "update", "delete"
    opmerking = Column(Text, nullable=True)
    
    # Geldigheid
    geldig_van = Column(DateTime(timezone=True), nullable=False)
    geldig_tot = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    gewijzigd_door = relationship("User", foreign_keys=[gewijzigd_door_id])


class ProjectHistorie(Base):
    """Historie voor projects tabel"""
    __tablename__ = "projects_historie"
    
    id = Column(String, primary_key=True)
    project_id = Column(String, ForeignKey('projects.id'), nullable=False, index=True)
    versie_nummer = Column(Integer, nullable=False)
    
    # Snapshot
    project_nummer = Column(String)
    naam = Column(String)
    beschrijving = Column(Text)
    status = Column(String)
    budget_totaal = Column(Integer)
    budget_besteed = Column(Integer)
    start_datum = Column(DateTime(timezone=True))
    eind_datum = Column(DateTime(timezone=True))
    projectleider_id = Column(String)
    
    # Meta
    gewijzigd_door_id = Column(String, ForeignKey('users.id'), nullable=True)
    gewijzigd_op = Column(DateTime(timezone=True), server_default=func.now())
    actie = Column(String)
    opmerking = Column(Text, nullable=True)
    
    geldig_van = Column(DateTime(timezone=True), nullable=False)
    geldig_tot = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    gewijzigd_door = relationship("User", foreign_keys=[gewijzigd_door_id])


class ContractHistorie(Base):
    """Historie voor contracts tabel"""
    __tablename__ = "contracts_historie"
    
    id = Column(String, primary_key=True)
    contract_id = Column(String, ForeignKey('contracts.id'), nullable=False, index=True)
    versie_nummer = Column(Integer, nullable=False)
    
    # Snapshot
    contract_nummer = Column(String)
    naam = Column(String)
    beschrijving = Column(Text)
    type = Column(String)
    status = Column(String)
    leverancier_id = Column(String)
    contract_bedrag = Column(String)  # JSON string voor Numeric
    gefactureerd_bedrag = Column(String)
    start_datum = Column(DateTime(timezone=True))
    eind_datum = Column(DateTime(timezone=True))
    getekend_datum = Column(DateTime(timezone=True))
    goedgekeurd_door_id = Column(String)
    goedkeurings_datum = Column(DateTime(timezone=True))
    opmerkingen = Column(Text)
    project_id = Column(String)
    verantwoordelijke_id = Column(String)
    
    # Meta
    gewijzigd_door_id = Column(String, ForeignKey('users.id'), nullable=True)
    gewijzigd_op = Column(DateTime(timezone=True), server_default=func.now())
    actie = Column(String)
    opmerking = Column(Text, nullable=True)
    
    geldig_van = Column(DateTime(timezone=True), nullable=False)
    geldig_tot = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    contract = relationship("Contract", foreign_keys=[contract_id])
    gewijzigd_door = relationship("User", foreign_keys=[gewijzigd_door_id])


class LeverancierHistorie(Base):
    """Historie voor leveranciers tabel"""
    __tablename__ = "leveranciers_historie"
    
    id = Column(String, primary_key=True)
    leverancier_id = Column(String, ForeignKey('leveranciers.id'), nullable=False, index=True)
    versie_nummer = Column(Integer, nullable=False)
    
    # Snapshot
    naam = Column(String)
    kvk_nummer = Column(String)
    btw_nummer = Column(String)
    type = Column(String)
    status = Column(String)
    contactpersoon = Column(String)
    email = Column(String)
    telefoon = Column(String)
    mobiel = Column(String)
    website = Column(String)
    adres_straat = Column(String)
    adres_huisnummer = Column(String)
    adres_postcode = Column(String)
    adres_plaats = Column(String)
    adres_land = Column(String)
    iban = Column(String)
    bank_naam = Column(String)
    notities = Column(Text)
    
    # Meta
    gewijzigd_door_id = Column(String, ForeignKey('users.id'), nullable=True)
    gewijzigd_op = Column(DateTime(timezone=True), server_default=func.now())
    actie = Column(String)
    opmerking = Column(Text, nullable=True)
    
    geldig_van = Column(DateTime(timezone=True), nullable=False)
    geldig_tot = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    leverancier = relationship("Leverancier", foreign_keys=[leverancier_id])
    gewijzigd_door = relationship("User", foreign_keys=[gewijzigd_door_id])


class ProjectFaseHistorie(Base):
    """Historie voor project_fases tabel"""
    __tablename__ = "project_fases_historie"
    
    id = Column(String, primary_key=True)
    fase_id = Column(String, ForeignKey('project_fases.id'), nullable=False, index=True)
    versie_nummer = Column(Integer, nullable=False)
    
    # Snapshot
    project_id = Column(String)
    fase_nummer = Column(Integer)
    naam = Column(String)
    beschrijving = Column(Text)
    status = Column(String)
    verantwoordelijke_id = Column(String)
    leverancier_id = Column(String)
    geplande_start_datum = Column(DateTime(timezone=True))
    geplande_eind_datum = Column(DateTime(timezone=True))
    werkelijke_start_datum = Column(DateTime(timezone=True))
    werkelijke_eind_datum = Column(DateTime(timezone=True))
    
    # Meta
    gewijzigd_door_id = Column(String, ForeignKey('users.id'), nullable=True)
    gewijzigd_op = Column(DateTime(timezone=True), server_default=func.now())
    actie = Column(String)
    opmerking = Column(Text, nullable=True)
    
    geldig_van = Column(DateTime(timezone=True), nullable=False)
    geldig_tot = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    fase = relationship("ProjectFase", foreign_keys=[fase_id])
    gewijzigd_door = relationship("User", foreign_keys=[gewijzigd_door_id])


# ============================================================================
# AUTOMATISCHE HISTORIE TRACKING (SQLAlchemy Events)
# ============================================================================

def create_historie_record(mapper, connection, target, actie: str, user_id: str = None):
    """
    Maak een historie record aan voor een wijziging
    
    Args:
        mapper: SQLAlchemy mapper
        connection: Database connection
        target: Het object dat gewijzigd wordt
        actie: "create", "update", of "delete"
        user_id: ID van de gebruiker die de wijziging doet
    """
    import uuid
    
    tabel_naam = target.__tablename__
    record_id = target.id
    
    # Get versie nummer
    versie = getattr(target, 'versie_nummer', 1)
    
    # Convert object to dict
    data = {}
    if hasattr(target, 'to_dict'):
        data = target.to_dict()
    else:
        for column in target.__table__.columns:
            value = getattr(target, column.name)
            if isinstance(value, datetime):
                data[column.name] = value.isoformat()
            elif hasattr(value, 'value'):
                data[column.name] = value.value
            else:
                data[column.name] = value
    
    # Bepaal data_voor en data_na
    data_voor = None
    data_na = data
    
    if actie == "update":
        # Voor update: we hebben oude data nodig (complex, vereist extra tracking)
        # Voor nu: alleen nieuwe data opslaan
        pass
    elif actie == "delete":
        data_voor = data
        data_na = None
    
    # Insert historie record
    historie_table = HistorieRecord.__table__
    connection.execute(
        historie_table.insert().values(
            id=str(uuid.uuid4()),
            tabel_naam=tabel_naam,
            record_id=record_id,
            versie_nummer=versie,
            actie=actie,
            data_voor=json.dumps(data_voor) if data_voor else None,
            data_na=json.dumps(data_na) if data_na else None,
            gewijzigd_door_id=user_id,
            gewijzigd_op=datetime.now(timezone.utc)
        )
    )


# Event listeners - DEZE MOET JE REGISTREREN IN JE APPLICATIE!
"""
Voorbeeld van hoe je deze registreert in je main.py of app startup:

from sqlalchemy import event
from app.models.project import Project
from app.models.contract import Contract
from app.models.leverancier import Leverancier
from app.models.user import User
from app.models.projectfase import ProjectFase

# Register event listeners
@event.listens_for(Project, 'after_insert')
def project_after_insert(mapper, connection, target):
    create_historie_record(mapper, connection, target, "create")

@event.listens_for(Project, 'after_update')
def project_after_update(mapper, connection, target):
    target.increment_versie()
    create_historie_record(mapper, connection, target, "update")

@event.listens_for(Project, 'after_delete')
def project_after_delete(mapper, connection, target):
    create_historie_record(mapper, connection, target, "delete")

# Herhaal voor Contract, Leverancier, User, ProjectFase, etc.
"""


# ============================================================================
# HELPER FUNCTIES
# ============================================================================

def get_record_historie(db: Session, tabel_naam: str, record_id: str) -> list:
    """
    Haal alle historie records op voor een specifiek record
    
    Args:
        db: Database session
        tabel_naam: Naam van de tabel
        record_id: ID van het record
    
    Returns:
        List van HistorieRecord objecten, gesorteerd op datum (nieuwste eerst)
    """
    return db.query(HistorieRecord).filter(
        HistorieRecord.tabel_naam == tabel_naam,
        HistorieRecord.record_id == record_id
    ).order_by(HistorieRecord.gewijzigd_op.desc()).all()


def get_record_versie(db: Session, tabel_naam: str, record_id: str, versie: int) -> dict:
    """
    Haal een specifieke versie van een record op
    
    Args:
        db: Database session
        tabel_naam: Naam van de tabel
        record_id: ID van het record
        versie: Versie nummer
    
    Returns:
        Dictionary met de data van die versie
    """
    historie = db.query(HistorieRecord).filter(
        HistorieRecord.tabel_naam == tabel_naam,
        HistorieRecord.record_id == record_id,
        HistorieRecord.versie_nummer == versie
    ).first()
    
    if not historie:
        return None
    
    return json.loads(historie.data_na) if historie.data_na else None


def compare_versies(db: Session, tabel_naam: str, record_id: str, versie1: int, versie2: int) -> dict:
    """
    Vergelijk twee versies van een record
    
    Args:
        db: Database session
        tabel_naam: Naam van de tabel
        record_id: ID van het record
        versie1: Eerste versie nummer
        versie2: Tweede versie nummer
    
    Returns:
        Dictionary met verschillen
    """
    data1 = get_record_versie(db, tabel_naam, record_id, versie1)
    data2 = get_record_versie(db, tabel_naam, record_id, versie2)
    
    if not data1 or not data2:
        return None
    
    verschillen = {}
    all_keys = set(data1.keys()) | set(data2.keys())
    
    for key in all_keys:
        val1 = data1.get(key)
        val2 = data2.get(key)
        
        if val1 != val2:
            verschillen[key] = {
                "oud": val1,
                "nieuw": val2
            }
    
    return verschillen


def restore_versie(db: Session, tabel_naam: str, record_id: str, versie: int, user_id: str = None):
    """
    Herstel een record naar een oude versie
    
    BELANGRIJK: Deze functie alleen gebruiken als je weet wat je doet!
    Dit maakt een NIEUWE versie aan met de oude data.
    
    Args:
        db: Database session
        tabel_naam: Naam van de tabel
        record_id: ID van het record
        versie: Versie nummer om naar terug te gaan
        user_id: Wie doet de restore
    """
    # Implementatie afhankelijk van je specifieke modellen
    # Dit is een placeholder
    raise NotImplementedError("Restore functie moet per model geïmplementeerd worden")


# ============================================================================
# AUDIT QUERIES
# ============================================================================

def get_user_activiteit(db: Session, user_id: str, limit: int = 50) -> list:
    """Haal recente activiteit van een gebruiker op"""
    return db.query(HistorieRecord).filter(
        HistorieRecord.gewijzigd_door_id == user_id
    ).order_by(HistorieRecord.gewijzigd_op.desc()).limit(limit).all()


def get_tabel_activiteit(db: Session, tabel_naam: str, limit: int = 100) -> list:
    """Haal recente activiteit van een tabel op"""
    return db.query(HistorieRecord).filter(
        HistorieRecord.tabel_naam == tabel_naam
    ).order_by(HistorieRecord.gewijzigd_op.desc()).limit(limit).all()


def get_recent_changes(db: Session, hours: int = 24) -> list:
    """Haal alle wijzigingen van de laatste X uren op"""
    from datetime import timedelta
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    
    return db.query(HistorieRecord).filter(
        HistorieRecord.gewijzigd_op >= cutoff
    ).order_by(HistorieRecord.gewijzigd_op.desc()).all()
