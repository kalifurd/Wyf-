"""
WYF* (What's Your Fantasy) - AI-Powered Interactive Romance Novel Engine
FastAPI server with static file serving, CORS support, and OpenRouter AI integration.
"""

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="WYF* Engine",
    description="AI-Powered Interactive Romance Novel Engine",
    version="0.1.0"
)

# ============================================================================
# CORS Configuration - Allow local development
# ============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8000",
        "http://localhost:3000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Environment Configuration
# ============================================================================
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
AI_MODEL = "moonshotai/kimi-k2"  # Full provider/model string for OpenRouter

if not OPENROUTER_API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY not found in environment. "
        "Please create a .env file with OPENROUTER_API_KEY=your_key"
    )

# ============================================================================
# Root Endpoint
# ============================================================================
@app.get("/")
async def root():
    """Health check and API information."""
    return {
        "status": "running",
        "app": "WYF* Engine",
        "version": "0.1.0",
        "endpoints": {
            "health": "/health",
            "generate": "/api/generate",
            "greenhouse": "/api/wyf/greenhouse",
            "frontend": "http://localhost:8000 (served via StaticFiles)"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "ai_model": AI_MODEL,
        "api_configured": bool(OPENROUTER_API_KEY)
    }


# ============================================================================
# AI Generation Endpoint - Primary
# ============================================================================
@app.post("/api/generate")
async def generate(request: dict):
    """
    Generate narrative content using OpenRouter AI.
    
    Expected JSON body:
    {
        "prompt": "user prompt",
        "context": "scene/state context",
        "model": "optional - defaults to moonshotai/kimi-k2"
    }
    """
    return await _generate_narrative(request)


# ============================================================================
# AI Generation Endpoint - Greenhouse (Compatibility Route)
# ============================================================================
@app.post("/api/wyf/greenhouse")
async def greenhouse(request: dict):
    """
    Generate greenhouse narrative (compatibility route for existing frontend).
    Routes to the same handler as /api/generate.
    """
    return await _generate_narrative(request)


# ============================================================================
# Shared Generation Logic
# ============================================================================
async def _generate_narrative(request: dict):
    """
    Internal handler for narrative generation.
    """
    try:
        prompt = request.get("prompt")
        context = request.get("context", "")
        model = request.get("model", AI_MODEL)
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Build system message from caretaker persona
        system_message = load_caretaker_prompt()
        
        # Prepare OpenRouter request
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": f"{context}\n\nUser: {prompt}"}
            ],
            "temperature": 0.8,
            "max_tokens": 1024,
        }
        
        # Call OpenRouter API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            response.raise_for_status()
        
        data = response.json()
        
        return {
            "success": True,
            "response": data["choices"][0]["message"]["content"],
            "model": data["model"],
            "usage": data.get("usage", {})
        }
    
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"OpenRouter API error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Generation error: {str(e)}"
        )


# ============================================================================
# Helper Functions
# ============================================================================
def load_caretaker_prompt() -> str:
    """Load the Caretaker persona prompt from prompts/caretaker.txt"""
    caretaker_path = Path(__file__).parent / "prompts" / "caretaker.txt"
    
    try:
        with open(caretaker_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        # Fallback system prompt if caretaker.txt not found
        return (
            "You are the Caretaker, a witty and romantic AI narrator for an interactive "
            "romance novel engine. Guide the user through an immersive, emotionally engaging "
            "Victorian-era narrative. Maintain narrative consistency, respond to user choices, "
            "and generate dynamic, character-driven prose."
        )


# ============================================================================
# Static Files - Serve frontend from /static directory
# ============================================================================
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
else:
    print(f"Warning: Static directory not found at {static_dir}")


# ============================================================================
# Run Server
# ============================================================================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
