import math
import sys
import pygame
import asyncio
import os
import json
import random

SAVE_KEY = "haven_hopper_save"
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "save.json"     )
WIDTH,HEIGHT=960,540
FPS=60
TILE=40
GRAVITY=0.8
JUMP_SPEED=-15
MOVE_SPEED=5
COYOTE_TIME = 0.12
JUMP_BUFFER_TIME=0.12

LEVELS = [
    [
        "                                                  ",
        "                                                  ",
        "               B                   B              ",
        "                         C C C                    ",
        "                        #######             C     ",
        "             C                             ###   F",
        "           #####               E               ###",
        "   P                 ###########K    C            ",
        "#######    E    ###              ######  ^^  #####",
        "##################################################",
    ],
    [
        "                                                            ",
        "                  B                    C          B         ",
        "                          C C        #####                  ",
        "                         #####                    C        F",
        "             C    E                        E     ###    ####",
        "            ###########          C     #######              ",
        "   P                     ^^    #####   K                    ",
        "######         C      ######                  ^^^   ####    ",
        "######   E   #####                  E    ##########         ",
        "############################   #############################",
    ],
    [
        "                  B                         B                         ", 
        "                                                        C  C  C     F ",
        "                                     C       E         ########   ####",
        "                     C   C          ###   #######                     ",
        "         E        ##########                          ^^              ",
        "     ###########                ^^           C      #####             ",
        "  P                     E     #######K     #####                      ",
        "#####        C      ##########         ^^           E                 ",
        "#####   ^^  ###                     ########   ##########    ^^^      ",
        "######################   ##############################################",
    ],
]

WHITE=(255,255,255)
SKY=(110,180,255)
GROUND=(90,60,40)
GRASS=(70,170,70)
PLAYER_C=(255,200,40)
ENEMY_C=(220,50,60)
COIN_C=(255,230,0)
SPIKE_C=(160,160,170)
FLAG_C=(40,200,120)

def make_sound(freq, ms, volume=0.3):
    try: 
        import array
        rate = 22050
        n= int(rate*ms/1000)
        period = max(1,int(rate/freq))
        amp =int(32767 * volume)
        buf = array.array("h", [amp if (i // (period//2 or 1))%2 else -amp for i in range(n)])
        return pygame.mixer.Sound(buffer=buf)
    except Exception:
        return None

def load_save():
    default = {"high_score": 0, "best_level": 1}
    try:
        if sys.platform == "emscripten":
            import platform
            raw=platform.window.localStorage.getItem(SAVE_KEY)
        else:
         with open(SAVE_FILE) as f:   
            raw = f.read() 
        data = json.loads(raw) if raw else {}
        return{"high_score": data.get("high_score", 0), "best_level": data.get("best_level", 1)}    
    except Exception:
           pass
    return default

def write_save(data):
    try:
        raw = json.dumps(data)
        if sys.platform == "emscripten":
            import platform
            platform.window.localStorage.setItem(SAVE_KEY, raw)
        else:
            with open(SAVE_FILE, "w") as f:
                f.write(raw)
    except Exception:
        pass


class Player(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__()
        self.image= pygame.Surface((30,38)) 
        self.image.fill(PLAYER_C)
        pygame.draw.rect(self.image,(0,0,0),(18,8,6,6))
        self.rect=self.image.get_rect(topleft=(x,y)) 
        self.vel=pygame.Vector2(0,0)
        self.on_ground = False
        self.jumps_left =2
        self.coyote_timer =0.0
        self.jump_buffer =0.0
        self.just_jumped = False
        self.draw_w, self.draw_h = 30.0, 38.0
    def update(self,keys,walls,dt=1/60):
        self.vel.x=0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel.x=-MOVE_SPEED   
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel.x = MOVE_SPEED
        self.vel.y = min(self.vel.y + GRAVITY, 18)
        self.coyote_timer=COYOTE_TIME if self.on_ground else max(0.0, self.coyote_timer-dt)
        self.jump_buffer=max(0.0,self.jump_buffer-dt)
        if self.jump_buffer > 0 and (self.on_ground or self.coyote_timer > 0 or self.jumps_left >0):
            self._perform_jump()

        self.rect.x += self.vel.x
        for w in walls:
            if self.rect.colliderect(w):
                if self.vel.x > 0:
                    self.rect.right = w.left
                elif self.vel.x < 0:
                    self.rect.left=w.right

        self.rect.y += self.vel.y
        was_on_ground = self.on_ground
        self.on_ground = False
        for w in walls:
            if self.rect.colliderect   (w):
                        if self.vel.y>0:
                              self.rect.bottom = w.top
                              self.on_ground =True
                        elif self.vel.y<0:
                             self.rect.top = w.bottom
                        self.vel.y =0
        if self.on_ground and not was_on_ground:
            self.draw_w, self.draw_h = 40.0, 28.0
        self.draw_w += (30 -self.draw_w) * 0.2
        self.draw_h += (38 - self.draw_h) * 0.2             
        if self.rect.left < 0:
             self.rect.left = 0                         

    def _perform_jump(self):
     if self.on_ground or self.coyote_timer > 0:
         self.vel.y = JUMP_SPEED
         self.on_ground = False
         self.coyote_timer =0.0
         self.jumps_left = 1
         self.jump_buffer = 0.0
         self._start_jump()
         return True
     if self.jumps_left > 0:
         self.vel.y = JUMP_SPEED * 0.92
         self.jumps_left -= 1
         self.jump_buffer = 0.0
         self._start_jump()
         return True 
     return False
    def _start_jump(self):
        self.just_jumped= True
        self.draw_w , self.draw_h = 22.0,48.0

    def draw(self, screen, cx):
        w, h = int(self.draw_w), int(self.draw_h)
        img = pygame.transform.scale(self.image,(w,h)) 
        screen.blit(img,img.get_rect(midbottom=(self.rect.centerx - cx, self.rect.bottom)))
           
    def jump (self):
        self.jump_buffer=JUMP_BUFFER_TIME
        return self._perform_jump()





class Enemy(pygame.sprite.Sprite):
    def __init__(self,x,y)    :
        super().__init__()
        self.image = pygame.Surface((34,30))
        self.image.fill(ENEMY_C)
        pygame.draw.rect(self.image, WHITE, (6,6,8,8))
        pygame.draw.rect(self.image, WHITE, (20,6,8,8))
        self.rect = self.image.get_rect(bottomleft=(x,y+TILE))
        self.speed=2
        self.vy=0
    def update(self,walls) :
         self.rect.x += self.speed 
         hit = any(self.rect.colliderect(w) for w in walls)  
         probe = self.rect.move(self.rect.width if self.speed > 0 else -self.rect.width,2)
         ledge = not any(probe.colliderect(w) for w in walls)
         if hit or ledge:
              self.rect.x -=self.speed
              self.speed *=-1
class Flyer(pygame.sprite.Sprite):
    def __init__(self,x,y):
        super().__init__()
        self. image= pygame.Surface((34,24), pygame.SRCALPHA)
        pygame.draw.ellipse(self.image,(120,60,160), (0,4,34,18))
        pygame.draw.rect(self.image, WHITE, (9, 9, 5, 5))
        pygame.draw.rect(self.image, WHITE, (20, 9, 5, 5))
        self.rect = self.image.get_rect(center=(x+TILE //2, y+ TILE//2))
        self.base_y = self.rect.y
        self.t = random.uniform(0, 6.28)
        self.speed = 1.5
        self.start_x = x

    def update(self,walls):
        self.t += 0.05
        self.rect.y = self.base_y + int(math.sin(self.t)* 30)
        self.rect.x += self.speed
        if abs(self.rect.x - self.start_x) > 80:
            self.speed *= -1    
class Coin(pygame.sprite.Sprite):
     def __init__(self,x,y):
          super().__init__()
          self.image =pygame. Surface((20,20), pygame.SRCALPHA) 
          pygame.draw.circle(self.image, COIN_C,(10,10), 9)
          pygame.draw.circle(self.image,(200,160,0),(10,10),9,2)
          self.rect =self.image.get_rect(center=(x+TILE//2, y+TILE//2))

class Particle:
    def __init__(self, x, y, vx, vy, life, color):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = life
        self.color = color

    def update (self):
        self.vy += 0.3
        self.x += self.vx
        self.y += self.vy
        self.life -= 1

    def draw (self, screen, cx):
        size = max(1, self.life // 8 +1)
        pygame.draw.rect(screen, self.color, (int(self.x-cx), int(self.y), size, size))  

class Game:
    def __init__(self):
        pygame.mixer.pre_init(22050, -16, 1, 512)
        pygame.init()
        pygame.display.set_caption("Haven Hopper")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("arial", 28, bold=True)
        self.big = pygame.font.SysFont("arial", 64, bold=True)
        self.snd = {
            "jump": make_sound(520, 90),
            "coin": make_sound(1200, 80),
            "stomp": make_sound(200, 120),
            "hurt": make_sound(110, 300),
            "win": make_sound(880, 300),
        }
        self.state = "menu"
        self.menu_index = 0
        self.score = 0
        self.lives = 3
        self.level_index = 0
        self.walls = []
        self.spikes = []
        self.enemies = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.flag = None
        self.player = None
        self.cam_x = 0
        self.save = load_save()    
        self.new_record = False
        self.particles = []
        self.shake = 0    
    def record_score(self):
        self.new_record = self.score > self.save["high_score"]
        if self.new_record:
            self.save["high_score"] = self.score
        self.save["best_level"] = max(self.save["best_level"], min(self.level_index + 1, len(LEVELS)))
        write_save(self.save)
    def play(self, name):
        s = self.snd.get(name)
        if s:
            s.play()
    def burst(self, x, y, colors, count=15, life=30):
        for _ in range(count):
            self.particles.append(Particle(
                x, y,
                random.uniform(-3,3), random.uniform(-5,1),
                random.randint(life//2, life),
                random.choice(colors)
            ))
    def load_level(self, idx):
        self.particles=[]
        self.walls, self.spikes = [], []
        self.enemies = pygame.sprite.Group()
        self.coins = pygame.sprite.Group()
        self.flag = None
        self.checkpoints=[]
        self.active_checkpoint=None
        rows = LEVELS[idx]
        self.level_w = len(rows[0]) * TILE
        for r, row in enumerate(rows):
            for c, ch in enumerate(row):
                x, y = c * TILE, r * TILE
                if ch == "#":
                    self.walls.append(pygame.Rect(x, y, TILE, TILE))
                elif ch == "P":
                    self.player = Player(x, y)
                    self.spawn = (x, y)
                elif ch == "E":
                    self.enemies.add(Enemy(x, y))
                elif ch == "B":
                    self.enemies.add(Flyer(x, y))
                elif ch == "K":
                    self.checkpoints.append(pygame.Rect(x+15, y, 10, TILE))     
                elif ch == "C":
                    self.coins.add(Coin(x, y))
                elif ch == "^":
                    self.spikes.append(pygame.Rect(x + 4, y + TILE // 2, TILE - 8, TILE // 2))
                elif ch == "F":
                    self.flag = pygame.Rect(x + 15, y - TILE, 10, TILE * 2)
        self.cam_x = 0

    def new_game(self):
        self.score, self.lives, self.level_index = 0, 3, 0
        self.load_level(0)
        self.state = "play"

    def die(self):
        self.play("hurt")
        self.shake = 15
        self.lives -= 1
        if self.lives <= 0:
            self.state = "gameover"
            self.record_score()
        else:
            self.player.rect.topleft = self.spawn
            self.player.vel.update(0,0)
            self.cam_x= max(0, min(self.spawn[0] - WIDTH // 2, self.level_w- WIDTH))

    async def run(self):
        while True:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if e.type == pygame.KEYDOWN:
                    self.on_key(e.key)
            if self.state == "play":
                self.update(dt)
            self.draw()
            pygame.display.flip()
            await asyncio.sleep(0)  # Allow other tasks to run

    def on_key(self, key):
        if self.state == "menu":
            if key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s):
                self.menu_index = 1 - self.menu_index
            elif key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.menu_index == 0:
                    self.new_game()
                else:
                    pygame.quit()
                    sys.exit()
        elif self.state == "play":
            if key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    self.player.jump()
            elif key == pygame.K_ESCAPE:
                self.state = "paused"
        elif self.state == "paused":
            if key == pygame.K_ESCAPE:
                self.state = "play"
            elif key == pygame.K_q:
                self.state = "menu"
        elif self.state in ("gameover", "win"):
            if key == pygame.K_RETURN:
                self.state = "menu"

    def update(self,dt=1/60):
        keys = pygame.key.get_pressed()
        p = self.player
        p.update(keys, self.walls, dt)
        p.rect.right = min(p.rect.right, self.level_w)
        if p.just_jumped:
            self.play("jump")
            p.just_jumped= False
        for pt in self.particles:
            pt.update()
        self.particles = [pt for pt in self.particles if pt.life > 0]        
        if self.shake > 0:
            self.shake -= 1
        for en in self.enemies:
            en.update(self.walls)

        for coin in pygame.sprite.spritecollide(p, self.coins, True):
            self.score += 10
            self.play("coin")
            self.burst(coin.rect.centerx, coin.rect.centery,
                       [COIN_C, WHITE, (255,250,180)], 14, 25)

        for en in pygame.sprite.spritecollide(p, self.enemies, False):
            if p.vel.y > 0 and p.rect.bottom - en.rect.top < 20:
                en.kill()
                self.burst(en.rect.centerx, en.rect.centery,
                           [ENEMY_C, (255,120,90), (140,20,30)], 22, 35)
                p.vel.y = JUMP_SPEED * 0.6
                self.score += 50
                self.play("stomp")
            else:
                self.die()
                return

        if p.rect.top > HEIGHT or any(p.rect.colliderect(s) for s in self.spikes):
            self.die()
            return
        for k in self.checkpoints:
            if k is not self.active_checkpoint and p.rect.colliderect(k):
                self.active_checkpoint = k
                self.spawn = (k.x - 15, k.bottom - p.rect.height)
                self.play("coin")
                self.burst(k.centerx, k.top, [FLAG_C, WHITE], 12, 25)

        if self.flag and p.rect.colliderect(self.flag):
            self.play("win")
            self.score += 100
            self.level_index += 1
            if self.level_index >= len(LEVELS):
                self.state = "win"
                self.record_score()
            else:
                self.load_level(self.level_index)
            return

        target = p.rect.centerx - WIDTH // 2
        self.cam_x += (target - self.cam_x) * 0.1
        self.cam_x = max(0, min(self.cam_x, self.level_w - WIDTH))

    def text(self, msg, font, y, color=WHITE):
        surf = font.render(msg, True, color)
        self.screen.blit(surf, surf.get_rect(center=(WIDTH // 2, y)))

    def draw_world(self):
        self.screen.fill(SKY)
        cx = int(self.cam_x)
        if self.shake > 0:
            cx+= random.randint(-5, 5)
        for i in range(-1, 8):
            hx = i * 300 - (cx // 3) % 300
            pygame.draw.circle(self.screen, (120, 200, 140), (hx, HEIGHT + 60), 200)

        for w in self.walls:
            r = w.move(-cx, 0)
            pygame.draw.rect(self.screen, GROUND, r)
            pygame.draw.rect(self.screen, GRASS, (r.x, r.y, TILE, 8))

        for s in self.spikes:
            r = s.move(-cx, 0)
            pygame.draw.polygon(self.screen, SPIKE_C, [(r.left, r.bottom), (r.centerx, r.top), (r.right, r.bottom)])

        if self.flag:
            f = self.flag.move(-cx, 0)
            pygame.draw.rect(self.screen, WHITE, f)
            pygame.draw.polygon(self.screen, FLAG_C, [(f.right, f.top), (f.right + 35, f.top + 15), (f.right, f.top + 30)])

        for k in self.checkpoints:
            r = k.move(-cx, 0)
            color= FLAG_C if k is self.active_checkpoint else(200, 60, 60)
            pygame.draw.rect(self.screen, WHITE, r)
            pygame.draw.polygon(self.screen, color,
                                [(r.right, r.top), (r.right + 22, r.top + 8), (r.right, r.top + 16)])
          
        for grp in (self.coins, self.enemies):
            for sp in grp:
                self.screen.blit(sp.image, sp.rect.move(-cx, 0))

        for pt in self.particles:
            pt.draw(self.screen, cx)
        self.player.draw(self.screen, cx)    
        hud = self.font.render(f"Score {self.score}   Lives {self.lives}   Level {self.level_index + 1}", True, WHITE)
        self.screen.blit(hud, (16, 12))

    def draw(self):
        if self.state == "menu":
            self.screen.fill((30, 30, 60))
            self.text("HAVEN HOPPER", self.big, 150, COIN_C)
            for i, label in enumerate(["Play", "Quit"]):
                color = COIN_C if i == self.menu_index else WHITE
                self.text(("> " if i == self.menu_index else "") + label, self.font, 280 + i * 50, color)
            self.text("Move: A/D or arrows   Jump: Space/W/Up (double-jump!)", self.font, 450, (180, 180, 200))
            self.text("Esc pauses during play", self.font, 485, (180, 180, 200))            
            self.text(f"High score: {self.save['high_score']}   Best level: {self.save['best_level']}", self.font, 400, COIN_C)
        elif self.state == "play":
            self.draw_world()
        elif self.state == "paused":
            self.draw_world()
            self.text("PAUSED", self.big, HEIGHT // 2 - 30)
            self.text("Esc resume - Q quit to menu", self.font, HEIGHT // 2 + 40)
        elif self.state == "gameover":
            self.screen.fill((40, 0, 0))
            self.text("GAME OVER", self.big, 200, ENEMY_C)
            self.text(f"Score: {self.score}", self.font, 290)
            self.draw_record()
            self.text("Press Enter", self.font, 400)
        elif self.state == "win":
            self.screen.fill((0, 50, 30))
            self.text("YOU WIN!", self.big, 200, FLAG_C)
            self.text(f"Final score: {self.score}", self.font, 290)
            self.draw_record()
            self.text("Press Enter", self.font, 400)

    def draw_record(self):
        if self.new_record:
            self.text("NEW RECORD!", self.font, 340, COIN_C)
        else:
           self.text(f"High score: {self.save['high_score']}   Best level: {self.save['best_level']}", self.font, 340, COIN_C)
if __name__ == "__main__":
    asyncio.run(Game().run())
             