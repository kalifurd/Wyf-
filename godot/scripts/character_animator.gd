# Character Animation System for WYF* Desktop App
# Handles sprite rendering, animation states, and emotional expressions

extends Node
class_name CharacterAnimator

# Animation states and their properties
var animation_states = {
	"idle": {
		"frame": 0,
		"duration": 2.0,
		"emotion": "waiting",
		"body_language": "relaxed"
	},
	"anticipation": {
		"frame": 1,
		"duration": 1.5,
		"emotion": "eager",
		"body_language": "leaning_forward",
		"effects": ["eye_sparkle", "subtle_glow"]
	},
	"vulnerable": {
		"frame": 2,
		"duration": 2.0,
		"emotion": "uncertain",
		"body_language": "closed_off",
		"effects": ["soft_light"]
	},
	"playful": {
		"frame": 3,
		"duration": 1.2,
		"emotion": "flirty",
		"body_language": "animated",
		"effects": ["sparkles"]
	},
	"romantic": {
		"frame": 4,
		"duration": 2.5,
		"emotion": "intimate",
		"body_language": "open",
		"effects": ["heart_particles", "glow"]
	},
	"conflicted": {
		"frame": 5,
		"duration": 1.8,
		"emotion": "confused",
		"body_language": "turned_away",
		"effects": ["uncertainty_aura"]
	},
	"confident": {
		"frame": 6,
		"duration": 1.5,
		"emotion": "assured",
		"body_language": "eye_contact",
		"effects": ["confidence_aura"]
	},
	"shy": {
		"frame": 7,
		"duration": 2.0,
		"emotion": "bashful",
		"body_language": "looking_down",
		"effects": ["blush"]
	}
}

# Sprite and animation references
var character_container: Control
var current_sprite: TextureRect
var current_state: String = "idle"
var animation_timer: Timer
var particle_systems: Dictionary = {}
var chemistry_level: int = 50
var trust_level: int = 50
var conflict_level: int = 30

func setup(container: Control):
	"""Initialize character animator with container."""
	character_container = container
	
	# Create main sprite
	current_sprite = TextureRect.new()
	current_sprite.expand_mode = TextureRect.EXPAND_FIT_SIZE
	current_sprite.anchor_left = 0.5
	current_sprite.anchor_top = 0.5
	current_sprite.anchor_right = 0.5
	current_sprite.anchor_bottom = 1.0
	current_sprite.offset_x = -128
	current_sprite.offset_y = -256
	character_container.add_child(current_sprite)
	
	# Create animation timer
	animation_timer = Timer.new()
	add_child(animation_timer)
	animation_timer.timeout.connect(_on_animation_timer_timeout)
	
	# Create particle systems
	_setup_particle_systems()
	
	# Load initial sprite (placeholder)
	_load_character_sprite("res://assets/characters/default_character.png")

func _setup_particle_systems():
	"""Initialize particle effect systems."""
	var effects = ["eye_sparkle", "sparkles", "heart_particles", "glow", "blush", "confidence_aura", "uncertainty_aura", "soft_light"]
	
	for effect in effects:
		var particles = CPUParticles2D.new()
		particles.emitting = false
		character_container.add_child(particles)
		particle_systems[effect] = particles
		_configure_particle_system(effect, particles)

func _configure_particle_system(effect_type: String, particles: CPUParticles2D):
	"""Configure individual particle systems."""
	match effect_type:
		"eye_sparkle":
			particles.amount = 8
			particles.lifetime = 0.8
			particles.emission_shape = CPUParticles2D.EMISSION_SHAPE_POINT
			particles.gravity = Vector2(0, 50)
		"sparkles":
			particles.amount = 12
			particles.lifetime = 1.2
			particles.emission_shape = CPUParticles2D.EMISSION_SHAPE_CIRCLE
			particles.emission_shape_scale = 50
		"heart_particles":
			particles.amount = 6
			particles.lifetime = 2.0
			particles.emission_shape = CPUParticles2D.EMISSION_SHAPE_POINT
			particles.gravity = Vector2(0, -30)
		"glow":
			particles.amount = 20
			particles.lifetime = 0.5
			particles.emission_shape = CPUParticles2D.EMISSION_SHAPE_CIRCLE
			particles.emission_shape_scale = 80
		"blush":
			particles.amount = 4
			particles.lifetime = 1.0
			particles.emission_shape = CPUParticles2D.EMISSION_SHAPE_POINT
		"confidence_aura":
			particles.amount = 16
			particles.lifetime = 1.5
			particles.emission_shape = CPUParticles2D.EMISSION_SHAPE_RING
			particles.emission_shape_scale = 100
		"uncertainty_aura":
			particles.amount = 10
			particles.lifetime = 1.2
			particles.emission_shape = CPUParticles2D.EMISSION_SHAPE_CIRCLE
			particles.emission_shape_scale = 60
		"soft_light":
			particles.amount = 8
			particles.lifetime = 1.0
			particles.emission_shape = CPUParticles2D.EMISSION_SHAPE_POINT

func play_animation(animation_name: String):
	"""Play animation by state name."""
	if animation_states.has(animation_name):
		current_state = animation_name
		var state_data = animation_states[animation_name]
		
		# Stop current animations
		animation_timer.stop()
		_disable_all_particles()
		
		# Play new animation
		animation_timer.start(state_data.get("duration", 1.0))
		
		# Enable relevant particle effects
		for effect in state_data.get("effects", []):
			if particle_systems.has(effect):
				particle_systems[effect].emitting = true
		
		# Apply visual changes based on body language
		_apply_body_language(state_data.get("body_language", ""))
		
		# Update sprite based on relationship metrics
		_update_sprite_based_on_metrics()

func _apply_body_language(body_language: String):
	"""Apply visual body language changes to character."""
	var tween = create_tween()
	tween.set_trans(Tween.TRANS_SINE)
	tween.set_ease(Tween.EASE_IN_OUT)
	
	match body_language:
		"leaning_forward":
			tween.tween_property(current_sprite, "position:y", -50, 0.5)
			tween.tween_property(current_sprite, "scale", Vector2(1.1, 1.1), 0.5)
		"closed_off":
			tween.tween_property(current_sprite, "scale", Vector2(0.9, 1.0), 0.5)
			tween.tween_property(current_sprite, "modulate", Color(0.8, 0.8, 0.9, 1.0), 0.5)
		"animated":
			tween.tween_property(current_sprite, "rotation", 0.1, 0.3)
			tween.tween_property(current_sprite, "rotation", -0.1, 0.3)
		"eye_contact":
			tween.tween_property(current_sprite, "position:x", 0, 0.5)
			current_sprite.modulate = Color(1.0, 1.0, 1.0, 1.0)
		"looking_down":
			tween.tween_property(current_sprite, "position:y", 30, 0.5)
		"open":
			tween.tween_property(current_sprite, "scale", Vector2(1.15, 1.15), 0.5)
			tween.tween_property(current_sprite, "modulate", Color(1.0, 1.0, 1.0, 1.0), 0.5)
		"turned_away":
			tween.tween_property(current_sprite, "position:x", 100, 0.5)

func _update_sprite_based_on_metrics():
	"""Update sprite appearance based on relationship metrics."""
	var color_tint = Color.WHITE
	
	# Chemistry affects brightness and warmth
	var chemistry_factor = float(chemistry_level) / 100.0
	color_tint = color_tint.lerp(Color(1.0, 0.8, 0.8, 1.0), chemistry_factor * 0.3)
	
	# Trust affects overall glow
	var trust_factor = float(trust_level) / 100.0
	var glow_intensity = 0.8 + (trust_factor * 0.2)
	
	# Conflict dims the character
	var conflict_factor = float(conflict_level) / 100.0
	color_tint = color_tint.darkened(conflict_factor * 0.2)
	
	current_sprite.modulate = color_tint

func _disable_all_particles():
	"""Stop all particle effects."""
	for particles in particle_systems.values():
		particles.emitting = false

func _on_animation_timer_timeout():
	"""Handle animation timer completion."""
	# Loop animation or return to idle
	if current_state != "idle":
		play_animation("idle")

func _load_character_sprite(path: String):
	"""Load character sprite texture."""
	var texture = load(path)
	if texture:
		current_sprite.texture = texture
	else:
		# Create placeholder sprite
		var placeholder = Image.create(256, 512, false, Image.FORMAT_RGBA8)
		placeholder.fill(Color(0.5, 0.5, 0.5, 1.0))
		current_sprite.texture = ImageTexture.create_from_image(placeholder)

func update_metrics(chemistry: int, trust: int, conflict: int):
	"""Update relationship metrics and refresh sprite."""
	chemistry_level = clamp(chemistry, 0, 100)
	trust_level = clamp(trust, 0, 100)
	conflict_level = clamp(conflict, 0, 100)
	_update_sprite_based_on_metrics()

func set_character_preset(archetype: String):
	"""Load character sprite based on archetype."""
	var sprite_path = "res://assets/characters/%s.png" % archetype.to_lower()
	_load_character_sprite(sprite_path)
