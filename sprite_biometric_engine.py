"""
WYF* Sprite Biometric Engine
=============================

Real-time biometric awareness system for interactive sprites across Godot, Unreal Engine 5, and web.
Handles eye tracking, haptic feedback, typing detection, and engagement scoring.

The sprite engine is ENGINE-AGNOSTIC: it outputs standardized animation states, gaze vectors,
and haptic choreography that any engine (Godot, UE5, web canvas) can consume.

Architecture:
- WebSocket server for real-time biometric streaming
- Eye tracking via WebGazer (browser) + fallback to input simulation
- Haptic event detection from keyboard/mouse
- Engagement scoring (0-100) based on gaze, interaction rate, and presence
- Output: Standardized JSON events consumed by sprite renderers
"""

import asyncio
import json
import time
import logging
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class BiometricType(Enum):
    """Types of biometric input."""
    GAZE = "gaze"              # Eye tracking
    BLINK = "blink"            # Eye closure detection
    PUPIL = "pupil"            # Pupil dilation
    TYPING = "typing"          # Keyboard input
    CLICK = "click"            # Mouse click
    HAPTIC = "haptic"          # Haptic feedback request
    PRESENCE = "presence"      # User present/away


class EngagementLevel(Enum):
    """Player engagement categories."""
    ABSENT = "absent"          # 0-10%: User not looking
    DISTRACTED = "distracted"  # 10-40%: Occasional eye contact
    ENGAGED = "engaged"        # 40-70%: Regular attention
    FOCUSED = "focused"        # 70-100%: Intense focus


class SpriteAnimationState(Enum):
    """Sprite animation states (cross-engine compatible)."""
    IDLE = "idle"
    LOOKING_AT_PLAYER = "looking_at_player"
    LOOKING_AWAY = "looking_away"
    BLINKING = "blinking"
    INTERESTED = "interested"
    CONFUSED = "confused"
    SUSPICIOUS = "suspicious"
    EXCITED = "excited"
    SAD = "sad"
    ANGRY = "angry"
    TYPING_WATCH = "typing_watch"  # Watches your hands type
    WAITING = "waiting"            # Waiting for input


@dataclass
class GazePoint:
    """Normalized gaze coordinates and metadata."""
    x: float                   # 0.0-1.0 (left to right)
    y: float                   # 0.0-1.0 (top to bottom)
    confidence: float          # 0.0-1.0 (tracking confidence)
    timestamp: float           # Unix timestamp
    
    def to_dict(self):
        return asdict(self)


@dataclass
class BiometricEvent:
    """A single biometric input event."""
    event_type: BiometricType
    timestamp: float
    data: Dict[str, Any]       # Type-specific data
    session_id: str            # Track user session
    
    def to_dict(self):
        return {
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "data": self.data,
            "session_id": self.session_id
        }


@dataclass
class EngagementScore:
    """Player engagement metrics."""
    overall: float             # 0-100
    gaze_contact: float        # 0-100 (% time looking at sprite)
    interaction_rate: float    # 0-100 (typing speed normalized)
    presence: bool             # Is user present?
    primary_level: EngagementLevel
    timestamp: float
    
    def to_dict(self):
        return {
            "overall": self.overall,
            "gaze_contact": self.gaze_contact,
            "interaction_rate": self.interaction_rate,
            "presence": self.presence,
            "primary_level": self.primary_level.value,
            "timestamp": self.timestamp
        }


@dataclass
class SpriteState:
    """Complete sprite state for rendering engines."""
    animation_state: SpriteAnimationState
    gaze_vector: GazePoint     # Where sprite should look
    engagement_level: EngagementLevel
    micro_expression: Optional[str]  # Subtle emotional cue
    haptic_event: Optional[Dict[str, Any]]  # Haptic feedback payload
    timestamp: float
    storyline_context: Optional[Dict[str, str]]  # Story A/B/C influence
    
    def to_dict(self):
        return {
            "animation_state": self.animation_state.value,
            "gaze_vector": self.gaze_vector.to_dict() if self.gaze_vector else None,
            "engagement_level": self.engagement_level.value,
            "micro_expression": self.micro_expression,
            "haptic_event": self.haptic_event,
            "timestamp": self.timestamp,
            "storyline_context": self.storyline_context
        }


# ============================================================================
# Eye Tracking / Gaze Detection
# ============================================================================

class GazeTracker:
    """
    Aggregates gaze data from multiple sources:
    - WebGazer (browser-based eye tracking)
    - Input simulation (fallback for dev/testing)
    - Calibration-free estimation
    
    WebGazer.js runs in the browser and sends gaze data via WebSocket.
    This class processes and smooths the incoming data.
    """
    
    def __init__(self, smoothing_window: int = 5):
        """
        Args:
            smoothing_window: Number of frames to average (reduces jitter)
        """
        self.gaze_history: List[GazePoint] = []
        self.smoothing_window = smoothing_window
        self.last_gaze: Optional[GazePoint] = None
        self.calibration_offset = {"x": 0.0, "y": 0.0}
    
    def process_gaze_sample(self, raw_gaze: Dict[str, float]) -> GazePoint:
        """
        Process a raw gaze sample from WebGazer.
        
        Args:
            raw_gaze: {
                "x": 0-1,
                "y": 0-1,
                "confidence": 0-1
            }
        
        Returns:
            Smoothed GazePoint
        """
        # Apply calibration offset
        x = max(0.0, min(1.0, raw_gaze["x"] + self.calibration_offset["x"]))
        y = max(0.0, min(1.0, raw_gaze["y"] + self.calibration_offset["y"]))
        
        gaze = GazePoint(
            x=x,
            y=y,
            confidence=raw_gaze.get("confidence", 0.5),
            timestamp=time.time()
        )
        
        # Add to history and smooth
        self.gaze_history.append(gaze)
        if len(self.gaze_history) > self.smoothing_window:
            self.gaze_history.pop(0)
        
        # Return smoothed average
        smoothed = self._smooth_gaze()
        self.last_gaze = smoothed
        return smoothed
    
    def _smooth_gaze(self) -> GazePoint:
        """Average recent gaze points to reduce jitter."""
        if not self.gaze_history:
            return GazePoint(0.5, 0.5, 0.0, time.time())
        
        avg_x = sum(g.x for g in self.gaze_history) / len(self.gaze_history)
        avg_y = sum(g.y for g in self.gaze_history) / len(self.gaze_history)
        avg_conf = sum(g.confidence for g in self.gaze_history) / len(self.gaze_history)
        
        return GazePoint(
            x=avg_x,
            y=avg_y,
            confidence=avg_conf,
            timestamp=time.time()
        )
    
    def calibrate(self, screen_point: tuple, gaze_point: tuple):
        """
        Simple 1-point calibration.
        User looks at a known screen location; system calculates offset.
        
        Args:
            screen_point: (x, y) where user should look
            gaze_point: (x, y) what WebGazer reported
        """
        self.calibration_offset["x"] = screen_point[0] - gaze_point[0]
        self.calibration_offset["y"] = screen_point[1] - gaze_point[1]
        logger.info(f"Gaze calibration: offset={self.calibration_offset}")


# ============================================================================
# Haptic & Typing Detection
# ============================================================================

class InputDetector:
    """
    Tracks keyboard and mouse input to detect:
    - Typing speed (WPM, character rate)
    - Click patterns
    - Idle periods
    """
    
    def __init__(self, wpm_window: int = 60):
        """
        Args:
            wpm_window: Seconds over which to measure WPM
        """
        self.keystroke_times: List[float] = []
        self.wpm_window = wpm_window
        self.last_activity_time = time.time()
        self.is_idle = False
        self.idle_threshold = 5.0  # Seconds before considered "idle"
    
    def process_keystroke(self):
        """Record a keyboard input event."""
        now = time.time()
        self.keystroke_times.append(now)
        
        # Clean old keystrokes outside window
        self.keystroke_times = [
            t for t in self.keystroke_times
            if now - t < self.wpm_window
        ]
        
        self.last_activity_time = now
        self.is_idle = False
    
    def process_click(self):
        """Record a mouse click event."""
        self.last_activity_time = time.time()
        self.is_idle = False
    
    def get_typing_speed(self) -> Dict[str, float]:
        """
        Calculate typing metrics.
        
        Returns:
            {
                "wpm": words per minute,
                "cpm": characters per minute,
                "keystrokes_recent": # of keystrokes in window
            }
        """
        now = time.time()
        keystrokes = len(self.keystroke_times)
        
        if self.wpm_window > 0:
            wpm = (keystrokes / 5) * (60 / self.wpm_window)  # Assume 5 chars per word
            cpm = keystrokes * (60 / self.wpm_window)
        else:
            wpm, cpm = 0, 0
        
        return {
            "wpm": round(wpm, 2),
            "cpm": round(cpm, 2),
            "keystrokes_recent": keystrokes
        }
    
    def update_idle_state(self):
        """Check if user has become idle."""
        idle_time = time.time() - self.last_activity_time
        self.is_idle = idle_time > self.idle_threshold


# ============================================================================
# Engagement Scoring
# ============================================================================

class EngagementEngine:
    """
    Synthesizes biometric data into a single engagement score.
    
    Factors:
    - Gaze contact (how much user looks at sprite)
    - Interaction rate (typing speed, click frequency)
    - Presence (user actively at device)
    - Storyline context (Story A/B/C affects baseline)
    """
    
    def __init__(self):
        self.gaze_contact_history: List[bool] = []
        self.interaction_history: List[float] = []
        self.window_size = 300  # Last 5 minutes
        self.baseline = 50.0    # Default engagement
    
    def calculate_engagement(
        self,
        gaze: Optional[GazePoint],
        typing_speed: Dict[str, float],
        is_idle: bool,
        sprite_bounds: tuple = (0.2, 0.2, 0.8, 0.8)  # (left, top, right, bottom) normalized
    ) -> EngagementScore:
        """
        Compute engagement level.
        
        Args:
            gaze: Current gaze point
            typing_speed: Output from InputDetector.get_typing_speed()
            is_idle: Whether user is idle
            sprite_bounds: Screen region where sprite is (normalized 0-1)
            
        Returns:
            EngagementScore with components
        """
        now = time.time()
        
        # 1. Gaze contact score (0-100)
        gaze_score = 0.0
        if gaze and gaze.confidence > 0.3:
            # Check if gaze is within sprite bounds
            in_bounds = (
                sprite_bounds[0] <= gaze.x <= sprite_bounds[2] and
                sprite_bounds[1] <= gaze.y <= sprite_bounds[3]
            )
            gaze_score = 100.0 if in_bounds else 30.0  # Still engaged if looking nearby
        
        self.gaze_contact_history.append(gaze_score > 50)
        
        # 2. Interaction score (0-100)
        wpm = typing_speed.get("wpm", 0)
        interaction_score = min(100.0, (wpm / 60.0) * 100)  # 60 WPM = max score
        
        self.interaction_history.append(interaction_score)
        
        # 3. Presence score (0-100)
        presence_score = 0.0 if is_idle else 100.0
        
        # Clean history
        self.gaze_contact_history = self.gaze_contact_history[-self.window_size:]
        self.interaction_history = self.interaction_history[-self.window_size:]
        
        # Weighted average
        gaze_weight = 0.4
        interaction_weight = 0.3
        presence_weight = 0.3
        
        overall = (
            gaze_score * gaze_weight +
            interaction_score * interaction_weight +
            presence_score * presence_weight
        )
        
        # Determine level
        if overall < 10:
            level = EngagementLevel.ABSENT
        elif overall < 40:
            level = EngagementLevel.DISTRACTED
        elif overall < 70:
            level = EngagementLevel.ENGAGED
        else:
            level = EngagementLevel.FOCUSED
        
        # Average gaze contact over window
        gaze_contact_pct = (
            sum(self.gaze_contact_history) / len(self.gaze_contact_history) * 100
            if self.gaze_contact_history else 0
        )
        
        return EngagementScore(
            overall=round(overall, 1),
            gaze_contact=round(gaze_contact_pct, 1),
            interaction_rate=round(interaction_score, 1),
            presence=not is_idle,
            primary_level=level,
            timestamp=now
        )


# ============================================================================
# Sprite Behavior Mapper
# ============================================================================

class SpriteBehaviorEngine:
    """
    Maps biometric input and engagement to sprite animation states.
    Output is ENGINE-AGNOSTIC: can be consumed by Godot, UE5, or web canvas.
    
    Decision tree:
    1. If user absent → idle or looking away
    2. If typing detected → watch user's hands
    3. If high engagement + gaze contact → look at player with interest
    4. If storyline context (A/B/C) → emotional inflection
    """
    
    def __init__(self):
        self.last_blink_time = time.time()
        self.blink_interval = 4.0  # Seconds between blinks
        self.last_animation_state = SpriteAnimationState.IDLE
    
    def compute_sprite_state(
        self,
        engagement: EngagementScore,
        gaze: Optional[GazePoint],
        typing_speed: Dict[str, float],
        storyline_type: Optional[str] = None,
        storyline_progress: float = 0.0
    ) -> SpriteState:
        """
        Synthesize engagement + biometrics into sprite state.
        
        Args:
            engagement: EngagementScore
            gaze: GazePoint or None
            typing_speed: Typing metrics
            storyline_type: "main_a", "main_b", "hidden_c"
            storyline_progress: 0-100 progress in story
            
        Returns:
            SpriteState ready for rendering engines
        """
        now = time.time()
        
        # Determine base animation state
        if engagement.primary_level == EngagementLevel.ABSENT:
            anim_state = SpriteAnimationState.LOOKING_AWAY
        elif typing_speed.get("cpm", 0) > 5:  # User is actively typing
            anim_state = SpriteAnimationState.TYPING_WATCH
        elif engagement.primary_level == EngagementLevel.FOCUSED:
            anim_state = SpriteAnimationState.LOOKING_AT_PLAYER
        elif engagement.primary_level == EngagementLevel.ENGAGED:
            anim_state = SpriteAnimationState.INTERESTED
        else:  # DISTRACTED
            anim_state = SpriteAnimationState.WAITING
        
        # Periodic blinking
        if now - self.last_blink_time > self.blink_interval:
            anim_state = SpriteAnimationState.BLINKING
            self.last_blink_time = now
        
        self.last_animation_state = anim_state
        
        # Compute micro-expression (emotional subtext)
        micro_expr = self._compute_micro_expression(
            engagement, storyline_type, storyline_progress
        )
        
        # Haptic feedback payload (optional)
        haptic = self._compute_haptic_feedback(engagement, typing_speed)
        
        # Gaze direction for the sprite to look
        gaze_vector = gaze if gaze else GazePoint(0.5, 0.5, 0.0, now)
        
        # Storyline context influence
        context = {}
        if storyline_type:
            context["storyline_type"] = storyline_type
            context["progress"] = storyline_progress
            # In Story C, character is more suspicious/calculating
            if storyline_type == "hidden_c":
                context["character_tone"] = "calculating"
            elif storyline_type == "main_b":
                context["character_tone"] = "wary"
            else:
                context["character_tone"] = "romantic"
        
        return SpriteState(
            animation_state=anim_state,
            gaze_vector=gaze_vector,
            engagement_level=engagement.primary_level,
            micro_expression=micro_expr,
            haptic_event=haptic,
            timestamp=now,
            storyline_context=context if context else None
        )
    
    def _compute_micro_expression(
        self,
        engagement: EngagementScore,
        storyline_type: Optional[str],
        progress: float
    ) -> Optional[str]:
        """
        Subtle emotional cues based on engagement + storyline.
        Micro-expressions are quick, hard to control emotional tells.
        """
        if engagement.overall < 20:
            return "bored"
        elif engagement.overall < 40:
            return "distracted"
        elif engagement.overall > 85:
            return "delighted"
        elif engagement.interaction_rate > 70:
            return "focused"
        
        # Storyline-based suspicion
        if storyline_type == "hidden_c" and progress > 50:
            return "calculating"
        elif storyline_type == "main_b" and progress > 60:
            return "defensive"
        
        return None
    
    def _compute_haptic_feedback(
        self,
        engagement: EngagementScore,
        typing_speed: Dict[str, float]
    ) -> Optional[Dict[str, Any]]:
        """
        Generate haptic feedback choreography.
        
        Returns:
            Haptic payload for device, or None
        """
        haptic = None
        
        # High engagement → gentle haptic pulse
        if engagement.overall > 75:
            haptic = {
                "type": "pulse",
                "intensity": int(engagement.overall / 100 * 100),  # 0-100
                "duration_ms": 200,
                "pattern": "heartbeat"
            }
        
        # User typing fast → subtle vibration
        if typing_speed.get("cpm", 0) > 20:
            haptic = {
                "type": "vibration",
                "intensity": min(100, int(typing_speed["cpm"])),
                "duration_ms": 50,
                "pattern": "rhythmic"
            }
        
        # User absent → warning haptic
        if engagement.primary_level == EngagementLevel.ABSENT:
            haptic = {
                "type": "alert",
                "intensity": 30,
                "duration_ms": 300,
                "pattern": "attention"
            }
        
        return haptic


# ============================================================================
# Engine-Specific Export (Cross-Platform Compatibility)
# ============================================================================

class EngineExporter:
    """
    Converts SpriteState to engine-specific formats.
    Godot, UE5, and web all consume the same intermediate format (JSON),
    then adapt locally.
    """
    
    @staticmethod
    def to_generic_json(sprite_state: SpriteState) -> Dict[str, Any]:
        """
        Standard JSON format consumable by any engine.
        """
        return sprite_state.to_dict()
    
    @staticmethod
    def to_godot_gd(sprite_state: SpriteState) -> str:
        """
        Export as GDScript variable assignment for Godot.
        Can be loaded via JsonRpc or WebSocket.
        """
        data = sprite_state.to_dict()
        return f"var sprite_state = {json.dumps(data, indent=2)}"
    
    @staticmethod
    def to_ue5_json(sprite_state: SpriteState) -> str:
        """
        JSON format compatible with UE5's animation blueprints.
        """
        data = sprite_state.to_dict()
        return json.dumps(data, indent=2)
    
    @staticmethod
    def to_tripo3d_format(sprite_state: SpriteState, model_id: str) -> Dict[str, Any]:
        """
        Format for Tripo3D export preparation.
        Includes animation state for model rigging.
        """
        return {
            "tripo_model_id": model_id,
            "animation": sprite_state.animation_state.value,
            "gaze": {
                "look_at_x": sprite_state.gaze_vector.x,
                "look_at_y": sprite_state.gaze_vector.y,
            },
            "expression": sprite_state.micro_expression,
            "haptic_feedback": sprite_state.haptic_event,
            "timestamp": sprite_state.timestamp
        }


# ============================================================================
# Example Usage
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    # Initialize components
    gaze_tracker = GazeTracker()
    input_detector = InputDetector()
    engagement_engine = EngagementEngine()
    behavior_engine = SpriteBehaviorEngine()
    
    print("🎯 WYF* Sprite Biometric Engine - Test Simulation\n")
    
    # Simulate biometric stream
    test_scenarios = [
        {
            "name": "User absent",
            "gaze": None,
            "typing": {"wpm": 0, "cpm": 0},
            "idle": True
        },
        {
            "name": "User typing focused",
            "gaze": {"x": 0.5, "y": 0.5, "confidence": 0.9},
            "typing": {"wpm": 60, "cpm": 35},
            "idle": False
        },
        {
            "name": "User engaged with character",
            "gaze": {"x": 0.6, "y": 0.45, "confidence": 0.85},
            "typing": {"wpm": 25, "cpm": 12},
            "idle": False
        },
        {
            "name": "User distracted",
            "gaze": {"x": 0.2, "y": 0.8, "confidence": 0.5},
            "typing": {"wpm": 5, "cpm": 2},
            "idle": False
        },
    ]
    
    for scenario in test_scenarios:
        print(f"Scenario: {scenario['name']}")
        
        gaze = gaze_tracker.process_gaze_sample(scenario["gaze"]) if scenario["gaze"] else None
        engagement = engagement_engine.calculate_engagement(
            gaze, scenario["typing"], scenario["idle"]
        )
        sprite_state = behavior_engine.compute_sprite_state(
            engagement, gaze, scenario["typing"],
            storyline_type="main_a", storyline_progress=35
        )
        
        print(f"  Engagement: {engagement.overall}% ({engagement.primary_level.value})")
        print(f"  Animation: {sprite_state.animation_state.value}")
        print(f"  Expression: {sprite_state.micro_expression}")
        if sprite_state.haptic_event:
            print(f"  Haptic: {sprite_state.haptic_event['type']}")
        
        # Export to multiple formats
        generic = EngineExporter.to_generic_json(sprite_state)
        print(f"  → JSON: {json.dumps(generic, indent=2)}\n")
