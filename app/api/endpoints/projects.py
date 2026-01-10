"""
Projects endpoints - Complete CRUD with error handling
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi import status as http_status
from sqlalchemy.orm import Session
from typing import Optional
import uuid
from datetime import datetime

from app.db.session import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.project import Project, ProjectStatus
from app.models.projectfase import ProjectFase, ProjectFaseStatus
from app.models.proces_template import ProcesTemplate, TemplateStap
from app.models.historie_setup import HistorieContext
from sqlalchemy.orm import joinedload

router = APIRouter(tags=["Projects"])


@router.get("/projects")
def list_projects(
    page: int = 1,
    limit: int = 25,
    search: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List projects with pagination and filters
    """
    try:
        # Base query
        query = db.query(Project)
        
        # Apply filters
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (Project.naam.ilike(search_term)) |
                (Project.project_nummer.ilike(search_term))
            )
        
        if status:
            try:
                query = query.filter(Project.status == ProjectStatus(status))
            except ValueError:
                pass  # Invalid status, ignore filter
        
        # Count total
        total = query.count()
        
        # Pagination
        offset = (page - 1) * limit
        projects = query.offset(offset).limit(limit).all()
        
        # Format response
        project_list = []
        for p in projects:
            try:
                project_data = {
                    "id": p.id,
                    "project_nummer": p.project_nummer,
                    "naam": p.naam,
                    "beschrijving": p.beschrijving,
                    "status": p.status.value if p.status else "concept",
                    "budget": {
                        "totaal": p.budget_totaal or 0,
                        "besteed": p.budget_besteed or 0,
                        "percentage": p.budget_percentage
                    },
                    "start_datum": p.start_datum.isoformat() if p.start_datum else None,
                    "eind_datum": p.eind_datum.isoformat() if p.eind_datum else None,
                    "projectleider": {
                        "id": p.projectleider.id,
                        "name": p.projectleider.name,
                        "email": p.projectleider.email,
                        "role": p.projectleider.role.value
                    } if p.projectleider else None,
                    "created_at": p.created_at.isoformat() if p.created_at else None,
                    "updated_at": p.updated_at.isoformat() if p.updated_at else None
                }
                project_list.append(project_data)
            except Exception as e:
                print(f"Error formatting project {p.id}: {e}")
                continue
        
        return {
            "success": True,
            "data": project_list,
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
        print(f"Error in list_projects: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch projects: {str(e)}"
        )


@router.get("/projects/{project_id}")
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get project details
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()

        if not project:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        return {
            "success": True,
            "data": {
                "id": project.id,
                "project_nummer": project.project_nummer,
                "naam": project.naam,
                "beschrijving": project.beschrijving,
                "status": project.status.value if project.status else "concept",
                "budget": {
                    "totaal": project.budget_totaal or 0,
                    "besteed": project.budget_besteed or 0,
                    "percentage": project.budget_percentage
                },
                "start_datum": project.start_datum.isoformat() if project.start_datum else None,
                "eind_datum": project.eind_datum.isoformat() if project.eind_datum else None,
                "projectleider": {
                    "id": project.projectleider.id,
                    "name": project.projectleider.name,
                    "email": project.projectleider.email,
                    "role": project.projectleider.role.value
                } if project.projectleider else None,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_project: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch project: {str(e)}"
        )


@router.post("/projects")
def create_project(
    project_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new project
    """
    try:
        # Validate required fields
        required_fields = ["project_nummer", "naam", "budget_totaal", "projectleider_id"]
        for field in required_fields:
            if field not in project_data or not project_data[field]:
                raise HTTPException(
                    status_code=http_status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Check if project_nummer already exists
        existing = db.query(Project).filter(
            Project.project_nummer == project_data.get("project_nummer")
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="Project nummer already exists"
            )
        
        # Parse dates if provided
        start_datum = None
        if project_data.get("start_datum"):
            try:
                start_datum = datetime.fromisoformat(project_data["start_datum"].replace('Z', '+00:00'))
            except:
                pass
        
        eind_datum = None
        if project_data.get("eind_datum"):
            try:
                eind_datum = datetime.fromisoformat(project_data["eind_datum"].replace('Z', '+00:00'))
            except:
                pass
        
        # Create project
        project = Project(
            id=f"prj_{uuid.uuid4().hex[:8]}",
            project_nummer=project_data["project_nummer"],
            naam=project_data["naam"],
            beschrijving=project_data.get("beschrijving"),
            status=ProjectStatus(project_data.get("status", "concept")),
            budget_totaal=int(project_data["budget_totaal"]),
            budget_besteed=int(project_data.get("budget_besteed", 0)),
            start_datum=start_datum,
            eind_datum=eind_datum,
            projectleider_id=project_data["projectleider_id"],
            template_id=project_data.get("template_id")
        )

        db.add(project)
        db.flush()  # Get project ID

        # If template_id is provided, create projectfases from template
        if project_data.get("template_id"):
            template = db.query(ProcesTemplate).options(
                joinedload(ProcesTemplate.stappen)
            ).filter(ProcesTemplate.id == project_data["template_id"]).first()

            if template:
                print(f"Applying template '{template.naam}' with {len(template.stappen)} steps to project {project.id}")

                # Create a ProjectFase for each TemplateStap
                for template_stap in sorted(template.stappen, key=lambda s: s.stap_nummer):
                    projectfase = ProjectFase(
                        id=f"fase_{uuid.uuid4().hex[:8]}",
                        project_id=project.id,
                        naam=template_stap.naam,
                        beschrijving=template_stap.beschrijving,
                        fase_nummer=template_stap.stap_nummer,
                        status=ProjectFaseStatus.NIET_GESTART,
                        verantwoordelijke_id=project.projectleider_id
                    )
                    db.add(projectfase)
                    print(f"  Created fase {template_stap.stap_nummer}: {template_stap.naam}")

                # Update template usage count
                template.aantal_keer_gebruikt += 1

        db.commit()
        db.refresh(project)
        
        return {
            "success": True,
            "data": {
                "id": project.id,
                "project_nummer": project.project_nummer,
                "naam": project.naam,
                "status": project.status.value
            },
            "message": "Project created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in create_project: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create project: {str(e)}"
        )


@router.patch("/projects/{project_id}")
def update_project(
    project_id: str,
    project_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update project
    """
    try:
        HistorieContext.set_user_id(current_user.id)
        HistorieContext.set_opmerking("Project bijgewerkt via API")

        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Update fields
        for key, value in project_data.items():
            if hasattr(project, key) and value is not None:
                if key == "status":
                    setattr(project, key, ProjectStatus(value))
                elif key in ["start_datum", "eind_datum"]:
                    try:
                        setattr(project, key, datetime.fromisoformat(value.replace('Z', '+00:00')))
                    except:
                        pass
                else:
                    setattr(project, key, value)
        
        db.commit()
        db.refresh(project)

        HistorieContext.clear()
        
        return {
            "success": True,
            "data": {
                "id": project.id,
                "project_nummer": project.project_nummer,
                "naam": project.naam,
                "status": project.status.value
            },
            "message": "Project updated successfully",
            "versie": project.versie_nummer
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in update_project: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project: {str(e)}"
        )


@router.delete("/projects/{project_id}")
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete project
    """
    try:
        project = db.query(Project).filter(Project.id == project_id).first()
        
        if not project:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )

        # Store project info for response
        project_info = {
            "id": project.id,
            "project_nummer": project.project_nummer,
            "naam": project.naam
        }
        
        # Delete
        db.delete(project)
        db.commit()
        
        return {
            "success": True,
            "data": project_info,
            "message": "Project deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"Error in delete_project: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete project: {str(e)}"
        )
