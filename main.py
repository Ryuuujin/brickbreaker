import pygame
import mysql.connector
import random

# Initialize Pygame and mixer
pygame.init()
pygame.mixer.init()

# Screen dimensions
SCREEN_WIDTH = 850
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# Paddle settings
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 10
PADDLE_SPEED = 10

# Ball settings
BALL_RADIUS = 10
BALL_SPEED = 5

# Brick settings
BRICK_WIDTH = 75
BRICK_HEIGHT = 20
BRICK_PADDING = 10
BRICK_OFFSET_TOP = 100

# Levels
LEVELS = [
    {
        'description': 'Level 1: Easy start',
        'layout': [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ],
    },
    {
        'description': 'Level 2: Alternating pattern',
        'layout': [
            [1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
            [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
            [1, 0, 1, 0, 1, 0, 1, 0, 1, 0],
        ],
    },
    {
        'description': 'Level 3: Central gap',
        'layout': [
            [1, 1, 1, 1, 0, 0, 1, 1, 1, 1],
            [1, 1, 0, 0, 1, 1, 0, 0, 1, 1],
            [0, 0, 1, 1, 0, 0, 1, 1, 0, 0],
        ],
    },
]

# Load images
paddle_img = pygame.image.load('assets/img/paddle.png')  # Load your paddle image
ball_img = pygame.image.load('assets/img/ball.png')  # Load your ball image
brick_img = pygame.image.load('assets/img/brick.png')  # Load your brick image

# Scale images to appropriate sizes
paddle_img = pygame.transform.scale(paddle_img, (PADDLE_WIDTH, PADDLE_HEIGHT))
ball_img = pygame.transform.scale(ball_img, (BALL_RADIUS * 2, BALL_RADIUS * 2))
brick_img = pygame.transform.scale(brick_img, (BRICK_WIDTH, BRICK_HEIGHT))

# Load sound effects and background music
brick_hit_sound = pygame.mixer.Sound('assets/wav/brick_hit.wav')  # Load your brick hit sound
background_music = 'assets/wav/background_music.mp3'  # Load your background music
win_sound = pygame.mixer.Sound('assets/wav/win_sound.wav')  # Load your win sound

# Set volume for win sound
win_sound.set_volume(1.0)  # Set volume to the maximum (1.0)

# Play background music
pygame.mixer.music.load(background_music)
pygame.mixer.music.play(-1)  # -1 means the music will loop indefinitely

# Create the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Brick Breaker")

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Database connection
db_connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="brickbreaker_user"
)

# Score tracking
current_score = 0
previous_score = 0
high_score = 0
current_player_name = ""
lives = 3  # Add lives variable

# Load high score
def load_high_score():
    global high_score
    cursor = db_connection.cursor()
    cursor.execute("SELECT MAX(score) FROM scores")
    result = cursor.fetchone()
    if result[0] is not None:
        high_score = result[0]
    cursor.close()

# Save high score
def save_high_score(score):
    cursor = db_connection.cursor()
    cursor.execute("INSERT INTO scores (player_name, score) VALUES (%s, %s)", (current_player_name, score))
    db_connection.commit()
    cursor.close()

# Load player name
def load_player_name():
    global current_player_name
    try:
        with open("playername.txt", "r") as file:
            current_player_name = file.read().strip()
    except FileNotFoundError:
        current_player_name = ""

# Save player name
def save_player_name(name):
    global current_player_name
    current_player_name = name
    with open("playername.txt", "w") as file:
        file.write(name)

class Paddle:
    def __init__(self):
        self.rect = pygame.Rect(SCREEN_WIDTH // 2 - PADDLE_WIDTH // 2, SCREEN_HEIGHT - 30, PADDLE_WIDTH, PADDLE_HEIGHT)

    def move(self, dx):
        self.rect.x += dx
        if self.rect.x < 0:
            self.rect.x = 0
        elif self.rect.x > SCREEN_WIDTH - PADDLE_WIDTH:
            self.rect.x = SCREEN_WIDTH - PADDLE_WIDTH

    def draw(self, screen):
        screen.blit(paddle_img, self.rect.topleft)

class Ball:
    def __init__(self):
        self.rect = pygame.Rect(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, BALL_RADIUS * 2, BALL_RADIUS * 2)
        self.dx = BALL_SPEED * random.choice([-1, 1])
        self.dy = -BALL_SPEED
        self.angular_velocity = 0  # Angular velocity for spin effect

    def move(self):
        self.rect.x += self.dx
        self.rect.y += self.dy
        self.rect.x += self.angular_velocity  # Apply spin effect to horizontal movement

        if self.rect.left <= 0 or self.rect.right >= SCREEN_WIDTH:
            self.dx = -self.dx

        if self.rect.top <= 0:
            self.dy = -self.dy

    def draw(self, screen):
        screen.blit(ball_img, self.rect.topleft)

    def reset(self):
        self.rect.x = SCREEN_WIDTH // 2
        self.rect.y = SCREEN_HEIGHT // 2
        self.dx = BALL_SPEED * random.choice([-1, 1])
        self.dy = -BALL_SPEED
        self.angular_velocity = 0  # Reset angular velocity

class Brick:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)

    def draw(self, screen):
        screen.blit(brick_img, self.rect.topleft)

def create_level(level):
    bricks = []
    for row_idx, row in enumerate(level['layout']):
        for col_idx, brick in enumerate(row):
            if brick:
                x = col_idx * (BRICK_WIDTH + BRICK_PADDING) + BRICK_PADDING // 2
                y = row_idx * (BRICK_HEIGHT + BRICK_PADDING) + BRICK_OFFSET_TOP
                bricks.append(Brick(x, y))
    return bricks

def main_menu():
    global current_player_name

    menu = True
    while menu:
        screen.fill(BLACK)
        font = pygame.font.Font(None, 50)
        title_text = font.render("Brick Breaker", True, WHITE)
        start_text = font.render("Press Enter to Start", True, WHITE)
        enter_name_text = font.render("Enter Your Name:", True, WHITE)
        quit_text = font.render("Press Q to Quit", True, WHITE)

        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, SCREEN_HEIGHT // 3))
        screen.blit(start_text, (SCREEN_WIDTH // 2 - start_text.get_width() // 2, SCREEN_HEIGHT // 2))
        screen.blit(enter_name_text, (SCREEN_WIDTH // 2 - enter_name_text.get_width() // 2, SCREEN_HEIGHT // 2 + 50))

        # Render player name input
        font_input = pygame.font.Font(None, 36)
        player_input_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 100, 200, 36)
        pygame.draw.rect(screen, WHITE, player_input_rect, 1)
        player_name_text = font_input.render(current_player_name, True, WHITE)
        screen.blit(player_name_text, (player_input_rect.x + 5, player_input_rect.y + 5))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN and current_player_name:
                    menu = False
                if event.key == pygame.K_q:
                    pygame.quit()
                    exit()
                if event.key == pygame.K_BACKSPACE:
                    current_player_name = current_player_name[:-1]
                else:
                    current_player_name += event.unicode

def you_win():
    global current_score, previous_score, high_score

    pygame.mixer.Sound.play(win_sound)  # Play win sound effect

    win = True
    while win:
        screen.fill(BLACK)
        font = pygame.font.Font(None, 74)
        win_text = font.render("YOU WIN!", True, WHITE)
        retry_text = font.render("Press Enter to Retry", True, WHITE)
        quit_text = font.render("Press Q to Quit", True, WHITE)

        screen.blit(win_text, (SCREEN_WIDTH // 2 - win_text.get_width() // 2, SCREEN_HEIGHT // 3))
        screen.blit(retry_text, (SCREEN_WIDTH // 2 - retry_text.get_width() // 2, SCREEN_HEIGHT // 2))
        screen.blit(quit_text, (SCREEN_WIDTH // 2 - quit_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    win = False
                if event.key == pygame.K_q:
                    pygame.quit()
                    exit()

def game_over():
    global current_score, previous_score, high_score, lives

    if current_score > high_score:
        save_high_score(current_score)
        high_score = current_score

    over = True
    while over:
        screen.fill(BLACK)
        font = pygame.font.Font(None, 74)
        over_text = font.render("GAME OVER", True, WHITE)
        retry_text = font.render("Press Enter to Retry", True, WHITE)
        quit_text = font.render("Press Q to Quit", True, WHITE)

        screen.blit(over_text, (SCREEN_WIDTH // 2 - over_text.get_width() // 2, SCREEN_HEIGHT // 3))
        screen.blit(retry_text, (SCREEN_WIDTH // 2 - retry_text.get_width() // 2, SCREEN_HEIGHT // 2))
        screen.blit(quit_text, (SCREEN_WIDTH // 2 - quit_text.get_width() // 2, SCREEN_HEIGHT // 2 + 100))

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    over = False
                    lives = 3  # Reset lives
                if event.key == pygame.K_q:
                    pygame.quit()
                    exit()

def main():
    global current_score, previous_score, high_score, current_level, lives

    load_high_score()
    load_player_name()

    main_menu()

    current_level = 0
    bricks = create_level(LEVELS[current_level])

    paddle = Paddle()
    ball = Ball()

    running = True
    while running:
        screen.fill(BLACK)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            paddle.move(-PADDLE_SPEED)
        if keys[pygame.K_RIGHT]:
            paddle.move(PADDLE_SPEED)

        ball.move()

        # Ball collision with paddle
        if ball.rect.colliderect(paddle.rect):
            ball.dy = -ball.dy

        # Ball collision with bricks
        for brick in bricks[:]:
            if ball.rect.colliderect(brick.rect):
                pygame.mixer.Sound.play(brick_hit_sound)
                ball.dy = -ball.dy
                bricks.remove(brick)
                current_score += 10

        # Ball falls below the paddle
        if ball.rect.top > SCREEN_HEIGHT:
            lives -= 1
            if lives > 0:
                ball.reset()
            else:
                game_over()
                main_menu()
                current_level = 0
                bricks = create_level(LEVELS[current_level])
                current_score = 0
                paddle = Paddle()
                ball = Ball()
                lives = 3

        # Check if level is completed
        if not bricks:
            current_level += 1
            if current_level >= len(LEVELS):
                you_win()
                main_menu()
                current_level = 0
                current_score = 0
            bricks = create_level(LEVELS[current_level])

        paddle.draw(screen)
        ball.draw(screen)

        for brick in bricks:
            brick.draw(screen)

        # Display score and lives
        font = pygame.font.Font(None, 36)
        score_text = font.render(f"Score: {current_score}", True, WHITE)
        lives_text = font.render(f"Lives: {lives}", True, WHITE)
        level_text = font.render(LEVELS[current_level]['description'], True, WHITE)
        high_score_text = font.render(f"High Score: {high_score}", True, WHITE)

        screen.blit(score_text, (20, 20))
        screen.blit(lives_text, (20, 60))
        screen.blit(level_text, (SCREEN_WIDTH // 2 - level_text.get_width() // 2, 20))
        screen.blit(high_score_text, (SCREEN_WIDTH - high_score_text.get_width() - 20, 20))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
