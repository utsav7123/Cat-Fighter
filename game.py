import pygame, sys, random
pygame.init()

# Background Music
try:
    pygame.mixer.music.load("bgm.mp3")
    pygame.mixer.music.set_volume(0.5)  # 0.0 to 1.0 (optional)
    pygame.mixer.music.play(-1)         # -1 means loop forever
except Exception as e:
    print("Couldn't load background music:", e)

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
WIN_W, WIN_H = 900, 500
FPS          = 60
GRAVITY      = 0.8
GROUND_Y     = WIN_H - 60

PLATFORMS = [               # x, y, w, h
    pygame.Rect(0,    GROUND_Y, WIN_W, 20),   # invisible floor
    pygame.Rect(150,  380, 120, 20),
    pygame.Rect(400,  320, 120, 20),
    pygame.Rect(650,  260, 120, 20),
    pygame.Rect(250,  200, 120, 20),
    pygame.Rect(550,  140, 120, 20)
]

FRAME_W, FRAME_H = 16, 16
SCALE   = 3
FRAMES  = 6   # 0 idle, 1 punch, 2 jump, 3 hurt, 4 dead, 5 win

WHITE, BLACK = (255, 255, 255), (0, 0, 0)
GREEN, RED   = (0, 255, 0), (220, 30, 60)

# Add after the CONFIG section
GAME_STATE = "menu"  # "menu", "1player", "2player"
AI_DIFFICULTY = 0.7  # Chance of AI making a decision each frame

# -------------------------------------------------
# WINDOW & ASSETS
# -------------------------------------------------
WIN = pygame.display.set_mode((WIN_W, WIN_H))
pygame.display.set_caption("Cat Fighter")

# For file directly from upload location:
BG_IMG = pygame.image.load("bakground.jpg").convert()
BG_IMG = pygame.transform.scale(BG_IMG, (WIN_W, WIN_H))


SPRITES = [
    pygame.image.load("cat1.png").convert_alpha(),
    pygame.image.load("cat2.png").convert_alpha()
]
# Add this debug code
print(f"Sprite 1 size: {SPRITES[0].get_size()}")
print(f"Sprite 2 size: {SPRITES[1].get_size()}")

try:    # sounds (optional)
    snd_light = pygame.mixer.Sound("punch_light.mp3")
    snd_heavy = pygame.mixer.Sound("punch_heavy.mp3")
    snd_jump  = pygame.mixer.Sound("jump.mp3")
    snd_hit   = pygame.mixer.Sound("hit.mp3")
except:
    snd_light = snd_heavy = snd_jump = snd_hit = None

clock = pygame.time.Clock()
font  = pygame.font.SysFont("consolas", 32)

# -------------------------------------------------
# FIGHTER
# -------------------------------------------------
class Fighter:
    def __init__(self, x, y, sprite_idx, controls, facing):
        self.rect   = pygame.Rect(x, y, 30, 80)
        self.vel_y  = 0
        self.health = 100
        self.sprite = SPRITES[sprite_idx]
        self.controls = controls
        self.facing = facing
        self.on_ground = False
        self.attack_cd = 0
        self.frame = 0
        self.anim_timer = 0
        self.hurt_timer = 0
        self.dead = False
        self.winner = False

    # input -------------------------------------------------
    def handle_input(self, keys, opponent):
        if self.dead or self.winner:
            return
        dx = 0
        if keys[self.controls["left"]]:
            dx = -5
            self.facing = -1
        if keys[self.controls["right"]]:
            dx = 5
            self.facing = 1
        if keys[self.controls["jump"]] and self.on_ground:
            self.vel_y = -15
            self.frame = 2
            self.anim_timer = 15
            if snd_jump: snd_jump.play()
        self.rect.x += dx

        if self.attack_cd <= 0:
            if keys[self.controls["light"]]:
                self.attack(opponent, 10, 50, 8, 15)
            elif keys[self.controls["heavy"]]:
                self.attack(opponent, 25, 40, 15, 35)

    # attack -------------------------------------------------
    def attack(self, opponent, dmg, reach, dur, cd):
        self.frame = 1        # <- show punch frame!
        self.anim_timer = 7   # <- punch lasts a bit (tweak as you wish)
        self.attack_cd = cd
        r = pygame.Rect(
            self.rect.centerx + self.facing * reach//2 - reach//2,
            self.rect.y + 20, reach, 40
        )
        if r.colliderect(opponent.rect) and not opponent.dead:
            opponent.health -= dmg
            opponent.hurt_timer = 18
            opponent.frame = 3
            if snd_hit: snd_hit.play()
            if dmg == 10 and snd_light: snd_light.play()
            elif snd_heavy: snd_heavy.play()
            opponent.rect.x += self.facing * 10

    # physics -------------------------------------------------
    def physics(self):
        if self.dead:
            return
            
        # Apply gravity
        self.vel_y += GRAVITY
        
        # Update vertical position
        self.rect.y += self.vel_y
        self.on_ground = False

        # Check platform collisions with more forgiving detection
        for plat in PLATFORMS:
            # Only check collision when moving downward
            if self.vel_y >= 0:
                # Check if player's feet are at or slightly below platform top
                # and were above the platform in the previous frame
                if (self.rect.bottom >= plat.top and 
                    self.rect.bottom - self.vel_y <= plat.top + 5 and  # More forgiving collision
                    self.rect.right > plat.left and 
                    self.rect.left < plat.right):
                    
                    self.rect.bottom = plat.top  # Snap to platform
                    self.vel_y = 0
                    self.on_ground = True
                    break

        #if self.on_ground:
            #print(f"Player grounded at y={self.rect.bottom}")
        #else:
            #print(f"Player falling at y={self.rect.bottom} with velocity={self.vel_y}")

    # update -------------------------------------------------
    def update(self, keys, opponent):
        if not self.dead:
            if self.attack_cd > 0:
                self.attack_cd -= 1
            if self.hurt_timer > 0:
                self.hurt_timer -= 1
            if self.anim_timer > 0:
                self.anim_timer -= 1
            else:
                if self.hurt_timer == 0 and not self.winner:  # Add winner check
                    self.frame = 0
            self.handle_input(keys, opponent)
            self.physics()
            if self.health <= 0:
                self.health = 0
                self.dead = True
                self.frame = 4

    # draw -------------------------------------------------
    def draw(self, surf):
        frame_id = max(0, min(self.frame, FRAMES-1))
        src = pygame.Rect(frame_id * FRAME_W, 0, FRAME_W, FRAME_H)
        img = self.sprite.subsurface(src)
        img = pygame.transform.scale_by(img, SCALE)
        if self.facing == -1:
            img = pygame.transform.flip(img, True, False)
        surf.blit(img, img.get_rect(midbottom=(self.rect.centerx, self.rect.bottom)))
        # Removed the debug rectangle line:
        # pygame.draw.rect(surf, RED, self.rect, 2)

    # Add to Fighter class
    def ai_control(self, opponent):
        if self.dead or self.winner:
            return
            
        # Check health and update state
        if self.health <= 0:
            self.health = 0
            self.dead = True
            self.frame = 4
            return
            
        # Basic AI logic
        dx = 0
        dist_x = opponent.rect.centerx - self.rect.centerx
        dist_y = opponent.rect.centery - self.rect.centery
        
        # Update animation frame like player
        if self.anim_timer > 0:
            self.anim_timer -= 1
        else:
            if self.hurt_timer == 0 and not self.winner:
                self.frame = 0
    
        # AI decision making with improved intelligence
        if random.random() < AI_DIFFICULTY:
            # Dynamic optimal distance based on health
            optimal_distance = 60 if self.health > 50 else 100
            
            # Defensive behavior when low health
            if self.health < 30:
                optimal_distance = 120  # Stay further away when hurt
                
                # Try to jump to higher platforms to recover
                if self.on_ground and random.random() < 0.3:
                    self.vel_y = -15
                    self.frame = 2
                    self.anim_timer = 15
                    if snd_jump: snd_jump.play()
        
            # Movement logic
            if abs(dist_x) > optimal_distance:
                dx = 5 if dist_x > 0 else -5
                self.facing = 1 if dist_x > 0 else -1
            elif abs(dist_x) < optimal_distance - 30:
                dx = -5 if dist_x > 0 else 5
                self.facing = -1 if dist_x > 0 else 1
                
            # Improved jump logic
            if self.on_ground:
                # Jump if opponent is above
                if dist_y < -40:
                    self.vel_y = -15
                    self.frame = 2
                    self.anim_timer = 15
                    if snd_jump: snd_jump.play()
                # Jump to dodge if opponent is attacking and close
                elif abs(dist_x) < 60 and opponent.frame == 1:
                    self.vel_y = -15
                    self.frame = 2
                    self.anim_timer = 15
                    if snd_jump: snd_jump.play()
        
            # Enhanced attack strategy
            if self.attack_cd <= 0:
                if abs(dist_x) < 80:  # In attack range
                    if self.health > opponent.health:  # Winning - be aggressive
                        if abs(dist_x) < 50:
                            # Close range - prefer heavy attacks
                            if random.random() < 0.7:
                                self.attack(opponent, 25, 40, 15, 35)  # Heavy attack
                            else:
                                # Medium range - mix attacks
                                if random.random() < 0.6:
                                    self.attack(opponent, 10, 50, 8, 15)
                                else:
                                    self.attack(opponent, 25, 40, 15, 35)
                    else:  # Losing - be more tactical
                        # Counter-attack when opponent is vulnerable
                        if opponent.attack_cd > 0:
                            if random.random() < 0.8:
                                self.attack(opponent, 25, 40, 15, 35)
                        elif random.random() < 0.4:
                            self.attack(opponent, 10, 50, 8, 15)
    
        # Apply movement
        self.rect.x += dx
        
        # Update timers
        if self.attack_cd > 0:
            self.attack_cd -= 1
        if self.hurt_timer > 0:
            self.hurt_timer -= 1

# -------------------------------------------------
# UTILS
# -------------------------------------------------
def health_bar(surf, x, y, pct):
    pct = max(min(pct, 100), 0)
    pygame.draw.rect(surf, BLACK, (x-2, y-2, 204, 24))
    pygame.draw.rect(surf, RED,   (x, y, 200, 20))
    pygame.draw.rect(surf, GREEN, (x, y, 200 * pct / 100, 20))

def reset():
    # Spawn players exactly at ground level
    p1 = Fighter(150, GROUND_Y - 80, 0,  # subtract exact height
                 {"left": pygame.K_a, "right": pygame.K_d,
                  "jump": pygame.K_w, "light": pygame.K_r, "heavy": pygame.K_t}, 1)
    p2 = Fighter(WIN_W - 180, GROUND_Y - 80, 1,
                 {"left": pygame.K_LEFT, "right": pygame.K_RIGHT,
                  "jump": pygame.K_UP, "light": pygame.K_KP1, "heavy": pygame.K_KP2}, -1)
    return p1, p2  # Make sure to return both players

# Add to UTILS section
def draw_menu(surf):
    title = font.render("Cat Fighter", True, BLACK)
    option1 = font.render("Press 1 for Single Player", True, BLACK)
    option2 = font.render("Press 2 for Two Players", True, BLACK)
    
    surf.blit(title, title.get_rect(center=(WIN_W//2, WIN_H//3)))
    surf.blit(option1, option1.get_rect(center=(WIN_W//2, WIN_H//2)))
    surf.blit(option2, option2.get_rect(center=(WIN_W//2, WIN_H//2 + 50)))

p1, p2 = reset()

# Replace the main game loop
while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            pygame.quit(); sys.exit()
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_F1:
                p1, p2 = reset()
                GAME_STATE = "menu"
            elif GAME_STATE == "menu":
                if e.key == pygame.K_1:
                    GAME_STATE = "1player"
                    p1, p2 = reset()
                elif e.key == pygame.K_2:
                    GAME_STATE = "2player"
                    p1, p2 = reset()

    # Draw background
    WIN.blit(BG_IMG, (0, 0))

    if GAME_STATE == "menu":
        draw_menu(WIN)
    else:
        keys = pygame.key.get_pressed()
        p1.update(keys, p2)
        
        if GAME_STATE == "2player":
            p2.update(keys, p1)
        else:  # 1player mode
            p2.ai_control(p1)
            p2.physics()  # Make sure physics still applies to AI

        # winner
        if p1.dead and not p2.winner:
            p2.winner = True
            p2.frame = 5  # This is correct
            if p2.anim_timer <= 0:  # Add this to keep the frame
                p2.anim_timer = 30  # Reset timer to keep winner frame visible
        if p2.dead and not p1.winner:
            p1.winner = True
            p1.frame = 5  # This is correct
            if p1.anim_timer <= 0:  # Add this to keep the frame
                p1.anim_timer = 30  # Reset timer to keep winner frame visible

        # --- DRAW EVERYTHING ---
        # black floor
        pygame.draw.rect(WIN, BLACK, (0, GROUND_Y, WIN_W, WIN_H - GROUND_Y))
        # platforms
        for plat in PLATFORMS:  # Draw ALL platforms
            pygame.draw.rect(WIN, BLACK, plat)
        # Add after drawing platforms but before drawing players
        # Debug: Draw ground line
        pygame.draw.line(WIN, RED, (0, GROUND_Y), (WIN_W, GROUND_Y), 2)
        
        p1.draw(WIN)
        p2.draw(WIN)
        # Debug position logs - commented out
        #print(f"P1: y={p1.rect.bottom} ground={GROUND_Y}")
        #print(f"P2: y={p2.rect.bottom} ground={GROUND_Y}")
        health_bar(WIN, 20, 20, p1.health)
        health_bar(WIN, WIN_W-220, 20, p2.health)

        if p1.winner or p2.winner:
            w = "Player 1" if p1.winner else "Player 2"
            txt = font.render(f"{w} wins!  F1 = restart", True, BLACK)
            WIN.blit(txt, txt.get_rect(center=(WIN_W//2, WIN_H//2)))

    # keep cats inside screen
    for f in (p1, p2):
        f.rect.x = max(0, min(f.rect.x, WIN_W - f.rect.width))

    pygame.display.flip()
    clock.tick(FPS)  # Make sure this line is present