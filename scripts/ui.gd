extends CanvasLayer

onready var health_label: Label = $VBoxContainer/HealthLabel
onready var allies_label: Label = $VBoxContainer/AlliesLabel

func _ready():
    add_to_group("ui")
    # başlangıç textleri
    health_label.text = "Can: -"
    allies_label.text = "Yardımcılar: 0"

func on_player_health_changed(new_health):
    health_label.text = "Can: %d" % new_health

func on_allies_changed(count):
    allies_label.text = "Yardımcılar: %d" % count
