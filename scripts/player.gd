extends CharacterBody3D

@export var speed := 4.5
@export var jump_velocity := 4.0
@export var gravity := ProjectSettings.get_setting("physics/3d/default_gravity")
@export var attack_cooldown := 0.6
@export var attack_damage := 1
@export var max_health := 12

var velocity: Vector3 = Vector3.ZERO
var last_attack_time := -10.0
var health := max_health

onready var cam: Camera3D = $Camera3D
onready var attack_area: Area3D = $AttackArea

func _ready():
    add_to_group("player")
    add_to_group("allies") # bebeği de 'allies' grubuna koy; dostlara zarar vermesin
    attack_area.monitoring = false
    get_tree().call_group("ui", "on_player_health_changed", health)

func _unhandled_input(event):
    if event is InputEventMouseMotion:
        rotate_y(-event.relative.x * 0.003)
        cam.rotate_x(-event.relative.y * 0.003)
        cam.rotation.x = clamp(cam.rotation.x, deg2rad(-80), deg2rad(80))

func _physics_process(delta):
    var input_dir = Vector3.ZERO
    input_dir.z = Input.get_action_strength("move_back") - Input.get_action_strength("move_forward")
    input_dir.x = Input.get_action_strength("move_right") - Input.get_action_strength("move_left")
    if input_dir.length() > 0:
        input_dir = input_dir.normalized()
    var forward = -global_transform.basis.z
    var right = global_transform.basis.x
    var dir_world = (forward * input_dir.z + right * input_dir.x) * speed
    velocity.x = dir_world.x
    velocity.z = dir_world.z

    if not is_on_floor():
        velocity.y -= gravity * delta
    else:
        if Input.is_action_just_pressed("jump"):
            velocity.y = jump_velocity
        else:
            velocity.y = 0

    if Input.is_action_just_pressed("attack"):
        _try_attack()

    velocity = move_and_slide(velocity, Vector3.UP)

func _try_attack():
    var now = Engine.get_physics_time()
    if now - last_attack_time < attack_cooldown:
        return
    last_attack_time = now
    attack_area.monitoring = true
    # kısa pencere ile aktif et
    await get_tree().create_timer(0.12).timeout
    attack_area.monitoring = false

func take_damage(dmg: int, source=null):
    health -= dmg
    get_tree().call_group("ui", "on_player_health_changed", health)
    if health <= 0:
        die()

func heal(amount: int):
    health = min(health + amount, max_health)
    get_tree().call_group("ui", "on_player_health_changed", health)

func die():
    print("Bebek öldü — sahne yeniden yüklenecek.")
    await get_tree().create_timer(0.5).timeout
    get_tree().reload_current_scene()
