import pygame
import sys
from enum import Enum

# Pygame'i başlat
pygame.init()

# Ekran ayarları
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60

# Renkler
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 100, 255)
GREEN = (0, 255, 0)
GRAY = (100, 100, 100)
YELLOW = (255, 255, 0)

# Fizik
GRAVITY = 0.6
JUMP_POWER = 15
MAX_FALL_SPEED = 20


class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((40, 50))
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Fizik özellikleri
        self.vel_y = 0
        self.vel_x = 0
        self.on_ground = False
        self.max_speed = 5
        self.acceleration = 0.5
        
    def handle_input(self, keys):
        # Yatay hareket
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.vel_x = max(self.vel_x - self.acceleration, -self.max_speed)
        elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.vel_x = min(self.vel_x + self.acceleration, self.max_speed)
        else:
            # Sürtünme
            self.vel_x *= 0.85
        
        # Atlama
        if (keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]) and self.on_ground:
            self.vel_y = -JUMP_POWER
            self.on_ground = False
    
    def update(self, platforms, enemies):
        # Yerçekimi
        self.vel_y = min(self.vel_y + GRAVITY, MAX_FALL_SPEED)
        
        # Hareket
        self.rect.x += self.vel_x
        self.rect.y += self.vel_y
        
        # Ekran sınırları (yanlar)
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        
        # Platform çarpışması
        self.on_ground = False
        for platform in platforms:
            if self.rect.colliderect(platform.rect):
                # Üstten çarpıyor
                if self.vel_y > 0 and self.rect.bottom <= platform.rect.top + 10:
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True
                # Alttan çarpıyor
                elif self.vel_y < 0:
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0
                # Yanlardan çarpıyor
                elif self.vel_x > 0:
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0:
                    self.rect.left = platform.rect.right
        
        # Düşman çarpışması
        for enemy in enemies:
            if self.rect.colliderect(enemy.rect):
                # Üstten vurma
                if self.vel_y > 0 and self.rect.bottom <= enemy.rect.top + 20:
                    self.rect.bottom = enemy.rect.top
                    self.vel_y = -8
                    enemy.kill()
                    return True  # Düşman öldü
                else:
                    # Oyuncu hasar aldı
                    return False
        
        # Ekranın altına düştü
        if self.rect.top > SCREEN_HEIGHT:
            return False
        
        return None
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height, color=GRAY):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y, left_bound, right_bound):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        self.left_bound = left_bound
        self.right_bound = right_bound
        self.speed = 2
        self.direction = 1  # 1 = sağa, -1 = sola
    
    def update(self):
        self.rect.x += self.speed * self.direction
        
        # Sınır kontrolü
        if self.rect.left <= self.left_bound or self.rect.right >= self.right_bound:
            self.direction *= -1
    
    def draw(self, surface):
        surface.blit(self.image, self.rect)
    
    def kill(self):
        self.alive = False


class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Baby - Platform Game")
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.load_level()
    
    def load_level(self):
        # Oyuncu
        self.player = Player(100, SCREEN_HEIGHT - 150)
        
        # Platformlar
        self.platforms = [
            # Zemin
            Platform(0, SCREEN_HEIGHT - 40, SCREEN_WIDTH, 40, GREEN),
            # Platformlar
            Platform(200, 450, 200, 20),
            Platform(500, 350, 200, 20),
            Platform(700, 450, 200, 20),
            Platform(100, 300, 150, 20),
            Platform(750, 250, 150, 20),
        ]
        
        # Düşmanlar
        self.enemies = [
            Enemy(250, 400, 200, 400),
            Enemy(550, 300, 500, 700),
            Enemy(780, 400, 700, 900),
        ]
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
    
    def update(self):
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        
        result = self.player.update(self.platforms, self.enemies)
        
        if result is False:
            print("Oyun Bitti! Düşman vurdu veya düştün!")
            self.load_level()
        
        for enemy in self.enemies:
            enemy.update()
    
    def draw(self):
        self.screen.fill(WHITE)
        
        # Platformlar
        for platform in self.platforms:
            platform.draw(self.screen)
        
        # Düşmanlar
        for enemy in self.enemies:
            enemy.draw(self.screen)
        
        # Oyuncu
        self.player.draw(self.screen)
        
        # FPS göster
        font = pygame.font.Font(None, 36)
        fps_text = font.render(f"FPS: {int(self.clock.get_fps())}", True, BLACK)
        self.screen.blit(fps_text, (10, 10))
        
        pygame.display.flip()
    
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
