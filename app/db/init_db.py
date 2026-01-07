"""
Initialize database with tables and seed data
"""
from sqlalchemy.orm import Session
import uuid
from datetime import datetime, timezone, timedelta, date

from app.db.session import engine, Base, SessionLocal

# BELANGRIJK: Import ALLE models hier zodat SQLAlchemy ze kent!
from app.models.user import User, UserRole
from app.models.project import Project, ProjectStatus  
from app.models.contract import Contract, ContractStatus, ContractType  
from app.models.leverancier import Leverancier, LeverancierStatus, LeverancierType
from app.models.projectfase import (
    ProjectFase, ProjectFaseDocument, ProjectFaseCommentaar,
    ProjectFaseStatus, DocumentType, CommentaarType, CommentaarStatus
)

from app.core.security import get_password_hash

# Import voor historie tracking
from app.models.historie_setup import disable_historie_tracking, enable_historie_tracking


def init_db():
    """
    Initialize database: create tables and seed data
    """
    # Create all tables
    print("📦 Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created")
    
    # Seed test data
    db = SessionLocal()
    
    # DISABLE HISTORIE TRACKING tijdens seeding!
    disable_historie_tracking(db)
    
    try:
        # Check if users already exist
        existing_users = db.query(User).count()
        
        if existing_users == 0:
            print("🌱 Creating seed data...")
            
            # ============================================================
            # 1. LEVERANCIERS
            # ============================================================
            print("\n📍 Creating leveranciers...")
            
            leverancier_bouwbedrijf = Leverancier(
                id=f"lev_{uuid.uuid4().hex[:8]}",
                naam="Bouwbedrijf de Bouwer BV",
                kvk_nummer="12345678",
                btw_nummer="NL123456789B01",
                type=LeverancierType.BOUW,
                status=LeverancierStatus.ACTIEF,
                contactpersoon="Jan de Bouwer",
                email="info@debouwer.nl",
                telefoon="010-1234567",
                mobiel="06-12345678",
                website="https://www.debouwer.nl",
                adres_straat="Bouwstraat",
                adres_huisnummer="123",
                adres_postcode="3011 AB",
                adres_plaats="Rotterdam",
                adres_land="Nederland",
                bank_naam="ING Bank",
                iban="NL12INGB0001234567",
                rating=4.5,
                notities="Betrouwbare partner voor grote projecten"
            )
            db.add(leverancier_bouwbedrijf)
            
            leverancier_installatie = Leverancier(
                id=f"lev_{uuid.uuid4().hex[:8]}",
                naam="InstallatieTech Solutions",
                kvk_nummer="87654321",
                btw_nummer="NL987654321B01",
                type=LeverancierType.INSTALLATIE,
                status=LeverancierStatus.ACTIEF,
                contactpersoon="Maria Monteur",
                email="contact@installatietech.nl",
                telefoon="020-9876543",
                mobiel="06-98765432",
                website="https://www.installatietech.nl",
                adres_straat="Installatieweg",
                adres_huisnummer="45",
                adres_postcode="1012 AB",
                adres_plaats="Amsterdam",
                adres_land="Nederland",
                bank_naam="ABN AMRO",
                iban="NL98ABNA0009876543",
                rating=4.8,
                notities="Specialist in duurzame installaties"
            )
            db.add(leverancier_installatie)
            
            db.flush()
            print(f"✅ Created 2 leveranciers")
            
            # ============================================================
            # 2. USERS (inclusief leverancier users!)
            # ============================================================
            print("\n👤 Creating test users...")
            
            # Interne users
            user_projectleider = User(
                id=f"usr_{uuid.uuid4().hex[:8]}",
                email="projectleider@comaker.cloud",
                name="Piet Project",
                role=UserRole.PROJECTLEIDER,
                hashed_password=get_password_hash("Test1234!"),
                is_active=True,
                leverancier_id=None
            )
            db.add(user_projectleider)
            
            user_beheerder = User(
                id=f"usr_{uuid.uuid4().hex[:8]}",
                email="beheerder@comaker.cloud",
                name="Bella Beheer",
                role=UserRole.BEHEERDER,
                hashed_password=get_password_hash("Test1234!"),
                is_active=True,
                leverancier_id=None
            )
            db.add(user_beheerder)
            
            user_controleur = User(
                id=f"usr_{uuid.uuid4().hex[:8]}",
                email="controleur@comaker.cloud",
                name="Karel Controleur",
                role=UserRole.CONTROLEUR,
                hashed_password=get_password_hash("Test1234!"),
                is_active=True,
                leverancier_id=None
            )
            db.add(user_controleur)
            
            user_admin = User(
                id=f"usr_{uuid.uuid4().hex[:8]}",
                email="admin@comaker.cloud",
                name="Annabel Admin",
                role=UserRole.ADMINISTRATIEF_MEDEWERKER,
                hashed_password=get_password_hash("Test1234!"),
                is_active=True,
                leverancier_id=None
            )
            db.add(user_admin)
            
            # LEVERANCIER USERS (gekoppeld aan leveranciers!)
            user_leverancier_bouw = User(
                id=f"usr_{uuid.uuid4().hex[:8]}",
                email="jan@debouwer.nl",
                name="Jan de Bouwer",
                role=UserRole.LEVERANCIER,
                hashed_password=get_password_hash("Test1234!"),
                is_active=True,
                leverancier_id=leverancier_bouwbedrijf.id
            )
            db.add(user_leverancier_bouw)
            
            user_leverancier_installatie = User(
                id=f"usr_{uuid.uuid4().hex[:8]}",
                email="maria@installatietech.nl",
                name="Maria Monteur",
                role=UserRole.LEVERANCIER,
                hashed_password=get_password_hash("Test1234!"),
                is_active=True,
                leverancier_id=leverancier_installatie.id
            )
            db.add(user_leverancier_installatie)
            
            db.flush()
            print(f"✅ Created 6 users (4 internal, 2 leveranciers)")
            
            # ============================================================
            # 3. PROJECT
            # ============================================================
            print("\n🏗️  Creating project...")
            
            project = Project(
                id=f"prj_{uuid.uuid4().hex[:8]}",
                project_nummer = "PRJ-001",
                naam="Renovatie Kantoorpand Centrum",
                beschrijving="Complete renovatie van kantoorpand inclusief nieuwe installaties",
                status=ProjectStatus.IN_UITVOERING,
                projectleider_id=user_projectleider.id,
                budget_totaal=250000.00,
                start_datum=datetime.now(timezone.utc) - timedelta(days=30),
                eind_datum=datetime.now(timezone.utc) + timedelta(days=90),
                versie_nummer=1,
                opmerkingen="Prioriteit project voor Q1"
            )
            db.add(project)
            db.flush()
            print(f"✅ Created project: {project.naam}")
            
            # ============================================================
            # 4. CONTRACT - ✅ FIXED: Gebruik correcte velden!
            # ============================================================
            print("\n📄 Creating contract...")
            
            contract = Contract(
                id=f"ctr_{uuid.uuid4().hex[:8]}",
                project_id=project.id,
                leverancier_id=leverancier_bouwbedrijf.id,
                contract_nummer="CTR-2025-001",
                naam="Bouw renovatie kantoorpand",  # ✅ naam ipv omschrijving
                beschrijving="Bouwwerkzaamheden renovatie kantoorpand",  # ✅ beschrijving
                type=ContractType.AANNEMING,
                status=ContractStatus.ACTIEF,
                verantwoordelijke_id=user_projectleider.id,  # ✅ TOEGEVOEGD: verplicht!
                start_datum=date.today() - timedelta(days=20),  # ✅ date ipv datetime
                eind_datum=date.today() + timedelta(days=80),   # ✅ date ipv datetime
                contract_bedrag=180000.00,
                # ❌ VERWIJDERD: betaalvoorwaarden bestaat niet meer
                # ❌ VERWIJDERD: contactpersoon_leverancier bestaat niet meer
                # ❌ VERWIJDERD: betalingstermijn_dagen bestaat niet meer
                opmerkingen="Hoofdcontract voor bouwwerkzaamheden"  # ✅ opmerkingen wel
            )
            db.add(contract)
            db.flush()
            print(f"✅ Created contract: {contract.contract_nummer}")
            
            # ============================================================
            # 5. PROJECTFASES
            # ============================================================
            print("\n📋 Creating projectfases...")
            
            fase_voorbereiding = ProjectFase(
                id=str(uuid.uuid4()),
                project_id=project.id,
                fase_nummer=1,
                naam="Voorbereiding",
                beschrijving="Voorbereidende werkzaamheden en vergunningen",
                status=ProjectFaseStatus.AFGEROND,
                verantwoordelijke_id=user_projectleider.id,
                leverancier_id=None,
                geplande_start_datum=datetime.now(timezone.utc) - timedelta(days=30),
                geplande_eind_datum=datetime.now(timezone.utc) - timedelta(days=20),
                werkelijke_start_datum=datetime.now(timezone.utc) - timedelta(days=30),
                werkelijke_eind_datum=datetime.now(timezone.utc) - timedelta(days=22)
            )
            db.add(fase_voorbereiding)
            
            fase_sloop = ProjectFase(
                id=str(uuid.uuid4()),
                project_id=project.id,
                fase_nummer=2,
                naam="Sloopwerkzaamheden",
                beschrijving="Sloop oude installaties en verbouwing",
                status=ProjectFaseStatus.AFGEROND,
                verantwoordelijke_id=user_projectleider.id,
                leverancier_id=leverancier_bouwbedrijf.id,
                geplande_start_datum=datetime.now(timezone.utc) - timedelta(days=20),
                geplande_eind_datum=datetime.now(timezone.utc) - timedelta(days=10),
                werkelijke_start_datum=datetime.now(timezone.utc) - timedelta(days=20),
                werkelijke_eind_datum=datetime.now(timezone.utc) - timedelta(days=12)
            )
            db.add(fase_sloop)
            
            fase_bouw = ProjectFase(
                id=str(uuid.uuid4()),
                project_id=project.id,
                fase_nummer=3,
                naam="Bouwwerkzaamheden",
                beschrijving="Nieuwbouw wanden, plafonds en vloeren",
                status=ProjectFaseStatus.IN_UITVOERING,
                verantwoordelijke_id=user_projectleider.id,
                leverancier_id=leverancier_bouwbedrijf.id,
                geplande_start_datum=datetime.now(timezone.utc) - timedelta(days=10),
                geplande_eind_datum=datetime.now(timezone.utc) + timedelta(days=30),
                werkelijke_start_datum=datetime.now(timezone.utc) - timedelta(days=10)
            )
            db.add(fase_bouw)
            
            fase_installatie = ProjectFase(
                id=str(uuid.uuid4()),
                project_id=project.id,
                fase_nummer=4,
                naam="Installaties",
                beschrijving="Elektrische en sanitaire installaties",
                status=ProjectFaseStatus.NIET_GESTART,
                verantwoordelijke_id=user_projectleider.id,
                leverancier_id=leverancier_installatie.id,
                geplande_start_datum=datetime.now(timezone.utc) + timedelta(days=30),
                geplande_eind_datum=datetime.now(timezone.utc) + timedelta(days=60)
            )
            db.add(fase_installatie)
            
            fase_afwerking = ProjectFase(
                id=str(uuid.uuid4()),
                project_id=project.id,
                fase_nummer=5,
                naam="Afwerking",
                beschrijving="Afwerking en schilderwerk",
                status=ProjectFaseStatus.NIET_GESTART,
                verantwoordelijke_id=user_projectleider.id,
                leverancier_id=leverancier_bouwbedrijf.id,
                geplande_start_datum=datetime.now(timezone.utc) + timedelta(days=60),
                geplande_eind_datum=datetime.now(timezone.utc) + timedelta(days=80)
            )
            db.add(fase_afwerking)
            
            db.flush()
            print(f"✅ Created 5 projectfases")
            
            # ============================================================
            # 6. PROJECTFASE DOCUMENTEN
            # ============================================================
            print("\n📎 Creating fase documenten...")
            
            doc_offerte = ProjectFaseDocument(
                id=str(uuid.uuid4()),
                fase_id=fase_sloop.id,
                naam="Offerte Sloopwerkzaamheden",
                beschrijving="Offerte voor sloop oude installaties",
                type=DocumentType.OFFERTE,
                bestandsnaam="offerte_sloop_2025.pdf",
                bestandstype="pdf",
                bestandsgrootte=245680,
                opslag_type="local",
                opslag_pad="/fake/path/offerte_sloop_2025.pdf",
                versie="1.0",
                is_definitief=True,
                geupload_door_id=user_projectleider.id,
                zichtbaar_voor_leverancier=True
            )
            db.add(doc_offerte)
            
            doc_intern = ProjectFaseDocument(
                id=str(uuid.uuid4()),
                fase_id=fase_bouw.id,
                naam="Interne Kostenbegroting",
                beschrijving="Interne berekening en marges",
                type=DocumentType.ANDERS,
                bestandsnaam="interne_begroting.xlsx",
                bestandstype="xlsx",
                bestandsgrootte=89432,
                opslag_type="local",
                opslag_pad="/fake/path/interne_begroting.xlsx",
                versie="2.1",
                is_definitief=False,
                geupload_door_id=user_beheerder.id,
                zichtbaar_voor_leverancier=False
            )
            db.add(doc_intern)
            
            doc_tekening = ProjectFaseDocument(
                id=str(uuid.uuid4()),
                fase_id=fase_bouw.id,
                naam="Bouwtekeningen verdieping 2",
                beschrijving="Definitieve tekeningen tweede verdieping",
                type=DocumentType.TEKENING,
                bestandsnaam="tekening_v2_def.dwg",
                bestandstype="dwg",
                bestandsgrootte=1234567,
                opslag_type="local",
                opslag_pad="/fake/path/tekening_v2_def.dwg",
                versie="3.0",
                is_definitief=True,
                geupload_door_id=user_projectleider.id,
                zichtbaar_voor_leverancier=True
            )
            db.add(doc_tekening)
            
            db.flush()
            print(f"✅ Created 3 fase documenten")
            
            # ============================================================
            # 7. PROJECTFASE COMMENTAREN
            # ============================================================
            print("\n💬 Creating fase commentaren...")
            
            comment_medewerker = ProjectFaseCommentaar(
                id=str(uuid.uuid4()),
                fase_id=fase_sloop.id,
                type=CommentaarType.MEDEWERKER,
                status=CommentaarStatus.GEPUBLICEERD,
                onderwerp="Status update",
                bericht="Sloopwerkzaamheden zijn volgens planning verlopen. Geen asbest aangetroffen.",
                auteur_id=user_projectleider.id,
                leverancier_id=None,
                gepubliceerd_op=datetime.now(timezone.utc) - timedelta(days=5)
            )
            db.add(comment_medewerker)
            
            comment_leverancier = ProjectFaseCommentaar(
                id=str(uuid.uuid4()),
                fase_id=fase_sloop.id,
                type=CommentaarType.COMAKER,
                status=CommentaarStatus.GEPUBLICEERD,
                onderwerp="Oplevering sloopwerk",
                bericht="Sloopwerkzaamheden zijn afgerond. Ruimte is opgeleverd en gereed voor de volgende fase.",
                auteur_id=user_leverancier_bouw.id,
                leverancier_id=leverancier_bouwbedrijf.id,
                gepubliceerd_op=datetime.now(timezone.utc) - timedelta(days=3)
            )
            db.add(comment_leverancier)
            
            comment_voortgang = ProjectFaseCommentaar(
                id=str(uuid.uuid4()),
                fase_id=fase_bouw.id,
                type=CommentaarType.MEDEWERKER,
                status=CommentaarStatus.GEPUBLICEERD,
                onderwerp="Voortgang bouwwerkzaamheden",
                bericht="De bouw ligt op schema. Verwachte oplevering over 3 weken.",
                auteur_id=user_controleur.id,
                leverancier_id=None,
                gepubliceerd_op=datetime.now(timezone.utc) - timedelta(days=1)
            )
            db.add(comment_voortgang)
            
            comment_lev_bouw = ProjectFaseCommentaar(
                id=str(uuid.uuid4()),
                fase_id=fase_bouw.id,
                type=CommentaarType.COMAKER,
                status=CommentaarStatus.GEPUBLICEERD,
                onderwerp="Materiaal vertraging",
                bericht="Let op: levering gipsplaten is 2 dagen vertraagd. Dit heeft geen gevolgen voor de planning.",
                auteur_id=user_leverancier_bouw.id,
                leverancier_id=leverancier_bouwbedrijf.id,
                gepubliceerd_op=datetime.now(timezone.utc)
            )
            db.add(comment_lev_bouw)
            
            db.flush()
            print(f"✅ Created 4 fase commentaren")
            
            # ============================================================
            # COMMIT ALLES
            # ============================================================
            db.commit()
            
            print("\n" + "="*60)
            print("✅ SEED DATA CREATED SUCCESSFULLY!")
            print("="*60)
            
            print("\n🔐 Test credentials:")
            print(f"   Projectleider: projectleider@comaker.cloud / Test1234!")
            print(f"   Beheerder:     beheerder@comaker.cloud / Test1234!")
            print(f"   Controleur:    controleur@comaker.cloud / Test1234!")
            print(f"   Admin:         admin@comaker.cloud / Test1234!")
            print(f"   Leverancier 1: jan@debouwer.nl / Test1234!")
            print(f"   Leverancier 2: maria@installatietech.nl / Test1234!")
            
            print("\n📊 Summary:")
            print(f"   • 2 Leveranciers")
            print(f"   • 6 Users (4 internal, 2 leveranciers)")
            print(f"   • 1 Project")
            print(f"   • 1 Contract")
            print(f"   • 5 Projectfases")
            print(f"   • 3 Documents (1 intern, 2 voor leverancier)")
            print(f"   • 4 Commentaren (2 medewerker, 2 leverancier)")
            
            print("\n🧪 Test scenarios:")
            print("   1. Login als jan@debouwer.nl → Zie alleen fases 2, 3, 5")
            print("   2. Login als maria@installatietech.nl → Zie alleen fase 4")
            print("   3. Leveranciers zien document 'Interne Kostenbegroting' NIET")
            print("   4. Beheerder ziet alles")
            
        else:
            print(f"ℹ️  Database already initialized with {existing_users} users")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        # RE-ENABLE HISTORIE TRACKING
        enable_historie_tracking(db)
        db.close()


if __name__ == "__main__":
    print("🚀 Initializing database...")
    print()
    init_db()
    print()
    print("✅ Done!")
