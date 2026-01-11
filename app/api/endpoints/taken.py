"""
Mijn Taken (My Tasks) endpoints
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime, timedelta, timezone
from typing import List

from app.db.session import get_db
from app.models.user import User
from app.models.projectfase import ProjectFase, ProjectFaseStatus, ProjectFaseDocument
from app.models.project import Project
from app.schemas.taken import MijnTakenResponse, TaakItem
from app.core.deps import get_current_user

router = APIRouter(tags=["Mijn Taken"])


def calculate_priority(deadline: datetime = None) -> str:
    """
    Calculate priority based on deadline
    - Hoog: deadline binnen 3 dagen of verlopen
    - Middel: deadline binnen 7 dagen
    - Laag: deadline > 7 dagen of geen deadline
    """
    if not deadline:
        return "laag"

    now = datetime.now(timezone.utc)
    days_until_deadline = (deadline - now).days

    if days_until_deadline <= 3:
        return "hoog"
    elif days_until_deadline <= 7:
        return "middel"
    else:
        return "laag"


@router.get("/me/taken", response_model=MijnTakenResponse)
def get_mijn_taken(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current user's tasks

    Returns:
    - open_fases: Fases waar gebruiker verantwoordelijke is EN status != AFGEROND
    - wacht_op_acceptatie: Fases die wachten op acceptatie (voor beheerders/projectleiders)
    - binnenkort_verlopen: Deadlines binnen 7 dagen
    - missende_documenten: Fases zonder documenten
    """

    # 1. OPEN FASES - waar gebruiker verantwoordelijke is
    open_fases_query = db.query(ProjectFase).join(
        Project, ProjectFase.project_id == Project.id
    ).filter(
        and_(
            ProjectFase.verantwoordelijke_id == current_user.id,
            ProjectFase.status != ProjectFaseStatus.AFGEROND
        )
    ).all()

    open_fases = []
    for fase in open_fases_query:
        open_fases.append(TaakItem(
            fase_id=fase.id,
            project_id=fase.project.id,
            project_naam=fase.project.naam,
            project_nummer=fase.project.project_nummer,
            fase_naam=fase.naam,
            fase_nummer=fase.fase_nummer,
            deadline=fase.geplande_eind_datum,
            status=fase.status.value,
            prioriteit=calculate_priority(fase.geplande_eind_datum),
            type="open_fase",
            beschrijving=f"Verantwoordelijk voor {fase.naam}"
        ))

    # 2. WACHT OP ACCEPTATIE - fases in review status (alleen voor beheerders/projectleiders)
    wacht_op_acceptatie = []
    if current_user.role in ['beheerder', 'projectleider', 'controleur']:
        acceptatie_query = db.query(ProjectFase).join(
            Project, ProjectFase.project_id == Project.id
        ).filter(
            ProjectFase.status == ProjectFaseStatus.IN_REVIEW
        ).all()

        for fase in acceptatie_query:
            # Voor projectleiders: alleen hun eigen projecten
            if current_user.role == 'projectleider':
                if fase.project.projectleider_id != current_user.id:
                    continue

            wacht_op_acceptatie.append(TaakItem(
                fase_id=fase.id,
                project_id=fase.project.id,
                project_naam=fase.project.naam,
                project_nummer=fase.project.project_nummer,
                fase_naam=fase.naam,
                fase_nummer=fase.fase_nummer,
                deadline=fase.geplande_eind_datum,
                status=fase.status.value,
                prioriteit=calculate_priority(fase.geplande_eind_datum),
                type="wacht_op_acceptatie",
                beschrijving=f"Wacht op goedkeuring voor {fase.naam}"
            ))

    # 3. BINNENKORT VERLOPEN - deadlines binnen 7 dagen
    seven_days_from_now = datetime.now(timezone.utc) + timedelta(days=7)

    binnenkort_verlopen_query = db.query(ProjectFase).join(
        Project, ProjectFase.project_id == Project.id
    ).filter(
        and_(
            ProjectFase.verantwoordelijke_id == current_user.id,
            ProjectFase.status != ProjectFaseStatus.AFGEROND,
            ProjectFase.geplande_eind_datum.isnot(None),
            ProjectFase.geplande_eind_datum <= seven_days_from_now
        )
    ).order_by(ProjectFase.geplande_eind_datum.asc()).all()

    binnenkort_verlopen = []
    for fase in binnenkort_verlopen_query:
        binnenkort_verlopen.append(TaakItem(
            fase_id=fase.id,
            project_id=fase.project.id,
            project_naam=fase.project.naam,
            project_nummer=fase.project.project_nummer,
            fase_naam=fase.naam,
            fase_nummer=fase.fase_nummer,
            deadline=fase.geplande_eind_datum,
            status=fase.status.value,
            prioriteit=calculate_priority(fase.geplande_eind_datum),
            type="deadline",
            beschrijving=f"Deadline voor {fase.naam}"
        ))

    # 4. MISSENDE DOCUMENTEN - fases zonder documenten (in uitvoering of in review)
    missende_documenten_query = db.query(ProjectFase).join(
        Project, ProjectFase.project_id == Project.id
    ).outerjoin(
        ProjectFaseDocument, ProjectFase.id == ProjectFaseDocument.fase_id
    ).filter(
        and_(
            ProjectFase.verantwoordelijke_id == current_user.id,
            ProjectFase.status.in_([ProjectFaseStatus.IN_UITVOERING, ProjectFaseStatus.IN_REVIEW]),
            ProjectFaseDocument.id.is_(None)  # No documents
        )
    ).all()

    missende_documenten = []
    for fase in missende_documenten_query:
        missende_documenten.append(TaakItem(
            fase_id=fase.id,
            project_id=fase.project.id,
            project_naam=fase.project.naam,
            project_nummer=fase.project.project_nummer,
            fase_naam=fase.naam,
            fase_nummer=fase.fase_nummer,
            deadline=fase.geplande_eind_datum,
            status=fase.status.value,
            prioriteit="middel",
            type="missend_document",
            beschrijving=f"Geen documenten geüpload voor {fase.naam}"
        ))

    # Calculate total
    totaal = len(open_fases) + len(wacht_op_acceptatie) + len(binnenkort_verlopen) + len(missende_documenten)

    return MijnTakenResponse(
        open_fases=open_fases,
        wacht_op_acceptatie=wacht_op_acceptatie,
        binnenkort_verlopen=binnenkort_verlopen,
        missende_documenten=missende_documenten,
        totaal_aantal=totaal
    )
