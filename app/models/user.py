"""
Database models
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from app.db.session import Base


class UserRole(str, enum.Enum):
    """User roles"""
    BEHEERDER = "beheerder"
    PROJECTLEIDER = "projectleider"
    CONTROLEUR = "controleur"
    ADMINISTRATIEF_MEDEWERKER = "administratief_medewerker"
    LEVERANCIER = "leverancier"
    READ_ONLY = "read_only"


class User(Base):
    """
    User model
    """
    __tablename__ = "users"
    
    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    avatar = Column(String, nullable=True)
    
    # ✅ NIEUW: Link naar leverancier (voor users met role LEVERANCIER)
    leverancier_id = Column(String, ForeignKey('leveranciers.id'), nullable=True, index=True)
    
    # Versiebeheer
    versie_nummer = Column(Integer, default=1, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # ✅ NIEUW: Relationship
    leverancier = relationship("Leverancier", back_populates="users")
    
    def __repr__(self):
        return f"<User {self.email}>"
