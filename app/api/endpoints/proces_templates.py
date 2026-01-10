"""
ProcesTemplate API Endpoints
============================

CRUD operaties voor:
- ProcesTemplates
- TemplateStappen
- TemplateDocumentSjablonen

Met rechten checks voor beheerders
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List, Optional
from pydantic import BaseModel
import uuid
from datetime import datetime, timezone

from app.db.session import get_db
from app.models.proces_template import (
    ProcesTemplate, TemplateStap, TemplateDocumentSjabloon,
    ProcesCategorie, TemplateStapStatus
)
from app.models.user import User, UserRole
from app.core.deps import get_current_user
from app.models.historie_setup import HistorieContext

router = APIRouter()


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class TemplateDocumentSjabloonBase(BaseModel):
    naam: str
    beschrijving: Optional[str] = None
    is_verplicht: bool = False
    verwacht_type: Optional[str] = None

class TemplateDocumentSjabloonCreate(TemplateDocumentSjabloonBase):
    pass

class TemplateDocumentSjabloonResponse(TemplateDocumentSjabloonBase):
    id: str
    stap_id: str

    class Config:
        from_attributes = True


class TemplateStapBase(BaseModel):
    stap_nummer: int
    naam: str
    beschrijving: Optional[str] = None
    default_status: TemplateStapStatus = TemplateStapStatus.NIET_GESTART
    geschatte_doorlooptijd_dagen: Optional[int] = None
    vereist_leverancier: bool = False
    instructies: Optional[str] = None

class TemplateStapCreate(TemplateStapBase):
    verwachte_documenten: List[TemplateDocumentSjabloonCreate] = []

class TemplateStapResponse(TemplateStapBase):
    id: str
    template_id: str
    verwachte_documenten: List[TemplateDocumentSjabloonResponse] = []

    class Config:
        from_attributes = True


class ProcesTemplateBase(BaseModel):
    naam: str
    beschrijving: Optional[str] = None
    categorie: ProcesCategorie
    is_actief: bool = True

class ProcesTemplateCreate(ProcesTemplateBase):
    stappen: List[TemplateStapCreate] = []

class ProcesTemplateUpdate(BaseModel):
    naam: Optional[str] = None
    beschrijving: Optional[str] = None
    categorie: Optional[ProcesCategorie] = None
    is_actief: Optional[bool] = None
    is_standaard: Optional[bool] = None

class ProcesTemplateResponse(ProcesTemplateBase):
    id: str
    is_standaard: bool
    aantal_keer_gebruikt: int
    gemaakt_door_id: str
    stappen: List[TemplateStapResponse] = []
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProcesTemplateListItem(BaseModel):
    id: str
    naam: str
    beschrijving: Optional[str] = None
    categorie: ProcesCategorie
    is_actief: bool
    is_standaard: bool
    aantal_keer_gebruikt: int
    aantal_stappen: int
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# HELPER FUNCTIONS - RECHTEN CHECKS
# ============================================================================

def check_admin_rights(user: User):
    """
    Check of user admin rechten heeft (beheerder of admin medewerker)
    """
    if user.role not in [UserRole.BEHEERDER, UserRole.ADMINISTRATIEF_MEDEWERKER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Je hebt geen rechten om templates te beheren"
        )


# ============================================================================
# ENDPOINTS - PROCES TEMPLATES
# ============================================================================

@router.get("/proces-templates", response_model=List[ProcesTemplateListItem])
def get_proces_templates(
    categorie: Optional[ProcesCategorie] = None,
    is_actief: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Haal alle proces templates op (met optionele filters)

    Iedereen mag templates bekijken
    """
    query = db.query(ProcesTemplate).options(
        joinedload(ProcesTemplate.stappen)
    )

    if categorie:
        query = query.filter(ProcesTemplate.categorie == categorie)

    if is_actief is not None:
        query = query.filter(ProcesTemplate.is_actief == is_actief)

    templates = query.order_by(
        ProcesTemplate.is_standaard.desc(),
        ProcesTemplate.naam
    ).all()

    # Map naar list items met aantal_stappen
    result = []
    for template in templates:
        result.append(ProcesTemplateListItem(
            id=template.id,
            naam=template.naam,
            beschrijving=template.beschrijving,
            categorie=template.categorie,
            is_actief=template.is_actief,
            is_standaard=template.is_standaard,
            aantal_keer_gebruikt=template.aantal_keer_gebruikt,
            aantal_stappen=len(template.stappen),
            created_at=template.created_at
        ))

    return result


@router.get("/proces-templates/{template_id}", response_model=ProcesTemplateResponse)
def get_proces_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Haal een specifieke proces template op (met alle stappen en document sjablonen)

    Iedereen mag templates bekijken
    """
    template = db.query(ProcesTemplate).options(
        joinedload(ProcesTemplate.stappen).joinedload(TemplateStap.verwachte_documenten)
    ).filter(ProcesTemplate.id == template_id).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template niet gevonden"
        )

    return template


@router.post("/proces-templates", response_model=ProcesTemplateResponse, status_code=status.HTTP_201_CREATED)
def create_proces_template(
    template_data: ProcesTemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Maak een nieuwe proces template aan

    Alleen beheerders mogen templates aanmaken
    """
    check_admin_rights(current_user)

    # Set historie context
    with HistorieContext(db, current_user.id, "Proces template aangemaakt"):
        # Check of naam al bestaat
        existing = db.query(ProcesTemplate).filter(
            ProcesTemplate.naam == template_data.naam
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template met naam '{template_data.naam}' bestaat al"
            )

        # Maak template aan
        template = ProcesTemplate(
            id=str(uuid.uuid4()),
            naam=template_data.naam,
            beschrijving=template_data.beschrijving,
            categorie=template_data.categorie,
            is_actief=template_data.is_actief,
            is_standaard=False,
            aantal_keer_gebruikt=0,
            gemaakt_door_id=current_user.id
        )
        db.add(template)
        db.flush()

        # Maak stappen aan
        for stap_data in template_data.stappen:
            stap = TemplateStap(
                id=str(uuid.uuid4()),
                template_id=template.id,
                stap_nummer=stap_data.stap_nummer,
                naam=stap_data.naam,
                beschrijving=stap_data.beschrijving,
                default_status=stap_data.default_status,
                geschatte_doorlooptijd_dagen=stap_data.geschatte_doorlooptijd_dagen,
                vereist_leverancier=stap_data.vereist_leverancier,
                instructies=stap_data.instructies
            )
            db.add(stap)
            db.flush()

            # Maak document sjablonen aan voor deze stap
            for doc_sjabloon_data in stap_data.verwachte_documenten:
                doc_sjabloon = TemplateDocumentSjabloon(
                    id=str(uuid.uuid4()),
                    template_id=template.id,
                    stap_id=stap.id,
                    naam=doc_sjabloon_data.naam,
                    beschrijving=doc_sjabloon_data.beschrijving,
                    is_verplicht=doc_sjabloon_data.is_verplicht,
                    verwacht_type=doc_sjabloon_data.verwacht_type
                )
                db.add(doc_sjabloon)

        db.commit()
        db.refresh(template)

        # Reload met alle relaties
        template = db.query(ProcesTemplate).options(
            joinedload(ProcesTemplate.stappen).joinedload(TemplateStap.verwachte_documenten)
        ).filter(ProcesTemplate.id == template.id).first()

        return template


@router.patch("/proces-templates/{template_id}", response_model=ProcesTemplateResponse)
def update_proces_template(
    template_id: str,
    template_data: ProcesTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update een proces template

    Alleen beheerders mogen templates updaten
    """
    check_admin_rights(current_user)

    template = db.query(ProcesTemplate).filter(
        ProcesTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template niet gevonden"
        )

    with HistorieContext(db, current_user.id, "Proces template aangepast"):
        # Update velden
        if template_data.naam is not None:
            # Check of nieuwe naam al bestaat
            existing = db.query(ProcesTemplate).filter(
                ProcesTemplate.naam == template_data.naam,
                ProcesTemplate.id != template_id
            ).first()

            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Template met naam '{template_data.naam}' bestaat al"
                )

            template.naam = template_data.naam

        if template_data.beschrijving is not None:
            template.beschrijving = template_data.beschrijving

        if template_data.categorie is not None:
            template.categorie = template_data.categorie

        if template_data.is_actief is not None:
            template.is_actief = template_data.is_actief

        if template_data.is_standaard is not None:
            # Als deze template standaard wordt, haal standaard weg bij anderen
            if template_data.is_standaard:
                db.query(ProcesTemplate).filter(
                    ProcesTemplate.id != template_id
                ).update({"is_standaard": False})

            template.is_standaard = template_data.is_standaard

        db.commit()
        db.refresh(template)

        # Reload met alle relaties
        template = db.query(ProcesTemplate).options(
            joinedload(ProcesTemplate.stappen).joinedload(TemplateStap.verwachte_documenten)
        ).filter(ProcesTemplate.id == template.id).first()

        return template


@router.delete("/proces-templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_proces_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Verwijder een proces template

    Alleen beheerders mogen templates verwijderen
    """
    check_admin_rights(current_user)

    template = db.query(ProcesTemplate).filter(
        ProcesTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template niet gevonden"
        )

    with HistorieContext(db, current_user.id, "Proces template verwijderd"):
        db.delete(template)
        db.commit()


@router.post("/proces-templates/{template_id}/set-standaard", response_model=ProcesTemplateResponse)
def set_standaard_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Maak een template de standaard template

    Alleen beheerders mogen de standaard template wijzigen
    """
    check_admin_rights(current_user)

    template = db.query(ProcesTemplate).filter(
        ProcesTemplate.id == template_id
    ).first()

    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template niet gevonden"
        )

    with HistorieContext(db, current_user.id, "Standaard template gewijzigd"):
        # Haal standaard weg bij alle andere templates
        db.query(ProcesTemplate).filter(
            ProcesTemplate.id != template_id
        ).update({"is_standaard": False})

        # Maak deze template standaard
        template.is_standaard = True

        db.commit()
        db.refresh(template)

        # Reload met alle relaties
        template = db.query(ProcesTemplate).options(
            joinedload(ProcesTemplate.stappen).joinedload(TemplateStap.verwachte_documenten)
        ).filter(ProcesTemplate.id == template.id).first()

        return template
