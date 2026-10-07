import threading
import time
import requests
import os

VLM_ENDPOINT = os.getenv("VLM_ENDPOINT", "http://vlm:8000")

class GPUResourceManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.current_owner = "IDLE"
        self.vram_total = 32.0 # GB
        self.vram_used = 0.0

    def acquire_vlm(self):
        """Acquire the GPU lock for VLM inference."""
        self.lock.acquire()
        try:
            if self.current_owner != "VLM":
                print("GPU Manager: Switching context to VLM...")
                # In sequential mode, we would offload FLUX here if needed.
                self.current_owner = "VLM"
                self.vram_used = 22.0 # Approximation for Llama 3.2 11B Vision
            return True
        except Exception as e:
            print(f"Error acquiring VLM: {e}")
            self.lock.release()
            return False

    def release_vlm(self):
        """Release the GPU lock for VLM inference."""
        # For sequential/aggressive offload policies, we might unload the model here.
        self.lock.release()

    def acquire_image(self):
        """Acquire the GPU lock for Image generation."""
        self.lock.acquire()
        try:
            if self.current_owner != "IMAGE":
                print("GPU Manager: Switching context to IMAGE (ComfyUI)...")
                # In sequential mode, we would offload VLM here.
                # (e.g., unload vLLM models from VRAM)
                self.current_owner = "IMAGE"
                self.vram_used = 24.0 # Approximation for FLUX Schnell
            return True
        except Exception as e:
            print(f"Error acquiring IMAGE: {e}")
            self.lock.release()
            return False
            
    def release_image(self):
        """Release the GPU lock for Image generation."""
        # For sequential policies, we might trigger a ComfyUI memory wipe here.
        # requests.get(f"{COMFY_ENDPOINT}/free") # Pseudo-code
        self.lock.release()
        
    def status(self):
        return {
            "owner": self.current_owner,
            "vram_used": self.vram_used,
            "vram_total": self.vram_total
        }

gpu_manager = GPUResourceManager()
