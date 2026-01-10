"""
ProcesTemplate models - Template systeem voor standaard processen
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.session import Base


# ============================================================================
# ENUMS
# ============================================================================

class ProcesCategorie(str, enum.Enum):
    """Categorie van proces template"""
    ONDERHOUD = "onderhoud"
    RENOVATIE = "renovatie"
    NIEUWBOUW = "nieuwbouw"
    INSPECTIE = "inspectie"
    CALAMITEIT = "calamiteit"
    ANDERS = "anders"


class TemplateStapStatus(str, enum.Enum):
    """Status voor template stap (gebruikt als default voor nieuwe projecten)"""
    NIET_GESTART = "niet_gestart"
    IN_UITVOERING = "in_uitvoering"
    IN_REVIEW = "in_review"
    GOEDGEKEURD = "goedgekeurd"
    AFGEROND = "afgerond"


# ============================================================================
# MODEL 1: ProcesTemplate (HOOFDMODEL)
# ============================================================================

class ProcesTemplate(Base):
    """
    ProcesTemplate model

    Een herbruikbare template voor standaard processen
    Bijvoorbeeld: "9-stappen DUWO proces", "Snelle reparatie", "Jaarlijkse inspectie"

    Een template bestaat uit:
    - Basis informatie (naam, beschrijving, categorie)
    - Meerdere TemplateStappen (fase 1 t/m N)
    - Documentsjablonen die standaard verwacht worden
    """
    __tablename__ = "proces_templates"

    # Primary key
    id = Column(String, primary_key=True, index=True)

    # Basic info
    naam = Column(String, nullable=False, unique=True)
    beschrijving = Column(Text, nullable=True)
    categorie = Column(SQLEnum(ProcesCategorie), nullable=False)

    # Status
    is_actief = Column(Boolean, default=True, nullable=False)
    is_standaard = Column(Boolean, default=False, nullable=False)  # Is dit de standaard template?

    # Usage stats
    aantal_keer_gebruikt = Column(Integer, default=0, nullable=False)

    # Owner
    gemaakt_door_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)

    # Relationships
    gemaakt_door = relationship("User", foreign_keys=[gemaakt_door_id])
    stappen = relationship("TemplateStap", back_populates="template", cascade="all, delete-orphan", order_by="TemplateStap.stap_nummer")
    document_sjablonen = relationship("TemplateDocumentSjabloon", back_populates="template", cascade="all, delete-orphan")

    # Versiebeheer
    versie_nummer = Column(Integer, default=1, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<ProcesTemplate {self.naam}>"

    @property
    def aantal_stappen(self) -> int:
        """Return aantal stappen in deze template"""
        return len(self.stappen) if self.stappen else 0


# ============================================================================
# MODEL 2: TemplateStap
# ============================================================================

class TemplateStap(Base):
    """
    TemplateStap model

    Een stap binnen een proces template
    Bijvoorbeeld: "1. Initiatief", "2. Projectschouw", "3. Planvorming", etc.

    Wanneer een project wordt aangemaakt op basis van een template,
    wordt voor elke TemplateStap automatisch een ProjectFase aangemaakt
    """
    __tablename__ = "template_stappen"

    # Primary key
    id = Column(String, primary_key=True, index=True)

    # Relatie met template
    template_id = Column(String, ForeignKey('proces_templates.id'), nullable=False, index=True)

    # Stap info
    stap_nummer = Column(Integer, nullable=False)
    naam = Column(String, nullable=False)
    beschrijving = Column(Text, nullable=True)

    # Default status bij aanmaken
    default_status = Column(SQLEnum(TemplateStapStatus), default=TemplateStapStatus.NIET_GESTART, nullable=False)

    # Geschatte doorlooptijd (in dagen)
    geschatte_doorlooptijd_dagen = Column(Integer, nullable=True)

    # Vereist leverancier?
    vereist_leverancier = Column(Boolean, default=False, nullable=False)

    # Instructies voor deze stap
    instructies = Column(Text, nullable=True)

    # Relationships
    template = relationship("ProcesTemplate", back_populates="stappen")
    verwachte_documenten = relationship("TemplateDocumentSjabloon", back_populates="stap", cascade="all, delete-orphan")

    # Versiebeheer
    versie_nummer = Column(Integer, default=1, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<TemplateStap {self.stap_nummer}: {self.naam}>"


# ============================================================================
# MODEL 3: TemplateDocumentSjabloon
# ============================================================================

class TemplateDocumentSjabloon(Base):
    """
    TemplateDocumentSjabloon model

    Documentsjabloon verwacht bij een specifieke stap
    Bijvoorbeeld: Bij stap "Aanbieding" verwacht je documenten zoals "Offerte" en "Begroting"

    Dit is GEEN fysiek document, maar een sjabloon/verwachting
    Wordt gebruikt om checkboxes/reminders te tonen in de UI
    """
    __tablename__ = "template_document_sjablonen"

    # Primary key
    id = Column(String, primary_key=True, index=True)

    # Relaties
    template_id = Column(String, ForeignKey('proces_templates.id'), nullable=False, index=True)
    stap_id = Column(String, ForeignKey('template_stappen.id'), nullable=False, index=True)

    # Document sjabloon info
    naam = Column(String, nullable=False)
    beschrijving = Column(Text, nullable=True)

    # Is dit document verplicht?
    is_verplicht = Column(Boolean, default=False, nullable=False)

    # Document type (optioneel)
    verwacht_type = Column(String, nullable=True)  # bijv. "pdf", "xlsx", "docx"

    # Relationships
    template = relationship("ProcesTemplate", back_populates="document_sjablonen")
    stap = relationship("TemplateStap", back_populates="verwachte_documenten")

    # Versiebeheer
    versie_nummer = Column(Integer, default=1, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<TemplateDocumentSjabloon {self.naam}>"
