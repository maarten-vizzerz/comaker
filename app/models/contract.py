"""
Contract model - UPDATED with Leverancier relationship
"""
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, ForeignKey, Numeric, Date, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
import enum

from app.db.session import Base


class ContractStatus(str, enum.Enum):
    """Contract status"""
    CONCEPT = "concept"
    TER_GOEDKEURING = "ter_goedkeuring"
    GOEDGEKEURD = "goedgekeurd"
    GETEKEND = "getekend"
    ACTIEF = "actief"
    VERLOPEN = "verlopen"
    BEEINDIGD = "beeindigd"


class ContractType(str, enum.Enum):
    """Contract type"""
    ONDERHOUDSCONTRACT = "onderhoudscontract"
    DIENSTVERLENING = "dienstverlening"
    LEVERING = "levering"
    AANNEMING = "aanneming"
    RAAMOVEREENKOMST = "raamovereenkomst"
    HUUR = "huur"
    ANDERS = "anders"


class Contract(Base):
    """
    Contract model - UPDATED with Leverancier relationship
    """
    __tablename__ = "contracts"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Basic info
    contract_nummer = Column(String, unique=True, nullable=False, index=True)
    naam = Column(String, nullable=False, index=True)
    beschrijving = Column(Text, nullable=True)
    type = Column(SQLEnum(ContractType), nullable=False)
    status = Column(SQLEnum(ContractStatus), default=ContractStatus.CONCEPT, nullable=False)
    
    # Leverancier - UPDATED: Now a relationship instead of embedded fields!
    leverancier_id = Column(String, ForeignKey('leveranciers.id'), nullable=False, index=True)
    
    # Bedragen
    contract_bedrag = Column(Numeric(12, 2), nullable=False)
    gefactureerd_bedrag = Column(Numeric(12, 2), default=0, nullable=False)
    
    # Datums
    start_datum = Column(Date, nullable=True)
    eind_datum = Column(Date, nullable=True)
    getekend_datum = Column(Date, nullable=True)
    
    # Goedkeuring
    goedgekeurd_door_id = Column(String, ForeignKey('users.id'), nullable=True)
    goedkeurings_datum = Column(DateTime(timezone=True), nullable=True)
    opmerkingen = Column(Text, nullable=True)
    
    # Relations
    project_id = Column(String, ForeignKey('projects.id'), nullable=True, index=True)
    verantwoordelijke_id = Column(String, ForeignKey('users.id'), nullable=False, index=True)
    
    # Relationships - UPDATED: Add leverancier relationship!
    leverancier = relationship("Leverancier", foreign_keys=[leverancier_id])
    project = relationship("Project", foreign_keys=[project_id])
    verantwoordelijke = relationship("User", foreign_keys=[verantwoordelijke_id])
    goedgekeurd_door = relationship("User", foreign_keys=[goedgekeurd_door_id])
    
    # Versiebeheer
    versie_nummer = Column(Integer, default=1, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Contract {self.contract_nummer}>"
    
    @property
    def gefactureerd_percentage(self) -> float:
        """Calculate percentage invoiced"""
        if not self.contract_bedrag or self.contract_bedrag == 0:
            return 0.0
        
        percentage = (float(self.gefactureerd_bedrag) / float(self.contract_bedrag)) * 100
        return round(min(percentage, 100.0), 2)
    
    @property
    def restant_bedrag(self) -> float:
        """Calculate remaining amount"""
        return float(self.contract_bedrag - self.gefactureerd_bedrag)
    
    @property
    def is_actief(self) -> bool:
        """Check if contract is active based on status and dates"""
        try:
            if self.status != ContractStatus.ACTIEF:
                return False
            
            now = datetime.now(timezone.utc)
            
            if self.start_datum:
                start = self.start_datum
                if start.tzinfo is None:
                    from datetime import timezone as dt_timezone
                    start = datetime.combine(start, datetime.min.time()).replace(tzinfo=dt_timezone.utc)
                else:
                    start = datetime.combine(start, datetime.min.time()).replace(tzinfo=start.tzinfo)
                
                if start > now:
                    return False
            
            if self.eind_datum:
                eind = self.eind_datum
                if eind.tzinfo is None:
                    from datetime import timezone as dt_timezone
                    eind = datetime.combine(eind, datetime.min.time()).replace(tzinfo=dt_timezone.utc)
                else:
                    eind = datetime.combine(eind, datetime.min.time()).replace(tzinfo=eind.tzinfo)
                
                if eind < now:
                    return False
            
            return True
        except Exception as e:
            print(f"Warning in is_actief: {e}")
            return self.status == ContractStatus.ACTIEF
