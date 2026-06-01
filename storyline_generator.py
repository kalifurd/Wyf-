"""
WYF* Storyline Generator Addon
===============================
Generates interconnected storylines with:
- Story A: Main visible narrative path
- Story B: Alternative visible narrative path  
- Story C: Hidden side story unknown to reader (influences A & B subtly)

The three stories weave together, with C providing hidden context and conflicts
that affect the main narratives through subtle environmental cues and NPC behavior.
"""

import json
import random
from typing import Optional, Dict, List, Any
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum


# ============================================================================
# Data Models
# ============================================================================

class StorylineType(Enum):
    """Types of storylines in the system."""
    MAIN_A = "main_a"           # Primary visible storyline
    MAIN_B = "main_b"           # Alternative visible storyline
    HIDDEN_C = "hidden_c"       # Secret side story


class StoryTone(Enum):
    """Narrative tone for story generation."""
    ROMANTIC = "romantic"
    MYSTERIOUS = "mysterious"
    DRAMATIC = "dramatic"
    WHIMSICAL = "whimsical"
    DARK = "dark"
    COMEDIC = "comedic"


@dataclass
class Character:
    """Represents a character in the storyline."""
    name: str
    role: str  # protagonist, love_interest, antagonist, ally, etc.
    description: str
    motivations: List[str]
    secrets: List[str]  # Hidden secrets that may be revealed
    affiliations: Dict[str, str]  # storyline_type -> relationship
    
    def to_dict(self):
        return asdict(self)


@dataclass
class StorylineScene:
    """Represents a scene in a storyline."""
    id: str
    title: str
    description: str
    emotional_arc: str  # tension, resolution, discovery, conflict, etc.
    characters_present: List[str]  # character names
    choices: List[str]  # player decision options
    hidden_elements: Optional[Dict[str, Any]]  # elements only visible if this is story C
    
    def to_dict(self):
        return asdict(self)


@dataclass
class Storyline:
    """Represents a complete storyline."""
    storyline_type: StorylineType
    title: str
    theme: str
    tone: StoryTone
    setting: str
    protagonist: str
    antagonist: Optional[str]
    goal: str
    synopsis: str
    scenes: List[StorylineScene]
    characters: Dict[str, Character]
    connections_to_other_stories: Dict[str, List[str]]  # story_type -> scene_ids
    
    def to_dict(self):
        return {
            "storyline_type": self.storyline_type.value,
            "title": self.title,
            "theme": self.theme,
            "tone": self.tone.value,
            "setting": self.setting,
            "protagonist": self.protagonist,
            "antagonist": self.antagonist,
            "goal": self.goal,
            "synopsis": self.synopsis,
            "scenes": [scene.to_dict() for scene in self.scenes],
            "characters": {name: char.to_dict() for name, char in self.characters.items()},
            "connections_to_other_stories": self.connections_to_other_stories
        }


# ============================================================================
# Storyline Generator
# ============================================================================

class StorylineGenerator:
    """
    Generates interconnected storylines with hidden side stories.
    """
    
    def __init__(self, ai_client=None):
        """
        Initialize the storyline generator.
        
        Args:
            ai_client: Optional AI client for narrative generation
        """
        self.ai_client = ai_client
        self.storylines: Dict[str, Storyline] = {}
        self.character_pool: Dict[str, Character] = {}
        
    def generate_trilogy(
        self,
        base_prompt: str,
        setting: str = "Victorian Era",
        tone_a: StoryTone = StoryTone.ROMANTIC,
        tone_b: StoryTone = StoryTone.MYSTERIOUS,
        tone_c: StoryTone = StoryTone.DARK
    ) -> Dict[str, Storyline]:
        """
        Generate all three interconnected storylines.
        
        Args:
            base_prompt: Core concept for all stories (e.g., "A lost heirloom")
            setting: Physical/temporal setting
            tone_a: Tone for Story A
            tone_b: Tone for Story B
            tone_c: Tone for Hidden Story C
            
        Returns:
            Dictionary with keys "main_a", "main_b", "hidden_c"
        """
        
        # Step 1: Generate shared character pool
        self.character_pool = self._generate_characters(base_prompt, setting)
        
        # Step 2: Generate Story A (visible, optimistic)
        story_a = self._generate_storyline(
            base_prompt=base_prompt,
            setting=setting,
            storyline_type=StorylineType.MAIN_A,
            tone=tone_a,
            num_scenes=5
        )
        self.storylines[StorylineType.MAIN_A.value] = story_a
        
        # Step 3: Generate Story B (visible, alternative perspective)
        story_b = self._generate_storyline(
            base_prompt=base_prompt,
            setting=setting,
            storyline_type=StorylineType.MAIN_B,
            tone=tone_b,
            num_scenes=5,
            contrasting_to=story_a
        )
        self.storylines[StorylineType.MAIN_B.value] = story_b
        
        # Step 4: Generate Story C (hidden, revealing true context)
        story_c = self._generate_storyline(
            base_prompt=base_prompt,
            setting=setting,
            storyline_type=StorylineType.HIDDEN_C,
            tone=tone_c,
            num_scenes=5,
            revealing_truth_about=[story_a, story_b]
        )
        self.storylines[StorylineType.HIDDEN_C.value] = story_c
        
        # Step 5: Create cross-story connections
        self._link_storylines()
        
        return self.storylines
    
    
    def _generate_characters(self, base_prompt: str, setting: str) -> Dict[str, Character]:
        """Generate a pool of characters that appear across all three storylines."""
        
        characters = {
            "Isabelle": Character(
                name="Isabelle",
                role="protagonist",
                description="A mysterious woman with connections to all three stories",
                motivations=["Uncover the truth", "Protect those she loves"],
                secrets=["Her past is more complex than it appears"],
                affiliations={
                    StorylineType.MAIN_A.value: "romantic_lead",
                    StorylineType.MAIN_B.value: "unreliable_narrator",
                    StorylineType.HIDDEN_C.value: "central_to_conspiracy"
                }
            ),
            "Lord Ashford": Character(
                name="Lord Ashford",
                role="antagonist",
                description="A nobleman with ambitions that span all three timelines",
                motivations=["Power", "Revenge"],
                secrets=["He orchestrates events behind the scenes"],
                affiliations={
                    StorylineType.MAIN_A.value: "charming_suitor",
                    StorylineType.MAIN_B.value: "true_antagonist",
                    StorylineType.HIDDEN_C.value: "puppet_master"
                }
            ),
            "Margaret": Character(
                name="Margaret",
                role="ally",
                description="Isabelle's trusted confidant and lady's maid",
                motivations=["Loyalty", "Justice"],
                secrets=["She knows more than she reveals"],
                affiliations={
                    StorylineType.MAIN_A.value: "loyal_friend",
                    StorylineType.MAIN_B.value: "unreliable_ally",
                    StorylineType.HIDDEN_C.value: "key_witness"
                }
            ),
            "Viscount Thorne": Character(
                name="Viscount Thorne",
                role="love_interest",
                description="A man caught between duty and desire",
                motivations=["Honor", "Love"],
                secrets=["His allegiances shift between stories"],
                affiliations={
                    StorylineType.MAIN_A.value: "true_love",
                    StorylineType.MAIN_B.value: "false_hope",
                    StorylineType.HIDDEN_C.value: "reluctant_participant"
                }
            ),
            "Dr. Crane": Character(
                name="Dr. Crane",
                role="ally",
                description="A mysterious physician with hidden knowledge",
                motivations=["Redemption", "Knowledge"],
                secrets=["He holds crucial information about the past"],
                affiliations={
                    StorylineType.MAIN_A.value: "healer",
                    StorylineType.MAIN_B.value: "suspicious_figure",
                    StorylineType.HIDDEN_C.value: "unwilling_conspirator"
                }
            )
        }
        
        return characters
    
    
    def _generate_storyline(
        self,
        base_prompt: str,
        setting: str,
        storyline_type: StorylineType,
        tone: StoryTone,
        num_scenes: int = 5,
        contrasting_to: Optional[Storyline] = None,
        revealing_truth_about: Optional[List[Storyline]] = None
    ) -> Storyline:
        """Generate a complete storyline."""
        
        # Select protagonist and antagonist
        if storyline_type == StorylineType.MAIN_A:
            protagonist = "Isabelle"
            antagonist = None
            title = f"The Path of {base_prompt} - A Story"
            theme = "Love Overcomes All"
            goal = "Find happiness and truth through love"
        elif storyline_type == StorylineType.MAIN_B:
            protagonist = "Isabelle"
            antagonist = "Lord Ashford"
            title = f"The Path of {base_prompt} - B Story"
            theme = "Deception and Discovery"
            goal = "Expose the conspiracy and protect the innocent"
        else:  # HIDDEN_C
            protagonist = "Margaret"
            antagonist = "Lord Ashford"
            title = f"The Truth Behind {base_prompt} - Hidden Story"
            theme = "Behind Every Story Lies Another"
            goal = "Reveal the hidden machinations controlling all events"
        
        # Generate synopsis
        synopsis = self._generate_synopsis(
            base_prompt, storyline_type, tone, protagonist, antagonist
        )
        
        # Generate scenes
        scenes = self._generate_scenes(
            storyline_type, num_scenes, tone, protagonist, antagonist
        )
        
        return Storyline(
            storyline_type=storyline_type,
            title=title,
            theme=theme,
            tone=tone,
            setting=setting,
            protagonist=protagonist,
            antagonist=antagonist,
            goal=goal,
            synopsis=synopsis,
            scenes=scenes,
            characters=self.character_pool.copy(),
            connections_to_other_stories={}
        )
    
    
    def _generate_synopsis(
        self,
        base_prompt: str,
        storyline_type: StorylineType,
        tone: StoryTone,
        protagonist: str,
        antagonist: Optional[str]
    ) -> str:
        """Generate a synopsis for a storyline."""
        
        if storyline_type == StorylineType.MAIN_A:
            return (
                f"In a Victorian {base_prompt} scenario, {protagonist} embarks on a journey "
                f"of discovery and romance. As events unfold, she finds herself drawn into "
                f"a tale of passion and destiny, where every choice shapes her future."
            )
        elif storyline_type == StorylineType.MAIN_B:
            return (
                f"The same {base_prompt} situation unfolds differently when viewed through "
                f"a lens of intrigue and suspicion. {protagonist} discovers that {antagonist} "
                f"may not be what he seems, leading to a thrilling investigation."
            )
        else:  # HIDDEN_C
            return (
                f"Behind the scenes of all visible events, {protagonist} witnesses the true "
                f"conspiracy. {antagonist}'s machinations have been orchestrating both storylines, "
                f"and the truth is far darker than anyone suspects."
            )
    
    
    def _generate_scenes(
        self,
        storyline_type: StorylineType,
        num_scenes: int,
        tone: StoryTone,
        protagonist: str,
        antagonist: Optional[str]
    ) -> List[StorylineScene]:
        """Generate individual scenes for a storyline."""
        
        scenes = []
        emotional_arcs = ["tension", "discovery", "conflict", "resolution", "revelation"]
        
        for i in range(num_scenes):
            emotional_arc = emotional_arcs[i % len(emotional_arcs)]
            
            if storyline_type == StorylineType.MAIN_A:
                title = f"Scene {i+1}: The Bloom"
                description = f"A romantic moment unfolds as {protagonist} navigates {tone.value} circumstances."
                characters = ["Isabelle", "Viscount Thorne", "Margaret"]
                choices = [
                    "Follow your heart",
                    "Listen to reason",
                    "Trust your instincts"
                ]
            elif storyline_type == StorylineType.MAIN_B:
                title = f"Scene {i+1}: The Shadow"
                description = f"Suspicion clouds {protagonist}'s mind as she questions {antagonist}'s motives."
                characters = ["Isabelle", "Lord Ashford", "Dr. Crane", "Margaret"]
                choices = [
                    "Confront him directly",
                    "Gather evidence in secret",
                    "Confide in an ally"
                ]
            else:  # HIDDEN_C
                title = f"Scene {i+1}: The Truth"
                description = f"{protagonist} discovers {antagonist}'s hidden agenda and must decide what to do."
                characters = ["Margaret", "Lord Ashford", "Dr. Crane"]
                choices = [
                    "Expose the conspiracy",
                    "Play along to learn more",
                    "Protect the innocent unknowingly"
                ]
            
            scene = StorylineScene(
                id=f"{storyline_type.value}_scene_{i+1}",
                title=title,
                description=description,
                emotional_arc=emotional_arc,
                characters_present=characters,
                choices=choices,
                hidden_elements={
                    "true_stakes": f"This scene affects all three storylines",
                    "subtle_hint": f"Careful observers may notice inconsistencies"
                } if storyline_type == StorylineType.HIDDEN_C else None
            )
            scenes.append(scene)
        
        return scenes
    
    
    def _link_storylines(self):
        """Create cross-story connections and influence maps."""
        
        story_a = self.storylines[StorylineType.MAIN_A.value]
        story_b = self.storylines[StorylineType.MAIN_B.value]
        story_c = self.storylines[StorylineType.HIDDEN_C.value]
        
        # Story C influences Story A and B
        for i, scene in enumerate(story_a.scenes):
            # Hidden C scenes influence A scenes
            story_a.connections_to_other_stories.setdefault(
                StorylineType.HIDDEN_C.value, []
            ).append(f"hidden_c_scene_{(i % 5) + 1}")
        
        for i, scene in enumerate(story_b.scenes):
            # Hidden C scenes influence B scenes
            story_b.connections_to_other_stories.setdefault(
                StorylineType.HIDDEN_C.value, []
            ).append(f"hidden_c_scene_{(i % 5) + 1}")
        
        # A and B influence each other through shared characters
        story_a.connections_to_other_stories[StorylineType.MAIN_B.value] = [
            "main_b_scene_1", "main_b_scene_3"  # Key decision points
        ]
        story_b.connections_to_other_stories[StorylineType.MAIN_A.value] = [
            "main_a_scene_2", "main_a_scene_4"  # Contradictory evidence
        ]
    
    
    def get_visible_storylines(self) -> Dict[str, Storyline]:
        """Get only the visible storylines (A and B)."""
        return {
            k: v for k, v in self.storylines.items()
            if k != StorylineType.HIDDEN_C.value
        }
    
    
    def get_hidden_storyline(self) -> Optional[Storyline]:
        """Get the hidden storyline (C)."""
        return self.storylines.get(StorylineType.HIDDEN_C.value)
    
    
    def reveal_hidden_storyline_gradually(self, progress_percentage: float) -> Dict[str, Any]:
        """
        Gradually reveal the hidden storyline as the player progresses.
        
        Args:
            progress_percentage: Player progress (0-100)
            
        Returns:
            Dictionary with revelations appropriate for the progress level
        """
        storyline_c = self.get_hidden_storyline()
        if not storyline_c:
            return {}
        
        revelations = {
            "25%": "You notice an inconsistency in what you've been told...",
            "50%": "Margaret seems to know more than she's saying...",
            "75%": "The true conspiracy begins to take shape in your mind...",
            "100%": "Everything you thought you knew was orchestrated by..."
        }
        
        scenes_to_reveal = []
        if progress_percentage >= 25:
            scenes_to_reveal.append(storyline_c.scenes[0])
        if progress_percentage >= 50:
            scenes_to_reveal.extend(storyline_c.scenes[1:3])
        if progress_percentage >= 75:
            scenes_to_reveal.extend(storyline_c.scenes[3:])
        
        return {
            "progress": progress_percentage,
            "revelation_text": revelations.get(f"{int(progress_percentage)}%", ""),
            "revealed_scenes": [s.to_dict() for s in scenes_to_reveal],
            "hidden_truth": storyline_c.goal
        }
    
    
    def export_to_json(self, filename: str = "storylines.json"):
        """Export all storylines to JSON format."""
        data = {
            "generated_at": datetime.now().isoformat(),
            "storylines": {k: v.to_dict() for k, v in self.storylines.items()},
            "characters": {name: char.to_dict() for name, char in self.character_pool.items()},
            "connections": {
                k: v.connections_to_other_stories
                for k, v in self.storylines.items()
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filename
    
    
    def get_suggested_choices_for_scene(
        self,
        storyline_type: str,
        scene_id: str,
        player_history: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Get suggested choices for a scene, accounting for player history
        and hidden story context.
        
        Args:
            storyline_type: Type of storyline ("main_a", "main_b", "hidden_c")
            scene_id: ID of the scene
            player_history: History of previous player choices
            
        Returns:
            Dictionary with available choices and their consequences
        """
        storyline = self.storylines.get(storyline_type)
        if not storyline:
            return {}
        
        # Find the scene
        scene = next((s for s in storyline.scenes if s.id == scene_id), None)
        if not scene:
            return {}
        
        return {
            "scene": scene.to_dict(),
            "available_choices": scene.choices,
            "story_type": storyline_type,
            "affects_other_stories": storyline.connections_to_other_stories.get(
                StorylineType.HIDDEN_C.value if storyline_type != StorylineType.HIDDEN_C.value else None,
                []
            )
        }


# ============================================================================
# Example Usage / Testing
# ============================================================================

if __name__ == "__main__":
    # Initialize the generator
    generator = StorylineGenerator()
    
    # Generate a trilogy of stories
    print("🎭 Generating interconnected storylines...\n")
    
    storylines = generator.generate_trilogy(
        base_prompt="The Lost Heirloom",
        setting="Victorian London, 1888",
        tone_a=StoryTone.ROMANTIC,
        tone_b=StoryTone.MYSTERIOUS,
        tone_c=StoryTone.DARK
    )
    
    # Display visible storylines
    print("=" * 70)
    print("📖 VISIBLE STORYLINES (Known to Reader)")
    print("=" * 70)
    
    for story_type, storyline in generator.get_visible_storylines().items():
        print(f"\n✦ {storyline.title}")
        print(f"  Theme: {storyline.theme}")
        print(f"  Tone: {storyline.tone.value}")
        print(f"  Goal: {storyline.goal}")
        print(f"  Synopsis: {storyline.synopsis}")
        print(f"  Protagonist: {storyline.protagonist}")
        if storyline.antagonist:
            print(f"  Antagonist: {storyline.antagonist}")
        print(f"  Scenes: {len(storyline.scenes)}")
    
    # Display hidden storyline (preview)
    print("\n" + "=" * 70)
    print("🔒 HIDDEN STORYLINE (Unknown to Reader)")
    print("=" * 70)
    
    hidden = generator.get_hidden_storyline()
    print(f"\n✦ {hidden.title}")
    print(f"  Theme: {hidden.theme}")
    print(f"  Goal: {hidden.goal}")
    print(f"  [Content hidden from player until revelation]")
    
    # Show gradual revelation
    print("\n" + "=" * 70)
    print("🔓 REVELATION TIMELINE")
    print("=" * 70)
    
    for progress in [25, 50, 75, 100]:
        result = generator.reveal_hidden_storyline_gradually(progress)
        print(f"\n📍 {progress}% Progress:")
        print(f"   {result.get('revelation_text', '')}")
    
    # Export to JSON
    print("\n" + "=" * 70)
    print("💾 Exporting storylines...")
    filename = generator.export_to_json("storylines.json")
    print(f"✓ Exported to {filename}")
