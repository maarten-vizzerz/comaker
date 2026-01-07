"""
Contracts endpoints - Complete CRUD
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from datetime import datetime
from decimal import Decimal

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.contract import Contract, ContractStatus, ContractType
from app.models.leverancier import Leverancier  
from app.models.historie_setup import HistorieContext

router = APIRouter(tags=["Contracts"])


@router.get("/contracts")
def list_contracts(
    page: int = 1,
    limit: int = 25,
    search: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
    project_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List contracts with pagination and filters
    """
    try:
        # Base query
        query = db.query(Contract)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.join(Contract.leverancier).filter(  # ← JOIN!
                (Contract.naam.ilike(search_term)) |
                (Contract.contract_nummer.ilike(search_term)) |
                (Leverancier.naam.ilike(search_term))  # ← USE LEVERANCIER TABLE
            )
        
        if status:
            try:
                query = query.filter(Contract.status == ContractStatus(status))
            except ValueError:
                pass
        
        if type:
            try:
                query = query.filter(Contract.type == ContractType(type))
            except ValueError:
                pass
        
        if project_id:
            query = query.filter(Contract.project_id == project_id)
        
        # Count total
        total = query.count()
        
        # Pagination
        offset = (page - 1) * limit
        contracts = query.offset(offset).limit(limit).all()
        
        # Format response
        contract_list = []
        for c in contracts:
            try:
                contract_data = {
                    "id": c.id,
                    "contract_nummer": c.contract_nummer,
                    "naam": c.naam,
                    "beschrijving": c.beschrijving,
                    "type": c.type.value if c.type else None,
                    "status": c.status.value if c.status else "concept",
                    "leverancier": {
                        "id": c.leverancier.id,
                        "naam": c.leverancier.naam,
                        "kvk_nummer": c.leverancier.kvk_nummer,
                        "contactpersoon": c.leverancier.contactpersoon,
                        "email": c.leverancier.email,
                        "telefoon": c.leverancier.telefoon
                    } if c.leverancier else None,
                    "bedragen": {
                        "contract": float(c.contract_bedrag or 0),
                        "gefactureerd": float(c.gefactureerd_bedrag or 0),
                        "restant": c.restant_bedrag,
                        "percentage": c.gefactureerd_percentage
                    },
                    "start_datum": c.start_datum.isoformat() if c.start_datum else None,
                    "eind_datum": c.eind_datum.isoformat() if c.eind_datum else None,
                    "getekend_datum": c.getekend_datum.isoformat() if c.getekend_datum else None,
                    "is_actief": c.is_actief,
                    "project": {
                        "id": c.project.id,
                        "naam": c.project.naam,
                        "project_nummer": c.project.project_nummer
                    } if c.project else None,
                    "verantwoordelijke": {
                        "id": c.verantwoordelijke.id,
                        "name": c.verantwoordelijke.name,
                        "email": c.verantwoordelijke.email
                    } if c.verantwoordelijke else None,
                    "created_at": c.created_at.isoformat() if c.created_at else None,
                    "updated_at": c.updated_at.isoformat() if c.updated_at else None
                }
                contract_list.append(contract_data)
            except Exception as e:
                print(f"Error formatting contract {c.id}: {e}")
                continue
        
        return {
            "success": True,
            "data": contract_list,
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
        print(f"Error in list_contracts: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch contracts: {str(e)}"
        )


@router.get("/contracts/{contract_id}")
def get_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get contract details
    """
    try:
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        return {
            "success": True,
            "data": {
                "id": contract.id,
                "contract_nummer": contract.contract_nummer,
                "naam": contract.naam,
                "beschrijving": contract.beschrijving,
                "type": contract.type.value if contract.type else None,
                "status": contract.status.value if contract.status else "concept",
                "leverancier": {
                    "leverancier_id": contract.leverancier_id,
                },
                "bedragen": {
                    "contract": float(contract.contract_bedrag or 0),
                    "gefactureerd": float(contract.gefactureerd_bedrag or 0),
                    "restant": contract.restant_bedrag,
                    "percentage": contract.gefactureerd_percentage
                },
                "start_datum": contract.start_datum.isoformat() if contract.start_datum else None,
                "eind_datum": contract.eind_datum.isoformat() if contract.eind_datum else None,
                "getekend_datum": contract.getekend_datum.isoformat() if contract.getekend_datum else None,
                #"document_pad": contract.document_pad,
                "is_actief": contract.is_actief,
                "goedkeuring": {
                    "goedgekeurd_door": {
                        "id": contract.goedgekeurd_door.id,
                        "name": contract.goedgekeurd_door.name
                    } if contract.goedgekeurd_door else None,
                    "datum": contract.goedkeurings_datum.isoformat() if contract.goedkeurings_datum else None,
                    #"opmerkingen": contract.goedkeurings_opmerkingen
                },
                "project": {
                    "id": contract.project.id,
                    "naam": contract.project.naam,
                    "project_nummer": contract.project.project_nummer
                } if contract.project else None,
                "verantwoordelijke": {
                    "id": contract.verantwoordelijke.id,
                    "name": contract.verantwoordelijke.name,
                    "email": contract.verantwoordelijke.email,
                    "role": contract.verantwoordelijke.role.value
                } if contract.verantwoordelijke else None,
                "created_at": contract.created_at.isoformat() if contract.created_at else None,
                "updated_at": contract.updated_at.isoformat() if contract.updated_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_contract: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch contract: {str(e)}"
        )


@router.post("/contracts")
def create_contract(
    contract_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new contract
    """
    try:
        # Validate required fields
        required_fields = ["contract_nummer", "naam", "type", "leverancier_id", "contract_bedrag", "verantwoordelijke_id"]
        for field in required_fields:
            if field not in contract_data or not contract_data[field]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Check if contract_nummer already exists
        existing = db.query(Contract).filter(
            Contract.contract_nummer == contract_data.get("contract_nummer")
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Contract nummer already exists"
            )
        
        # Parse dates
        start_datum = None
        if contract_data.get("start_datum"):
            try:
                start_datum = datetime.fromisoformat(contract_data["start_datum"].replace('Z', '+00:00'))
            except:
                pass
        
        eind_datum = None
        if contract_data.get("eind_datum"):
            try:
                eind_datum = datetime.fromisoformat(contract_data["eind_datum"].replace('Z', '+00:00'))
            except:
                pass
        
        # Verify leverancier exists
        leverancier = db.query(Leverancier).filter(
            Leverancier.id == contract_data["leverancier_id"]
        ).first()

        if not leverancier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Leverancier not found"
            )
        
        # Create contract
        contract = Contract(
            id=f"ctr_{uuid.uuid4().hex[:8]}",
            contract_nummer=contract_data["contract_nummer"],
            naam=contract_data["naam"],
            beschrijving=contract_data.get("beschrijving"),
            type=ContractType(contract_data["type"]),
            status=ContractStatus(contract_data.get("status", "concept")),
            leverancier_id=contract_data["leverancier_id"],
            contract_bedrag=Decimal(str(contract_data["contract_bedrag"])),
            gefactureerd_bedrag=Decimal(str(contract_data.get("gefactureerd_bedrag", 0))),
            start_datum=start_datum,
            eind_datum=eind_datum,
            project_id=contract_data.get("project_id"),
            verantwoordelijke_id=contract_data["verantwoordelijke_id"]
        )
        
        db.add(contract)
        db.commit()
        db.refresh(contract)
        
        return {
            "success": True,
            "data": {
                "id": contract.id,
                "contract_nummer": contract.contract_nummer,
                "naam": contract.naam,
                "status": contract.status.value
            },
            "message": "Contract created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in create_contract: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create contract: {str(e)}"
        )


@router.patch("/contracts/{contract_id}")
def update_contract(
    contract_id: str,
    contract_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update contract
    """
    try:
        HistorieContext.set_user_id(current_user.id)
        HistorieContext.set_opmerking("Contract bijgewerkt via API")
    
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        # Update fields
        for key, value in contract_data.items():
            if hasattr(contract, key) and value is not None:
                if key == "status":
                    setattr(contract, key, ContractStatus(value))
                elif key == "type":
                    setattr(contract, key, ContractType(value))
                elif key in ["start_datum", "eind_datum", "getekend_datum", "goedkeurings_datum"]:
                    try:
                        setattr(contract, key, datetime.fromisoformat(value.replace('Z', '+00:00')))
                    except:
                        pass
                elif key in ["contract_bedrag", "gefactureerd_bedrag"]:
                    setattr(contract, key, Decimal(str(value)))
                else:
                    setattr(contract, key, value)
        
        db.commit()
        db.refresh(contract)
        
        HistorieContext.clear()

        return {
            "success": True,
            "data": {
                "id": contract.id,
                "contract_nummer": contract.contract_nummer,
                "naam": contract.naam,
                "status": contract.status.value
            },
            "message": "Contract updated successfully",
            "versie": contract.versie_nummer
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in update_contract: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contract: {str(e)}"
        )


@router.delete("/contracts/{contract_id}")
def delete_contract(
    contract_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete contract
    """
    try:
        contract = db.query(Contract).filter(Contract.id == contract_id).first()
        
        if not contract:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Contract not found"
            )
        
        # Store info for response
        contract_info = {
            "id": contract.id,
            "contract_nummer": contract.contract_nummer,
            "naam": contract.naam
        }
        
        # Delete
        db.delete(contract)
        db.commit()
        
        return {
            "success": True,
            "data": contract_info,
            "message": "Contract deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in delete_contract: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete contract: {str(e)}"
        )
