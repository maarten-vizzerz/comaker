"""
Database Reset Script - MET HISTORIE TABELLEN
==============================================

Dit script dropt alle tabellen en maakt ze opnieuw aan.
Gebruik dit ALLEEN in development!

Usage:
    python reset_database.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

print("=" * 70)
print("🔄 DATABASE RESET SCRIPT - MET HISTORIE TABELLEN")
print("=" * 70)

# Import database
try:
    from app.db.session import engine, Base
    print("✅ Database connection OK")
except Exception as e:
    print(f"❌ Database connection FAILED: {e}")
    sys.exit(1)

# Import ALL models (dit is cruciaal zodat SQLAlchemy ze kent!)
print("\n📦 Importeren van models...")

try:
    from app.models.user import User, UserRole
    print("   ✅ User model")
except Exception as e:
    print(f"   ❌ User model: {e}")

try:
    from app.models.leverancier import Leverancier, LeverancierStatus, LeverancierType
    print("   ✅ Leverancier model")
except Exception as e:
    print(f"   ❌ Leverancier model: {e}")

try:
    from app.models.project import Project, ProjectStatus
    print("   ✅ Project model")
except Exception as e:
    print(f"   ❌ Project model: {e}")

try:
    from app.models.contract import Contract, ContractStatus, ContractType
    print("   ✅ Contract model")
except Exception as e:
    print(f"   ❌ Contract model: {e}")

try:
    from app.models.projectfase import (
        ProjectFase, 
        ProjectFaseDocument, 
        ProjectFaseCommentaar,
        ProjectFaseStatus,
        DocumentType,
        CommentaarType,
        CommentaarStatus
    )
    print("   ✅ ProjectFase models (3 classes)")
except Exception as e:
    print(f"   ❌ ProjectFase models: {e}")

# Import HISTORIE models ⭐ NIEUW!
print("\n📜 Importeren van historie models...")
try:
    from app.models.historie import (
        HistorieRecord,
        UserHistorie,
        ProjectHistorie,
        ContractHistorie,
        LeverancierHistorie,
        ProjectFaseHistorie
    )
    print("   ✅ HistorieRecord (centrale tabel)")
    print("   ✅ UserHistorie")
    print("   ✅ ProjectHistorie")
    print("   ✅ ContractHistorie")
    print("   ✅ LeverancierHistorie")
    print("   ✅ ProjectFaseHistorie")
except ImportError as e:
    print(f"   ⚠️  Historie models niet gevonden: {e}")
    print("   ⚠️  Historie tabellen worden NIET aangemaakt!")
    print("   💡 Tip: Zorg dat app/models/historie.py bestaat")
except Exception as e:
    print(f"   ❌ Historie models error: {e}")


def reset_database():
    """Drop all tables and recreate them"""
    print("\n" + "=" * 70)
    print("⚠️  WARNING: Dit verwijdert ALLE data!")
    print("=" * 70)
    
    response = input("\n🤔 Weet je zeker dat je door wilt gaan? (typ 'yes'): ")
    
    if response.lower() != "yes":
        print("❌ Geannuleerd")
        return
    
    print("\n🗑️  Dropping alle tabellen...")
    try:
        Base.metadata.drop_all(bind=engine)
        print("✅ Tabellen verwijderd")
    except Exception as e:
        print(f"❌ Error bij verwijderen: {e}")
        return
    
    print("\n🔨 Aanmaken nieuwe tabellen...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Tabellen aangemaakt")
    except Exception as e:
        print(f"❌ Error bij aanmaken: {e}")
        return
    
    # Verifieer welke tabellen zijn aangemaakt
    print("\n🔍 Verificatie van aangemaakte tabellen...")
    try:
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print(f"\n📊 Totaal {len(tables)} tabellen aangemaakt:")
        
        # Categoriseer tabellen
        hoofd_tabellen = []
        historie_tabellen = []
        andere_tabellen = []
        
        for table in sorted(tables):
            if '_historie' in table or table == 'historie_records':
                historie_tabellen.append(table)
            elif table in ['users', 'leveranciers', 'projects', 'contracts', 
                          'project_fases', 'project_fase_documenten', 'project_fase_commentaren']:
                hoofd_tabellen.append(table)
            else:
                andere_tabellen.append(table)
        
        print("\n🏢 Hoofdtabellen:")
        for table in hoofd_tabellen:
            marker = "⭐ NIEUW" if 'fase' in table else ""
            print(f"   • {table:30} {marker}")
        
        if historie_tabellen:
            print("\n📜 Historie/Versiebeheer tabellen:")
            for table in historie_tabellen:
                print(f"   • {table:30} ⭐ NIEUW")
        else:
            print("\n⚠️  Geen historie tabellen gevonden!")
            print("   💡 Check of app/models/historie.py correct is geïmporteerd")
        
        if andere_tabellen:
            print("\n📋 Overige tabellen:")
            for table in andere_tabellen:
                print(f"   • {table}")
        
    except Exception as e:
        print(f"⚠️  Kan tabellen niet verifiëren: {e}")
    
    print("\n" + "=" * 70)
    print("✅ DATABASE RESET COMPLEET!")
    print("=" * 70)
    print("\n💡 Volgende stappen:")
    print("   1. Check of alle tabellen zijn aangemaakt (zie lijst hierboven)")
    print("   2. Start je applicatie: python main.py")
    print("   3. Test in Swagger docs: http://localhost:8000/docs")
    print("\n🚀 Veel succes!")


if __name__ == "__main__":
    reset_database()
