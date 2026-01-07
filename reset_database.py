"""
Database Reset Script
=====================

Dit script dropt alle tabellen en maakt ze opnieuw aan.
Gebruik dit ALLEEN in development!

Usage:
    python reset_database.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from app.db.session import engine, Base

# Import ALL models (dit is cruciaal zodat SQLAlchemy ze kent!)
from app.models.user import User, UserRole
from app.models.leverancier import Leverancier, LeverancierStatus, LeverancierType
from app.models.project import Project, ProjectStatus
from app.models.contract import Contract, ContractStatus, ContractType
from app.models.projectfase import (
    ProjectFase, 
    ProjectFaseDocument, 
    ProjectFaseCommentaar,
    ProjectFaseStatus,
    DocumentType,
    CommentaarType,
    CommentaarStatus
)


def reset_database():
    """Drop all tables and recreate them"""
    print("⚠️  WARNING: Dit verwijdert ALLE data!")
    print("=" * 50)
    
    response = input("Weet je zeker dat je door wilt gaan? (yes/no): ")
    
    if response.lower() != "yes":
        print("❌ Geannuleerd")
        return
    
    print("\n🗑️  Dropping alle tabellen...")
    Base.metadata.drop_all(bind=engine)
    print("✅ Tabellen verwijderd")
    
    print("\n🔨 Aanmaken nieuwe tabellen...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tabellen aangemaakt")
    
    print("\n" + "=" * 50)
    print("✅ DATABASE RESET COMPLEET!")
    print("=" * 50)
    print("\n📋 Nieuwe tabellen:")
    print("   • users")
    print("   • leveranciers")
    print("   • projects")
    print("   • contracts")
    print("   • project_fases              ⭐ NIEUW!")
    print("   • project_fase_documenten    ⭐ NIEUW!")
    print("   • project_fase_commentaren   ⭐ NIEUW!")
    print("\n💡 Je kunt nu je applicatie starten met: python main.py")


if __name__ == "__main__":
    reset_database()
