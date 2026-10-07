import threading
import time
import uuid
from app.comfy.client import comfy_client
from app.gpu.manager import gpu_manager

class ImageJobQueue:
    def __init__(self):
        self.jobs = {}
        self.queue = []
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()

    def add_job(self, request_data: dict):
        job_id = str(uuid.uuid4())[:8]
        job = {
            "job_id": job_id,
            "status": "queued",
            "request": request_data,
            "created_at": time.time(),
            "comfy_prompt_id": None,
            "image_url": None,
            "error": None
        }
        self.jobs[job_id] = job
        self.queue.append(job_id)
        return job_id

    def get_job(self, job_id: str):
        return self.jobs.get(job_id)

    def _process_queue(self):
        while True:
            if not self.queue:
                time.sleep(1)
                continue

            job_id = self.queue[0]
            job = self.jobs[job_id]
            
            # Wait for GPU lock
            job["status"] = "waiting_for_gpu"
            gpu_manager.acquire_image()
            try:
                job["status"] = "running"
                req = job["request"]
                
                # Submit to ComfyUI
                result = comfy_client.generate_image(
                    prompt=req["prompt"], 
                    width=req.get("width", 1024), 
                    height=req.get("height", 1024), 
                    seed=req.get("seed", -1)
                )
                
                if result["status"] == "success":
                    prompt_id = result["prompt_id"]
                    job["comfy_prompt_id"] = prompt_id
                    
                    # Poll ComfyUI until done
                    while True:
                        status_res = comfy_client.get_job_status(prompt_id)
                        if status_res["status"] == "completed":
                            filename = status_res["filename"]
                            job["image_url"] = f"/images/{filename}" # Assuming gateway maps this
                            job["status"] = "completed"
                            job["generation_time"] = time.time() - job["created_at"]
                            break
                        elif status_res["status"] == "error":
                            job["status"] = "error"
                            job["error"] = status_res["message"]
                            break
                        time.sleep(1)
                else:
                    job["status"] = "error"
                    job["error"] = result.get("message")
            except Exception as e:
                job["status"] = "error"
                job["error"] = str(e)
            finally:
                gpu_manager.release_image()
                # Remove from queue
                self.queue.pop(0)

image_queue = ImageJobQueue()
