from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from analyzer import analyze_website
from generator import generate_project
from models import AnalyzeRequest, GenerateProjectRequest


app = FastAPI(
    title="Web2App LAB API",
    version="2.0.0",
    description="Website to PWA, Android and WebView project generator API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "name": "Web2App LAB",
        "version": "2.0.0",
        "status": "online",
        "message": "Web2App LAB backend is running"
    }


@app.get("/api/health")
async def health():
    return {
        "status": "online",
        "service": "web2app-lab-backend",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@app.post("/api/analyze")
async def analyze(payload: AnalyzeRequest):
    try:
        return await analyze_website(payload.url)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Website analysis failed: {str(exc)}"
        )


@app.post("/api/projects/generate")
async def project_generate(payload: GenerateProjectRequest):
    try:
        return generate_project(payload)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Project generation failed: {str(exc)}"
        )