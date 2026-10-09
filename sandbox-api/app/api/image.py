import os
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.safety.sanitizer import PromptSanitizer
from app.comfy.queue import QueueFullError, image_queue

router = APIRouter()
MAX_PROMPT_LENGTH = int(os.getenv("MAX_PROMPT_LENGTH", "1000"))
MAX_IMAGE_DIMENSION = int(os.getenv("MAX_IMAGE_DIMENSION", "1536"))


class ImageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    prompt: str = Field(min_length=1, max_length=MAX_PROMPT_LENGTH)
    width: int = Field(default=1024, ge=512, le=MAX_IMAGE_DIMENSION, multiple_of=8)
    height: int = Field(default=1024, ge=512, le=MAX_IMAGE_DIMENSION, multiple_of=8)
    # -1 means "choose a random seed" in this API only; client.py converts it
    # to a valid non-negative ComfyUI seed before submitting the workflow.
    seed: int = Field(default=-1, ge=-1, lt=2**64)

    @field_validator("prompt")
    @classmethod
    def reject_blank_prompt(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Prompt cannot be empty or whitespace only.")
        return value.strip()


@router.post("/generate")
def generate_image(request: ImageRequest):
    safety_result = PromptSanitizer.is_allowed(request.prompt)
    if not safety_result.get("allowed", False):
        raise HTTPException(
            status_code=400,
            detail=safety_result.get("reason", "Prompt rejected by safety filter."),
        )

    try:
        job_id = image_queue.add_job(request.model_dump())
    except QueueFullError as exc:
        raise HTTPException(status_code=429, detail=str(exc)) from exc

    return {"job_id": job_id, "status": "queued"}


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    job = image_queue.get_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Image job not found. The API may have restarted; submit a new request.",
        )

    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "image_url": job.get("image_url"),
        "error": job.get("error"),
        "queue_position": image_queue.get_queue_position(job_id),
        "generation_time": job.get("generation_time"),
        "seed": job.get("seed"),
    }
