"""Single-worker queue for GPU-backed image generation."""

import os
import threading
import time
import uuid
from collections import deque
from copy import deepcopy
from typing import Any

from app.comfy.client import comfy_client
from app.gpu.manager import gpu_manager

MAX_PENDING_JOBS = int(os.getenv("MAX_QUEUE_SIZE", "10"))
JOB_TIMEOUT_SECONDS = float(os.getenv("COMFY_JOB_TIMEOUT_SECONDS", "600"))
POLL_INTERVAL_SECONDS = float(os.getenv("COMFY_POLL_INTERVAL_SECONDS", "1"))


class QueueFullError(RuntimeError):
    """Raised when the station's pending image queue is full."""


class ImageJobQueue:
    def __init__(self, start_worker: bool = True):
        self.jobs: dict[str, dict[str, Any]] = {}
        self.queue: deque[str] = deque()
        self._condition = threading.Condition(threading.RLock())
        self._worker_thread: threading.Thread | None = None
        if start_worker:
            self._worker_thread = threading.Thread(
                target=self._process_queue,
                name="image-job-worker",
                daemon=True,
            )
            self._worker_thread.start()

    def add_job(self, request_data: dict[str, Any]) -> str:
        with self._condition:
            if len(self.queue) >= MAX_PENDING_JOBS:
                raise QueueFullError(
                    f"Image queue is full ({MAX_PENDING_JOBS} pending jobs). Please retry shortly."
                )
            job_id = str(uuid.uuid4())[:8]
            self.jobs[job_id] = {
                "job_id": job_id,
                "status": "queued",
                "request": deepcopy(request_data),
                "created_at": time.time(),
                "comfy_prompt_id": None,
                "image_url": None,
                "error": None,
                "generation_time": None,
                "seed": None,
            }
            self.queue.append(job_id)
            self._condition.notify()
            return job_id

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._condition:
            job = self.jobs.get(job_id)
            return deepcopy(job) if job is not None else None

    def get_queue_position(self, job_id: str) -> int:
        with self._condition:
            try:
                return list(self.queue).index(job_id) + 1
            except ValueError:
                job = self.jobs.get(job_id)
                # A job waiting for the shared GPU lock is the next active job.
                if job and job.get("status") == "waiting_for_gpu":
                    return 1
                return -1

    def _update(self, job_id: str, **values: Any) -> None:
        with self._condition:
            job = self.jobs.get(job_id)
            if job is not None:
                job.update(values)
                self._condition.notify_all()

    def _process_queue(self) -> None:
        while True:
            with self._condition:
                while not self.queue:
                    self._condition.wait()
                job_id = self.queue.popleft()
                job = self.jobs.get(job_id)
                if job is None:
                    continue
                job["status"] = "waiting_for_gpu"
                self._condition.notify_all()
                request_data = deepcopy(job["request"])

            gpu_acquired = False
            started_at = time.monotonic()
            try:
                # Begin try/except before acquiring the shared GPU lock so an acquisition
                # failure cannot silently kill this worker thread.
                gpu_manager.acquire_image()
                gpu_acquired = True
                self._update(job_id, status="running")

                result = comfy_client.generate_image(
                    prompt=request_data["prompt"],
                    width=request_data.get("width", 1024),
                    height=request_data.get("height", 1024),
                    seed=request_data.get("seed", -1),
                )
                if result.get("status") != "success":
                    self._update(
                        job_id,
                        status="failed",
                        error=result.get("message", "ComfyUI failed to accept the workflow."),
                        generation_time=time.monotonic() - started_at,
                    )
                    continue

                prompt_id = result["prompt_id"]
                self._update(job_id, comfy_prompt_id=prompt_id, seed=result.get("seed"))
                deadline = time.monotonic() + JOB_TIMEOUT_SECONDS

                while time.monotonic() < deadline:
                    status_result = comfy_client.get_job_status(prompt_id)
                    status = status_result.get("status")

                    if status == "completed":
                        image_url = status_result.get("image_url")
                        if not image_url:
                            # Compatibility fallback; current ComfyClient returns image_url.
                            filename = status_result.get("filename")
                            image_url = f"/images/{filename}" if filename else None
                        if not image_url:
                            self._update(
                                job_id,
                                status="failed",
                                error="ComfyUI reported completion but returned no image URL.",
                                generation_time=time.monotonic() - started_at,
                            )
                        else:
                            self._update(
                                job_id,
                                status="completed",
                                image_url=image_url,
                                generation_time=time.monotonic() - started_at,
                                error=None,
                            )
                        break

                    if status in {"error", "failed"}:
                        self._update(
                            job_id,
                            status="failed",
                            error=status_result.get("message", "ComfyUI image generation failed."),
                            generation_time=time.monotonic() - started_at,
                        )
                        break

                    if status != "queued_or_running":
                        self._update(
                            job_id,
                            status="failed",
                            error=f"Unexpected ComfyUI job status: {status!r}",
                            generation_time=time.monotonic() - started_at,
                        )
                        break

                    time.sleep(max(0.1, POLL_INTERVAL_SECONDS))
                else:
                    self._update(
                        job_id,
                        status="failed",
                        error=f"Image generation timed out after {JOB_TIMEOUT_SECONDS:.0f} seconds.",
                        generation_time=time.monotonic() - started_at,
                    )

            except Exception as exc:  # Keep the worker alive for subsequent jobs.
                self._update(
                    job_id,
                    status="failed",
                    error=f"Image worker failed: {exc}",
                    generation_time=time.monotonic() - started_at,
                )
            finally:
                if gpu_acquired:
                    try:
                        gpu_manager.release_image()
                    except Exception as exc:
                        # Job state is already terminal; log lock-release failures for ops.
                        print(f"ERROR: failed to release image GPU lock: {exc}", flush=True)


image_queue = ImageJobQueue()
