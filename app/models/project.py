"""
Project model - FIXED budget_percentage
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from app.db.session import Base


class ProjectStatus(str, enum.Enum):
    """Project status"""
    CONCEPT = "concept"
    IN_PLANNING = "in_planning"
    OFFERTE_AANVRAAG = "offerte_aanvraag"
    IN_UITVOERING = "in_uitvoering"
    KWALITEITSCONTROLE = "kwaliteitscontrole"
    VOORLOPIG_OPGELEVERD = "voorlopig_opgeleverd"
    AFGEROND = "afgerond"


class Project(Base):
    """
    Project model
    """
    __tablename__ = "projects"
    
    # Primary key
    id = Column(String, primary_key=True, index=True)
    
    # Basic info
    project_nummer = Column(String, unique=True, nullable=False, index=True)
    naam = Column(String, nullable=False)
    beschrijving = Column(Text, nullable=True)
    status = Column(SQLEnum(ProjectStatus), default=ProjectStatus.CONCEPT, nullable=False)
    
    # Budget - NULLABLE voor veiligheid
    budget_totaal = Column(Integer, nullable=True, default=0)
    budget_besteed = Column(Integer, nullable=True, default=0)
    
    # Dates
    start_datum = Column(DateTime(timezone=True), nullable=True)
    eind_datum = Column(DateTime(timezone=True), nullable=True)
    
    # Foreign keys
    projectleider_id = Column(String, ForeignKey("users.id"), nullable=True)
    template_id = Column(String, nullable=True)  # Will be FK after migration
    vestiging_id = Column(String, ForeignKey("vestigingen.id"), nullable=True, index=True)

    # Relationships
    projectleider = relationship("User", backref="projecten")
    vestiging = relationship("Vestiging", backref="projecten")
    
    opmerkingen = Column(Text, nullable=True)
    
    # Versiebeheer
    versie_nummer = Column(Integer, default=1, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<Project {self.project_nummer}: {self.naam}>"
    
    @property
    def budget_percentage(self) -> int:
        """
        Calculate budget percentage
        SAFE: Handles None values
        """
        try:
            # Handle None values
            totaal = self.budget_totaal or 0
            besteed = self.budget_besteed or 0
            
            # Avoid division by zero
            if totaal == 0:
                return 0
            
            # Calculate percentage
            percentage = int((besteed / totaal) * 100)
            
            # Cap at 100%
            return min(percentage, 100)
        except:
            # Fallback to 0 if anything goes wrong
            return 0
