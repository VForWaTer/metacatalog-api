from fastapi import APIRouter

router = APIRouter()

# Manager-specific API endpoints
@router.get("/status")
async def manager_status():
    """Get the status of the manager application"""
    return {
        "app": "manager",
        "status": "running"
    }

# Add more manager-specific endpoints here as needed
# @router.get("/api/special")
# async def special_endpoint():
#     return {"message": "This is a manager-specific API endpoint"} 