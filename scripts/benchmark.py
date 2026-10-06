import time
import requests

def run_benchmark():
    print("=================================")
    print("Multimodal Sandbox Benchmark")
    print("=================================")
    
    print("Starting VLM test...")
    start_vlm = time.time()
    try:
        # Mock checking VLM health
        r = requests.get("http://localhost:8000/api/status")
        vlm_time = time.time() - start_vlm
        print(f"VLM responded in {vlm_time:.2f}s")
    except Exception as e:
        print("VLM check failed:", e)

    print("Starting Image generation test...")
    start_img = time.time()
    try:
        r = requests.post("http://localhost:8000/api/image/generate", json={
            "prompt": "benchmark test image",
            "width": 1024,
            "height": 1024
        })
        if r.status_code == 200:
            job_id = r.json()["job_id"]
            while True:
                status_r = requests.get(f"http://localhost:8000/api/image/jobs/{job_id}")
                if status_r.json()["status"] == "completed":
                    break
                time.sleep(0.5)
            img_time = time.time() - start_img
            print(f"Image generated in {img_time:.2f}s")
        else:
            print("Image generation request failed:", r.status_code)
    except Exception as e:
        print("Image check failed:", e)
        
if __name__ == "__main__":
    run_benchmark()
