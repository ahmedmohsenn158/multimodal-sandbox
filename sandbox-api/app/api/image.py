from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.safety.sanitizer import PromptSanitizer
from app.comfy.queue import image_queue

router = APIRouter()

class ImageRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024
    seed: int = -1

@router.post("/generate")
def generate_image(request: ImageRequest):
    # Safety Check Layer
    safety_result = PromptSanitizer.is_allowed(request.prompt)
    if not safety_result["allowed"]:
        raise HTTPException(status_code=400, detail=safety_result["reason"])

    job_id = image_queue.add_job(request.model_dump())
    
    return {"job_id": job_id, "status": "queued"}

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    job = image_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Calculate queue position if it's queued
    position = -1
    if job["status"] in ["queued", "waiting_for_gpu"]:
        try:
            position = image_queue.queue.index(job_id) + 1
        except ValueError:
            pass
            
    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "image_url": job.get("image_url"),
        "error": job.get("error"),
        "queue_position": position
    }
