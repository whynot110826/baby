import pygame
import sys
import random
import math
from enum import Enum

# Pygame'i başlat
pygame.init()

# Ekran ayarları
SCREEN_WIDTH = 1200
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

# Fizik
GRAVITY = 0.6
JUMP_POWER = 15
MAX_FALL_SPEED = 20

# Oyun Durumları
class GameState(Enum):
    PLAYING = 1
    LEVEL_COMPLETE = 2
    GAME_OVER = 3
    START = 4


class Particle(pygame.sprite.Sprite):
    """Parçacık efektleri için"""
    def __init__(self, x, y, color, vel_x, vel_y):
        super().__init__()
        self.image = pygame.Surface((5, 5))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=(x, y))
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.lifetime = 30
        self.alpha = 255
    
    def update(self):
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        self.vel_y += GRAVITY / 2
        self.lifetime -= 1
        
        if self.lifetime <= 0:
            self.kill()


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((35, 45))
        self.image.fill(BLUE)
        self.draw_baby()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Fizik
        self.vel_y = 0
        self.vel_x = 0
        self.on_ground = False
        self.max_speed = 5
        self.acceleration = 0.5
        
        # Parlama efekti
        self.glow = 0
        
    def draw_baby(self):
        """Mistik bebek çiz"""
        # Vücut
        pygame.draw.circle(self.image, BLUE, (17, 25), 12)
        # Baş
        pygame.draw.circle(self.image, PINK, (17, 12), 8)
        # Gözler (parlayan)
        pygame.draw.circle(self.image, YELLOW, (13, 10), 2)
        pygame.draw.circle(self.image, YELLOW, (21, 10), 2)
        pygame.draw.circle(self.image, WHITE, (14, 9), 1)
        pygame.draw.circle(self.image, WHITE, (22, 9), 1)
        
    def handle_input(self, keys):
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vel_x = max(self.vel_x - self.acceleration, -self.max_speed)
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel_x = min(self.vel_x + self.acceleration, self.max_speed)
        else:
            self.vel_x *= 0.85
        
        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
            self.vel_y = -JUMP_POWER
            self.on_ground = False
    
    def update(self, platforms, enemies, collectibles, particles):
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
        
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        
        # Platform çarpışması
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                if self.vel_y > 0 and self.rect.bottom <= platform.rect.top + 10:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                elif self.vel_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0
                elif self.vel_x > 0:
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0:
                    self.rect.left = platform.rect.right
        
        # Ödül topla
        for collectible in collectibles[:]:
            if self.rect.colliderect(collectible.rect):
                # Parçacık efekti
                for _ in range(10):
                    angle = random.uniform(0, 2 * math.pi)
                    speed = random.uniform(2, 5)
                    particle = Particle(
                        collectible.rect.centerx, collectible.rect.centery,
                        collectible.color,
                        math.cos(angle) * speed,
                        math.sin(angle) * speed
                    )
                    particles.append(particle)
                collectible.kill()
                return ("collect", collectible.points)
        
        # Düşman çarpışması
        for enemy in enemies[:]:
            if self.rect.colliderect(enemy.rect):
                if self.vel_y > 0 and self.rect.bottom <= enemy.rect.top + 20:
                    self.rect.bottom = enemy.rect.top
                    self.vel_y = -8
                    # Parçacık efekti
                    for _ in range(15):
                        angle = random.uniform(0, 2 * math.pi)
                        speed = random.uniform(2, 6)
                        particle = Particle(
                            enemy.rect.centerx, enemy.rect.centery,
                            RED,
                            math.cos(angle) * speed,
                            math.sin(angle) * speed
                        )
                        particles.append(particle)
                    enemy.kill()
                    return ("kill", 20)
                else:
                    return ("hit", -1)
        
        if self.rect.top > SCREEN_HEIGHT:
            return ("fall", -1)
        
        return None
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color=GRAY):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        # Mistik kenar
        pygame.draw.rect(self.image, LIGHT_PURPLE, self.image.get_rect(), 2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Collectible(pygame.sprite.Sprite):
    """Ödül nesneleri"""
    TYPES = {
        "cookie": {"color": (200, 100, 50), "points": 10, "name": "🍪"},
        "toy": {"color": (255, 100, 100), "points": 10, "name": "🧸"},
        "balloon": {"color": (255, 150, 200), "points": 10, "name": "🎈"},
        "honey": {"color": (255, 200, 0), "points": 10, "name": "🍯"},
        "angel": {"color": (255, 255, 200), "points": 15, "name": "👼"},
        "crystal": {"color": (150, 200, 255), "points": 15, "name": "🌟"},
        "music": {"color": (200, 100, 255), "points": 15, "name": "🎶"},
    }
    
    def __init__(self, x, y, c_type="cookie"):
        super().__init__()
        self.c_type = c_type
        self.info = self.TYPES.get(c_type, self.TYPES["cookie"])
        self.color = self.info["color"]
        self.points = self.info["points"]
        
        self.image = pygame.Surface((20, 20))
        self.image.fill(self.color)
        pygame.draw.circle(self.image, WHITE, (10, 10), 8, 2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        self.bob = 0
        self.bob_speed = 0.1
    
    def update(self):
        self.bob += self.bob_speed
        self.rect.y += math.sin(self.bob) * 0.5
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Enemy(pygame.sprite.Sprite):
    """Düşman sınıfı - farklı türleri var"""
    TYPES = {
        "mosquito": {
            "color": (100, 50, 100),
            "size": (15, 15),
            "speed": 3,
            "behavior": "flying",
            "name": "🦟"
        },
        "syringe": {
            "color": (200, 100, 100),
            "size": (20, 30),
            "speed": 1.5,
            "behavior": "walking",
            "name": "💉"
        },
        "mouse": {
            "color": (150, 100, 100),
            "size": (25, 20),
            "speed": 4,
            "behavior": "walking",
            "name": "🐭"
        },
        "ghost": {
            "color": (200, 200, 255),
            "size": (25, 30),
            "speed": 2,
            "behavior": "floating",
            "name": "👻"
        },
        "nightmare": {
            "color": (100, 50, 150),
            "size": (35, 35),
            "speed": 1.5,
            "behavior": "walking",
            "name": "🌙"
        },
        "spider": {
            "color": (50, 50, 50),
            "size": (20, 20),
            "speed": 3.5,
            "behavior": "jumping",
            "name": "🕷️"
        },
        "alarm": {
            "color": (255, 100, 0),
            "size": (20, 25),
            "speed": 2,
            "behavior": "bouncing",
            "name": "🔔"
        },
    }
    
    def __init__(self, x, y, e_type, left_bound, right_bound):
        super().__init__()
        self.e_type = e_type
        self.info = self.TYPES.get(e_type, self.TYPES["mosquito"])
        self.color = self.info["color"]
        
        size = self.info["size"]
        self.image = pygame.Surface(size)
        self.image.fill(self.color)
        pygame.draw.rect(self.image, LIGHT_PURPLE, self.image.get_rect(), 1)
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.speed = self.info["speed"]
        self.direction = 1
        
        self.behavior = self.info["behavior"]
        self.animation_counter = 0
        self.jump_cooldown = 0
    
    def update(self):
        self.animation_counter += 1
        
        if self.behavior == "flying":
            # Uçan - dalgalı hareket
            self.rect.x += self.speed * self.direction
            self.rect.y += math.sin(self.animation_counter * 0.05) * 0.5
        
        elif self.behavior == "walking":
            # Yürüyen
            self.rect.x += self.speed * self.direction
        
        elif self.behavior == "floating":
            # Yüzen
            self.rect.x += self.speed * self.direction
            self.rect.y += math.sin(self.animation_counter * 0.03) * 0.3
        
        elif self.behavior == "jumping":
            # Atlayan örümcek
            self.rect.x += self.speed * self.direction
            if self.animation_counter % 40 == 0:
                self.rect.y -= 20
            elif self.animation_counter % 40 == 20:
                self.rect.y += 20
        
        elif self.behavior == "bouncing":
            # Zıplayan alarm
            self.rect.x += self.speed * self.direction
            if self.animation_counter % 30 == 0:
                self.rect.y -= 15
            elif self.animation_counter % 30 == 15:
                self.rect.y += 15
        
        # Sınır kontrolü
        if self.rect.left <= self.left_bound or self.rect.right >= self.right_bound:
            self.direction *= -1
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)
    
    def kill(self):
        self.alive = False


class Boss(pygame.sprite.Sprite):
    """Ana düşman - Boss"""
    def __init__(self, x, y):
        super().__init__()
        self.size = (60, 60)
        self.image = pygame.Surface(self.size)
        self.image.fill(PURPLE)
        
        # Boss tasarımı
        pygame.draw.circle(self.image, LIGHT_PURPLE, (30, 30), 28, 3)
        pygame.draw.circle(self.image, YELLOW, (20, 20), 5)
        pygame.draw.circle(self.image, YELLOW, (40, 20), 5)
        pygame.draw.polygon(self.image, RED, [(10, 30), (30, 50), (50, 30)])
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        self.health = 5
        self.speed = 2
        self.direction = 1
        self.animation_counter = 0
        self.attack_cooldown = 0
    
    def update(self):
        self.animation_counter += 1
        
        # Boss hareketi
        self.rect.x += self.speed * self.direction
        self.rect.y += math.sin(self.animation_counter * 0.02) * 0.3
        
        # Sınırlar
        if self.rect.left <= 50 or self.rect.right >= SCREEN_WIDTH - 50:
            self.direction *= -1
        
        self.attack_cooldown = max(0, self.attack_cooldown - 1)
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)
        
        # Sağlık çubuğu
        bar_width = 50
        bar_height = 5
        bar_x = self.rect.centerx - bar_width // 2
        bar_y = self.rect.top - 15
        
        pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(surface, GREEN, (bar_x, bar_y, bar_width * (self.health / 5), bar_height))


class Level:
    """Seviye yöneticisi"""
    def __init__(self, level_num):
        self.level_num = level_num
        self.platforms = []
        self.enemies = []
        self.collectibles = []
        self.boss = None
        
        self.setup_level()
    
    def setup_level(self):
        """Seviyeleri kur"""
        # Zemin her zaman var
        self.platforms.append(Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40, GREEN))
        
        if self.level_num == 1:
            self.setup_level_1()
        elif self.level_num == 2:
            self.setup_level_2()
        elif self.level_num == 3:
            self.setup_level_3()
        elif self.level_num == 4:
            self.setup_level_boss()
    
    def setup_level_1(self):
        """Level 1: Parlak Oda - Kolay"""
        # Platformlar
        self.platforms.extend([
            Platform(150, 500, 200, 20),
            Platform(450, 400, 200, 20),
            Platform(750, 500, 200, 20),
            Platform(100, 300, 150, 20),
            Platform(850, 300, 150, 20),
        ])
        
        # Düşmanlar (3 türü)
        self.enemies.extend([
            Enemy(200, 450, "mosquito", 150, 350),
            Enemy(500, 350, "syringe", 450, 650),
            Enemy(800, 450, "mouse", 750, 950),
        ])
        
        # Ödüller
        self.collectibles.extend([
            Collectible(160, 470, "cookie"),
            Collectible(460, 370, "toy"),
            Collectible(800, 470, "balloon"),
        ])
    
    def setup_level_2(self):
        """Level 2: Gecelik Bahçe - Orta"""
        self.platforms.extend([
            Platform(100, 550, 150, 20),
            Platform(350, 450, 150, 20),
            Platform(600, 350, 150, 20),
            Platform(850, 450, 150, 20),
            Platform(200, 250, 120, 20),
            Platform(900, 200, 150, 20),
        ])
        
        # Düşmanlar (4 türü)
        self.enemies.extend([
            Enemy(150, 500, "mosquito", 100, 250),
            Enemy(400, 400, "ghost", 350, 550),
            Enemy(650, 300, "spider", 600, 750),
            Enemy(900, 400, "alarm", 850, 950),
        ])
        
        # Ödüller
        self.collectibles.extend([
            Collectible(110, 520, "honey"),
            Collectible(360, 420, "angel"),
            Collectible(610, 320, "crystal"),
            Collectible(860, 420, "music"),
        ])
    
    def setup_level_3(self):
        """Level 3: Toy Box Şehri - Zor"""
        self.platforms.extend([
            Platform(0, 600, 120, 20),
            Platform(200, 500, 120, 20),
            Platform(400, 400, 120, 20),
            Platform(600, 500, 120, 20),
            Platform(800, 400, 120, 20),
            Platform(1000, 500, 200, 20),
            Platform(250, 300, 100, 20),
            Platform(750, 250, 100, 20),
        ])
        
        # Düşmanlar (5 türü)
        self.enemies.extend([
            Enemy(50, 550, "mosquito", 0, 120),
            Enemy(250, 450, "syringe", 200, 320),
            Enemy(450, 350, "mouse", 400, 500),
            Enemy(650, 450, "ghost", 600, 720),
            Enemy(850, 350, "spider", 800, 900),
        ])
        
        # Ödüller
        for i, c_type in enumerate(["cookie", "toy", "balloon", "honey", "angel"]):
            x = 150 + i * 180
            y = 400 + (i % 2) * 100
            self.collectibles.append(Collectible(x, y, c_type))
    
    def setup_level_boss(self):
        """Level 4: Boss Level"""
        self.platforms.extend([
            Platform(100, 600, 150, 20),
            Platform(400, 500, 150, 20),
            Platform(700, 600, 150, 20),
            Platform(250, 350, 150, 20),
            Platform(800, 350, 150, 20),
        ])
        
        # Boss
        self.boss = Boss(SCREEN_WIDTH // 2 - 30, 150)
        
        # Düşmanlar (tüm türleri)
        self.enemies.extend([
            Enemy(200, 550, "mosquito", 100, 250),
            Enemy(500, 450, "syringe", 450, 550),
            Enemy(800, 550, "mouse", 750, 850),
            Enemy(300, 300, "ghost", 250, 350),
            Enemy(900, 300, "spider", 800, 950),
            Enemy(150, 400, "alarm", 100, 200),
            Enemy(1050, 400, "nightmare", 1000, 1100),
        ])
        
        # Ödüller
        self.collectibles.extend([
            Collectible(110, 570, "crystal"),
            Collectible(410, 470, "angel"),
            Collectible(710, 570, "music"),
        ])


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Baby - Mistik Platform Oyunu")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.state = GameState.START
        self.current_level = 1
        self.total_score = 0
        self.lives = 3
        self.level_score = 0
        self.combo = 0
        
        self.load_level(1)
    
    def load_level(self, level_num):
        self.current_level = level_num
        self.level_score = 0
        self.combo = 0
        
        level = Level(level_num)
        self.platforms = level.platforms
        self.enemies = level.enemies
        self.collectibles = level.collectibles
        self.boss = level.boss
        
        self.player = Player(50, SCREEN_HEIGHT - 100)
        self.particles = []
        
        self.state = GameState.PLAYING
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                if self.state == GameState.START and event.key == pygame.K_SPACE:
                    self.load_level(1)
                if self.state == GameState.LEVEL_COMPLETE and event.key == pygame.K_SPACE:
                    if self.current_level < 4:
                        self.load_level(self.current_level + 1)
                    else:
                        self.state = GameState.START
                        self.total_score = 0
                        self.lives = 3
                if self.state == GameState.GAME_OVER and event.key == pygame.K_SPACE:
                    self.load_level(self.current_level)
    
    def update(self):
        if self.state != GameState.PLAYING:
            return
        
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
        result = self.player.update(self.platforms, self.enemies, self.collectibles, self.particles)
        
        if result:
            action, points = result
            if action == "collect":
                self.level_score += points
                self.total_score += points
                self.combo += 1
            elif action == "kill":
                self.level_score += points + (self.combo * 5)
                self.total_score += points + (self.combo * 5)
                self.combo += 1
            elif action == "hit":
                self.lives -= 1
                self.combo = 0
                if self.lives <= 0:
                    self.state = GameState.GAME_OVER
                else:
                    self.player.rect.x = 50
                    self.player.rect.y = SCREEN_HEIGHT - 100
            elif action == "fall":
                self.lives -= 1
                self.combo = 0
                if self.lives <= 0:
                    self.state = GameState.GAME_OVER
                else:
                    self.player.rect.x = 50
                    self.player.rect.y = SCREEN_HEIGHT - 100
        
        # Düşmanları güncelle
        for enemy in self.enemies[:]:
            enemy.update()
        
        # Ödülleri güncelle
        for collectible in self.collectibles:
            collectible.update()
        
        # Parçacıkları güncelle
        for particle in self.particles[:]:
            particle.update()
        
        # Boss'u güncelle
        if self.boss:
            self.boss.update()
            if self.player.rect.colliderect(self.boss.rect):
                if self.player.vel_y > 0 and self.player.rect.bottom <= self.boss.rect.top + 20:
                    self.player.rect.bottom = self.boss.rect.top
                    self.player.vel_y = -8
                    self.boss.health -= 1
                    self.level_score += 50
                    self.total_score += 50
                    self.combo += 1
                    if self.boss.health <= 0:
                        self.state = GameState.LEVEL_COMPLETE
                else:
                    self.lives -= 1
                    self.combo = 0
                    if self.lives <= 0:
                        self.state = GameState.GAME_OVER
        
        # Seviye tamamlandı mı?
        if len(self.collectibles) == 0 and not self.boss:
            self.state = GameState.LEVEL_COMPLETE
            self.level_score += 100
            self.total_score += 100
    
    def draw(self):
        self.screen.fill(DARK_BLUE)
        
        if self.state == GameState.START:
            self.draw_start_screen()
        elif self.state == GameState.PLAYING:
            self.draw_playing()
        elif self.state == GameState.LEVEL_COMPLETE:
            self.draw_level_complete()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over()
        
        pygame.display.flip()
    
    def draw_playing(self):
        # Platformlar
        for platform in self.platforms:
            platform.draw(self.screen)
        
        # Düşmanlar
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        # Ödüller
        for collectible in self.collectibles:
            collectible.draw(self.screen)
        
        # Parçacıklar
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Boss
        if self.boss:
            self.boss.draw(self.screen)
        
        # Oyuncu
        self.player.draw(self.screen)
        
        # UI
        self.draw_ui()
    
    def draw_ui(self):
        font_large = pygame.font.Font(None, 36)
        font_small = pygame.font.Font(None, 24)
        
        # Puan
        score_text = font_large.render(f"Puan: {self.level_score}", True, YELLOW)
        self.screen.blit(score_text, (10, 10))
        
        # Hayat
        lives_text = font_large.render(f"Hayat: {self.lives}", True, RED)
        self.screen.blit(lives_text, (10, 50))
        
        # Seviye
        level_text = font_small.render(f"Seviye {self.current_level}", True, WHITE)
        self.screen.blit(level_text, (SCREEN_WIDTH - 200, 10))
        
        # Combo
        if self.combo > 1:
            combo_text = font_large.render(f"Combo: x{self.combo}", True, LIGHT_PURPLE)
            self.screen.blit(combo_text, (SCREEN_WIDTH // 2 - 80, 10))
    
    def draw_start_screen(self):
        font_large = pygame.font.Font(None, 60)
        font_small = pygame.font.Font(None, 36)
        
        title = font_large.render("Baby", True, LIGHT_PURPLE)
        subtitle = font_small.render("Mistik Platform Oyunu", True, YELLOW)
        start_text = font_small.render("SPACE'ye basarak başla", True, WHITE)
        
        self.screen.blit(title, (SCREEN_WIDTH // 2 - 80, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - 150, SCREEN_HEIGHT // 2))
        self.screen.blit(start_text, (SCREEN_WIDTH // 2 - 170, SCREEN_HEIGHT // 2 + 100))
    
    def draw_level_complete(self):
        font_large = pygame.font.Font(None, 60)
        font_small = pygame.font.Font(None, 36)
        
        complete_text = font_large.render("Seviye Tamamlandı!", True, GREEN)
        score_text = font_small.render(f"Puan: {self.level_score}", True, YELLOW)
        next_text = font_small.render("SPACE'ye basarak devam et", True, WHITE)
        
        self.screen.blit(complete_text, (SCREEN_WIDTH // 2 - 250, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - 120, SCREEN_HEIGHT // 2))
        self.screen.blit(next_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 100))
    
    def draw_game_over(self):
        font_large = pygame.font.Font(None, 60)
        font_small = pygame.font.Font(None, 36)
        
        gameover_text = font_large.render("Oyun Bitti!", True, RED)
        score_text = font_small.render(f"Toplam Puan: {self.total_score}", True, YELLOW)
        retry_text = font_small.render("SPACE'ye basarak tekrar dene", True, WHITE)
        
        self.screen.blit(gameover_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2 - 100))
        self.screen.blit(score_text, (SCREEN_WIDTH // 2 - 180, SCREEN_HEIGHT // 2))
        self.screen.blit(retry_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2 + 100))
    
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
