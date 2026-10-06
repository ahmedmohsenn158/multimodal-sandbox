from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import health, image, status

app = FastAPI(title="Multimodal Sandbox API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(image.router, prefix="/api/image", tags=["image"])
app.include_router(status.router, prefix="/api/status", tags=["status"])

@app.get("/")
def root():
    return {"message": "Sandbox API Running"}
