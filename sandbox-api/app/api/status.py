from fastapi import APIRouter
from app.gpu.manager import gpu_manager
from app.comfy.queue import image_queue
from app.comfy.client import comfy_client

router = APIRouter()

@router.get("/")
def get_status():
    gpu_status = gpu_manager.status()
    queue_len = len(image_queue.queue)
    
    # In a full implementation, we'd also check VLM health
    comfy_ready = "READY" if comfy_client.check_health() else "UNAVAILABLE"
    vlm_ready = "UNKNOWN" # To be integrated with vLLM health check
    
    return {
        "gpu": "RTX 5090", # Static for now
        "vram": f"{gpu_status['vram_used']} / {gpu_status['vram_total']} GB",
        "vlm": vlm_ready,
        "flux": comfy_ready,
        "current_owner": gpu_status["owner"],
        "queue_size": queue_len
    }
