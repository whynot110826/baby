extends Node

@export var bad_toy_scene: PackedScene
@export var good_toy_scene: PackedScene
@export var spawn_area_center := Vector3.ZERO
@export var spawn_area_size := Vector3(6, 0, 6)
@export var initial_bad := 4
@export var initial_good := 2
@export var respawn_interval := 6.0

func _ready():
    randomize()
    for i in range(initial_bad):
        _spawn(bad_toy_scene)
    for i in range(initial_good):
        _spawn(good_toy_scene)
    if respawn_interval > 0:
        _start_respawn_timer()

func _spawn(scene: PackedScene):
    if not scene:
        return
    var pos = spawn_area_center + Vector3(
        randf_range(-spawn_area_size.x/2, spawn_area_size.x/2),
        0,
        randf_range(-spawn_area_size.z/2, spawn_area_size.z/2)
    )
    var inst = scene.instantiate()
    inst.global_transform = Transform(inst.global_transform.basis, pos)
    get_tree().current_scene.add_child(inst)

func _start_respawn_timer():
    var t = Timer.new()
    t.wait_time = respawn_interval
    t.autostart = true
    t.one_shot = false
    t.connect("timeout", Callable(self, "_on_respawn_timer"))
    add_child(t)

func _on_respawn_timer():
    # basit: %50 kötü, %50 iyi spawn
    if randi() % 2 == 0:
        _spawn(bad_toy_scene)
    else:
        _spawn(good_toy_scene)
