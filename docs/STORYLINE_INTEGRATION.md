"""
Integration Guide: Storyline Generator + FastAPI Server
========================================================

This document explains how to wire the StorylineGenerator into server.py
to enable dynamic hidden story influence during gameplay.

ARCHITECTURE OVERVIEW
=====================

The StorylineGenerator creates three interconnected storylines (A, B, C) where:
- Stories A & B are visible to the player
- Story C is hidden and revealed gradually
- As C is revealed, it modifies the Caretaker's system prompt to subtly shift
  narrative tone, character behavior, and player choice consequences

DATA FLOW
=========

1. STARTUP (once per session)
   - Initialize StorylineGenerator
   - Call generate_trilogy() to create all three stories
   - Load base caretaker.txt with {{HIDDEN_CONTEXT}} marker

2. GAMEPLAY (per user action)
   - Player chooses action/dialogue
   - Frontend sends: { prompt, context, storyline, scene_id, progress }
   - Server calls generate_caretaker_context() to modify base prompt
   - Modified prompt + player action sent to AI
   - AI generates narrative response with hidden context baked in

3. PROGRESS TRACKING
   - Maintain player progress (0-100%) in session/database
   - Pass progress to generate_caretaker_context()
   - As progress increases, {{HIDDEN_CONTEXT}} injection becomes richer

IMPLEMENTATION
==============

Step 1: Add to imports in server.py
-----------------------------------

from storyline_generator import (
    StorylineGenerator,
    StoryTone,
)

Step 2: Initialize generator at startup
----------------------------------------

# Near the top of server.py, after app creation:

# Initialize storyline generator
storyline_generator = StorylineGenerator()

print("🎭 Generating storylines...")
storylines = storyline_generator.generate_trilogy(
    base_prompt="The Lost Heirloom",
    setting="Victorian London, 1888",
    tone_a=StoryTone.ROMANTIC,
    tone_b=StoryTone.MYSTERIOUS,
    tone_c=StoryTone.DARK
)
print(f"✓ Generated {len(storylines)} storylines")

Step 3: Load caretaker prompt with marker
------------------------------------------

def load_caretaker_prompt() -> str:
    '''Load the Caretaker persona prompt from prompts/caretaker.txt'''
    caretaker_path = Path(__file__).parent / "prompts" / "caretaker.txt"
    
    try:
        with open(caretaker_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            # Verify marker exists
            if "{{HIDDEN_CONTEXT}}" not in content:
                print(
                    "⚠️  WARNING: {{HIDDEN_CONTEXT}} marker not found in caretaker.txt. "
                    "Hidden story injection will not work."
                )
            return content
    except FileNotFoundError:
        # Fallback prompt
        return (
            "You are the Caretaker, a witty and romantic AI narrator for an interactive "
            "romance novel engine. Guide the user through an immersive, emotionally engaging "
            "Victorian-era narrative. Maintain narrative consistency, respond to user choices, "
            "and generate dynamic, character-driven prose.\\n\\n{{HIDDEN_CONTEXT}}"
        )

Step 4: Modify _generate_narrative to use hidden context
---------------------------------------------------------

async def _generate_narrative(request: dict):
    '''
    Internal handler for narrative generation.
    
    Expected JSON body:
    {
        "prompt": "user action",
        "context": "scene description",
        "storyline": "main_a" or "main_b",
        "scene_id": "main_a_scene_1",
        "progress": 0-100,  # Player progress percentage
        "model": "kimi-k2"  # optional
    }
    '''
    try:
        prompt = request.get("prompt")
        context = request.get("context", "")
        model = request.get("model", AI_MODEL)
        storyline = request.get("storyline", "main_a")
        scene_id = request.get("scene_id", "main_a_scene_1")
        progress = request.get("progress", 0)
        
        if not prompt:
            raise HTTPException(status_code=400, detail="Prompt is required")
        
        # Load base caretaker prompt
        base_caretaker_prompt = load_caretaker_prompt()
        
        # INJECT hidden story context into the prompt
        modified_system_message = storyline_generator.generate_caretaker_context(
            storyline_type=storyline,
            scene_id=scene_id,
            progress_percentage=progress,
            base_caretaker_prompt=base_caretaker_prompt
        )
        
        if AI_PROVIDER == "ollama":
            return await _generate_ollama(
                prompt, context, model, modified_system_message
            )
        elif AI_PROVIDER == "openrouter":
            return await _generate_openrouter(
                prompt, context, model, modified_system_message
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Unknown AI provider: {AI_PROVIDER}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation error: {str(e)}")

Step 5: New endpoint to get scene metadata with influences
----------------------------------------------------------

@app.post("/api/scene/info")
async def get_scene_info(request: dict):
    '''
    Get scene metadata including influence information.
    Useful for UI to surface high-impact consequences to player.
    
    Request body:
    {
        "storyline": "main_a",
        "scene_id": "main_a_scene_1",
        "progress": 45
    }
    
    Returns:
    {
        "scene": {...},
        "influences": {
            "dialogue_hints": [...],
            "choice_impacts": {...},  # Shows consequence severity
            "narrative_directives": [...]
        },
        "progression_level": "developing"
    }
    '''
    try:
        storyline = request.get("storyline")
        scene_id = request.get("scene_id")
        progress = request.get("progress", 0)
        
        if not storyline or not scene_id:
            raise HTTPException(
                status_code=400,
                detail="storyline and scene_id required"
            )
        
        scene_info = storyline_generator.get_scene_with_influences(
            storyline_type=storyline,
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
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

Step 6: Endpoint to reveal/check hidden story progress
-------------------------------------------------------

@app.post("/api/storyline/reveal")
async def reveal_hidden_progress(request: dict):
    '''
    Reveal hidden story content based on player progress.
    Call this periodically as player advances through the game.
    
    Request body:
    {
        "progress": 60  # 0-100
    }
    
    Returns:
    {
        "progress": 60,
        "revelation_text": "The true conspiracy begins to take shape...",
        "revealed_scenes": [...],
        "active_influence_count": 3,
        "hidden_truth": "Reveal the hidden machinations..."
    }
    '''
    try:
        progress = request.get("progress", 0)
        
        if progress < 0 or progress > 100:
            raise HTTPException(
                status_code=400,
                detail="progress must be 0-100"
            )
        
        revelation = storyline_generator.reveal_hidden_storyline_gradually(progress)
        
        return {
            "success": True,
            **revelation
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

FRONTEND USAGE EXAMPLES
=======================

Example 1: Generate narrative response with hidden context
----------------------------------------------------------

// Player types action in Story A at 45% progress
fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        prompt: "I take Ashford's hand.",
        context: "You are in the greenhouse with Lord Ashford. Moonlight streams through the glass ceiling.",
        storyline: "main_a",
        scene_id: "main_a_scene_2",
        progress: 45  // Player has seen some hidden clues
    })
})
.then(r => r.json())
.then(data => {
    // Response includes subtle hints about Ashford's true motives
    console.log(data.response);
});

At 45% progress, the Caretaker's prompt now includes:
  "When depicting Ashford's dialogue with Isabelle, emphasize his careful 
   attention to her family situation and financial circumstances..."

So the generated narrative reflects this—perhaps Ashford asks about her 
family's land holdings, or mentions knowing someone in her father's firm.

Example 2: Check what influence is active for a scene
------------------------------------------------------

fetch('/api/scene/info', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        storyline: "main_b",
        scene_id: "main_b_scene_3",
        progress: 75
    })
})
.then(r => r.json())
.then(data => {
    const influences = data.scene.influences;
    
    // Check for severe consequences
    if (influences.choice_impacts) {
        for (const [key, impact] of Object.entries(influences.choice_impacts)) {
            if (impact.severity === "severe") {
                // Highlight this choice in red/warning color
                console.log(`⚠️  ${key}: ${impact.description}`);
            }
        }
    }
});

Example 3: Trigger hidden story revelation
-------------------------------------------

// When player progress reaches a threshold, reveal more
fetch('/api/storyline/reveal', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ progress: 50 })
})
.then(r => r.json())
.then(data => {
    if (data.revelation_text) {
        // Show revelation message to player
        showNotification(data.revelation_text);
        
        // Optionally show revealed scenes
        console.log("Hidden scenes unlocked:", data.revealed_scenes.length);
    }
});

TESTING
=======

To verify the integration works:

1. Check marker exists:
   grep "{{HIDDEN_CONTEXT}}" prompts/caretaker.txt

2. Test prompt injection:
   python -c "
   from storyline_generator import StorylineGenerator
   gen = StorylineGenerator()
   gen.generate_trilogy('Test', setting='Test Setting')
   prompt = open('prompts/caretaker.txt').read()
   modified = gen.generate_caretaker_context('main_a', 'main_a_scene_1', 50, prompt)
   print('INJECTED' if '{{HIDDEN_CONTEXT}}' not in modified else 'MARKER STILL PRESENT')
   "

3. Test scene influence:
   python -c "
   from storyline_generator import StorylineGenerator
   gen = StorylineGenerator()
   gen.generate_trilogy('Test', setting='Test Setting')
   scene = gen.get_scene_with_influences('main_a', 'main_a_scene_1', 75)
   print('Influences:', scene.get('influences', {}).keys())
   "

4. Run the server and call endpoints:
   python server.py
   
   # In another terminal:
   curl -X POST http://localhost:8000/api/scene/info \\
     -H "Content-Type: application/json" \\
     -d '{"storyline": "main_a", "scene_id": "main_a_scene_1", "progress": 50}'

DEBUGGING
=========

If hidden context isn't injecting:

1. Check the marker exists:
   - Must be exactly: {{HIDDEN_CONTEXT}}
   - Case-sensitive
   - Must be in prompts/caretaker.txt

2. Enable logging:
   - Add to server.py: logging.basicConfig(level=logging.DEBUG)
   - Look for: "Injected hidden context for..." messages
   - Look for: "{{HIDDEN_CONTEXT}} marker not found..." warnings

3. Verify influences are generated:
   - Call /api/scene/info with progress > 25
   - Check "influences" contains "narrative_directives" entries

4. Manual test:
   from storyline_generator import StorylineGenerator, StoryTone
   gen = StorylineGenerator()
   gen.generate_trilogy("Test", tone_a=StoryTone.ROMANTIC)
   
   base = open('prompts/caretaker.txt').read()
   modified = gen.generate_caretaker_context(
       "main_a", "main_a_scene_1", 60, base
   )
   
   # Should NOT contain {{HIDDEN_CONTEXT}} if properly injected
   assert "{{HIDDEN_CONTEXT}}" not in modified
   print("✓ Injection successful")

PRODUCTION NOTES
================

1. PERFORMANCE
   - generate_trilogy() is called once at startup
   - generate_caretaker_context() is called per request (fast)
   - If concerns about prompt size, compress old revelations after 100%

2. STATE MANAGEMENT
   - Progress should be tracked per-user in session or database
   - Recommend storing: (user_id, progress, last_scene, timestamp)
   - Progress is not reset on page reload

3. CUSTOMIZATION
   - Modify narrative_context strings in _generate_scenes() to fit your world
   - Each HiddenElement.narrative_context is a prompt directive—quality matters
   - Add more HiddenElements at different trigger_percentage values for finer control

4. MULTIPLE STORYLINES
   - Current setup supports one trilogy per server instance
   - For multiple users/games, consider making generator per-session or per-game
   - Or: extend Storyline to include a game_id/user_id field
"""

# Minimal example integration snippet:
"""
# In server.py:

from storyline_generator import StorylineGenerator, StoryTone

# At startup:
storyline_generator = StorylineGenerator()
storyline_generator.generate_trilogy("The Lost Heirloom")

# In _generate_narrative():
base_prompt = load_caretaker_prompt()
modified_prompt = storyline_generator.generate_caretaker_context(
    storyline_type=request.get("storyline", "main_a"),
    scene_id=request.get("scene_id", "main_a_scene_1"),
    progress_percentage=request.get("progress", 0),
    base_caretaker_prompt=base_prompt
)
# Pass modified_prompt to AI instead of base_prompt
"""
