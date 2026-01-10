"""
Vestigingen endpoints - Complete CRUD
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.vestiging import Vestiging
from app.models.historie_setup import HistorieContext

router = APIRouter(tags=["Vestigingen"])


@router.get("/vestigingen")
def list_vestigingen(
    page: int = 1,
    limit: int = 25,
    search: Optional[str] = None,
    actief: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List vestigingen with pagination and filters
    """
    try:
        # Base query
        query = db.query(Vestiging)

        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Vestiging.naam.ilike(search_term)) |
                (Vestiging.code.ilike(search_term)) |
                (Vestiging.adres_plaats.ilike(search_term))
            )

        if actief is not None:
            query = query.filter(Vestiging.is_actief == actief)

        # Count total
        total = query.count()

        # Pagination
        offset = (page - 1) * limit
        vestigingen = query.order_by(Vestiging.naam).offset(offset).limit(limit).all()

        # Format response
        vestiging_list = []
        for v in vestigingen:
            try:
                vestiging_data = {
                    "id": v.id,
                    "naam": v.naam,
                    "code": v.code,
                    "adres": {
                        "straat": v.adres_straat,
                        "huisnummer": v.adres_huisnummer,
                        "postcode": v.adres_postcode,
                        "plaats": v.adres_plaats,
                        "land": v.adres_land,
                        "volledig": v.volledig_adres
                    },
                    "telefoon": v.telefoon,
                    "email": v.email,
                    "notities": v.notities,
                    "is_actief": v.is_actief,
                    "versie_nummer": v.versie_nummer,
                    "created_at": v.created_at.isoformat() if v.created_at else None,
                    "updated_at": v.updated_at.isoformat() if v.updated_at else None
                }
                vestiging_list.append(vestiging_data)
            except Exception as e:
                print(f"Error formatting vestiging {v.id}: {e}")
                continue

        return {
            "items": vestiging_list,
            "total": total,
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit
        }

    except Exception as e:
        print(f"Error listing vestigingen: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing vestigingen: {str(e)}"
        )


@router.get("/vestigingen/{vestiging_id}")
def get_vestiging(
    vestiging_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get vestiging by ID
    """
    vestiging = db.query(Vestiging).filter(Vestiging.id == vestiging_id).first()

    if not vestiging:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Vestiging {vestiging_id} niet gevonden"
        )

    return {
        "id": vestiging.id,
        "naam": vestiging.naam,
        "code": vestiging.code,
        "adres": {
            "straat": vestiging.adres_straat,
            "huisnummer": vestiging.adres_huisnummer,
            "postcode": vestiging.adres_postcode,
            "plaats": vestiging.adres_plaats,
            "land": vestiging.adres_land,
            "volledig": vestiging.volledig_adres
        },
        "telefoon": vestiging.telefoon,
        "email": vestiging.email,
        "notities": vestiging.notities,
        "is_actief": vestiging.is_actief,
        "versie_nummer": vestiging.versie_nummer,
        "created_at": vestiging.created_at.isoformat() if vestiging.created_at else None,
        "updated_at": vestiging.updated_at.isoformat() if vestiging.updated_at else None
    }


@router.post("/vestigingen")
def create_vestiging(
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new vestiging
    """
    try:
        # Check required fields
        required_fields = ["naam", "code", "adres_plaats"]
        for field in required_fields:
            if field not in data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Veld '{field}' is verplicht"
                )

        # Check unique code
        existing = db.query(Vestiging).filter(Vestiging.code == data["code"]).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Code '{data['code']}' is al in gebruik"
            )

        # Create vestiging
        vestiging = Vestiging(
            id=f"ves_{uuid.uuid4().hex[:8]}",
            naam=data["naam"],
            code=data["code"],
            adres_straat=data.get("adres_straat"),
            adres_huisnummer=data.get("adres_huisnummer"),
            adres_postcode=data.get("adres_postcode"),
            adres_plaats=data["adres_plaats"],
            adres_land=data.get("adres_land", "Nederland"),
            telefoon=data.get("telefoon"),
            email=data.get("email"),
            notities=data.get("notities"),
            is_actief=data.get("is_actief", True),
            versie_nummer=1
        )

        # Set historie context
        with HistorieContext(db, current_user.id, "create", "vestiging", vestiging.id):
            db.add(vestiging)
            db.commit()
            db.refresh(vestiging)

        return {
            "id": vestiging.id,
            "naam": vestiging.naam,
            "code": vestiging.code,
            "message": "Vestiging succesvol aangemaakt"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error creating vestiging: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating vestiging: {str(e)}"
        )


@router.put("/vestigingen/{vestiging_id}")
def update_vestiging(
    vestiging_id: str,
    data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update vestiging
    """
    try:
        vestiging = db.query(Vestiging).filter(Vestiging.id == vestiging_id).first()

        if not vestiging:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vestiging {vestiging_id} niet gevonden"
            )

        # Check unique code if changed
        if "code" in data and data["code"] != vestiging.code:
            existing = db.query(Vestiging).filter(Vestiging.code == data["code"]).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Code '{data['code']}' is al in gebruik"
                )

        # Update fields
        updateable_fields = [
            "naam", "code", "adres_straat", "adres_huisnummer",
            "adres_postcode", "adres_plaats", "adres_land",
            "telefoon", "email", "notities", "is_actief"
        ]

        for field in updateable_fields:
            if field in data:
                setattr(vestiging, field, data[field])

        vestiging.versie_nummer += 1

        # Set historie context
        with HistorieContext(db, current_user.id, "update", "vestiging", vestiging.id):
            db.commit()
            db.refresh(vestiging)

        return {
            "id": vestiging.id,
            "naam": vestiging.naam,
            "code": vestiging.code,
            "message": "Vestiging succesvol bijgewerkt"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error updating vestiging: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating vestiging: {str(e)}"
        )


@router.delete("/vestigingen/{vestiging_id}")
def delete_vestiging(
    vestiging_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete vestiging (soft delete by setting is_actief to False)
    """
    try:
        vestiging = db.query(Vestiging).filter(Vestiging.id == vestiging_id).first()

        if not vestiging:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vestiging {vestiging_id} niet gevonden"
            )

        # Soft delete
        vestiging.is_actief = False
        vestiging.versie_nummer += 1

        # Set historie context
        with HistorieContext(db, current_user.id, "delete", "vestiging", vestiging.id):
            db.commit()

        return {
            "message": "Vestiging succesvol gedeactiveerd"
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error deleting vestiging: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting vestiging: {str(e)}"
        )
