import threading
import time

class GPUResourceManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.current_owner = "IDLE"
        self.vram_total = 32.0 # GB
        self.vram_used = 0.0

    def acquire_vlm(self):
        with self.lock:
            if self.current_owner != "VLM":
                print("Switching GPU context to VLM...")
                # TODO: Implement model load/unload
                time.sleep(1) # mock switch time
                self.current_owner = "VLM"
                self.vram_used = 22.0
            return True

    def release_vlm(self):
        # We might keep it resident based on policy
        pass

    def acquire_image(self):
        with self.lock:
            if self.current_owner != "IMAGE":
                print("Switching GPU context to IMAGE...")
                # TODO: Implement model load/unload
                time.sleep(1) # mock switch time
                self.current_owner = "IMAGE"
                self.vram_used = 24.0
            return True
            
    def release_image(self):
        pass
        
    def status(self):
        return {
            "owner": self.current_owner,
            "vram_used": self.vram_used,
            "vram_total": self.vram_total
        }

gpu_manager = GPUResourceManager()
