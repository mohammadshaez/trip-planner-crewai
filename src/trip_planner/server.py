"""FastAPI web server for the Trip Planner CrewAI application.

Provides a clean REST API and serves an interactive single-page UI for configuring
expedition parameters, kicking off the Crew, and viewing the generated dossier.
"""

import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure project source is in Python search path
project_src = Path(__file__).resolve().parent.parent
if str(project_src) not in sys.path:
    sys.path.insert(0, str(project_src))

# Load .env variables
load_dotenv()

from trip_planner.crew import TripPlannerCrew

app = FastAPI(
    title="Wanderlust AI — Expedition Planner",
    description="CrewAI Hierarchical Multi-Agent Trip Planning System",
    version="1.0.0",
)

# Allow CORS for local development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
OUTPUT_FILE = Path("output/trip_plan.md")

# Mount static files directory if it exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


class PlanRequest(BaseModel):
    destination: str = Field(..., example="Kyoto, Japan")
    number_of_days: int = Field(default=5, ge=1, le=30, example=5)
    budget_tier: str = Field(default="mid", example="mid")
    interests: str = Field(
        default="food-focused cultural exploration, authentic tea houses, and historic temples",
        example="food-focused cultural exploration, authentic tea houses, and historic temples",
    )


class PlanResponse(BaseModel):
    success: bool
    markdown: str
    destination: str
    number_of_days: int
    budget_tier: str
    generated_at: str


@app.get("/", response_class=HTMLResponse)
async def serve_index():
    """Serves the main single page web application."""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Index HTML not found")
    return FileResponse(index_file)


@app.get("/api/last-plan")
async def get_last_plan():
    """Returns the most recently generated trip plan from output/trip_plan.md."""
    if not OUTPUT_FILE.exists():
        return {
            "exists": False,
            "content": "",
            "message": "No trip plan has been generated yet.",
        }

    try:
        content = OUTPUT_FILE.read_text(encoding="utf-8")
        modified_time = datetime.fromtimestamp(OUTPUT_FILE.stat().st_mtime).strftime(
            "%B %d, %Y at %I:%M %p"
        )
        return {
            "exists": True,
            "content": content,
            "updated_at": modified_time,
            "file_size": OUTPUT_FILE.stat().st_size,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read trip dossier: {e}")


def _execute_crew(inputs: Dict[str, Any]) -> str:
    """Synchronous worker that runs the Crew kickoff in an executor."""
    crew_instance = TripPlannerCrew().crew()
    result = crew_instance.kickoff(inputs=inputs)
    return str(result.raw)


@app.post("/api/plan", response_model=PlanResponse)
async def generate_plan(request: PlanRequest):
    """Kicks off the Trip Planner multi-agent crew with custom parameters."""
    inputs = {
        "destination": request.destination.strip(),
        "number_of_days": str(request.number_of_days),
        "budget_tier": request.budget_tier.strip().lower(),
        "interests": request.interests.strip(),
    }

    try:
        # Run synchronous CrewAI kickoff in thread pool to prevent blocking asyncio loop
        markdown_result = await asyncio.to_thread(_execute_crew, inputs)

        # Ensure output directory exists and file is up-to-date
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_FILE.write_text(markdown_result, encoding="utf-8")

        return PlanResponse(
            success=True,
            markdown=markdown_result,
            destination=request.destination,
            number_of_days=request.number_of_days,
            budget_tier=request.budget_tier,
            generated_at=datetime.now().strftime("%B %d, %Y at %I:%M %p"),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Crew execution encountered an error: {str(e)}"
        )


@app.get("/api/status")
async def get_system_status():
    """Returns runtime model and search capability status."""
    return {
        "status": "online",
        "model": os.getenv("MODEL", "gpt-4o-mini"),
        "search_enabled": bool(
            os.getenv("SERPER_API_KEY")
            and not os.getenv("SERPER_API_KEY", "").startswith("your_")
        ),
        "has_last_plan": OUTPUT_FILE.exists(),
    }


def serve():
    """Entry point for running the web UI server via CLI or hatch/uv scripts."""
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"\n🚀 Launching Wanderlust AI Trip Planner at: http://{host}:{port}\n")
    uvicorn.run("trip_planner.server:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    serve()
