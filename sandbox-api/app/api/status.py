from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def get_status():
    return {
        "gpu": "RTX 5090",
        "vram": "0 / 32 GB",
        "vlm": "READY",
        "flux": "READY",
        "current_owner": "IDLE",
        "queue_size": 0
    }
