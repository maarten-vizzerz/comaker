"""
Main API router - combines all endpoint routers
"""
from fastapi import APIRouter

from app.api.endpoints import auth, projects, reports, contracts, leveranciers, projectfase_endpoints, historie

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