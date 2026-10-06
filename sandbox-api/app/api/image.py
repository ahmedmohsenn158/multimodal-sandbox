from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
import time

router = APIRouter()

class ImageRequest(BaseModel):
    prompt: str
    width: int = 1024
    height: int = 1024
    seed: int = -1

# Dummy in-memory store for phase 1 mock
JOBS = {}

from app.safety.sanitizer import PromptSanitizer

@router.post("/generate")
def generate_image(request: ImageRequest):
    safety_result = PromptSanitizer.is_allowed(request.prompt)
    if not safety_result["allowed"]:
        raise HTTPException(status_code=400, detail=safety_result["reason"])

    job_id = str(uuid.uuid4())[:8]
    JOBS[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "request": request.model_dump(),
        "created_at": time.time()
    }
    return {"job_id": job_id, "status": "queued"}

@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Mock completion
    if job["status"] == "queued" and (time.time() - job["created_at"] > 2):
        job["status"] = "completed"
        job["image_url"] = f"/data/outputs/{job_id}.png"
        job["generation_time"] = time.time() - job["created_at"]

    return job
