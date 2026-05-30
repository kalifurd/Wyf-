"""
Character Creator Engine for WYF*
Generates hybrid modern romance character profiles with randomization and customization.
"""

import json
import random
from typing import Optional, Dict, List
from dataclasses import dataclass, asdict
from enum import Enum

# ============================================================================
# Character Enums & Templates
# ============================================================================

class Gender(Enum):
    MALE = "male"
    FEMALE = "female"
    NON_BINARY = "non-binary"
    PREFER_NOT_SAY = "prefer not to say"

class Archetype(Enum):
    CEO = "CEO"
    ARTIST = "artist"
    BARISTA = "barista"
    TECH_FOUNDER = "tech founder"
    WRITER = "writer"
    THERAPIST = "therapist"
    MUSICIAN = "musician"
    DESIGNER = "designer"
    ENTREPRENEUR = "entrepreneur"
    ACADEMIC = "academic"
    PHOTOGRAPHER = "photographer"
    CHEF = "chef"

class Personality(Enum):
    INTROVERTED = "introverted"
    EXTROVERTED = "extroverted"
    AMBIVERT = "ambivert"

class RelationshipGoal(Enum):
    CASUAL = "casual dating"
    SERIOUS = "long-term relationship"
    UNDECIDED = "figuring it out"
    MARRIAGE = "marriage"
    RECONNECTION = "reconnecting with ex"

# ============================================================================
# Character Data Class
# ============================================================================

@dataclass
class Character:
    """Modern romance character profile."""
    id: str
    name: str
    gender: str
    age: int
    archetype: str
    personality: str
    career: str
    location: str
    interests: List[str]
    relationship_goal: str
    relationship_history: str
    quirks: List[str]
    love_language: str
    biggest_fear: str
    secret: str
    photo_description: str
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def to_prompt_context(self) -> str:
        """Generate character context for AI narrator."""
        return f"""
Character Profile:
- Name: {self.name}
- Age: {self.age}
- Gender: {self.gender}
- Profession: {self.career}
- Location: {self.location}
- Personality: {self.personality}
- Interests: {', '.join(self.interests)}
- Relationship Goal: {self.relationship_goal}
- Love Language: {self.love_language}
- Biggest Fear: {self.biggest_fear}
- Quirks: {', '.join(self.quirks)}
- Secret: {self.secret}
- Physical: {self.photo_description}
"""

# ============================================================================
# Character Generator
# ============================================================================

class CharacterGenerator:
    """Generates modern romance character profiles."""
    
    FIRST_NAMES_MALE = [
        "Alex", "Jordan", "Casey", "Riley", "Morgan",
        "Sam", "Taylor", "Parker", "Quinn", "Drew",
        "Jamie", "Adrian", "Blake", "Evan", "Marcus",
        "Isaac", "Ethan", "Lucas", "Noah", "Liam"
    ]
    
    FIRST_NAMES_FEMALE = [
        "Emma", "Sophia", "Olivia", "Ava", "Isabella",
        "Mia", "Harper", "Evelyn", "Amelia", "Charlotte",
        "Sarah", "Jessica", "Anna", "Grace", "Lily",
        "Sophie", "Victoria", "Zoe", "Elena", "Nora"
    ]
    
    LAST_NAMES = [
        "Chen", "Rodriguez", "Johnson", "Kim", "Thompson",
        "Martinez", "Anderson", "Taylor", "Brown", "Davis",
        "Miller", "Wilson", "Moore", "Jackson", "Martin",
        "Lee", "Patel", "Garcia", "Jones", "Hassan"
    ]
    
    LOCATIONS = [
        "Brooklyn", "San Francisco", "Austin", "Denver",
        "Portland", "Nashville", "Chicago", "Miami",
        "Seattle", "Boston", "Los Angeles", "New York",
        "Atlanta", "Vancouver", "Toronto", "London",
        "Berlin", "Paris", "Melbourne", "Tokyo"
    ]
    
    INTERESTS = [
        "hiking", "reading", "cooking", "photography", "travel",
        "music festivals", "yoga", "coffee culture", "gaming",
        "painting", "film noir", "crafting", "fitness",
        "volunteering", "gardening", "podcasts", "vintage fashion",
        "board games", "rock climbing", "meditation", "DJ"
    ]
    
    QUIRKS = [
        "always late to everything",
        "talks to plants",
        "perfect memory for useless facts",
        "laughs at their own jokes",
        "collection of vintage records",
        "terrible dancer but loves trying",
        "overthinks every text message",
        "quotes movies constantly",
        "has a ritual for every morning",
        "leaves notes for strangers",
        "can't sleep without silence",
        "talks in their sleep",
        "makes weird sound effects",
        "obsessed with organizing",
        "always has a book nearby"
    ]
    
    LOVE_LANGUAGES = [
        "words of affirmation",
        "acts of service",
        "receiving gifts",
        "quality time",
        "physical touch"
    ]
    
    FEARS = [
        "being alone forever",
        "vulnerability and rejection",
        "losing independence",
        "not being enough",
        "commitment",
        "repeating past mistakes",
        "being seen as weak",
        "abandonment",
        "trust issues",
        "missing out on life"
    ]
    
    SECRETS = [
        "still in love with an ex",
        "hiding a big life decision",
        "afraid they're not good enough",
        "carrying guilt from the past",
        "hiding a personal struggle",
        "keeping a professional secret",
        "afraid of disappointing others",
        "struggling financially",
        "dealing with family conflict",
        "hasn't been honest about their past"
    ]
    
    PHOTO_DESCRIPTIONS = [
        "warm brown eyes, effortless style, genuine smile",
        "piercing gaze, dark hair, athletic build",
        "bright eyes that light up when laughing, creative vibe",
        "soft features, natural beauty, thoughtful expression",
        "strong jawline, confident presence, approachable",
        "elegant posture, mysterious allure, captivating eyes",
        "boyish charm, expressive face, artistic energy",
        "striking presence, kind eyes, magnetic smile",
        "delicate features, adventurous spirit, warm aura",
        "handsome despite not trying, genuine kindness in eyes"
    ]
    
    @staticmethod
    def generate(
        gender: Optional[str] = None,
        archetype: Optional[str] = None,
        customizations: Optional[Dict] = None
    ) -> Character:
        """
        Generate a character with optional customizations.
        
        Args:
            gender: Optional gender override
            archetype: Optional archetype override
            customizations: Dict of custom attributes to override
        
        Returns:
            Character profile
        """
        import uuid
        
        # Randomize or use provided values
        gender = gender or random.choice([g.value for g in Gender])
        archetype = archetype or random.choice([a.value for a in Archetype])
        
        # Select name pool based on gender
        if gender == "female":
            first_name = random.choice(CharacterGenerator.FIRST_NAMES_FEMALE)
        elif gender == "male":
            first_name = random.choice(CharacterGenerator.FIRST_NAMES_MALE)
        else:
            first_name = random.choice(
                CharacterGenerator.FIRST_NAMES_MALE +
                CharacterGenerator.FIRST_NAMES_FEMALE
            )
        
        last_name = random.choice(CharacterGenerator.LAST_NAMES)
        name = f"{first_name} {last_name}"
        
        # Build base character
        character = Character(
            id=str(uuid.uuid4())[:8],
            name=name,
            gender=gender,
            age=random.randint(23, 45),
            archetype=archetype,
            personality=random.choice([p.value for p in Personality]),
            career=CharacterGenerator._get_career_from_archetype(archetype),
            location=random.choice(CharacterGenerator.LOCATIONS),
            interests=random.sample(CharacterGenerator.INTERESTS, k=random.randint(3, 5)),
            relationship_goal=random.choice([rg.value for rg in RelationshipGoal]),
            relationship_history=CharacterGenerator._generate_relationship_history(),
            quirks=random.sample(CharacterGenerator.QUIRKS, k=random.randint(2, 4)),
            love_language=random.choice(CharacterGenerator.LOVE_LANGUAGES),
            biggest_fear=random.choice(CharacterGenerator.FEARS),
            secret=random.choice(CharacterGenerator.SECRETS),
            photo_description=random.choice(CharacterGenerator.PHOTO_DESCRIPTIONS)
        )
        
        # Apply customizations if provided
        if customizations:
            for key, value in customizations.items():
                if hasattr(character, key):
                    setattr(character, key, value)
        
        return character
    
    @staticmethod
    def _get_career_from_archetype(archetype: str) -> str:
        """Map archetype to realistic career description."""
        careers = {
            "CEO": "Executive Director at marketing firm",
            "artist": "Freelance graphic designer & illustrator",
            "barista": "Specialty coffee shop manager",
            "tech founder": "Startup CTO (SaaS platform)",
            "writer": "Freelance journalist & author",
            "therapist": "Licensed therapist in private practice",
            "musician": "Session guitarist & music producer",
            "designer": "Product designer at tech company",
            "entrepreneur": "Small business owner (boutique)",
            "academic": "University professor (literature)",
            "photographer": "Freelance photographer & creative director",
            "chef": "Head chef at farm-to-table restaurant"
        }
        return careers.get(archetype, "Creative professional")
    
    @staticmethod
    def _generate_relationship_history() -> str:
        """Generate a realistic relationship background."""
        histories = [
            "Long-term relationship ended amicably 6 months ago",
            "Coming out of a difficult breakup, finally healing",
            "Serial dater, never quite found the right person",
            "Was married, divorced 2 years ago, learning to trust again",
            "Recently ended a complicated on-and-off situation",
            "Haven't been in a serious relationship in years",
            "Just got out of a toxic situation, rebuilding confidence",
            "Long-distance relationship that didn't work out",
            "Been single by choice, now open to possibilities",
            "Widowed 3 years ago, ready to open heart again"
        ]
        return random.choice(histories)
