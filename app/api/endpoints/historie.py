"""
Historie API Endpoints
======================

Endpoints om historie/versiebeheer op te vragen
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.historie import (
    HistorieRecord,
    get_record_historie,
    get_record_versie,
    compare_versies,
    get_user_activiteit,
    get_tabel_activiteit,
    get_recent_changes
)
# from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()


# ============================================================================
# RECORD HISTORIE
# ============================================================================

@router.get("/{tabel_naam}/{record_id}/historie")
def get_historie(
    tabel_naam: str,
    record_id: str,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """
    Haal alle historie van een specifiek record op
    
    Bijvoorbeeld:
    - GET /historie/projects/abc-123/historie
    - GET /historie/contracts/xyz-789/historie
    """
    historie = get_record_historie(db, tabel_naam, record_id)
    
    if not historie:
        raise HTTPException(status_code=404, detail="Geen historie gevonden")
    
    return [
        {
            "id": h.id,
            "versie_nummer": h.versie_nummer,
            "actie": h.actie,
            "gewijzigd_door_id": h.gewijzigd_door_id,
            "gewijzigd_op": h.gewijzigd_op,
            "opmerking": h.opmerking,
            # data_voor en data_na zijn soms groot, alleen returnen als gevraagd
        }
        for h in historie
    ]


@router.get("/{tabel_naam}/{record_id}/historie/{versie}")
def get_versie(
    tabel_naam: str,
    record_id: str,
    versie: int,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """
    Haal een specifieke versie van een record op
    
    Bijvoorbeeld:
    - GET /historie/projects/abc-123/historie/3
      → Geeft versie 3 van project abc-123
    """
    data = get_record_versie(db, tabel_naam, record_id, versie)
    
    if not data:
        raise HTTPException(status_code=404, detail=f"Versie {versie} niet gevonden")
    
    return {
        "tabel_naam": tabel_naam,
        "record_id": record_id,
        "versie": versie,
        "data": data
    }


@router.get("/{tabel_naam}/{record_id}/compare")
def compare(
    tabel_naam: str,
    record_id: str,
    versie1: int = Query(..., description="Eerste versie om te vergelijken"),
    versie2: int = Query(..., description="Tweede versie om te vergelijken"),
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """
    Vergelijk twee versies van een record
    
    Bijvoorbeeld:
    - GET /historie/contracts/xyz-789/compare?versie1=2&versie2=5
      → Vergelijk versie 2 met versie 5
    """
    verschillen = compare_versies(db, tabel_naam, record_id, versie1, versie2)
    
    if verschillen is None:
        raise HTTPException(status_code=404, detail="Een of beide versies niet gevonden")
    
    return {
        "tabel_naam": tabel_naam,
        "record_id": record_id,
        "versie1": versie1,
        "versie2": versie2,
        "verschillen": verschillen,
        "aantal_verschillen": len(verschillen)
    }


# ============================================================================
# AUDIT / ACTIVITEIT QUERIES
# ============================================================================

@router.get("/activiteit/gebruiker/{user_id}")
def get_gebruiker_activiteit(
    user_id: str,
    limit: int = Query(50, le=200, description="Aantal records (max 200)"),
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """
    Haal recente activiteit van een gebruiker op
    
    Bijvoorbeeld:
    - GET /historie/activiteit/gebruiker/user-123?limit=100
    """
    # TODO: Check rechten - alleen beheerders of de gebruiker zelf
    
    activiteit = get_user_activiteit(db, user_id, limit)
    
    return [
        {
            "id": a.id,
            "tabel_naam": a.tabel_naam,
            "record_id": a.record_id,
            "versie_nummer": a.versie_nummer,
            "actie": a.actie,
            "gewijzigd_op": a.gewijzigd_op,
            "opmerking": a.opmerking
        }
        for a in activiteit
    ]


@router.get("/activiteit/tabel/{tabel_naam}")
def get_table_activiteit(
    tabel_naam: str,
    limit: int = Query(100, le=500, description="Aantal records (max 500)"),
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """
    Haal recente activiteit van een tabel op
    
    Bijvoorbeeld:
    - GET /historie/activiteit/tabel/contracts?limit=50
    """
    activiteit = get_tabel_activiteit(db, tabel_naam, limit)
    
    return [
        {
            "id": a.id,
            "record_id": a.record_id,
            "versie_nummer": a.versie_nummer,
            "actie": a.actie,
            "gewijzigd_door_id": a.gewijzigd_door_id,
            "gewijzigd_op": a.gewijzigd_op,
            "opmerking": a.opmerking
        }
        for a in activiteit
    ]


@router.get("/activiteit/recent")
def get_recente_wijzigingen(
    hours: int = Query(24, le=168, description="Aantal uren terug (max 168 = 1 week)"),
    tabel_naam: Optional[str] = Query(None, description="Filter op specifieke tabel"),
    actie: Optional[str] = Query(None, description="Filter op actie (create/update/delete)"),
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """
    Haal alle recente wijzigingen op
    
    Bijvoorbeeld:
    - GET /historie/activiteit/recent?hours=48
    - GET /historie/activiteit/recent?hours=24&tabel_naam=contracts
    - GET /historie/activiteit/recent?actie=delete
    """
    # TODO: Check rechten - alleen beheerders
    
    changes = get_recent_changes(db, hours)
    
    # Filter op tabel_naam indien opgegeven
    if tabel_naam:
        changes = [c for c in changes if c.tabel_naam == tabel_naam]
    
    # Filter op actie indien opgegeven
    if actie:
        changes = [c for c in changes if c.actie == actie]
    
    return [
        {
            "id": c.id,
            "tabel_naam": c.tabel_naam,
            "record_id": c.record_id,
            "versie_nummer": c.versie_nummer,
            "actie": c.actie,
            "gewijzigd_door_id": c.gewijzigd_door_id,
            "gewijzigd_op": c.gewijzigd_op,
            "opmerking": c.opmerking
        }
        for c in changes
    ]


# ============================================================================
# STATISTIEKEN
# ============================================================================

@router.get("/stats/overview")
def get_historie_stats(
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """
    Haal algemene statistieken op over historie
    
    Bijvoorbeeld:
    - GET /historie/stats/overview
    """
    # TODO: Check rechten - alleen beheerders
    
    # Totaal aantal wijzigingen
    total_changes = db.query(HistorieRecord).count()
    
    # Wijzigingen per tabel
    from sqlalchemy import func as sql_func
    changes_per_table = db.query(
        HistorieRecord.tabel_naam,
        sql_func.count(HistorieRecord.id).label('count')
    ).group_by(HistorieRecord.tabel_naam).all()
    
    # Wijzigingen per actie
    changes_per_action = db.query(
        HistorieRecord.actie,
        sql_func.count(HistorieRecord.id).label('count')
    ).group_by(HistorieRecord.actie).all()
    
    # Meest actieve gebruikers
    most_active_users = db.query(
        HistorieRecord.gewijzigd_door_id,
        sql_func.count(HistorieRecord.id).label('count')
    ).filter(
        HistorieRecord.gewijzigd_door_id.isnot(None)
    ).group_by(HistorieRecord.gewijzigd_door_id).order_by(
        sql_func.count(HistorieRecord.id).desc()
    ).limit(10).all()
    
    # Recente activiteit (laatste 24 uur)
    recent_count = db.query(HistorieRecord).filter(
        HistorieRecord.gewijzigd_op >= datetime.now() - timedelta(hours=24)
    ).count()
    
    return {
        "totaal_wijzigingen": total_changes,
        "per_tabel": {t: c for t, c in changes_per_table},
        "per_actie": {a: c for a, c in changes_per_action},
        "meest_actieve_gebruikers": [
            {"user_id": u, "aantal": c} for u, c in most_active_users
        ],
        "laatste_24_uur": recent_count
    }


@router.get("/stats/tabel/{tabel_naam}")
def get_tabel_stats(
    tabel_naam: str,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """
    Haal statistieken op voor een specifieke tabel
    
    Bijvoorbeeld:
    - GET /historie/stats/tabel/contracts
    """
    from sqlalchemy import func as sql_func
    
    # Totaal wijzigingen voor deze tabel
    total = db.query(HistorieRecord).filter(
        HistorieRecord.tabel_naam == tabel_naam
    ).count()
    
    # Per actie
    per_action = db.query(
        HistorieRecord.actie,
        sql_func.count(HistorieRecord.id).label('count')
    ).filter(
        HistorieRecord.tabel_naam == tabel_naam
    ).group_by(HistorieRecord.actie).all()
    
    # Gemiddeld aantal versies per record
    avg_versions = db.query(
        sql_func.avg(HistorieRecord.versie_nummer)
    ).filter(
        HistorieRecord.tabel_naam == tabel_naam
    ).scalar()
    
    # Max versie nummer
    max_version = db.query(
        sql_func.max(HistorieRecord.versie_nummer)
    ).filter(
        HistorieRecord.tabel_naam == tabel_naam
    ).scalar()
    
    return {
        "tabel_naam": tabel_naam,
        "totaal_wijzigingen": total,
        "per_actie": {a: c for a, c in per_action},
        "gemiddeld_versies": round(float(avg_versions or 0), 2),
        "max_versie_nummer": max_version or 0
    }
