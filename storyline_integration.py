"""
WYF* Storyline Integration Guide
=================================

This module demonstrates how to integrate the StorylineGenerator addon into server.py
to enable dynamic A/B/C narrative generation with hidden story influence.

KEY INTEGRATION POINTS:

1. Initialize the generator at startup
2. Modify _generate_narrative() to use context-aware prompts
3. Extend request schema to include storyline tracking
4. Add new endpoint for story progression tracking
"""

# ============================================================================
# SERVER.PY INTEGRATION EXAMPLE
# ============================================================================

"""
Add this to server.py after imports:

from storyline_generator import StorylineGenerator, StoryTone
import logging

# Initialize storyline generator at startup
storyline_gen = StorylineGenerator()

# Generate the trilogy once (or on-demand)
try:
    storylines = storyline_gen.generate_trilogy(
        base_prompt="The Lost Heirloom",
        setting="Victorian London, 1888",
        tone_a=StoryTone.ROMANTIC,
        tone_b=StoryTone.MYSTERIOUS,
        tone_c=StoryTone.DARK
    )
    print("✓ Storyline trilogy generated successfully")
except Exception as e:
    print(f"⚠ Warning: Could not generate storylines: {e}")
    storyline_gen = None
"""

# ============================================================================
# MODIFIED ENDPOINT: _generate_narrative with Storyline Support
# ============================================================================

INTEGRATION_EXAMPLE = """
# In server.py, replace _generate_narrative() with this enhanced version:

async def _generate_narrative(request: dict):
    '''
    Internal handler for narrative generation.
    Now supports Story A/B/C with dynamic context injection.
    
    Expected request body:
    {
        "prompt": "user action/dialogue",
        "context": "scene context",
        "model": "optional model override",
        "storyline": "main_a" or "main_b" (default: main_a),
        "scene_id": "main_a_scene_1" (scene to contextualize),
        "progress": 0-100 (player progress for hidden story reveals)
    }
    '''
    try:
        prompt = request.get("prompt")
        context = request.get("context", "")
        model = request.get("model", AI_MODEL)
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # NEW: Get storyline parameters
        storyline_type = request.get("storyline", "main_a")
        scene_id = request.get("scene_id", f"{storyline_type}_scene_1")
        progress_percentage = request.get("progress", 0)
        
        # Load base Caretaker prompt
        base_system_message = load_caretaker_prompt()
        
        # NEW: Generate context-aware prompt if storyline generator is available
        if storyline_gen:
            system_message = storyline_gen.generate_caretaker_context(
                storyline_type=storyline_type,
                scene_id=scene_id,
                progress_percentage=progress_percentage,
                base_caretaker_prompt=base_system_message
            )
        else:
            system_message = base_system_message
        
        # Route to AI provider
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
"""

# ============================================================================
# NEW ENDPOINT: Get Scene with Influences
# ============================================================================

NEW_ENDPOINT_EXAMPLE = """
# Add this endpoint to server.py after /api/generate:

@app.get("/api/storyline/scene/{storyline_type}/{scene_id}")
async def get_scene_with_influences(
    storyline_type: str,
    scene_id: str,
    progress: float = 0
):
    '''
    Get a scene from the storyline system with influences from Story C injected.
    
    Returns the scene structure plus influence metadata (dialogue hints, choice impacts, etc.)
    
    Args:
        storyline_type: "main_a" or "main_b"
        scene_id: e.g., "main_a_scene_1"
        progress: Player progress 0-100
        
    Returns:
        Scene dict with 'influences' key containing narrative modifications
    '''
    if not storyline_gen:
        raise HTTPException(
            status_code=503,
            detail="Storyline system not initialized"
        )
    
    try:
        scene_info = storyline_gen.get_scene_with_influences(
            storyline_type=storyline_type,
            scene_id=scene_id,
            progress_percentage=progress
        )
        
        if "error" in scene_info:
            raise HTTPException(status_code=404, detail=scene_info["error"])
        
        return {
            "success": True,
            "scene": scene_info,
            "progression_level": scene_info.get("progression_level")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scene retrieval error: {str(e)}")
"""

# ============================================================================
# NEW ENDPOINT: Reveal Hidden Storyline
# ============================================================================

REVEAL_ENDPOINT_EXAMPLE = """
# Add this endpoint to server.py:

@app.post("/api/storyline/progress")
async def update_story_progress(request: dict):
    '''
    Update player progress and return revelations from Story C.
    
    Call this periodically (e.g., every 15% of story completion) to unlock hidden content.
    
    Args:
        progress: float (0-100) - player's current progress
        
    Returns:
        Hidden story revelations, active influences, and unlocked scenes
    '''
    if not storyline_gen:
        raise HTTPException(
            status_code=503,
            detail="Storyline system not initialized"
        )
    
    try:
        progress = request.get("progress", 0)
        
        result = storyline_gen.reveal_hidden_storyline_gradually(progress)
        
        return {
            "success": True,
            "progress": result.get("progress"),
            "revelation": result.get("revelation_text"),
            "revealed_scenes": result.get("revealed_scenes", []),
            "active_influences": result.get("active_influence_count", 0),
            "hidden_truth": result.get("hidden_truth")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Progress update error: {str(e)}")
"""

# ============================================================================
# NEW ENDPOINT: List Available Storylines
# ============================================================================

LIST_ENDPOINT_EXAMPLE = """
# Add this endpoint to server.py:

@app.get("/api/storyline/list")
async def list_storylines():
    '''
    Return available storylines and their metadata.
    Hidden storyline (C) is NOT returned until progress > 0.
    '''
    if not storyline_gen:
        raise HTTPException(
            status_code=503,
            detail="Storyline system not initialized"
        )
    
    try:
        visible = storyline_gen.get_visible_storylines()
        
        return {
            "success": True,
            "available_storylines": [
                {
                    "type": s.storyline_type.value,
                    "title": s.title,
                    "theme": s.theme,
                    "tone": s.tone.value,
                    "protagonist": s.protagonist,
                    "antagonist": s.antagonist,
                    "goal": s.goal,
                    "num_scenes": len(s.scenes)
                }
                for s in visible.values()
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Listing error: {str(e)}")
"""

# ============================================================================
# CLIENT-SIDE USAGE EXAMPLE
# ============================================================================

CLIENT_EXAMPLE = """
// Frontend JavaScript example

async function generateNarrativeWithContext(playerAction, progress) {
    const response = await fetch('http://localhost:8000/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            prompt: playerAction,
            context: "You stand in the Victorian greenhouse, candlelight dancing across the glass.",
            storyline: "main_a",  // or "main_b"
            scene_id: "main_a_scene_1",
            progress: progress,   // Track player progress
            model: "kimi-k2"
        })
    });
    
    const data = await response.json();
    return data.response;  // AI-generated narrative with hidden context
}

async function checkForRevealedContent(progress) {
    const response = await fetch('http://localhost:8000/api/storyline/progress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ progress: progress })
    });
    
    const data = await response.json();
    
    if (data.revelation) {
        console.log("Hidden truth unlocked:", data.revelation);
        displayNewContent(data.revealed_scenes);
    }
}

async function getSceneWithInfluences(sceneId, progress) {
    const response = await fetch(
        `http://localhost:8000/api/storyline/scene/main_a/${sceneId}?progress=${progress}`
    );
    
    const data = await response.json();
    
    // data.scene.influences contains:
    // - dialogue_hints: NPC dialogue modifications
    // - env_modifications: Environment details that hint at hidden truth
    // - choice_impacts: Consequences of player choices
    // - narrative_directives: AI instruction changes
    
    console.log("Choice impacts:", data.scene.influences.choice_impacts);
}
"""

# ============================================================================
# REQUEST SCHEMA DOCUMENTATION
# ============================================================================

REQUEST_SCHEMA = """
POST /api/generate (Enhanced)
============================

Request Body:
{
    "prompt": string,              # Required. Player action/dialogue
    "context": string,             # Optional. Scene context
    "model": string,               # Optional. Override default model
    
    // NEW: Storyline tracking
    "storyline": "main_a|main_b",  # Optional. Which storyline path (default: main_a)
    "scene_id": string,            # Optional. Current scene for context (default: {storyline}_scene_1)
    "progress": number             # Optional. Player progress 0-100 (default: 0)
}

Response:
{
    "success": boolean,
    "response": string,            # AI-generated narrative
    "model": string,
    "provider": "ollama|openrouter",
    "usage": { ... }               # Token usage
}

EXAMPLE REQUEST:
{
    "prompt": "I reach out to touch his hand.",
    "context": "Ashford steps closer, the candlelight casting him in shadow.",
    "storyline": "main_a",
    "scene_id": "main_a_scene_2",
    "progress": 35
}
"""

# ============================================================================
# PROGRESS TRACKING LOGIC (Frontend Responsibility)
# ============================================================================

PROGRESS_TRACKING = """
Progress tracking should be based on:
- Scenes completed: (completed_scenes / total_scenes) * 100
- Choices made: (choices_made / expected_choices) * 100
- Time elapsed: (elapsed_seconds / expected_session_length) * 100

Example progression:
  0% - Player hasn't made any choices yet
  25% - Player has completed ~2-3 scenes
       → First hints at inconsistencies (reveal_hidden_storyline_gradually triggers)
  
  50% - Player is halfway through visible storylines
       → Margaret's hesitation becomes apparent
       → Environmental details hint at conspiracy
  
  75% - Player approaching end of Story A/B
       → Clear signs that something is wrong
       → Choice consequences become weighted
  
  100% - Story conclusion
        → Full access to Story C
        → Final revelation of conspiracy

Call /api/storyline/progress periodically to get updated revelations.
"""

# ============================================================================
# TESTING THE INTEGRATION
# ============================================================================

TESTING_EXAMPLE = """
# Quick test to verify storyline integration works:

import httpx
import asyncio

async def test_integration():
    async with httpx.AsyncClient() as client:
        # 1. Get available storylines
        resp = await client.get("http://localhost:8000/api/storyline/list")
        print("Available storylines:", resp.json())
        
        # 2. Generate narrative with Story A context
        resp = await client.post(
            "http://localhost:8000/api/generate",
            json={
                "prompt": "I look into your eyes.",
                "storyline": "main_a",
                "scene_id": "main_a_scene_1",
                "progress": 0
            }
        )
        print("Initial narrative:", resp.json()["response"][:100] + "...")
        
        # 3. Update progress to 50% and generate with hidden context
        resp = await client.post(
            "http://localhost:8000/api/generate",
            json={
                "prompt": "I look into your eyes.",
                "storyline": "main_a",
                "scene_id": "main_a_scene_1",
                "progress": 50  # Now with hidden context injected
            }
        )
        print("Mid-game narrative:", resp.json()["response"][:100] + "...")
        
        # 4. Check what's been revealed
        resp = await client.post(
            "http://localhost:8000/api/storyline/progress",
            json={"progress": 50}
        )
        result = resp.json()
        print("Revelation at 50%:", result["revelation"])
        print("Active influences:", result["active_influences"])

asyncio.run(test_integration())
"""

if __name__ == "__main__":
    print(__doc__)
    print("\n" + "=" * 70)
    print("INTEGRATION EXAMPLES")
    print("=" * 70)
    print("\n" + INTEGRATION_EXAMPLE)
    print("\n" + NEW_ENDPOINT_EXAMPLE)
    print("\n" + REVEAL_ENDPOINT_EXAMPLE)
    print("\n" + LIST_ENDPOINT_EXAMPLE)
    print("\n" + CLIENT_EXAMPLE)
    print("\n" + REQUEST_SCHEMA)
    print("\n" + PROGRESS_TRACKING)
    print("\n" + TESTING_EXAMPLE)
