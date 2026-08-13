extends "res://scripts/toy.gd"

@export var patrol_points := [] # set in editor: array of Vector3 world positions (exported as Variant)
@export var speed := 2.2
@export var aggro_distance := 7.5
@export var attack_distance := 1.0
@export var attack_damage := 1
@export var attack_cooldown := 1.2

var current_patrol_index := 0
var state := "patrol" # patrol / chase
var last_attack := -10.0
onready var player = null

func _ready():
    ._ready()
    var players = get_tree().get_nodes_in_group("player")
    if players.size() > 0:
        player = players[0]

func _physics_process(delta):
    if player:
        var dist_to_player = (player.global_transform.origin - global_transform.origin).length()
        if dist_to_player <= aggro_distance:
            state = "chase"
        elif state == "chase" and dist_to_player > aggro_distance * 1.2:
            state = "patrol"

    if state == "patrol":
        _do_patrol(delta)
    elif state == "chase":
        _do_chase(delta)

func _do_patrol(delta):
    if patrol_points.size() == 0:
        return
    var target = patrol_points[current_patrol_index]
    var dir = (target - global_transform.origin)
    if dir.length() < 0.25:
        current_patrol_index = (current_patrol_index + 1) % patrol_points.size()
        return
    translate(dir.normalized() * speed * delta)

func _do_chase(delta):
    if not player:
        return
    var dir = (player.global_transform.origin - global_transform.origin)
    var dist = dir.length()
    if dist > attack_distance:
        translate(dir.normalized() * speed * delta)
    else:
        _try_attack()

func _try_attack():
    var now = Engine.get_physics_time()
    if now - last_attack < attack_cooldown:
        return
    last_attack = now
    if player:
        player.take_damage(attack_damage, self)
