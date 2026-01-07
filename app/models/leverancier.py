"""
Leverancier model
"""
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, Text, Boolean, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.session import Base


class LeverancierStatus(str, enum.Enum):
    """Leverancier status"""
    ACTIEF = "actief"
    INACTIEF = "inactief"
    GEBLOKKEERD = "geblokkeerd"


class LeverancierType(str, enum.Enum):
    """Leverancier type"""
    ONDERHOUD = "onderhoud"
    BOUW = "bouw"
    INSTALLATIE = "installatie"
    SCHOONMAAK = "schoonmaak"
    BEVEILIGING = "beveiliging"
    ADVIES = "advies"
    LEVERANCIER = "leverancier"
    ANDERS = "anders"


class Leverancier(Base):
    """
    Leverancier model
    """
    __tablename__ = "leveranciers"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Basic info
    naam = Column(String, nullable=False, index=True)
    kvk_nummer = Column(String, nullable=True, unique=True, index=True)
    btw_nummer = Column(String, nullable=True)
    type = Column(SQLEnum(LeverancierType), nullable=False)
    status = Column(SQLEnum(LeverancierStatus), default=LeverancierStatus.ACTIEF, nullable=False)
    
    # Contact
    contactpersoon = Column(String, nullable=True)
    email = Column(String, nullable=True, index=True)
    telefoon = Column(String, nullable=True)
    mobiel = Column(String, nullable=True)
    website = Column(String, nullable=True)
    
    # Adres
    adres_straat = Column(String, nullable=True)
    adres_huisnummer = Column(String, nullable=True)
    adres_postcode = Column(String, nullable=True)
    adres_plaats = Column(String, nullable=True)
    adres_land = Column(String, nullable=True, default="Nederland")
    
    # Bank
    iban = Column(String, nullable=True)
    bank_naam = Column(String, nullable=True)
    
    # Extra
    notities = Column(Text, nullable=True)
    rating = Column(Float, nullable=True)
    
    # Relationships
    # contracten = relationship("Contract", back_populates="leverancier")
    # Note: Contract model needs to be updated to have leverancier_id FK
    
    # Versiebeheer
    versie_nummer = Column(Integer, default=1, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # ✅ NIEUW: Relationship naar users
    users = relationship("User", back_populates="leverancier")
    
    def __repr__(self):
        return f"<Leverancier {self.naam}>"
    
    @property
    def volledig_adres(self) -> str:
        """Return full address as string"""
        parts = []
        
        if self.adres_straat and self.adres_huisnummer:
            parts.append(f"{self.adres_straat} {self.adres_huisnummer}")
        elif self.adres_straat:
            parts.append(self.adres_straat)
        
        if self.adres_postcode and self.adres_plaats:
            parts.append(f"{self.adres_postcode} {self.adres_plaats}")
        elif self.adres_plaats:
            parts.append(self.adres_plaats)
        
        if self.adres_land and self.adres_land.lower() != "nederland":
            parts.append(self.adres_land)
        
        return ", ".join(parts) if parts else "Geen adres opgegeven"
    
    @property
    def is_actief(self) -> bool:
        """Check if leverancier is active"""
        return self.status == LeverancierStatus.ACTIEF
