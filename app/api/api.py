"""
Main API router - combines all endpoint routers
"""
from fastapi import APIRouter

from app.api.endpoints import auth, projects, reports, contracts, leveranciers, projectfase_endpoints, historie, proces_templates, users, vestigingen, taken

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
	auth.router
	, prefix="/auth"
	, tags=["auth"]
	)
api_router.include_router(
	projects.router
	, tags=["projects"]
	)
api_router.include_router(
	reports.router
	, prefix="/reports"
	, tags=["reports"]
	)
api_router.include_router(
	contracts.router
	, tags=["Contracts"]
	)
api_router.include_router(
	leveranciers.router
#	, prefix="/leveranciers"
	, tags=["Leveranciers"]
	) 
api_router.include_router(
    projectfase_endpoints.router
#    , prefix="/api"
    , tags=["projectfases"]
)
api_router.include_router(
    historie.router,
    #prefix="/api/historie",
    tags=["historie"]
)
api_router.include_router(
    proces_templates.router,
    tags=["proces-templates"]
)
api_router.include_router(
    users.router,
    tags=["users"]
)
api_router.include_router(
    vestigingen.router,
    tags=["vestigingen"]
)
api_router.include_router(
    taken.router,
    tags=["taken"]
)