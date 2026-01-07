"""
Leveranciers endpoints - Complete CRUD
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.leverancier import Leverancier, LeverancierStatus, LeverancierType
from app.models.historie_setup import HistorieContext

router = APIRouter(tags=["Leveranciers"])


@router.get("/leveranciers")
def list_leveranciers(
    page: int = 1,
    limit: int = 25,
    search: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List leveranciers with pagination and filters
    """
    try:
        # Base query
        query = db.query(Leverancier)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Leverancier.naam.ilike(search_term)) |
                (Leverancier.kvk_nummer.ilike(search_term)) |
                (Leverancier.contactpersoon.ilike(search_term)) |
                (Leverancier.email.ilike(search_term))
            )
        
        if status:
            try:
                query = query.filter(Leverancier.status == LeverancierStatus(status))
            except ValueError:
                pass
        
        if type:
            try:
                query = query.filter(Leverancier.type == LeverancierType(type))
            except ValueError:
                pass
        
        # Count total
        total = query.count()
        
        # Pagination
        offset = (page - 1) * limit
        leveranciers = query.offset(offset).limit(limit).all()
        
        # Format response
        leverancier_list = []
        for l in leveranciers:
            try:
                leverancier_data = {
                    "id": l.id,
                    "naam": l.naam,
                    "kvk_nummer": l.kvk_nummer,
                    "btw_nummer": l.btw_nummer,
                    "type": l.type.value if l.type else None,
                    "status": l.status.value if l.status else "actief",
                    "contactpersoon": l.contactpersoon,
                    "email": l.email,
                    "telefoon": l.telefoon,
                    "mobiel": l.mobiel,
                    "website": l.website,
                    "adres": {
                        "straat": l.adres_straat,
                        "huisnummer": l.adres_huisnummer,
                        "postcode": l.adres_postcode,
                        "plaats": l.adres_plaats,
                        "land": l.adres_land,
                        "volledig": l.volledig_adres
                    },
                    "bank": {
                        "iban": l.iban,
                        "naam": l.bank_naam
                    },
                    "is_actief": l.is_actief,
                    "created_at": l.created_at.isoformat() if l.created_at else None,
                    "updated_at": l.updated_at.isoformat() if l.updated_at else None
                }
                leverancier_list.append(leverancier_data)
            except Exception as e:
                print(f"Error formatting leverancier {l.id}: {e}")
                continue
        
        return {
            "success": True,
            "data": leverancier_list,
            "pagination": {
                "current_page": page,
                "per_page": limit,
                "total": total,
                "total_pages": max(1, (total + limit - 1) // limit),
                "has_next": page * limit < total,
                "has_prev": page > 1
            }
        }
    except Exception as e:
        print(f"Error in list_leveranciers: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch leveranciers: {str(e)}"
        )


@router.get("/leveranciers/{leverancier_id}")
def get_leverancier(
    leverancier_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get leverancier details
    """
    try:
        leverancier = db.query(Leverancier).filter(Leverancier.id == leverancier_id).first()
        
        if not leverancier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leverancier not found"
            )
        
        return {
            "success": True,
            "data": {
                "id": leverancier.id,
                "naam": leverancier.naam,
                "kvk_nummer": leverancier.kvk_nummer,
                "btw_nummer": leverancier.btw_nummer,
                "type": leverancier.type.value if leverancier.type else None,
                "status": leverancier.status.value if leverancier.status else "actief",
                "contactpersoon": leverancier.contactpersoon,
                "email": leverancier.email,
                "telefoon": leverancier.telefoon,
                "mobiel": leverancier.mobiel,
                "website": leverancier.website,
                "adres": {
                    "straat": leverancier.adres_straat,
                    "huisnummer": leverancier.adres_huisnummer,
                    "postcode": leverancier.adres_postcode,
                    "plaats": leverancier.adres_plaats,
                    "land": leverancier.adres_land,
                    "volledig": leverancier.volledig_adres
                },
                "bank": {
                    "iban": leverancier.iban,
                    "naam": leverancier.bank_naam
                },
                "notities": leverancier.notities,
                "is_actief": leverancier.is_actief,
                "created_at": leverancier.created_at.isoformat() if leverancier.created_at else None,
                "updated_at": leverancier.updated_at.isoformat() if leverancier.updated_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_leverancier: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch leverancier: {str(e)}"
        )


@router.post("/leveranciers")
def create_leverancier(
    leverancier_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new leverancier
    """
    try:
        # Validate required fields
        required_fields = ["naam", "type"]
        for field in required_fields:
            if field not in leverancier_data or not leverancier_data[field]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Check if KVK nummer already exists (if provided)
        if leverancier_data.get("kvk_nummer"):
            existing = db.query(Leverancier).filter(
                Leverancier.kvk_nummer == leverancier_data.get("kvk_nummer")
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="KVK nummer already exists"
                )
        
        # Create leverancier
        leverancier = Leverancier(
            id=f"lev_{uuid.uuid4().hex[:8]}",
            naam=leverancier_data["naam"],
            kvk_nummer=leverancier_data.get("kvk_nummer"),
            btw_nummer=leverancier_data.get("btw_nummer"),
            type=LeverancierType(leverancier_data["type"]),
            status=LeverancierStatus(leverancier_data.get("status", "actief")),
            contactpersoon=leverancier_data.get("contactpersoon"),
            email=leverancier_data.get("email"),
            telefoon=leverancier_data.get("telefoon"),
            mobiel=leverancier_data.get("mobiel"),
            website=leverancier_data.get("website"),
            adres_straat=leverancier_data.get("adres_straat"),
            adres_huisnummer=leverancier_data.get("adres_huisnummer"),
            adres_postcode=leverancier_data.get("adres_postcode"),
            adres_plaats=leverancier_data.get("adres_plaats"),
            adres_land=leverancier_data.get("adres_land", "Nederland"),
            iban=leverancier_data.get("iban"),
            bank_naam=leverancier_data.get("bank_naam"),
            notities=leverancier_data.get("notities")
        )
        
        db.add(leverancier)
        db.commit()
        db.refresh(leverancier)
        
        return {
            "success": True,
            "data": {
                "id": leverancier.id,
                "naam": leverancier.naam,
                "status": leverancier.status.value
            },
            "message": "Leverancier created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in create_leverancier: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create leverancier: {str(e)}"
        )


@router.patch("/leveranciers/{leverancier_id}")
def update_leverancier(
    leverancier_id: str,
    leverancier_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update leverancier
    """
    try:
        # SET CONTEXT
        HistorieContext.set_user_id(current_user.id)
        HistorieContext.set_opmerking("Leverancier bijgewerkt via API")
        
        leverancier = db.query(Leverancier).filter(Leverancier.id == leverancier_id).first()
        
        if not leverancier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leverancier not found"
            )
        
        # Update fields
        for key, value in leverancier_data.items():
            if hasattr(leverancier, key) and value is not None:
                if key == "status":
                    setattr(leverancier, key, LeverancierStatus(value))
                elif key == "type":
                    setattr(leverancier, key, LeverancierType(value))
                else:
                    setattr(leverancier, key, value)
        
        db.commit()
        db.refresh(leverancier)

        # Clear context
        HistorieContext.clear()
        
        return {
            "success": True,
            "data": {
                "id": leverancier.id,
                "naam": leverancier.naam,
                "status": leverancier.status.value
            },
            "message": "Leverancier updated successfully",
            "versie": leverancier.versie_nummer
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in update_leverancier: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update leverancier: {str(e)}"
        )


@router.delete("/leveranciers/{leverancier_id}")
def delete_leverancier(
    leverancier_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete leverancier
    """
    try:
        leverancier = db.query(Leverancier).filter(Leverancier.id == leverancier_id).first()
        
        if not leverancier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leverancier not found"
            )
        
        # Store info for response
        leverancier_info = {
            "id": leverancier.id,
            "naam": leverancier.naam
        }
        
        # Delete
        db.delete(leverancier)
        db.commit()
        
        return {
            "success": True,
            "data": leverancier_info,
            "message": "Leverancier deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in delete_leverancier: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete leverancier: {str(e)}"
        )
