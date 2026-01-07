"""
ProjectFase API Endpoints
=========================

CRUD operaties voor:
- ProjectFases
- ProjectFaseDocumenten (MET FILE UPLOAD)
- ProjectFaseCommentaren

Met ingebouwde rechten checks!
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import os
import shutil
from pathlib import Path

from app.db.session import get_db
from app.models.projectfase import (
    ProjectFase, ProjectFaseDocument, ProjectFaseCommentaar,
    ProjectFaseStatus, DocumentType, CommentaarType, CommentaarStatus
)
from app.models.user import User, UserRole

#ten behoeve van authenticatie
from app.core.deps import get_current_user
from app.models.historie_setup import HistorieContext

router = APIRouter()

# ============================================================================
# CONFIGURATIE
# ============================================================================

UPLOAD_DIR = Path("./uploads/documenten")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


# ============================================================================
# HELPER FUNCTIONS - RECHTEN CHECKS
# ============================================================================

def check_fase_toegang(fase: ProjectFase, user: User) -> bool:
    """
    Check of user toegang heeft tot deze fase
    
    - Beheerders: altijd toegang
    - Projectleiders: toegang tot hun projecten
    - Medewerkers: toegang tot hun projecten
    - Leveranciers: ALLEEN toegang als leverancier_id = hun leverancier
    """
    if user.role == UserRole.BEHEERDER:
        return True
    
    if user.role == UserRole.LEVERANCIER:
        # Leverancier mag alleen fases zien waar hij aan gekoppeld is
        if not user.leverancier_id:
            # User heeft LEVERANCIER role maar geen leverancier_id → geen toegang
            return False
        
        # Check of fase aan deze leverancier is toegewezen
        return fase.leverancier_id == user.leverancier_id
    
    # Medewerkers en projectleiders hebben toegang
    return True


def check_document_toegang(document: ProjectFaseDocument, user: User) -> bool:
    """
    Check of user dit document mag zien
    
    - Beheerders: altijd
    - Medewerkers: altijd
    - Leveranciers: alleen als zichtbaar_voor_leverancier = True
    """
    if user.role == UserRole.BEHEERDER:
        return True
    
    if user.role != UserRole.LEVERANCIER:
        return True
    
    # Leverancier: check zichtbaarheid flag
    return document.zichtbaar_voor_leverancier


def check_commentaar_edit_rechten(commentaar: ProjectFaseCommentaar, user: User) -> bool:
    """
    Check of user dit commentaar mag bewerken
    
    - Beheerders: altijd
    - Auteur: eigen commentaar
    - Anderen: nee
    """
    if user.role == UserRole.BEHEERDER:
        return True
    
    return commentaar.auteur_id == user.id


# ============================================================================
# PROJECTFASE ENDPOINTS
# ============================================================================

@router.get("/projects/{project_id}/fases", response_model=List[dict])
def get_project_fases(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Authenticatie
):
    """
    Haal alle fases van een project op
    """
    fases = db.query(ProjectFase).filter(
        ProjectFase.project_id == project_id
    ).order_by(ProjectFase.fase_nummer).all()
    
    # Filter op basis van user rechten
    if current_user.role == UserRole.LEVERANCIER:
        fases = [f for f in fases if check_fase_toegang(f, current_user)]
    
    return [
        {
            "id": f.id,
            "fase_nummer": f.fase_nummer,
            "naam": f.naam,
            "beschrijving": f.beschrijving,
            "status": f.status,
            "verantwoordelijke_id": f.verantwoordelijke_id,
            "leverancier_id": f.leverancier_id,
            "geplande_start_datum": f.geplande_start_datum,
            "geplande_eind_datum": f.geplande_eind_datum,
            "werkelijke_start_datum": f.werkelijke_start_datum,
            "werkelijke_eind_datum": f.werkelijke_eind_datum,
            "aantal_documenten": len(f.documenten),
            "aantal_commentaren": len(f.commentaren),
        }
        for f in fases
    ]


@router.post("/projects/{project_id}/fases", status_code=status.HTTP_201_CREATED)
def create_project_fase(
    project_id: str,
    fase_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Maak nieuwe projectfase aan
    """
    # Check rechten (alleen beheerder/projectleider)
    if current_user.role not in [UserRole.BEHEERDER, UserRole.PROJECTLEIDER]:
        raise HTTPException(
            status_code=403, 
            detail="Alleen beheerders en projectleiders mogen fases aanmaken"
        )
    
    # SET CONTEXT
    HistorieContext.set_user_id(current_user.id)
    HistorieContext.set_opmerking("Fase aangemaakt via API")
    
    fase = ProjectFase(
        id=str(uuid.uuid4()),
        project_id=project_id,
        fase_nummer=fase_data.get("fase_nummer"),
        naam=fase_data.get("naam"),
        beschrijving=fase_data.get("beschrijving"),
        status=fase_data.get("status", ProjectFaseStatus.NIET_GESTART),
        verantwoordelijke_id=fase_data.get("verantwoordelijke_id"),
        leverancier_id=fase_data.get("leverancier_id"),
        geplande_start_datum=fase_data.get("geplande_start_datum"),
        geplande_eind_datum=fase_data.get("geplande_eind_datum"),
    )
    
    db.add(fase)
    db.commit()
    db.refresh(fase)
    
    HistorieContext.clear()
    
    return {"message": "Fase aangemaakt", "id": fase.id}


@router.put("/fases/{fase_id}")
def update_project_fase(
    fase_id: str,
    fase_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update projectfase
    """
    fase = db.query(ProjectFase).filter(ProjectFase.id == fase_id).first()
    if not fase:
        raise HTTPException(status_code=404, detail="Fase niet gevonden")
    
    # Check rechten
    if not check_fase_toegang(fase, current_user):
        raise HTTPException(status_code=403, detail="Geen toegang tot deze fase")

    # Alleen beheerder en projectleider mogen wijzigen
    if current_user.role not in [UserRole.BEHEERDER, UserRole.PROJECTLEIDER]:
        raise HTTPException(
            status_code=403,
            detail="Alleen beheerders en projectleiders mogen fases wijzigen"
        )
    
    # SET CONTEXT 
    HistorieContext.set_user_id(current_user.id)
    HistorieContext.set_opmerking("Fase bijgewerkt via API")
    
    # Update fields
    for key, value in fase_data.items():
        if hasattr(fase, key):
            setattr(fase, key, value)
    
    db.commit()
    HistorieContext.clear()

    return {
        "message": "Fase bijgewerkt",
        "versie": fase.versie_nummer
    }


# ============================================================================
# DOCUMENT ENDPOINTS - MET FILE UPLOAD
# ============================================================================

@router.get("/fases/{fase_id}/documenten")
def get_fase_documenten(
    fase_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Haal alle documenten van een fase op
    
    Filtert automatisch op basis van rechten!
    """
    fase = db.query(ProjectFase).filter(ProjectFase.id == fase_id).first()
    if not fase:
        raise HTTPException(status_code=404, detail="Fase niet gevonden")
    
    if not check_fase_toegang(fase, current_user):
        raise HTTPException(status_code=403, detail="Geen toegang tot deze fase")
    
    documenten = fase.documenten
    
    # Filter op basis van user rechten (leveranciers zien niet alle documenten)
    if current_user.role == UserRole.LEVERANCIER:
        documenten = [d for d in documenten if check_document_toegang(d, current_user)]
    
    return [
        {
            "id": d.id,
            "naam": d.naam,
            "beschrijving": d.beschrijving,
            "type": d.type,
            "bestandsnaam": d.bestandsnaam,
            "bestandstype": d.bestandstype,
            "bestandsgrootte_mb": d.bestandsgrootte_mb,
            "versie": d.versie,
            "is_definitief": d.is_definitief,
            "geupload_door_id": d.geupload_door_id,
            "upload_datum": d.upload_datum,
            "zichtbaar_voor_leverancier": d.zichtbaar_voor_leverancier,
        }
        for d in documenten
    ]


@router.post("/fases/{fase_id}/documenten", status_code=status.HTTP_201_CREATED)
async def upload_fase_document(
    fase_id: str,
    file: UploadFile = File(...),
    naam: str = Form(...),
    beschrijving: Optional[str] = Form(None),
    type: str = Form("anders"),
    versie: str = Form("1.0"),
    is_definitief: bool = Form(False),
    zichtbaar_voor_leverancier: bool = Form(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Authenticatie
):
    """Upload document naar fase met ECHTE FILE UPLOAD"""
    
    # Check of fase bestaat
    fase = db.query(ProjectFase).filter(ProjectFase.id == fase_id).first()
    if not fase:
        raise HTTPException(status_code=404, detail="Fase niet gevonden")
    
    # Check file size
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400, 
            detail=f"Bestand te groot. Maximum {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # Genereer unieke bestandsnaam
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_extension = Path(file.filename).suffix
    unique_filename = f"{fase_id}_{timestamp}_{naam[:50]}{file_extension}"
    safe_filename = "".join(c for c in unique_filename if c.isalnum() or c in "._-")
    
    # Opslag pad
    file_path = UPLOAD_DIR / safe_filename
    
    try:
        # Sla bestand op
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Maak database record
        document = ProjectFaseDocument(
            id=str(uuid.uuid4()),
            fase_id=fase_id,
            naam=naam,
            beschrijving=beschrijving,
            type=type,
            bestandsnaam=safe_filename,
            bestandstype=file_extension.lstrip('.'),
            bestandsgrootte=file_size,
            opslag_type="local",
            opslag_pad=str(file_path),
            versie=versie,
            is_definitief=is_definitief,
            geupload_door_id=current_user.id,
            zichtbaar_voor_leverancier=zichtbaar_voor_leverancier
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        return {
            "id": document.id,
            "naam": document.naam,
            "bestandsnaam": document.bestandsnaam,
            "bestandsgrootte_mb": document.bestandsgrootte_mb,
            "message": "Document succesvol geüpload"
        }
        
    except Exception as e:
        # Cleanup bij fout
        if file_path.exists():
            file_path.unlink()
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/documenten/{document_id}/download")
async def download_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Download een document
    
    Retourneert het fysieke bestand voor download
    """
    document = db.query(ProjectFaseDocument).filter(
        ProjectFaseDocument.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document niet gevonden")
    
    # ✅ NIEUWE CHECK: Rechten controle
    if not check_document_toegang(document, current_user):
        raise HTTPException(status_code=403, detail="Geen toegang tot dit document")

    # Check fase toegang
    fase = db.query(ProjectFase).filter(ProjectFase.id == document.fase_id).first()
    if fase and not check_fase_toegang(fase, current_user):
        raise HTTPException(status_code=403, detail="Geen toegang tot deze fase")

    # Check opslag_pad ipv bestandspad
    file_path = Path(document.opslag_pad)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Bestand niet gevonden op server")
    
    return FileResponse(
        path=str(file_path),
        filename=document.bestandsnaam,
        media_type="application/octet-stream"
    )


@router.delete("/documenten/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verwijder een document
    
    Verwijdert zowel het fysieke bestand als de database record
    """
    document = db.query(ProjectFaseDocument).filter(
        ProjectFaseDocument.id == document_id
    ).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document niet gevonden")
    
    # ✅ NIEUWE CHECK: Alleen uploader of beheerder mag verwijderen
    if current_user.role != UserRole.BEHEERDER and document.geupload_door_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Alleen de uploader of een beheerder mag dit document verwijderen"
        )
    
    # Check fase toegang
    fase = db.query(ProjectFase).filter(ProjectFase.id == document.fase_id).first()
    if fase and not check_fase_toegang(fase, current_user):
        raise HTTPException(status_code=403, detail="Geen toegang tot deze fase")

    try:
        # Check opslag_pad ipv bestandspad
        file_path = Path(document.opslag_pad)
        if file_path.exists():
            file_path.unlink()
        
        # Verwijder database record
        db.delete(document)
        db.commit()
        
        return None
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

# ============================================================================
# COMMENTAAR ENDPOINTS
# ============================================================================

@router.get("/fases/{fase_id}/commentaren")
def get_fase_commentaren(
    fase_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Haal alle commentaren van een fase op
    
    Beide types (medewerker & comaker) zijn zichtbaar voor iedereen
    """
    fase = db.query(ProjectFase).filter(ProjectFase.id == fase_id).first()
    if not fase:
        raise HTTPException(status_code=404, detail="Fase niet gevonden")
    
    # Filter alleen gepubliceerde commentaren
    commentaren = [c for c in fase.commentaren if c.is_gepubliceerd]
    
    return [
        {
            "id": c.id,
            "type": c.type,
            "status": c.status,
            "onderwerp": c.onderwerp,
            "bericht": c.bericht,
            "auteur_id": c.auteur_id,
            "leverancier_id": c.leverancier_id,
            "parent_commentaar_id": c.parent_commentaar_id,
            "gepubliceerd_op": c.gepubliceerd_op,
            "bewerkt_op": c.bewerkt_op,
            "aantal_reacties": len(c.reacties) if hasattr(c, 'reacties') else 0,
        }
        for c in commentaren
    ]


@router.post("/fases/{fase_id}/commentaren", status_code=status.HTTP_201_CREATED)
def create_fase_commentaar(
    fase_id: str,
    commentaar_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Maak nieuw commentaar aan
    
    Type wordt automatisch bepaald op basis van user role:
    - UserRole.LEVERANCIER → CommentaarType.COMAKER
    - Andere roles → CommentaarType.MEDEWERKER
    """
    fase = db.query(ProjectFase).filter(ProjectFase.id == fase_id).first()
    if not fase:
        raise HTTPException(status_code=404, detail="Fase niet gevonden")
    
    # Bepaal type op basis van user role
    commentaar_type = (
        CommentaarType.COMAKER 
        if current_user.role == UserRole.LEVERANCIER 
        else CommentaarType.MEDEWERKER
    )
    
    # SET CONTEXT
    HistorieContext.set_user_id(current_user.id)
    HistorieContext.set_opmerking("Commentaar toegevoegd via API")
    
    commentaar = ProjectFaseCommentaar(
        id=str(uuid.uuid4()),
        fase_id=fase_id,
        type=commentaar_type,
        status=CommentaarStatus.GEPUBLICEERD,
        onderwerp=commentaar_data.get("onderwerp"),
        bericht=commentaar_data.get("bericht"),
        auteur_id=current_user.id,
        leverancier_id=commentaar_data.get("leverancier_id"),  # alleen voor comakers
        parent_commentaar_id=commentaar_data.get("parent_commentaar_id"),
        gepubliceerd_op=datetime.now(timezone.utc),
    )
    
    db.add(commentaar)
    db.commit()
    
    HistorieContext.clear()
    
    return {"message": "Commentaar toegevoegd", "id": commentaar.id}


@router.put("/commentaren/{commentaar_id}")
def update_commentaar(
    commentaar_id: str,
    commentaar_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update commentaar
    
    Alleen auteur of beheerder mag bewerken!
    """
    commentaar = db.query(ProjectFaseCommentaar).filter(
        ProjectFaseCommentaar.id == commentaar_id
    ).first()
    
    if not commentaar:
        raise HTTPException(status_code=404, detail="Commentaar niet gevonden")
    
    # Check rechten
    if not check_commentaar_edit_rechten(commentaar, current_user):
        raise HTTPException(status_code=403, detail="Geen rechten om dit commentaar te bewerken")

    # SET CONTEXT 
    HistorieContext.set_user_id(current_user.id)
    HistorieContext.set_opmerking("Commentaar bijgewerkt via API")
    
    # Update fields
    if "bericht" in commentaar_data:
        commentaar.bericht = commentaar_data["bericht"]
    if "onderwerp" in commentaar_data:
        commentaar.onderwerp = commentaar_data["onderwerp"]
    
    commentaar.bewerkt_op = datetime.now(timezone.utc)
    
    db.commit()

    HistorieContext.clear()

    return {
        "message": "Commentaar bijgewerkt",
        "versie": commentaar.versie_nummer
    }


@router.delete("/commentaren/{commentaar_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_commentaar(
    commentaar_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verwijder commentaar
    
    Alleen auteur of beheerder mag verwijderen!
    """
    commentaar = db.query(ProjectFaseCommentaar).filter(
        ProjectFaseCommentaar.id == commentaar_id
    ).first()
    
    if not commentaar:
        raise HTTPException(status_code=404, detail="Commentaar niet gevonden")
    
    # Check rechten
    if not check_commentaar_edit_rechten(commentaar, current_user):
        raise HTTPException(status_code=403, detail="Geen rechten om dit commentaar te verwijderen")

    db.delete(commentaar)
    db.commit()
    
    return None
