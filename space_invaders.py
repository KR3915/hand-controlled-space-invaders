import pygame
import random
import cv2
from src.MediPipeHandsModule.HandTrackingModule import hand_detector
from src.MediPipeHandsModule.GestureEvaluator import GestureEvaluator
import collections

# --- Game Object Classes ---

class Player(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height):
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.image = pygame.image.load("assets/player.png").convert_alpha()
        self.image = pygame.transform.scale(self.image, (50, 50))
        self.rect = self.image.get_rect()
        self.rect.x = (self.screen_width - self.rect.width) // 2
        self.rect.y = self.screen_height - self.rect.height - 10
        self.speed = 10
        self.bullet_cooldown = 500
        self.last_shot_time = 0

    def move_left(self):
        self.rect.x -= self.speed
        if self.rect.x < 0:
            self.rect.x = 0

    def move_right(self):
        self.rect.x += self.speed
        if self.rect.x > self.screen_width - self.rect.width:
            self.rect.x = self.screen_width - self.rect.width

    def shoot(self, all_sprites, bullets):
        now = pygame.time.get_ticks()
        if now - self.last_shot_time > self.bullet_cooldown:
            self.last_shot_time = now
            bullet = Bullet(self.rect.centerx, self.rect.top)
            all_sprites.add(bullet)
            bullets.add(bullet)



class Alien(pygame.sprite.Sprite):
    def __init__(self, x, y, alien_type, points):
        super().__init__()
        self.type = alien_type
        self.points = points
        if self.type == "red":
            self.color = (255, 0, 0)
        elif self.type == "yellow":
            self.color = (255, 255, 0)
        else:
            self.color = (0, 255, 0)
        image_path = f"assets/{alien_type}.png"
        self.image = pygame.image.load(image_path).convert_alpha()
        self.image = pygame.transform.scale(self.image, (40, 30))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

    def update(self):
        pass


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([5, 15])
        self.image.fill((255, 255, 255))  # White
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = -10

    def update(self):
        self.rect.y += self.speed
        if self.rect.y < 0:
            self.kill()

class AlienBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, screen_height, color):
        super().__init__()
        self.screen_height = screen_height
        self.image = pygame.Surface([5, 15])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 10

    def update(self):
        self.rect.y += self.speed
        if self.rect.y > self.screen_height:
            self.kill()

# --- Game Class ---

class Game:
    def __init__(self):
        pygame.init()

        self.infoObject = pygame.display.Info()
        self.SCREEN_WIDTH = self.infoObject.current_w
        self.SCREEN_HEIGHT = self.infoObject.current_h
        self.SCREEN = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Space Invaders")

        self.BLACK = (0, 0, 0)
        self.WHITE = (255, 255, 255)

        self.FONT = pygame.font.SysFont(None, 50)

        self.cap = cv2.VideoCapture(0)
        self.detector = hand_detector(max_hands=1, track_con=0.8)
        self.gesture_evaluator = GestureEvaluator("models/gesture_model.pkl")
        self.recent_gestures = collections.deque(maxlen=5)

        self.player = Player(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.all_sprites = pygame.sprite.Group()
        self.all_sprites.add(self.player)

        self.aliens = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.alien_bullets = pygame.sprite.Group()

        self.alien_direction = 1  # 1 for right, -1 for left
        self.alien_speed = 2
        self.alien_move_down_amount = 10
        self.score = 0

        self.alien_shoot_cooldown = 250
        self.last_alien_shot_time = 0

        self.clock = pygame.time.Clock()

    def create_aliens(self):
        for row in range(5):
            for col in range(10):
                if row == 0:
                    alien_type = "red"
                    points = 30
                elif row in [1, 2]:
                    alien_type = "yellow"
                    points = 20
                else:
                    alien_type = "green"
                    points = 10
                alien = Alien(col * 60 + 50, row * 50 + 50, alien_type, points)
                self.all_sprites.add(alien)
                self.aliens.add(alien)

    def message(self, msg, color):
        mesg = self.FONT.render(msg, True, color)
        self.SCREEN.blit(mesg, [self.SCREEN_WIDTH / 2 - mesg.get_width() / 2, self.SCREEN_HEIGHT / 2 - mesg.get_height() / 2])

    def draw_score(self):
        score_mesg = self.FONT.render(f"Score: {self.score}", True, self.WHITE)
        self.SCREEN.blit(score_mesg, [10, 10])

    def reset_game(self):
        self.all_sprites.empty()
        self.aliens.empty()
        self.bullets.empty()
        self.alien_bullets.empty()

        self.score = 0
        self.player = Player(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.all_sprites.add(self.player)
        self.create_aliens()
    def run(self):
        game_over = False
        game_close = False
        self.create_aliens()

        while not game_over:
            while game_close:
                self.SCREEN.fill(self.BLACK)
                self.message("You Lost! Press Q-Quit or C-Play Again", self.WHITE)
                pygame.display.update()

                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_q:
                            game_over = True
                            game_close = False
                        if event.key == pygame.K_c:
                            self.reset_game()
                            game_close = False

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game_over = True
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game_over = True

            # --- Gesture Recognition ---
            success, img = self.cap.read()
            if success:
                img = cv2.flip(img, 1)
                img = self.detector.find_hands(img)
                lm_list, bbox, _ = self.detector.get_bbox_location(img)
                handedness_list = self.detector.get_handedness()

                if lm_list and handedness_list:
                    if bbox:
                        gesture = self.gesture_evaluator.evaluate(lm_list, handedness_list[0], bbox)
                        self.recent_gestures.append(gesture[0])

                if len(self.recent_gestures) == self.recent_gestures.maxlen:
                    most_common_gesture = collections.Counter(self.recent_gestures).most_common(1)[0][0]

                    if most_common_gesture == 2:  # Left
                        self.player.move_left()
                    elif most_common_gesture == 4:  # Right
                        self.player.move_right()
                    elif most_common_gesture == 1:  # Shoot
                        self.player.shoot(self.all_sprites, self.bullets)


            # --- Game Logic ---
            self.all_sprites.update()

            # Alien movement
            move_down = False
            for alien in self.aliens:
                alien.rect.x += self.alien_speed * self.alien_direction
                if alien.rect.right > self.SCREEN_WIDTH or alien.rect.left < 0:
                    move_down = True

            if move_down:
                self.alien_direction *= -1
                for alien in self.aliens:
                    alien.rect.y += self.alien_move_down_amount

            # Collision detection
            bullet_alien_collisions = pygame.sprite.groupcollide(self.bullets, self.aliens, True, True)
            for bullet, aliens_hit in bullet_alien_collisions.items():
                for alien in aliens_hit:
                    self.score += alien.points

            player_alien_collisions = pygame.sprite.spritecollide(self.player, self.aliens, False)
            if player_alien_collisions:
                game_close = True

            for alien in self.aliens:
                if alien.rect.bottom >= self.player.rect.top:
                    game_close = True
                    break
            
            if not self.aliens:
                self.message("You Win! Press Q-Quit or C-Play Again", self.WHITE)
                pygame.display.update()
                pygame.time.wait(2000)
                game_close = True

            # Alien shooting
            now = pygame.time.get_ticks()
            if now - self.last_alien_shot_time > self.alien_shoot_cooldown and self.aliens:
                self.last_alien_shot_time = now
                random_alien = random.choice(self.aliens.sprites())
                alien_bullet = AlienBullet(random_alien.rect.centerx, random_alien.rect.bottom, self.SCREEN_HEIGHT, random_alien.color)
                self.all_sprites.add(alien_bullet)
                self.alien_bullets.add(alien_bullet)

            # Player-alien bullet collision
            player_hit = pygame.sprite.spritecollide(self.player, self.alien_bullets, True)
            if player_hit:
                game_close = True

            # --- Drawing ---
            self.SCREEN.fill(self.BLACK)
            self.all_sprites.draw(self.SCREEN)
            self.draw_score()

            # Display webcam feed
            if success:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_rgb = img_rgb.swapaxes(0, 1)
                frame = pygame.surfarray.make_surface(img_rgb)
                frame = pygame.transform.scale(frame, (400, 300))
                self.SCREEN.blit(frame, (self.SCREEN_WIDTH - 400, 0))


            pygame.display.update()
            self.clock.tick(60)

        self.cap.release()
        pygame.quit()
        quit()

if __name__ == "__main__":
    game = Game()
    game.run()
