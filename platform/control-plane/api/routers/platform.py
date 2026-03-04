from fastapi import APIRouter
from api.core.config import APP_NAME

router = APIRouter()

@router.get("/platform/info")
def platform_info():
    return {
        "platform": APP_NAME,
        "version": "v1",
        "control_plane": True
    }
