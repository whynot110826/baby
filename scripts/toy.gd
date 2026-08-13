extends CharacterBody3D

@export var max_health := 3
@export var is_good := false

signal died(toy)

var health := 0

func _ready():
    health = max_health

func take_damage(dmg: int, source=null):
    health -= dmg
    if health <= 0:
        emit_signal("died", self)
        queue_free()
