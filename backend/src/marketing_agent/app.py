"""Marketing Agent FastAPI Application

This module defines the FastAPI application for the Marketing Analyst Supervisor Agent.
It serves the marketing agent graph and provides endpoints for ad analysis workflows.
"""

import pathlib

from fastapi import FastAPI, Response
from fastapi.staticfiles import StaticFiles

from marketing_agent.graph import graph

# Define the FastAPI app for the marketing agent
app = FastAPI(
    title="Marketing Analyst Supervisor Agent",
    description="AI-powered marketing analysis agent for advertising insights, improvements, and strategic takeaways",
    version="1.0.0",
)


def create_frontend_router(build_dir="../frontend/dist"):
    """Creates a router to serve the React frontend.

    Args:
        build_dir: Path to the React build directory relative to this file.

    Returns:
        A Starlette application serving the frontend.
    """
    build_path = pathlib.Path(__file__).parent.parent.parent / build_dir

    if not build_path.is_dir() or not (build_path / "index.html").is_file():
        print(
            f"WARN: Frontend build directory not found or incomplete at {build_path}. Serving frontend will likely fail."
        )
        # Return a dummy router if build isn't ready
        from starlette.routing import Route

        async def dummy_frontend(request):
            return Response(
                "Frontend not built. Run 'npm run build' in the frontend directory.",
                media_type="text/plain",
                status_code=503,
            )

        return Route("/{path:path}", endpoint=dummy_frontend)

    return StaticFiles(directory=build_path, html=True)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for the marketing agent."""
    return {
        "status": "healthy",
        "agent": "marketing-analyst-supervisor-agent",
        "version": "1.0.0"
    }


# Agent info endpoint
@app.get("/agent/info")
async def agent_info():
    """Get information about the marketing agent capabilities."""
    return {
        "name": "Marketing Analyst Supervisor Agent",
        "description": "AI-powered marketing analysis for advertising insights and strategic recommendations",
        "capabilities": [
            "Date extraction from user queries",
            "Personalized greeting generation",
            "Ad image analysis using Gemini Vision",
            "Performance improvement suggestions",
            "Strategic takeaways synthesis"
        ],
        "supported_formats": ["jpg", "jpeg", "png", "webp"],
        "max_image_size": "10MB"
    }


# Mount the frontend under /app to not conflict with the LangGraph API routes
app.mount(
    "/app",
    create_frontend_router(),
    name="frontend",
)

# Export the graph for LangGraph server integration
__all__ = ["app", "graph"]

