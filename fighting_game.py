import pygame
import sys
import random
import math
from enum import Enum

# Pygame'i başlat
pygame.init()

# Ekran ayarları
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 700
FPS = 60

# Renkler
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (220, 50, 50)
BLUE = (100, 150, 255)
GREEN = (100, 255, 150)
GRAY = (150, 150, 150)
YELLOW = (255, 255, 100)
PURPLE = (180, 100, 255)
PINK = (255, 150, 200)
DARK_BLUE = (30, 50, 100)
LIGHT_PURPLE = (200, 150, 255)
ORANGE = (255, 150, 50)
CYAN = (100, 255, 255)

# Oyun Durumları
class GameState(Enum):
    MENU = 1
    CHARACTER_SELECT = 2
    FIGHTING = 3
    VICTORY = 4
    GAME_OVER = 5

# Karakter Tipileri
class CharacterType(Enum):
    BABY = 1
    GHOST = 2
    FLAME = 3
    FROST = 4


class Projectile(pygame.sprite.Sprite):
    """Özel yeteneklerden kaynaklanan ateş/buz projektilleri"""
    def __init__(self, x, y, direction, p_type="fire"):
        super().__init__()
        self.p_type = p_type
        self.direction = direction
        
        if p_type == "fire":
            self.color = ORANGE
            self.speed = 6
            self.size = 15
            self.damage = 20
        elif p_type == "ice":
            self.color = CYAN
            self.speed = 5
            self.size = 12
            self.damage = 15
        
        self.image = pygame.Surface((self.size, self.size))
        self.image.fill(self.color)
        pygame.draw.circle(self.image, WHITE, (self.size//2, self.size//2), self.size//2 - 2, 2)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        self.lifetime = 120
    
    def update(self):
        self.rect.x += self.speed * self.direction
        self.lifetime -= 1
        
        if self.lifetime <= 0 or self.rect.x < 0 or self.rect.x > SCREEN_WIDTH:
            self.kill()
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Character(pygame.sprite.Sprite):
    """Dövüş oyunu karakteri"""
    def __init__(self, x, y, char_type, player_num=1):
        super().__init__()
        self.char_type = char_type
        self.player_num = player_num  # 1 veya 2
        self.direction = 1 if player_num == 1 else -1  # Yüzüne dönüş yönü
        
        # Temel özellikler
        self.max_hp = 100
        self.hp = self.max_hp
        self.x = x
        self.y = y
        
        # Fizik
        self.vel_x = 0
        self.vel_y = 0
        self.on_ground = False
        self.gravity = 0.6
        self.max_speed = 6
        self.jump_power = 15
        
        # Dövüş
        self.is_blocking = False
        self.attack_cooldown = 0
        self.combo_counter = 0
        self.combo_timer = 0
        self.invincible_timer = 0
        
        # Enerji (Special yetenekler için)
        self.max_energy = 100
        self.energy = self.max_energy
        self.energy_regen = 0.5
        
        # Karakter özel özellikleri
        self.setup_character()
        
        # Görünüm
        self.image = pygame.Surface((50, 80))
        self.draw_character()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    
    def setup_character(self):
        """Karakter özel yeteneklerini ayarla"""
        if self.char_type == CharacterType.BABY:
            self.char_name = "Baby"
            self.speed = 7  # Hızlı
            self.punch_damage = 8
            self.kick_damage = 12
            self.color = BLUE
        
        elif self.char_type == CharacterType.GHOST:
            self.char_name = "Ghost"
            self.speed = 5
            self.punch_damage = 10
            self.kick_damage = 14
            self.color = LIGHT_PURPLE
        
        elif self.char_type == CharacterType.FLAME:
            self.char_name = "Flame Spirit"
            self.speed = 4  # Yavaş
            self.punch_damage = 12
            self.kick_damage = 16
            self.color = ORANGE
        
        elif self.char_type == CharacterType.FROST:
            self.char_name = "Frost"
            self.speed = 6
            self.punch_damage = 10
            self.kick_damage = 13
            self.color = CYAN
    
    def draw_character(self):
        """Karakteri çiz"""
        self.image.fill(BLACK)
        self.image.set_colorkey(BLACK)
        
        # Vücut
        pygame.draw.circle(self.image, self.color, (25, 40), 15)
        # Baş
        pygame.draw.circle(self.image, self.color, (25, 15), 10)
        # Gözler
        pygame.draw.circle(self.image, YELLOW, (20, 12), 2)
        pygame.draw.circle(self.image, YELLOW, (30, 12), 2)
        
        # Karakter özel görünümü
        if self.char_type == CharacterType.FLAME:
            # Ateş auraası
            pygame.draw.circle(self.image, ORANGE, (25, 40), 18, 2)
        elif self.char_type == CharacterType.FROST:
            # Buz auraası
            pygame.draw.circle(self.image, CYAN, (25, 40), 18, 2)
        elif self.char_type == CharacterType.GHOST:
            # Hayalet göründü
            pygame.draw.ellipse(self.image, LIGHT_PURPLE, (15, 5, 20, 30))
    
    def handle_input(self, keys, controls):
        """Oyuncu girdisini işle"""
        # Hareket
        if keys[controls["left"]]:
            self.vel_x = max(self.vel_x - 0.5, -self.speed)
        elif keys[controls["right"]]:
            self.vel_x = min(self.vel_x + 0.5, self.speed)
        else:
            self.vel_x *= 0.8
        
        # Zıplama
        if keys[controls["jump"]] and self.on_ground:
            self.vel_y = -self.jump_power
            self.on_ground = False
        
        # Blok
        self.is_blocking = keys[controls["block"]]
        
        return {
            "punch": keys[controls["punch"]],
            "kick": keys[controls["kick"]],
            "heavy": keys[controls["heavy"]],
            "special": keys[controls["special"]]
        }
    
    def attack(self, attack_type, opponent):
        """Saldırı yap"""
        if self.attack_cooldown > 0:
            return 0
        
        damage = 0
        energy_cost = 0
        
        if attack_type == "punch":
            damage = self.punch_damage
            self.attack_cooldown = 20
            energy_cost = 5
        
        elif attack_type == "kick":
            damage = self.kick_damage
            self.attack_cooldown = 25
            energy_cost = 8
        
        elif attack_type == "heavy":
            damage = int(self.punch_damage * 1.5 + self.kick_damage * 1.5)
            self.attack_cooldown = 35
            energy_cost = 15
        
        elif attack_type == "special":
            if self.energy < 30:
                return 0
            damage = self.get_special_attack(opponent)
            self.attack_cooldown = 40
            energy_cost = 30
        
        if self.energy >= energy_cost:
            self.energy -= energy_cost
            
            # Combo sistemi
            if self.combo_timer > 0:
                self.combo_counter += 1
                damage = int(damage * (1 + self.combo_counter * 0.15))
            else:
                self.combo_counter = 1
            
            self.combo_timer = 30
            
            # Blok kontrol
            if opponent.is_blocking:
                damage = int(damage * 0.5)
            
            return damage
        
        return 0
    
    def get_special_attack(self, opponent):
        """Özel saldırısı yap"""
        if self.char_type == CharacterType.BABY:
            # Işık Patlaması
            return 35
        elif self.char_type == CharacterType.GHOST:
            # Topaç Hareketi
            return 40
        elif self.char_type == CharacterType.FLAME:
            # Ateş Tornedosu
            return 45
        elif self.char_type == CharacterType.FROST:
            # Donma Alanı
            return 40
        
        return 30
    
    def take_damage(self, damage):
        """Hasar al"""
        if self.is_blocking:
            damage = int(damage * 0.5)
        
        self.hp = max(0, self.hp - damage)
        self.invincible_timer = 15
    
    def update(self, ground_y, opponent=None):
        """Karakteri güncelle"""
        # Yerçekimi
        self.vel_y = min(self.vel_y + self.gravity, 15)
        
        # Hareket
        self.x += self.vel_x
        self.y += self.vel_y
        
        # Ekran sınırları
        if self.x < 50:
            self.x = 50
        if self.x > SCREEN_WIDTH - 100:
            self.x = SCREEN_WIDTH - 100
        
        # Zemin çarpışması
        if self.y + 80 >= ground_y:
            self.y = ground_y - 80
            self.vel_y = 0
            self.on_ground = True
        else:
            self.on_ground = False
        
        # Cooldown'ları azalt
        self.attack_cooldown = max(0, self.attack_cooldown - 1)
        self.combo_timer = max(0, self.combo_timer - 1)
        self.invincible_timer = max(0, self.invincible_timer - 1)
        
        # Enerji regenerasyonu
        self.energy = min(self.max_energy, self.energy + self.energy_regen)
        
        # Rect güncelle
        self.rect.x = self.x
        self.rect.y = self.y
    
    def draw(self, surface):
        # Görünme efekti (hit olduktan sonra)
        if self.invincible_timer > 0 and self.invincible_timer % 5 < 3:
            return
        
        surface.blit(self.image, self.rect)
        
        # Blok gösterimi
        if self.is_blocking:
            pygame.draw.circle(surface, GREEN, (self.x + 25, self.y + 40), 40, 3)


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Mortal Kombat - Mistik Dövüş")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.state = GameState.MENU
        self.ground_y = SCREEN_HEIGHT - 100
        
        self.player1_char = None
        self.player2_char = None
        self.winner = None
        
        self.projectiles = []
        self.screen_shake = 0
    
    def show_menu(self):
        """Ana menü"""
        font_large = pygame.font.Font(None, 80)
        font_small = pygame.font.Font(None, 40)
        
        self.screen.fill(DARK_BLUE)
        
        title = font_large.render("MORTAL KOMBAT", True, RED)
        subtitle = font_small.render("Mistik Dövüş Oyunu", True, YELLOW)
        start = font_small.render("SPACE: Başla | ESC: Çıkış", True, WHITE)
        
        self.screen.blit(title, (SCREEN_WIDTH // 2 - 350, 150))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - 250, 250))
        self.screen.blit(start, (SCREEN_WIDTH // 2 - 300, 400))
    
    def show_character_select(self):
        """Karakter seçim ekranı"""
        font_large = pygame.font.Font(None, 50)
        font_small = pygame.font.Font(None, 30)
        
        self.screen.fill(DARK_BLUE)
        
        title = font_large.render("KARAKTERİ SEÇ", True, YELLOW)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - 200, 50))
        
        # Karakterler
        characters = [
            (CharacterType.BABY, "Baby", BLUE, 100),
            (CharacterType.GHOST, "Ghost", LIGHT_PURPLE, 350),
            (CharacterType.FLAME, "Flame Spirit", ORANGE, 600),
            (CharacterType.FROST, "Frost", CYAN, 850),
        ]
        
        player_text = font_large.render(f"Oyuncu {self.selected_player}:", True, WHITE)
        self.screen.blit(player_text, (50, 150))
        
        for i, (char_type, name, color, x) in enumerate(characters):
            # Karakter kutusu
            pygame.draw.rect(self.screen, color, (x, 250, 120, 200), 2)
            
            # Karakter adı
            text = font_small.render(name, True, color)
            self.screen.blit(text, (x + 10, 260))
            
            # Seçim talimatı
            info = font_small.render(f"[{i + 1}]", True, WHITE)
            self.screen.blit(info, (x + 35, 400))
    
    def setup_fight(self, p1_char, p2_char):
        """Dövüşü başlat"""
        self.player1_char = Character(200, 300, p1_char, 1)
        self.player2_char = Character(SCREEN_WIDTH - 250, 300, p2_char, 2)
        self.state = GameState.FIGHTING
        self.projectiles = []
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.FIGHTING:
                        self.state = GameState.MENU
                    else:
                        self.running = False
                
                if self.state == GameState.MENU and event.key == pygame.K_SPACE:
                    self.state = GameState.CHARACTER_SELECT
                    self.selected_player = 1
                    self.selected_chars = {}
                
                if self.state == GameState.CHARACTER_SELECT:
                    if event.key in [pygame.K_1]:
                        self.selected_chars[self.selected_player] = CharacterType.BABY
                        self.next_character_select()
                    elif event.key in [pygame.K_2]:
                        self.selected_chars[self.selected_player] = CharacterType.GHOST
                        self.next_character_select()
                    elif event.key in [pygame.K_3]:
                        self.selected_chars[self.selected_player] = CharacterType.FLAME
                        self.next_character_select()
                    elif event.key in [pygame.K_4]:
                        self.selected_chars[self.selected_player] = CharacterType.FROST
                        self.next_character_select()
                
                if self.state == GameState.VICTORY and event.key == pygame.K_SPACE:
                    self.state = GameState.MENU
    
    def next_character_select(self):
        if self.selected_player == 1:
            self.selected_player = 2
        else:
            # Seçim bitti, dövüş başlat
            self.setup_fight(self.selected_chars[1], self.selected_chars[2])
    
    def update(self):
        if self.state != GameState.FIGHTING:
            return
        
        # Oyuncu girdileri
        keys = pygame.key.get_pressed()
        
        # Player 1 kontrolleri (WASD)
        p1_controls = {
            "left": pygame.K_a,
            "right": pygame.K_d,
            "jump": pygame.K_w,
            "punch": pygame.K_q,
            "kick": pygame.K_e,
            "heavy": pygame.K_r,
            "block": pygame.K_f,
            "special": pygame.K_t
        }
        
        # Player 2 kontrolleri (Ok tuşları)
        p2_controls = {
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
            "jump": pygame.K_UP,
            "punch": pygame.K_u,
            "kick": pygame.K_i,
            "heavy": pygame.K_o,
            "block": pygame.K_p,
            "special": pygame.K_k
        }
        
        # Oyuncuların hareketlerini işle
        p1_actions = self.player1_char.handle_input(keys, p1_controls)
        p2_actions = self.player2_char.handle_input(keys, p2_controls)
        
        # Saldırıları işle
        if p1_actions["punch"]:
            damage = self.player1_char.attack("punch", self.player2_char)
            if damage > 0:
                self.player2_char.take_damage(damage)
                self.screen_shake = 5
        
        if p1_actions["kick"]:
            damage = self.player1_char.attack("kick", self.player2_char)
            if damage > 0:
                self.player2_char.take_damage(damage)
                self.screen_shake = 7
        
        if p1_actions["heavy"]:
            damage = self.player1_char.attack("heavy", self.player2_char)
            if damage > 0:
                self.player2_char.take_damage(damage)
                self.screen_shake = 10
        
        if p1_actions["special"]:
            damage = self.player1_char.attack("special", self.player2_char)
            if damage > 0:
                self.player2_char.take_damage(damage)
                self.screen_shake = 15
        
        if p2_actions["punch"]:
            damage = self.player2_char.attack("punch", self.player1_char)
            if damage > 0:
                self.player1_char.take_damage(damage)
                self.screen_shake = 5
        
        if p2_actions["kick"]:
            damage = self.player2_char.attack("kick", self.player1_char)
            if damage > 0:
                self.player1_char.take_damage(damage)
                self.screen_shake = 7
        
        if p2_actions["heavy"]:
            damage = self.player2_char.attack("heavy", self.player1_char)
            if damage > 0:
                self.player1_char.take_damage(damage)
                self.screen_shake = 10
        
        if p2_actions["special"]:
            damage = self.player2_char.attack("special", self.player1_char)
            if damage > 0:
                self.player1_char.take_damage(damage)
                self.screen_shake = 15
        
        # Karakterleri güncelle
        self.player1_char.update(self.ground_y, self.player2_char)
        self.player2_char.update(self.ground_y, self.player1_char)
        
        # Projektilleri güncelle
        for projectile in self.projectiles:
            projectile.update()
        
        # Ekran titremesini azalt
        self.screen_shake = max(0, self.screen_shake - 1)
        
        # Kazanan var mı? ✅ CAN BİTEN KAYBEDER
        if self.player1_char.hp <= 0:
            self.winner = 2
            self.state = GameState.VICTORY
        elif self.player2_char.hp <= 0:
            self.winner = 1
            self.state = GameState.VICTORY
    
    def draw(self):
        self.screen.fill(DARK_BLUE)
        
        if self.state == GameState.MENU:
            self.show_menu()
        elif self.state == GameState.CHARACTER_SELECT:
            self.show_character_select()
        elif self.state == GameState.FIGHTING:
            self.draw_fighting()
        elif self.state == GameState.VICTORY:
            self.draw_victory()
        
        pygame.display.flip()
    
    def draw_fighting(self):
        """Dövüş ekranını çiz"""
        # Arka plan
        self.screen.fill(DARK_BLUE)
        
        # Zemin
        pygame.draw.rect(self.screen, GRAY, (0, self.ground_y, SCREEN_WIDTH, SCREEN_HEIGHT - self.ground_y))
        
        # Çizgi
        pygame.draw.line(self.screen, LIGHT_PURPLE, (0, self.ground_y), (SCREEN_WIDTH, self.ground_y), 3)
        
        # Ekran titresi efekti
        shake_x = random.randint(-self.screen_shake, self.screen_shake)
        shake_y = random.randint(-self.screen_shake, self.screen_shake)
        
        # Karakterleri çiz
        self.player1_char.draw(self.screen)
        self.player2_char.draw(self.screen)
        
        # Projektilleri çiz
        for projectile in self.projectiles:
            projectile.draw(self.screen)
        
        # UI çiz
        self.draw_ui()
    
    def draw_ui(self):
        """Oyun arayüzünü çiz"""
        font_large = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 24)
        
        # Player 1 Bilgisi
        p1_name = font_large.render(self.player1_char.char_name, True, BLUE)
        self.screen.blit(p1_name, (20, 20))
        
        # Player 1 HP Barı
        bar_width = 200
        bar_height = 25
        hp_ratio = self.player1_char.hp / self.player1_char.max_hp
        
        pygame.draw.rect(self.screen, RED, (20, 60, bar_width, bar_height))
        pygame.draw.rect(self.screen, GREEN, (20, 60, int(bar_width * hp_ratio), bar_height))
        pygame.draw.rect(self.screen, WHITE, (20, 60, bar_width, bar_height), 2)
        
        hp_text = font_small.render(f"{int(self.player1_char.hp)}/{self.player1_char.max_hp}", True, WHITE)
        self.screen.blit(hp_text, (30, 67))
        
        # Player 1 Enerji Barı
        energy_ratio = self.player1_char.energy / self.player1_char.max_energy
        pygame.draw.rect(self.screen, ORANGE, (20, 100, bar_width, 15))
        pygame.draw.rect(self.screen, YELLOW, (20, 100, int(bar_width * energy_ratio), 15))
        pygame.draw.rect(self.screen, WHITE, (20, 100, bar_width, 15), 1)
        
        # Player 2 Bilgisi
        p2_name = font_large.render(self.player2_char.char_name, True, self.player2_char.color)
        self.screen.blit(p2_name, (SCREEN_WIDTH - 220, 20))
        
        # Player 2 HP Barı
        hp_ratio = self.player2_char.hp / self.player2_char.max_hp
        
        pygame.draw.rect(self.screen, RED, (SCREEN_WIDTH - 220, 60, bar_width, bar_height))
        pygame.draw.rect(self.screen, GREEN, (SCREEN_WIDTH - 220 + bar_width - int(bar_width * hp_ratio), 60, int(bar_width * hp_ratio), bar_height))
        pygame.draw.rect(self.screen, WHITE, (SCREEN_WIDTH - 220, 60, bar_width, bar_height), 2)
        
        hp_text = font_small.render(f"{int(self.player2_char.hp)}/{self.player2_char.max_hp}", True, WHITE)
        self.screen.blit(hp_text, (SCREEN_WIDTH - 210, 67))
        
        # Player 2 Enerji Barı
        energy_ratio = self.player2_char.energy / self.player2_char.max_energy
        pygame.draw.rect(self.screen, ORANGE, (SCREEN_WIDTH - 220, 100, bar_width, 15))
        pygame.draw.rect(self.screen, YELLOW, (SCREEN_WIDTH - 220 + bar_width - int(bar_width * energy_ratio), 100, int(bar_width * energy_ratio), 15))
        pygame.draw.rect(self.screen, WHITE, (SCREEN_WIDTH - 220, 100, bar_width, 15), 1)
        
        # Kontroller bilgisi
        font_tiny = pygame.font.Font(None, 18)
        info = font_tiny.render("P1: A/D Hareket, W Zıpla, Q Yumruk, E Tekme, R Heavy, F Blok, T Special", True, GRAY)
        self.screen.blit(info, (20, SCREEN_HEIGHT - 60))
        
        info2 = font_tiny.render("P2: Ok Tuşları Hareket, U Yumruk, I Tekme, O Heavy, P Blok, K Special | ESC: Menü", True, GRAY)
        self.screen.blit(info2, (20, SCREEN_HEIGHT - 30))
    
    def draw_victory(self):
        """Zafer ekranı"""
        font_large = pygame.font.Font(None, 80)
        font_small = pygame.font.Font(None, 40)
        
        self.screen.fill(DARK_BLUE)
        
        winner_text = font_large.render(f"OYUNCU {self.winner} KAZANDI!", True, RED)
        
        if self.winner == 1:
            winner_name = self.player1_char.char_name
            color = BLUE
        else:
            winner_name = self.player2_char.char_name
            color = self.player2_char.color
        
        name_text = font_small.render(winner_name, True, color)
        continue_text = font_small.render("SPACE: Menüye Dön", True, WHITE)
        
        self.screen.blit(winner_text, (SCREEN_WIDTH // 2 - 450, 150))
        self.screen.blit(name_text, (SCREEN_WIDTH // 2 - 150, 300))
        self.screen.blit(continue_text, (SCREEN_WIDTH // 2 - 250, 450))
    
    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
