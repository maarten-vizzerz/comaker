"""
ProjectFase models - Documentatie en Commentaren
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
import enum

from app.db.session import Base


# ============================================================================
# ENUMS
# ============================================================================

class ProjectFaseStatus(str, enum.Enum):
    """Status van een projectfase"""
    NIET_GESTART = "niet_gestart"
    IN_UITVOERING = "in_uitvoering"
    IN_REVIEW = "in_review"
    GOEDGEKEURD = "goedgekeurd"
    AFGEROND = "afgerond"


class DocumentType(str, enum.Enum):
    """Type document"""
    OFFERTE = "offerte"
    CONTRACT = "contract"
    TEKENING = "tekening"
    FOTO = "foto"
    FACTUUR = "factuur"
    OPLEVERING = "oplevering"
    CONTROLE = "controle"
    CORRESPONDENTIE = "correspondentie"
    ANDERS = "anders"


class CommentaarType(str, enum.Enum):
    """Type commentaar - bepaalt wie het mag zien/bewerken"""
    MEDEWERKER = "medewerker"      # Van interne medewerker
    COMAKER = "comaker"            # Van leverancier (comaker)
    SYSTEEM = "systeem"            # Automatische berichten


class CommentaarStatus(str, enum.Enum):
    """Status van commentaar"""
    CONCEPT = "concept"
    GEPUBLICEERD = "gepubliceerd"
    GEARCHIVEERD = "gearchiveerd"


# ============================================================================
# MODEL 1: ProjectFase (BASIS)
# ============================================================================

class ProjectFase(Base):
    """
    ProjectFase model
    
    Een project bestaat uit meerdere fases (bijv. Voorbereiding, Uitvoering, Oplevering)
    Elke fase kan documenten en commentaren bevatten
    """
    __tablename__ = "project_fases"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Relatie met project
    project_id = Column(String, ForeignKey('projects.id'), nullable=False, index=True)
    
    # Basic info
    fase_nummer = Column(Integer, nullable=False)
    naam = Column(String, nullable=False)
    beschrijving = Column(Text, nullable=True)
    status = Column(SQLEnum(ProjectFaseStatus), default=ProjectFaseStatus.NIET_GESTART, nullable=False)
    
    # Verantwoordelijke
    verantwoordelijke_id = Column(String, ForeignKey('users.id'), nullable=True, index=True)
    
    # Leverancier (comaker) - OPTIONEEL
    leverancier_id = Column(String, ForeignKey('leveranciers.id'), nullable=True, index=True)
    
    # Datums
    geplande_start_datum = Column(DateTime(timezone=True), nullable=True)
    geplande_eind_datum = Column(DateTime(timezone=True), nullable=True)
    werkelijke_start_datum = Column(DateTime(timezone=True), nullable=True)
    werkelijke_eind_datum = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    project = relationship("Project", foreign_keys=[project_id])
    verantwoordelijke = relationship("User", foreign_keys=[verantwoordelijke_id])
    leverancier = relationship("Leverancier", foreign_keys=[leverancier_id])
    
    # Backward relationships
    documenten = relationship("ProjectFaseDocument", back_populates="fase", cascade="all, delete-orphan")
    commentaren = relationship("ProjectFaseCommentaar", back_populates="fase", cascade="all, delete-orphan")
    
    # Versiebeheer
    versie_nummer = Column(Integer, default=1, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ProjectFase {self.fase_nummer}: {self.naam}>"
    
    @property
    def is_afgerond(self) -> bool:
        """Check of fase is afgerond"""
        return self.status == ProjectFaseStatus.AFGEROND
    
    @property
    def heeft_leverancier(self) -> bool:
        """Check of deze fase een leverancier heeft"""
        return self.leverancier_id is not None


# ============================================================================
# MODEL 2: ProjectFaseDocument
# ============================================================================

class ProjectFaseDocument(Base):
    """
    ProjectFaseDocument model
    
    Documenten gekoppeld aan een projectfase
    Eén fase kan meerdere documenten hebben
    """
    __tablename__ = "project_fase_documenten"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Relatie met fase
    fase_id = Column(String, ForeignKey('project_fases.id'), nullable=False, index=True)
    
    # Document info
    naam = Column(String, nullable=False)
    beschrijving = Column(Text, nullable=True)
    type = Column(SQLEnum(DocumentType), nullable=False)
    
    # Bestand info
    bestandsnaam = Column(String, nullable=False)
    bestandstype = Column(String, nullable=False)
    bestandsgrootte = Column(Integer, nullable=True)
    
    # Opslag locatie
    opslag_type = Column(String, nullable=False, default="local")
    opslag_pad = Column(String, nullable=False)
    sharepoint_id = Column(String, nullable=True)
    
    # Versie beheer
    versie = Column(String, nullable=False, default="1.0")
    is_definitief = Column(Boolean, default=False, nullable=False)
    
    # Upload info
    geupload_door_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)
    upload_datum = Column(DateTime(timezone=True), server_default=func.now())
    
    # RECHTEN: Wie mag dit document zien?
    zichtbaar_voor_leverancier = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    fase = relationship("ProjectFase", back_populates="documenten")
    geupload_door = relationship("User", foreign_keys=[geupload_door_id])
    
    # Versiebeheer
    versie_nummer = Column(Integer, default=1, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ProjectFaseDocument {self.naam} v{self.versie}>"
    
    @property
    def bestandsgrootte_mb(self) -> float:
        """Return file size in MB"""
        if not self.bestandsgrootte:
            return 0.0
        return round(self.bestandsgrootte / (1024 * 1024), 2)


# ============================================================================
# MODEL 3: ProjectFaseCommentaar
# ============================================================================

class ProjectFaseCommentaar(Base):
    """
    ProjectFaseCommentaar model
    
    Commentaren op een projectfase
    - Medewerkers kunnen interne commentaren plaatsen
    - Leveranciers (comakers) kunnen hun eigen commentaren plaatsen
    - Beide kunnen elkaars commentaren LEZEN
    - Alleen eigen commentaren kunnen worden BEWERKT
    """
    __tablename__ = "project_fase_commentaren"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Relatie met fase
    fase_id = Column(String, ForeignKey('project_fases.id'), nullable=False, index=True)
    
    # Type commentaar - CRUCIAAL voor rechten!
    type = Column(SQLEnum(CommentaarType), nullable=False, index=True)
    
    # Status
    status = Column(SQLEnum(CommentaarStatus), default=CommentaarStatus.GEPUBLICEERD, nullable=False)
    
    # Inhoud
    onderwerp = Column(String, nullable=True)
    bericht = Column(Text, nullable=False)
    
    # Auteur
    auteur_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)
    
    # OPTIONEEL: Als dit een leverancier commentaar is
    leverancier_id = Column(String, ForeignKey('leveranciers.id'), nullable=True, index=True)
    
    # Reactie op ander commentaar? (threading)
    parent_commentaar_id = Column(String, ForeignKey('project_fase_commentaren.id'), nullable=True)
    
    # Timestamps
    gepubliceerd_op = Column(DateTime(timezone=True), nullable=True)
    bewerkt_op = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    fase = relationship("ProjectFase", back_populates="commentaren")
    auteur = relationship("User", foreign_keys=[auteur_id])
    leverancier = relationship("Leverancier", foreign_keys=[leverancier_id])
    parent_commentaar = relationship("ProjectFaseCommentaar", remote_side=[id], backref="reacties")
    
    # Versiebeheer
    versie_nummer = Column(Integer, default=1, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ProjectFaseCommentaar {self.type} by {self.auteur_id}>"
    
    @property
    def is_van_leverancier(self) -> bool:
        """Check of commentaar van leverancier is"""
        return self.type == CommentaarType.COMAKER
    
    @property
    def is_van_medewerker(self) -> bool:
        """Check of commentaar van medewerker is"""
        return self.type == CommentaarType.MEDEWERKER
    
    @property
    def is_gepubliceerd(self) -> bool:
        """Check of commentaar gepubliceerd is"""
        return self.status == CommentaarStatus.GEPUBLICEERD
