"""
Models package - Import all models
"""
from app.models.user import User, UserRole
from app.models.leverancier import Leverancier, LeverancierStatus, LeverancierType
from app.models.project import Project, ProjectStatus
from app.models.contract import Contract, ContractStatus, ContractType
from app.models.projectfase import (
    ProjectFase, 
    ProjectFaseDocument, 
    ProjectFaseCommentaar,
    ProjectFaseStatus,
    DocumentType,
    CommentaarType,
    CommentaarStatus
)
from app.models.historie import (
    HistorieRecord,
    UserHistorie,
    ProjectHistorie,
    ContractHistorie,
    LeverancierHistorie,
    ProjectFaseHistorie
)

__all__ = [
    # User
    "User",
    "UserRole",
    # Leverancier
    "Leverancier",
    "LeverancierStatus",
    "LeverancierType",
    # Project
    "Project",
    "ProjectStatus",
    # Contract
    "Contract",
    "ContractStatus",
    "ContractType",
    # ProjectFase (NEW!)
    "ProjectFase",
    "ProjectFaseDocument",
    "ProjectFaseCommentaar",
    "ProjectFaseStatus",
    "DocumentType",
    "CommentaarType",
    "CommentaarStatus",
    "HistorieRecord",
    "UserHistorie",
    "ProjectHistorie",
    "ContractHistorie",
    "LeverancierHistorie",
    "ProjectFaseHistorie",
]
