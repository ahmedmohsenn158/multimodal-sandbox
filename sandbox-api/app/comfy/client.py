import os
import json
import uuid
import time
import requests
from pathlib import Path

COMFY_ENDPOINT = os.getenv("COMFY_ENDPOINT", "http://comfyui:8188")
WORKFLOWS_DIR = Path("/workflows") if os.path.exists("/workflows") else Path("./comfy/workflows")

class ComfyClient:
    def __init__(self):
        self.base_url = COMFY_ENDPOINT
    
    def check_health(self):
        try:
            r = requests.get(f"{self.base_url}/system_stats", timeout=2)
            return r.status_code == 200
        except:
            return False

    def load_workflow_template(self, template_name="flux_schnell_txt2img.json"):
        path = WORKFLOWS_DIR / template_name
        with open(path, "r") as f:
            return json.load(f)

    def generate_image(self, prompt: str, width: int = 1024, height: int = 1024, seed: int = -1):
        workflow = self.load_workflow_template()
        
        # Mapping inputs according to the fixed template node IDs
        # Node 3: KSampler (seed)
        # Node 5: EmptyLatentImage (width, height)
        # Node 6: CLIPTextEncode (positive prompt)
        
        workflow["3"]["inputs"]["seed"] = seed
        workflow["5"]["inputs"]["width"] = width
        workflow["5"]["inputs"]["height"] = height
        workflow["6"]["inputs"]["text"] = prompt
        
        # Submit prompt to ComfyUI
        payload = {"prompt": workflow}
        try:
            r = requests.post(f"{self.base_url}/prompt", json=payload, timeout=5)
            r.raise_for_status()
            data = r.json()
            prompt_id = data.get("prompt_id")
            
            return {"status": "success", "prompt_id": prompt_id}
        except requests.exceptions.Timeout:
            print("Error: ComfyUI request timed out. Is the ComfyUI container running?")
            return {"status": "error", "message": "ComfyUI connection timed out."}
        except Exception as e:
            print(f"Error submitting to ComfyUI: {e}")
            return {"status": "error", "message": str(e)}

    def get_job_status(self, prompt_id: str):
        try:
            r = requests.get(f"{self.base_url}/history/{prompt_id}")
            r.raise_for_status()
            data = r.json()
            
            if prompt_id in data:
                # Job completed
                outputs = data[prompt_id].get("outputs", {})
                # Output from Node 9 (Save Image)
                if "9" in outputs:
                    images = outputs["9"].get("images", [])
                    if images:
                        filename = images[0].get("filename")
                        # The image will be in /data/outputs/ (shared volume)
                        return {"status": "completed", "filename": filename}
            
            # If not in history, it might still be in queue
            return {"status": "queued_or_running"}
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

comfy_client = ComfyClient()
