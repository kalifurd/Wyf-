"""
WYF* (What's Your Fantasy) - AI-Powered Interactive Romance Novel Engine
FastAPI server with static file serving, CORS support, Ollama/OpenRouter AI,
Piper TTS, Hermes agent framework, and Kiwix offline content integration.
"""

import os
import json
import subprocess
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import httpx

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="WYF* Engine",
    description="AI-Powered Interactive Romance Novel Engine with Audio/Video Support",
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
        "http://localhost:8080",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Environment Configuration
# ============================================================================
AI_PROVIDER = os.getenv("AI_PROVIDER", "ollama").lower()
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# FastAPI Configuration
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "127.0.0.1")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", 8000))
FASTAPI_RELOAD = os.getenv("FASTAPI_RELOAD", "true").lower() == "true"
FASTAPI_LOG_LEVEL = os.getenv("FASTAPI_LOG_LEVEL", "info")

# Piper TTS Configuration
PIPER_ENABLED = os.getenv("PIPER_ENABLED", "false").lower() == "true"
PIPER_PATH = os.getenv("PIPER_PATH", "/usr/local/bin/piper")
PIPER_VOICE = os.getenv("PIPER_VOICE", "en_US-lessac-medium")
PIPER_OUTPUT_DIR = os.getenv("PIPER_OUTPUT_DIR", "./audio")

# Kiwix Configuration
KIWIX_ENABLED = os.getenv("KIWIX_ENABLED", "false").lower() == "true"
KIWIX_BASE_URL = os.getenv("KIWIX_BASE_URL", "http://localhost:8080")
KIWIX_DATA_DIR = os.getenv("KIWIX_DATA_DIR", "./kiwix-data")

# Hermes Agent Configuration
HERMES_ENABLED = os.getenv("HERMES_ENABLED", "false").lower() == "true"
HERMES_API_URL = os.getenv("HERMES_API_URL", "http://localhost:8001")
HERMES_MODEL = os.getenv("HERMES_MODEL", "hermes-2-pro-7b")

# Output Configuration
OUTPUT_AUDIO = os.getenv("OUTPUT_AUDIO", "false").lower() == "true"
OUTPUT_VIDEO = os.getenv("OUTPUT_VIDEO", "false").lower() == "true"
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./output")

# Create output directories
Path(PIPER_OUTPUT_DIR).mkdir(exist_ok=True)
Path(OUTPUT_DIR).mkdir(exist_ok=True)

# Model configuration per provider
if AI_PROVIDER == "ollama":
    AI_MODEL = os.getenv("OLLAMA_MODEL", "neural-chat")
    print(f"✓ Using Ollama provider")
    print(f"  URL: {OLLAMA_BASE_URL}")
    print(f"  Model: {AI_MODEL}")
    if not OLLAMA_BASE_URL:
        raise ValueError(
            "OLLAMA_BASE_URL not found in environment. "
            "Please create a .env file with OLLAMA_BASE_URL=http://localhost:11434"
        )
elif AI_PROVIDER == "openrouter":
    AI_MODEL = "moonshotai/kimi-k2"
    print(f"✓ Using OpenRouter provider")
    print(f"  Model: {AI_MODEL}")
    if not OPENROUTER_API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY not found in environment. "
            "Please create a .env file with OPENROUTER_API_KEY=your_key"
        )
else:
    raise ValueError(f"Unknown AI provider: {AI_PROVIDER}. Use 'ollama' or 'openrouter'")

# Print service status
if PIPER_ENABLED:
    print(f"✓ Piper TTS enabled (voice: {PIPER_VOICE})")
if KIWIX_ENABLED:
    print(f"✓ Kiwix offline content enabled ({KIWIX_BASE_URL})")
if HERMES_ENABLED:
    print(f"✓ Hermes agent enabled ({HERMES_API_URL})")

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
        "ai_provider": AI_PROVIDER,
        "ai_model": AI_MODEL,
        "services": {
            "piper_tts": PIPER_ENABLED,
            "kiwix": KIWIX_ENABLED,
            "hermes": HERMES_ENABLED,
        },
        "endpoints": {
            "health": "/health",
            "generate": "/api/generate",
            "generate_with_audio": "/api/generate/audio",
            "greenhouse": "/api/wyf/greenhouse",
            "frontend": "http://localhost:8000"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "ai_provider": AI_PROVIDER,
        "ai_model": AI_MODEL,
        "services": {
            "piper_tts": PIPER_ENABLED,
            "kiwix": KIWIX_ENABLED,
            "hermes": HERMES_ENABLED,
        }
    }


# ============================================================================
# AI Generation Endpoints
# ============================================================================
@app.post("/api/generate")
async def generate(request: dict):
    """
    Generate narrative content using configured AI provider.
    
    Expected JSON body:
    {
        "prompt": "user prompt",
        "context": "scene/state context",
        "model": "optional - uses default configured model"
    }
    """
    return await _generate_narrative(request)


@app.post("/api/generate/audio")
async def generate_with_audio(request: dict):
    """
    Generate narrative and convert to audio using Piper TTS.
    Returns both text and audio file path.
    
    Requires: PIPER_ENABLED=true
    """
    if not PIPER_ENABLED:
        raise HTTPException(
            status_code=503,
            detail="Piper TTS is not enabled. Set PIPER_ENABLED=true in .env"
        )
    
    # Generate narrative
    narrative_response = await _generate_narrative(request)
    
    if not narrative_response.get("success"):
        raise HTTPException(status_code=500, detail="Failed to generate narrative")
    
    # Convert to audio
    text = narrative_response.get("response", "")
    audio_path = await _generate_audio(text, request.get("character", "caretaker"))
    
    return {
        "success": True,
        "response": text,
        "audio_url": f"/audio/{Path(audio_path).name}",
        "audio_path": audio_path,
        "provider": narrative_response.get("provider"),
        "usage": narrative_response.get("usage", {})
    }


@app.post("/api/wyf/greenhouse")
async def greenhouse(request: dict):
    """
    Generate greenhouse narrative (compatibility route).
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
        
        system_message = load_caretaker_prompt()
        
        if AI_PROVIDER == "ollama":
            return await _generate_ollama(prompt, context, model, system_message)
        elif AI_PROVIDER == "openrouter":
            return await _generate_openrouter(prompt, context, model, system_message)
        else:
            raise HTTPException(status_code=500, detail=f"Unknown AI provider: {AI_PROVIDER}")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")


# ============================================================================
# Ollama Integration
# ============================================================================
async def _generate_ollama(prompt: str, context: str, model: str, system_message: str):
    """Generate narrative using Ollama local AI."""
    try:
        payload = {
            "model": model,
            "prompt": f"{system_message}\n\nContext: {context}\n\nUser: {prompt}",
            "stream": False,
            "temperature": 0.8,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=60.0
            )
            response.raise_for_status()
        
        data = response.json()
        
        return {
            "success": True,
            "response": data.get("response", "").strip(),
            "model": model,
            "provider": "ollama",
            "usage": {
                "prompt_tokens": data.get("prompt_eval_count", 0),
                "completion_tokens": data.get("eval_count", 0),
            }
        }
    
    except httpx.HTTPError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama API error: {str(e)}. Ensure Ollama is running at {OLLAMA_BASE_URL}"
        )


# ============================================================================
# OpenRouter Integration
# ============================================================================
async def _generate_openrouter(prompt: str, context: str, model: str, system_message: str):
    """Generate narrative using OpenRouter cloud AI."""
    try:
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
            "provider": "openrouter",
            "usage": data.get("usage", {})
        }
    
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"OpenRouter API error: {str(e)}")


# ============================================================================
# Piper TTS Integration
# ============================================================================
async def _generate_audio(text: str, character: str = "caretaker") -> str:
    """
    Convert narrative text to speech using Piper.
    Returns path to generated audio file.
    """
    if not PIPER_ENABLED:
        raise HTTPException(status_code=503, detail="Piper TTS is disabled")
    
    try:
        output_file = Path(PIPER_OUTPUT_DIR) / f"{character}_{hash(text)}.wav"
        
        # Run Piper (espeak-ng backend for prosody)
        process = subprocess.Popen(
            [
                PIPER_PATH,
                "--model", PIPER_VOICE,
                "--output_file", str(output_file),
                "--length_scale", "1.0",
                "--noise_scale", "0.667",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        
        stdout, stderr = process.communicate(input=text.encode("utf-8"))
        
        if process.returncode != 0:
            raise Exception(f"Piper error: {stderr.decode('utf-8')}")
        
        return str(output_file)
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"TTS generation error: {str(e)}"
        )


# ============================================================================
# Audio File Serving
# ============================================================================
@app.get("/audio/{filename}")
async def serve_audio(filename: str):
    """Serve generated audio files."""
    file_path = Path(PIPER_OUTPUT_DIR) / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(file_path, media_type="audio/wav")


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
        host=FASTAPI_HOST,
        port=FASTAPI_PORT,
        reload=FASTAPI_RELOAD,
        log_level=FASTAPI_LOG_LEVEL
    )
