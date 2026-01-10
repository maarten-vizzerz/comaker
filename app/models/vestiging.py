"""
Vestiging model
Vestigingen zijn locaties/kantoren waar projecten aan gekoppeld kunnen worden
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Vestiging(Base):
    """
    Vestiging model - Locaties/kantoren
    """
    __tablename__ = "vestigingen"

    # Primary key
    id = Column(String, primary_key=True, index=True)

    # Basic info
    naam = Column(String, nullable=False, index=True)
    code = Column(String, nullable=False, unique=True, index=True)  # Unieke code (LED, DFT, AMS, etc.)

    # Adres
    adres_straat = Column(String, nullable=True)
    adres_huisnummer = Column(String, nullable=True)
    adres_postcode = Column(String, nullable=True)
    adres_plaats = Column(String, nullable=False)  # Plaats is verplicht
    adres_land = Column(String, nullable=True, default="Nederland")

    # Contact
    telefoon = Column(String, nullable=True)
    email = Column(String, nullable=True)

    # Extra
    notities = Column(Text, nullable=True)
    is_actief = Column(Boolean, default=True, nullable=False)

    # Relationships
    # projecten = relationship("Project", back_populates="vestiging")

    # Versiebeheer
    versie_nummer = Column(Integer, default=1, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Vestiging {self.naam} - {self.adres_plaats}>"

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
