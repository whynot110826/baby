extends "res://scripts/toy.gd"

@export var follow_distance := 3.0
@export var assist_cooldown := 2.5
@export var assist_heal := 2
@export var attack_damage := 1
@export var attack_range := 1.2

var last_assist := -10.0
onready var player = null
onready var sense_area: Area3D = $SenseArea

func _ready():
    ._ready()
    is_good = true
    add_to_group("allies")
    var players = get_tree().get_nodes_in_group("player")
    if players.size() > 0:
        player = players[0]

func _physics_process(delta):
    if not player:
        return
    var to_player = player.global_transform.origin - global_transform.origin
    var dist = to_player.length()
    if dist > follow_distance:
        var dir = to_player.normalized()
        translate(dir * 2.5 * delta)
    # Periyodik şifa
    if dist <= follow_distance and Engine.get_physics_time() - last_assist > assist_cooldown:
        if player and player.has_method("heal"):
            player.heal(assist_heal)
            last_assist = Engine.get_physics_time()
    # Yakındaki kötü oyuncaklara otomatik saldır (sense_area içinden)
    var bodies = sense_area.get_overlapping_bodies()
    for b in bodies:
        if b and b.has_method("take_damage") and not b.is_in_group("allies"):
            b.take_damage(attack_damage, self)
