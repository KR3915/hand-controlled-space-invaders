import pygame
import random
import cv2
import json
import math
from src.MediPipeHandsModule.HandTrackingModule import hand_detector
from src.MediPipeHandsModule.GestureEvaluator import GestureEvaluator
import collections

# ============================================
# GAME 1: PAC-MAN STYLE MAZE GAME
# ============================================

class Pellet(pygame.sprite.Sprite):
    def __init__(self, x, y, is_power=False):
        super().__init__()
        self.is_power = is_power
        size = 16 if is_power else 6
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 200, 100), (size//2, size//2), size//2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.points = 50 if is_power else 10

class PacPlayer(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.size = 30
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.direction = 0  # 0=right, 1=down, 2=left, 3=up
        self.speed = 4
        self.mouth_open = 0
        self.mouth_direction = 1
        self.draw()
        
    def draw(self):
        self.image.fill((0, 0, 0, 0))
        center = self.size // 2
        # Animate mouth
        mouth_angle = 45 * (self.mouth_open / 10)
        start_angle = math.radians(self.direction * 90 + mouth_angle)
        end_angle = math.radians(self.direction * 90 + 360 - mouth_angle)
        
        points = [(center, center)]
        for angle in [start_angle + i * 0.1 for i in range(int((end_angle - start_angle) / 0.1))]:
            x = center + int(center * math.cos(angle))
            y = center + int(center * math.sin(angle))
            points.append((x, y))
        points.append((center, center))
        
        pygame.draw.polygon(self.image, (255, 255, 0), points)
        
    def update_animation(self):
        self.mouth_open += self.mouth_direction
        if self.mouth_open >= 10 or self.mouth_open <= 0:
            self.mouth_direction *= -1
        self.draw()
        
    def move(self, walls):
        old_x, old_y = self.rect.x, self.rect.y
        
        if self.direction == 0:  # Right
            self.rect.x += self.speed
        elif self.direction == 1:  # Down
            self.rect.y += self.speed
        elif self.direction == 2:  # Left
            self.rect.x -= self.speed
        elif self.direction == 3:  # Up
            self.rect.y -= self.speed
            
        # Check collision with walls
        if pygame.sprite.spritecollide(self, walls, False):
            self.rect.x, self.rect.y = old_x, old_y

class Ghost(pygame.sprite.Sprite):
    def __init__(self, x, y, color):
        super().__init__()
        self.size = 30
        self.color = color
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 2
        self.direction = random.randint(0, 3)
        self.change_direction_timer = 0
        self.draw()
        
    def draw(self):
        self.image.fill((0, 0, 0, 0))
        # Body
        pygame.draw.circle(self.image, self.color, (self.size//2, self.size//2), self.size//2)
        pygame.draw.rect(self.image, self.color, (0, self.size//2, self.size, self.size//2))
        # Wavy bottom
        for i in range(5):
            pygame.draw.circle(self.image, (0, 0, 0), (i * 7, self.size - 1), 4)
        # Eyes
        pygame.draw.circle(self.image, (255, 255, 255), (10, 12), 5)
        pygame.draw.circle(self.image, (255, 255, 255), (20, 12), 5)
        pygame.draw.circle(self.image, (0, 0, 255), (10, 12), 3)
        pygame.draw.circle(self.image, (0, 0, 255), (20, 12), 3)
        
    def update(self, walls):
        self.change_direction_timer += 1
        if self.change_direction_timer > 60:
            self.direction = random.randint(0, 3)
            self.change_direction_timer = 0
            
        old_x, old_y = self.rect.x, self.rect.y
        
        if self.direction == 0:
            self.rect.x += self.speed
        elif self.direction == 1:
            self.rect.y += self.speed
        elif self.direction == 2:
            self.rect.x -= self.speed
        elif self.direction == 3:
            self.rect.y -= self.speed
            
        if pygame.sprite.spritecollide(self, walls, False):
            self.rect.x, self.rect.y = old_x, old_y
            self.direction = random.randint(0, 3)

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.image = pygame.Surface((width, height))
        self.image.fill((0, 0, 255))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class PacManGame:
    def __init__(self, screen, cap, detector, gesture_evaluator):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.cap = cap
        self.detector = detector
        self.gesture_evaluator = gesture_evaluator
        self.recent_gestures = collections.deque(maxlen=5)
        
        self.font = pygame.font.SysFont('courier', 36, bold=True)
        self.title_font = pygame.font.SysFont('courier', 72, bold=True)
        
        self.player = None
        self.ghosts = pygame.sprite.Group()
        self.walls = pygame.sprite.Group()
        self.pellets = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        
        self.score = 0
        self.level = 1
        self.lives = 3
        
        self.setup_maze()
        
    def setup_maze(self):
        self.all_sprites.empty()
        self.walls.empty()
        self.pellets.empty()
        self.ghosts.empty()
        
        # Create maze layout (1=wall, 0=path, 2=pellet, 3=power pellet)
        maze = [
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
            [1,2,2,2,2,2,2,1,1,2,2,2,2,2,2,1],
            [1,3,1,1,2,1,2,1,1,2,1,2,1,1,3,1],
            [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
            [1,2,1,1,2,1,1,1,1,1,1,2,1,1,2,1],
            [1,2,2,2,2,2,2,1,1,2,2,2,2,2,2,1],
            [1,1,1,1,2,1,2,2,2,2,1,2,1,1,1,1],
            [1,2,2,2,2,2,2,1,1,2,2,2,2,2,2,1],
            [1,2,1,1,2,1,1,1,1,1,1,2,1,1,2,1],
            [1,2,2,2,2,2,2,2,2,2,2,2,2,2,2,1],
            [1,3,1,1,2,1,2,1,1,2,1,2,1,1,3,1],
            [1,2,2,2,2,2,2,1,1,2,2,2,2,2,2,1],
            [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
        ]
        
        cell_width = 60
        cell_height = 50
        offset_x = (self.width - len(maze[0]) * cell_width) // 2
        offset_y = 100
        
        for row_idx, row in enumerate(maze):
            for col_idx, cell in enumerate(row):
                x = offset_x + col_idx * cell_width
                y = offset_y + row_idx * cell_height
                
                if cell == 1:
                    wall = Wall(x, y, cell_width, cell_height)
                    self.walls.add(wall)
                    self.all_sprites.add(wall)
                elif cell == 2:
                    pellet = Pellet(x + cell_width//2 - 3, y + cell_height//2 - 3, False)
                    self.pellets.add(pellet)
                    self.all_sprites.add(pellet)
                elif cell == 3:
                    pellet = Pellet(x + cell_width//2 - 8, y + cell_height//2 - 8, True)
                    self.pellets.add(pellet)
                    self.all_sprites.add(pellet)
        
        # Create player
        self.player = PacPlayer(offset_x + cell_width * 8, offset_y + cell_height * 9)
        self.all_sprites.add(self.player)
        
        # Create ghosts
        colors = [(255, 0, 0), (255, 184, 255), (0, 255, 255), (255, 184, 82)]
        for i, color in enumerate(colors):
            ghost = Ghost(offset_x + cell_width * (7 + i % 2), 
                         offset_y + cell_height * (6 + i // 2), color)
            self.ghosts.add(ghost)
            self.all_sprites.add(ghost)
    
    def handle_gestures(self):
        success, img = self.cap.read()
        if success:
            img = cv2.flip(img, 1)
            img = self.detector.find_hands(img)
            lm_list, bbox, _ = self.detector.get_bbox_location(img)
            handedness_list = self.detector.get_handedness()

            if lm_list and handedness_list and bbox:
                gesture = self.gesture_evaluator.evaluate(lm_list, handedness_list[0], bbox)
                self.recent_gestures.append(gesture[0])

            if len(self.recent_gestures) == self.recent_gestures.maxlen:
                most_common = collections.Counter(self.recent_gestures).most_common(1)[0][0]
                
                if most_common == 2:  # Left
                    self.player.direction = 2
                elif most_common == 4:  # Right
                    self.player.direction = 0
                elif most_common == 3:  # Up (assuming gesture 3 is up)
                    self.player.direction = 3
                elif most_common == 5:  # Down (assuming gesture 5 is down)
                    self.player.direction = 1
                    
        return success, img if success else None
    
    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"
            
            success, img = self.handle_gestures()
            
            # Update
            self.player.move(self.walls)
            self.player.update_animation()
            self.ghosts.update(self.walls)
            
            # Check pellet collection
            pellets_hit = pygame.sprite.spritecollide(self.player, self.pellets, True)
            for pellet in pellets_hit:
                self.score += pellet.points
            
            # Check ghost collision
            if pygame.sprite.spritecollide(self.player, self.ghosts, False):
                self.lives -= 1
                if self.lives <= 0:
                    return "menu"
                self.player.rect.x = self.width // 2
                self.player.rect.y = self.height // 2
            
            # Check level complete
            if len(self.pellets) == 0:
                self.level += 1
                self.setup_maze()
            
            # Draw
            self.screen.fill((0, 0, 0))
            self.all_sprites.draw(self.screen)
            
            # Draw HUD
            score_text = self.font.render(f"SCORE: {self.score:05d}", True, (255, 255, 255))
            self.screen.blit(score_text, (20, 20))
            
            lives_text = self.font.render(f"LIVES: {self.lives}", True, (255, 255, 255))
            self.screen.blit(lives_text, (self.width - 200, 20))
            
            # Webcam
            if success and img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_rgb = img_rgb.swapaxes(0, 1)
                frame = pygame.surfarray.make_surface(img_rgb)
                frame = pygame.transform.scale(frame, (240, 180))
                self.screen.blit(frame, (self.width - 260, 60))
            
            pygame.display.flip()
            clock.tick(60)
        
        return "quit"

# ============================================
# GAME 2: BRICK BREAKER / BREAKOUT
# ============================================

class Paddle(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height):
        super().__init__()
        self.screen_width = screen_width
        self.image = pygame.Surface((120, 20))
        self.image.fill((0, 255, 0))
        self.rect = self.image.get_rect()
        self.rect.x = screen_width // 2 - 60
        self.rect.y = screen_height - 50
        self.speed = 12
        
    def move_left(self):
        self.rect.x -= self.speed
        if self.rect.x < 0:
            self.rect.x = 0
            
    def move_right(self):
        self.rect.x += self.speed
        if self.rect.x > self.screen_width - self.rect.width:
            self.rect.x = self.screen_width - self.rect.width

class Ball(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 255, 255), (8, 8), 8)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed_x = random.choice([-5, 5])
        self.speed_y = -6
        self.max_speed = 10
        
    def update(self, screen_width, screen_height):
        self.rect.x += self.speed_x
        self.rect.y += self.speed_y
        
        # Bounce off walls
        if self.rect.left <= 0 or self.rect.right >= screen_width:
            self.speed_x *= -1
        if self.rect.top <= 60:
            self.speed_y *= -1
            
    def bounce(self):
        self.speed_y *= -1

class Brick(pygame.sprite.Sprite):
    def __init__(self, x, y, color, points):
        super().__init__()
        self.image = pygame.Surface((70, 25))
        self.image.fill(color)
        pygame.draw.rect(self.image, (255, 255, 255), self.image.get_rect(), 2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.points = points

class BreakoutGame:
    def __init__(self, screen, cap, detector, gesture_evaluator):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.cap = cap
        self.detector = detector
        self.gesture_evaluator = gesture_evaluator
        self.recent_gestures = collections.deque(maxlen=5)
        
        self.font = pygame.font.SysFont('courier', 36, bold=True)
        
        self.paddle = Paddle(self.width, self.height)
        self.ball = Ball(self.width // 2, self.height // 2)
        self.bricks = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        
        self.score = 0
        self.lives = 3
        self.level = 1
        
        self.create_bricks()
        self.all_sprites.add(self.paddle, self.ball)
        
    def create_bricks(self):
        self.bricks.empty()
        colors = [
            (255, 0, 0),    # Red - 50 points
            (255, 128, 0),  # Orange - 40 points
            (255, 255, 0),  # Yellow - 30 points
            (0, 255, 0),    # Green - 20 points
            (0, 255, 255),  # Cyan - 10 points
        ]
        
        start_x = 80
        start_y = 100
        
        for row in range(5):
            for col in range(12):
                x = start_x + col * 80
                y = start_y + row * 35
                points = 50 - row * 10
                brick = Brick(x, y, colors[row], points)
                self.bricks.add(brick)
                self.all_sprites.add(brick)
    
    def handle_gestures(self):
        success, img = self.cap.read()
        if success:
            img = cv2.flip(img, 1)
            img = self.detector.find_hands(img)
            lm_list, bbox, _ = self.detector.get_bbox_location(img)
            handedness_list = self.detector.get_handedness()

            if lm_list and handedness_list and bbox:
                gesture = self.gesture_evaluator.evaluate(lm_list, handedness_list[0], bbox)
                self.recent_gestures.append(gesture[0])

            if len(self.recent_gestures) == self.recent_gestures.maxlen:
                most_common = collections.Counter(self.recent_gestures).most_common(1)[0][0]
                
                if most_common == 2:  # Left
                    self.paddle.move_left()
                elif most_common == 4:  # Right
                    self.paddle.move_right()
                    
        return success, img if success else None
    
    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"
            
            success, img = self.handle_gestures()
            
            # Update
            self.ball.update(self.width, self.height)
            
            # Ball-paddle collision
            if self.ball.rect.colliderect(self.paddle.rect) and self.ball.speed_y > 0:
                self.ball.bounce()
                # Adjust angle based on hit position
                hit_pos = (self.ball.rect.centerx - self.paddle.rect.left) / self.paddle.rect.width
                self.ball.speed_x = (hit_pos - 0.5) * 12
            
            # Ball-brick collision
            brick_hits = pygame.sprite.spritecollide(self.ball, self.bricks, True)
            if brick_hits:
                self.ball.bounce()
                for brick in brick_hits:
                    self.score += brick.points
            
            # Ball fell off screen
            if self.ball.rect.top > self.height:
                self.lives -= 1
                if self.lives <= 0:
                    return "menu"
                self.ball = Ball(self.width // 2, self.height // 2)
                self.all_sprites.add(self.ball)
            
            # Level complete
            if len(self.bricks) == 0:
                self.level += 1
                self.create_bricks()
                self.ball = Ball(self.width // 2, self.height // 2)
            
            # Draw
            self.screen.fill((0, 0, 0))
            pygame.draw.line(self.screen, (0, 255, 0), (0, 60), (self.width, 60), 2)
            
            self.all_sprites.draw(self.screen)
            
            # HUD
            score_text = self.font.render(f"SCORE: {self.score:05d}", True, (255, 255, 255))
            self.screen.blit(score_text, (20, 20))
            
            lives_text = self.font.render(f"LIVES: {self.lives}", True, (255, 255, 255))
            self.screen.blit(lives_text, (self.width - 200, 20))
            
            level_text = self.font.render(f"LVL: {self.level}", True, (255, 255, 255))
            self.screen.blit(level_text, (self.width // 2 - 50, 20))
            
            # Webcam
            if success and img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_rgb = img_rgb.swapaxes(0, 1)
                frame = pygame.surfarray.make_surface(img_rgb)
                frame = pygame.transform.scale(frame, (240, 180))
                self.screen.blit(frame, (self.width - 260, 80))
            
            pygame.display.flip()
            clock.tick(60)
        
        return "quit"

# ============================================
# GAME 3: FROGGER-STYLE CROSSING GAME
# ============================================

class Frog(pygame.sprite.Sprite):
    def __init__(self, screen_width, screen_height):
        super().__init__()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.size = 40
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.draw_frog()
        self.rect = self.image.get_rect()
        self.start_x = screen_width // 2 - 20
        self.start_y = screen_height - 60
        self.rect.x = self.start_x
        self.rect.y = self.start_y
        self.move_distance = 50
        
    def draw_frog(self):
        self.image.fill((0, 0, 0, 0))
        # Body
        pygame.draw.ellipse(self.image, (0, 200, 0), (5, 10, 30, 25))
        # Eyes
        pygame.draw.circle(self.image, (255, 255, 0), (12, 12), 6)
        pygame.draw.circle(self.image, (255, 255, 0), (28, 12), 6)
        pygame.draw.circle(self.image, (0, 0, 0), (12, 12), 3)
        pygame.draw.circle(self.image, (0, 0, 0), (28, 12), 3)
        # Legs
        pygame.draw.circle(self.image, (0, 180, 0), (5, 30), 8)
        pygame.draw.circle(self.image, (0, 180, 0), (35, 30), 8)
        
    def move_up(self):
        if self.rect.y > 100:
            self.rect.y -= self.move_distance
            
    def move_down(self):
        if self.rect.y < self.screen_height - 60:
            self.rect.y += self.move_distance
            
    def move_left(self):
        if self.rect.x > 0:
            self.rect.x -= self.move_distance
            
    def move_right(self):
        if self.rect.x < self.screen_width - self.size:
            self.rect.x += self.move_distance
            
    def reset(self):
        self.rect.x = self.start_x
        self.rect.y = self.start_y

class Vehicle(pygame.sprite.Sprite):
    def __init__(self, x, y, width, speed, color):
        super().__init__()
        self.image = pygame.Surface((width, 35))
        self.image.fill(color)
        pygame.draw.rect(self.image, (255, 255, 255), self.image.get_rect(), 2)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = speed
        self.screen_width = 0
        
    def update(self, screen_width):
        self.screen_width = screen_width
        self.rect.x += self.speed
        if self.speed > 0 and self.rect.left > screen_width:
            self.rect.right = 0
        elif self.speed < 0 and self.rect.right < 0:
            self.rect.left = screen_width

class GoalZone(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((80, 50))
        self.image.fill((0, 255, 0))
        pygame.draw.rect(self.image, (255, 255, 255), self.image.get_rect(), 3)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.filled = False

class FroggerGame:
    def __init__(self, screen, cap, detector, gesture_evaluator):
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        self.cap = cap
        self.detector = detector
        self.gesture_evaluator = gesture_evaluator
        self.recent_gestures = collections.deque(maxlen=5)
        self.last_gesture = None
        self.gesture_cooldown = 0
        
        self.font = pygame.font.SysFont('courier', 36, bold=True)
        
        self.frog = Frog(self.width, self.height)
        self.vehicles = pygame.sprite.Group()
        self.goals = pygame.sprite.Group()
        self.all_sprites = pygame.sprite.Group()
        
        self.score = 0
        self.lives = 3
        self.level = 1
        
        self.setup_level()
        
    def setup_level(self):
        self.vehicles.empty()
        self.all_sprites.empty()
        self.all_sprites.add(self.frog)
        
        # Create traffic lanes
        lanes = [
            (150, 3, (255, 0, 0), 80),
            (210, -4, (0, 0, 255), 100),
            (270, 5, (255, 255, 0), 70),
            (330, -3, (255, 0, 255), 90),
            (390, 4, (0, 255, 255), 85),
        ]
        
        for y, speed, color, width in lanes:
            for i in range(4):
                x = i * (self.width // 3)
                vehicle = Vehicle(x, y, width, speed, color)
                self.vehicles.add(vehicle)
                self.all_sprites.add(vehicle)
        
        # Create goal zones
        if not self.goals:
            for i in range(5):
                goal = GoalZone(100 + i * 200, 80)
                self.goals.add(goal)
                self.all_sprites.add(goal)
    
    def handle_gestures(self):
        success, img = self.cap.read()
        if success:
            img = cv2.flip(img, 1)
            img = self.detector.find_hands(img)
            lm_list, bbox, _ = self.detector.get_bbox_location(img)
            handedness_list = self.detector.get_handedness()

            if lm_list and handedness_list and bbox:
                gesture = self.gesture_evaluator.evaluate(lm_list, handedness_list[0], bbox)
                self.recent_gestures.append(gesture[0])

            if len(self.recent_gestures) == self.recent_gestures.maxlen and self.gesture_cooldown <= 0:
                most_common = collections.Counter(self.recent_gestures).most_common(1)[0][0]
                
                if most_common != self.last_gesture:
                    if most_common == 2:  # Left
                        self.frog.move_left()
                        self.gesture_cooldown = 15
                    elif most_common == 4:  # Right
                        self.frog.move_right()
                        self.gesture_cooldown = 15
                    elif most_common == 3:  # Up
                        self.frog.move_up()
                        self.gesture_cooldown = 15
                    elif most_common == 5:  # Down
                        self.frog.move_down()
                        self.gesture_cooldown = 15
                    self.last_gesture = most_common
                    
        if self.gesture_cooldown > 0:
            self.gesture_cooldown -= 1
                    
        return success, img if success else None
    
    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "quit"
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return "menu"
            
            success, img = self.handle_gestures()
            
            # Update vehicles
            for vehicle in self.vehicles:
                vehicle.update(self.width)
            
            # Check collision with vehicles
            if pygame.sprite.spritecollide(self.frog, self.vehicles, False):
                self.lives -= 1
                if self.lives <= 0:
                    return "menu"
                self.frog.reset()
            
            # Check if reached goal
            goal_hit = pygame.sprite.spritecollide(self.frog, self.goals, False)
            if goal_hit and not goal_hit[0].filled:
                goal_hit[0].filled = True
                goal_hit[0].image.fill((0, 150, 0))
                self.score += 200
                self.frog.reset()
                
                # Check if all goals filled
                if all(goal.filled for goal in self.goals):
                    self.level += 1
                    for goal in self.goals:
                        goal.filled = False
                        goal.image.fill((0, 255, 0))
                    # Increase difficulty
                    for vehicle in self.vehicles:
                        vehicle.speed *= 1.2
            
            # Draw
            self.screen.fill((0, 0, 0))
            
            # Draw road
            pygame.draw.rect(self.screen, (50, 50, 50), (0, 140, self.width, 310))
            for i in range(5):
                y = 150 + i * 60
                pygame.draw.line(self.screen, (255, 255, 255), (0, y), (self.width, y), 2)
            
            # Draw goal area
            pygame.draw.rect(self.screen, (0, 100, 0), (0, 70, self.width, 60))
            
            self.all_sprites.draw(self.screen)
            
            # Draw frog on top
            self.screen.blit(self.frog.image, self.frog.rect)
            
            # HUD
            pygame.draw.line(self.screen, (0, 255, 0), (0, 60), (self.width, 60), 2)
            
            score_text = self.font.render(f"SCORE: {self.score:05d}", True, (255, 255, 255))
            self.screen.blit(score_text, (20, 20))
            
            lives_text = self.font.render(f"LIVES: {self.lives}", True, (255, 255, 255))
            self.screen.blit(lives_text, (self.width - 200, 20))
            
            level_text = self.font.render(f"LVL: {self.level}", True, (255, 255, 255))
            self.screen.blit(level_text, (self.width // 2 - 50, 20))
            
            # Webcam
            if success and img is not None:
                img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                img_rgb = img_rgb.swapaxes(0, 1)
                frame = pygame.surfarray.make_surface(img_rgb)
                frame = pygame.transform.scale(frame, (240, 180))
                pygame.draw.rect(self.screen, (0, 255, 0), (self.width - 262, 78, 244, 184), 2)
                self.screen.blit(frame, (self.width - 260, 80))
            
            pygame.display.flip()
            clock.tick(60)
        
        return "quit"

# ============================================
# MAIN MENU
# ============================================

class GameMenu:
    def __init__(self):
        pygame.init()
        
        self.info = pygame.display.Info()
        self.width = self.info.current_w
        self.height = self.info.current_h
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.FULLSCREEN)
        pygame.display.set_caption("Retro Gesture Games")
        
        self.title_font = pygame.font.SysFont('courier', 72, bold=True)
        self.menu_font = pygame.font.SysFont('courier', 48, bold=True)
        self.font = pygame.font.SysFont('courier', 36, bold=True)
        
        self.cap = cv2.VideoCapture(0)
        self.detector = hand_detector(max_hands=1, track_con=0.8)
        self.gesture_evaluator = GestureEvaluator("models/gesture_model.pkl")
        
        self.menu_items = [
            "1. PAC-MAN MAZE",
            "2. BRICK BREAKER",
            "3. FROGGER CROSSING",
            "Q. QUIT"
        ]
        self.selected = 0
        
    def draw_menu(self):
        self.screen.fill((0, 0, 0))
        
        # Title with retro effect
        title = "RETRO GAMES"
        title_surf = self.title_font.render(title, True, (0, 255, 0))
        title_rect = title_surf.get_rect(center=(self.width // 2, 150))
        
        # Shadow effect
        shadow_surf = self.title_font.render(title, True, (0, 100, 0))
        self.screen.blit(shadow_surf, (title_rect.x + 4, title_rect.y + 4))
        self.screen.blit(title_surf, title_rect)
        
        # Subtitle
        subtitle = "GESTURE CONTROLLED"
        sub_surf = self.font.render(subtitle, True, (255, 255, 0))
        sub_rect = sub_surf.get_rect(center=(self.width // 2, 220))
        self.screen.blit(sub_surf, sub_rect)
        
        # Menu items
        y_start = 320
        for i, item in enumerate(self.menu_items):
            color = (255, 255, 0) if i == self.selected else (255, 255, 255)
            text_surf = self.menu_font.render(item, True, color)
            text_rect = text_surf.get_rect(center=(self.width // 2, y_start + i * 80))
            
            if i == self.selected:
                # Draw selector
                pygame.draw.rect(self.screen, (0, 255, 0), 
                               (text_rect.x - 20, text_rect.y - 5, 
                                text_rect.width + 40, text_rect.height + 10), 3)
            
            self.screen.blit(text_surf, text_rect)
        
        # Instructions
        instructions = [
            "GESTURE 2 = LEFT",
            "GESTURE 4 = RIGHT", 
            "GESTURE 3 = UP",
            "GESTURE 5 = DOWN",
            "GESTURE 1 = ACTION"
        ]
        
        y_pos = self.height - 250
        inst_title = self.font.render("CONTROLS:", True, (0, 255, 0))
        self.screen.blit(inst_title, (50, y_pos))
        
        for i, inst in enumerate(instructions):
            inst_surf = self.font.render(inst, True, (255, 255, 255))
            self.screen.blit(inst_surf, (50, y_pos + 40 + i * 35))
        
        # Border
        pygame.draw.rect(self.screen, (0, 255, 0), (10, 10, self.width - 20, self.height - 20), 5)
        
        pygame.display.flip()
    
    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        running = False
                    elif event.key == pygame.K_1:
                        result = PacManGame(self.screen, self.cap, self.detector, 
                                          self.gesture_evaluator).run()
                        if result == "quit":
                            running = False
                    elif event.key == pygame.K_2:
                        result = BreakoutGame(self.screen, self.cap, self.detector, 
                                            self.gesture_evaluator).run()
                        if result == "quit":
                            running = False
                    elif event.key == pygame.K_3:
                        result = FroggerGame(self.screen, self.cap, self.detector, 
                                           self.gesture_evaluator).run()
                        if result == "quit":
                            running = False
                    elif event.key == pygame.K_UP:
                        self.selected = (self.selected - 1) % len(self.menu_items)
                    elif event.key == pygame.K_DOWN:
                        self.selected = (self.selected + 1) % len(self.menu_items)
                    elif event.key == pygame.K_RETURN:
                        if self.selected == 0:
                            result = PacManGame(self.screen, self.cap, self.detector, 
                                              self.gesture_evaluator).run()
                            if result == "quit":
                                running = False
                        elif self.selected == 1:
                            result = BreakoutGame(self.screen, self.cap, self.detector, 
                                                self.gesture_evaluator).run()
                            if result == "quit":
                                running = False
                        elif self.selected == 2:
                            result = FroggerGame(self.screen, self.cap, self.detector, 
                                               self.gesture_evaluator).run()
                            if result == "quit":
                                running = False
                        elif self.selected == 3:
                            running = False
            
            self.draw_menu()
            clock.tick(60)
        
        self.cap.release()
        pygame.quit()

if __name__ == "__main__":
    menu = GameMenu()
    menu.run()
