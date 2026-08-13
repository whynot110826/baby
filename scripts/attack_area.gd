extends Area3D

@export var damage := 1

func _ready():
    connect("body_entered", Callable(self, "_on_body_entered"))

func _on_body_entered(body):
    # Saldırı yapanın Area'sı; dostlara zarar verme
    if not body:
        return
    if body.is_in_group("allies"):
        return
    if body.has_method("take_damage"):
        body.take_damage(damage, owner)
