"""
Crystal Caverns (Кристальные Пещеры) — 2D-платформер на Python Arcade.
Все модули объединены в один файл.

Запуск: python main.py
"""

import os
import csv
import math
import random
import struct
import wave
import arcade
from PIL import Image, ImageDraw

# ============================================================
#  КОНСТАНТЫ И НАСТРОЙКИ
# ============================================================

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
SCREEN_TITLE = "Кристальные Пещеры"

TILE_SIZE = 64
GRAVITY = 1.0
PLAYER_MOVE_SPEED = 5
PLAYER_JUMP_SPEED = 18
PLAYER_MAX_HEALTH = 3
PLAYER_SCALE = 1.0
ENEMY_SCALE = 1.0
ENEMY_SPEED = 2
ENEMY_PATROL_DISTANCE = 150

COLOR_SKY = (30, 30, 60)
COLOR_HUD_BG = (0, 0, 0, 150)
COLOR_CRYSTAL_YELLOW = (255, 215, 0)
COLOR_CRYSTAL_BLUE = (0, 180, 255)
COLOR_CRYSTAL_GREEN = (0, 255, 120)
COLOR_CRYSTAL_RED = (255, 60, 80)
COLOR_PLAYER = (80, 180, 255)
COLOR_PLAYER_DARK = (40, 100, 180)
COLOR_ENEMY_GREEN = (80, 200, 80)
COLOR_ENEMY_DARK = (40, 120, 40)
COLOR_WALL = (100, 80, 60)
COLOR_WALL_LIGHT = (140, 110, 80)
COLOR_PORTAL = (180, 80, 255)
COLOR_HEART = (255, 50, 70)
COLOR_LAVA = (255, 80, 20)
COLOR_TITLE = (255, 215, 0)
COLOR_TEXT = (220, 220, 240)
COLOR_TEXT_DIM = (150, 150, 170)
COLOR_BG_DARK = (20, 15, 35)
COLOR_BG_CAVE = (35, 25, 50)

PARTICLE_LIFETIME = 0.8
PARTICLE_COUNT_CRYSTAL = 15
PARTICLE_COUNT_ENEMY = 20
PARTICLE_SPEED = 3.0

CRYSTAL_SCORE = 100
ENEMY_KILL_SCORE = 250
LEVEL_COMPLETE_BONUS = 500

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(BASE_DIR, "assets", "sounds")
HIGH_SCORES_FILE = os.path.join(BASE_DIR, "high_scores.csv")

TOTAL_LEVELS = 3
INVINCIBLE_DURATION = 60
INVINCIBLE_BLINK_RATE = 5


# ============================================================
#  ХРАНЕНИЕ ДАННЫХ (CSV)
# ============================================================

def save_score(player_name: str, score: int, level_reached: int) -> None:
    """Сохранить результат игрока в CSV-файл."""
    file_exists = os.path.exists(HIGH_SCORES_FILE)
    with open(HIGH_SCORES_FILE, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["Имя", "Очки", "Уровень"])
        writer.writerow([player_name, score, level_reached])


def load_high_scores(limit: int = 5) -> list:
    """Загрузить таблицу рекордов из CSV."""
    if not os.path.exists(HIGH_SCORES_FILE):
        return []
    scores = []
    with open(HIGH_SCORES_FILE, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f, fieldnames=["Имя", "Очки", "Уровень"])
        next(reader, None)
        for row in reader:
            try:
                scores.append({
                    "name": row["Имя"],
                    "score": int(row["Очки"]),
                    "level": int(row["Уровень"]),
                })
            except (ValueError, KeyError):
                continue
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:limit]


# ============================================================
#  ГЕНЕРАТОР ЗВУКОВ
# ============================================================

def _generate_tone(filename, frequency, duration, volume=0.5, sample_rate=22050):
    """Сгенерировать простой тон и сохранить как WAV."""
    filepath = os.path.join(SOUNDS_DIR, filename)
    if os.path.exists(filepath):
        return filepath
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    n_samples = int(sample_rate * duration)
    data = []
    for i in range(n_samples):
        t = i / sample_rate
        value = math.sin(2.0 * math.pi * frequency * t) * volume
        fade_pos = i / n_samples
        if fade_pos > 0.7:
            value *= (1.0 - fade_pos) / 0.3
        sample = int(value * 32767)
        data.append(struct.pack("<h", max(-32767, min(32767, sample))))
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(data))
    return filepath


def _generate_sweep(filename, freq_start, freq_end, duration, volume=0.4):
    """Сгенерировать звук с изменением частоты."""
    filepath = os.path.join(SOUNDS_DIR, filename)
    if os.path.exists(filepath):
        return filepath
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    data = []
    for i in range(n_samples):
        t = i / sample_rate
        progress = i / n_samples
        freq = freq_start + (freq_end - freq_start) * progress
        value = math.sin(2.0 * math.pi * freq * t) * volume
        if progress > 0.6:
            value *= (1.0 - progress) / 0.4
        sample = int(value * 32767)
        data.append(struct.pack("<h", max(-32767, min(32767, sample))))
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(data))
    return filepath


def _generate_noise_burst(filename, duration, volume=0.3):
    """Сгенерировать шумовой эффект."""
    filepath = os.path.join(SOUNDS_DIR, filename)
    if os.path.exists(filepath):
        return filepath
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    sample_rate = 22050
    n_samples = int(sample_rate * duration)
    data = []
    random.seed(123)
    for i in range(n_samples):
        progress = i / n_samples
        value = (random.random() * 2 - 1) * volume
        value *= max(0, 1.0 - progress * 1.5)
        sample = int(value * 32767)
        data.append(struct.pack("<h", max(-32767, min(32767, sample))))
    with wave.open(filepath, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(data))
    return filepath


def generate_all_sounds():
    """Сгенерировать все звуковые эффекты."""
    sounds = {}
    sounds["jump"] = _generate_sweep("jump.wav", 300, 600, 0.15, 0.3)
    sounds["collect"] = _generate_sweep("collect.wav", 800, 1200, 0.2, 0.25)
    sounds["hit"] = _generate_noise_burst("hit.wav", 0.3, 0.4)
    sounds["enemy_kill"] = _generate_sweep("enemy_kill.wav", 400, 100, 0.3, 0.3)
    sounds["portal"] = _generate_sweep("portal.wav", 400, 800, 0.5, 0.2)
    sounds["game_over"] = _generate_sweep("game_over.wav", 500, 150, 0.8, 0.35)
    sounds["heal"] = _generate_sweep("heal.wav", 600, 900, 0.3, 0.2)
    sounds["lava"] = _generate_noise_burst("lava.wav", 0.2, 0.5)
    return sounds


# ============================================================
#  СИСТЕМА ЧАСТИЦ
# ============================================================

class Particle(arcade.SpriteCircle):
    """Одна частица с начальной скоростью и временем жизни."""

    def __init__(self, x, y, color, radius=4):
        super().__init__(radius, color)
        self.center_x = x
        self.center_y = y
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.0, PARTICLE_SPEED)
        self.change_x = math.cos(angle) * speed
        self.change_y = math.sin(angle) * speed
        self.lifetime = PARTICLE_LIFETIME
        self.age = 0.0
        self.initial_alpha = 255

    def update(self):
        """Обновить позицию и прозрачность."""
        self.center_x += self.change_x
        self.center_y += self.change_y
        self.change_x *= 0.96
        self.change_y *= 0.96
        self.change_y -= 0.05
        self.age += 1 / 60
        progress = self.age / self.lifetime
        self.alpha = int(self.initial_alpha * max(0, 1 - progress))

    def is_dead(self):
        return self.age >= self.lifetime


class ParticleSystem:
    """Менеджер систем частиц."""

    def __init__(self):
        self.emitters = []

    def emit_crystal_burst(self, x, y):
        """Взрыв частиц при сборе кристалла."""
        particles = arcade.SpriteList()
        colors = [COLOR_CRYSTAL_YELLOW, COLOR_CRYSTAL_BLUE, COLOR_CRYSTAL_GREEN]
        for _ in range(PARTICLE_COUNT_CRYSTAL):
            color = random.choice(colors)
            p = Particle(x, y, color, random.randint(3, 6))
            particles.append(p)
        self.emitters.append(particles)

    def emit_enemy_poof(self, x, y):
        """Облако пыли при уничтожении врага."""
        particles = arcade.SpriteList()
        for _ in range(PARTICLE_COUNT_ENEMY):
            shade = random.randint(80, 200)
            color = (shade, shade + 20, shade)
            p = Particle(x, y, color, random.randint(4, 8))
            p.change_y = abs(p.change_y) * 1.5
            particles.append(p)
        self.emitters.append(particles)

    def emit_lava_sparks(self, x, y):
        """Искры при контакте с лавой."""
        particles = arcade.SpriteList()
        colors = [(255, 100, 20), (255, 180, 40), (255, 60, 10)]
        for _ in range(10):
            color = random.choice(colors)
            p = Particle(x, y, color, random.randint(2, 5))
            p.change_y = abs(p.change_y) * 2.0
            particles.append(p)
        self.emitters.append(particles)

    def update(self):
        for sprite_list in self.emitters[:]:
            dead = []
            for particle in sprite_list:
                particle.update()
                if particle.is_dead():
                    dead.append(particle)
            for dp in dead:
                sprite_list.remove(dp)
            if len(sprite_list) == 0:
                self.emitters.remove(sprite_list)

    def draw(self):
        for sprite_list in self.emitters:
            sprite_list.draw()


# ============================================================
#  ИГРОК
# ============================================================

def _make_player_texture(color_body, color_dark, frame=0, facing=1):
    """Создать текстуру игрока программно."""
    size = TILE_SIZE
    pil_image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(pil_image)
    cx = size // 2
    leg_offset = 0
    if frame == 1:
        leg_offset = 6
    elif frame == 2:
        leg_offset = -6

    body_top = 8
    body_bottom = 44
    draw.rectangle([cx - 12, body_top, cx + 12, body_bottom], fill=color_body)

    head_r = 10
    draw.ellipse([cx - head_r, 2, cx + head_r, 2 + head_r * 2], fill=color_body)

    eye_y = 10
    if facing == 1:
        draw.rectangle([cx + 2, eye_y, cx + 7, eye_y + 5], fill=(255, 255, 255))
        draw.rectangle([cx + 4, eye_y + 1, cx + 7, eye_y + 4], fill=(0, 0, 0))
    else:
        draw.rectangle([cx - 7, eye_y, cx - 2, eye_y + 5], fill=(255, 255, 255))
        draw.rectangle([cx - 7, eye_y + 1, cx - 4, eye_y + 4], fill=(0, 0, 0))

    if frame == 3:
        draw.rectangle([cx - 10, body_bottom, cx - 4, body_bottom + 8], fill=color_dark)
        draw.rectangle([cx + 4, body_bottom, cx + 10, body_bottom + 8], fill=color_dark)
    else:
        draw.rectangle(
            [cx - 10 + leg_offset, body_bottom, cx - 4 + leg_offset, body_bottom + 14],
            fill=color_dark,
        )
        draw.rectangle(
            [cx + 4 - leg_offset, body_bottom, cx + 10 - leg_offset, body_bottom + 14],
            fill=color_dark,
        )

    draw.pieslice([cx - 12, -2, cx + 12, 14], start=180, end=0, fill=(220, 180, 40))
    draw.rectangle([cx - 3, 0, cx + 3, 5], fill=(255, 255, 200))

    texture = arcade.Texture(pil_image, name=f"player_{frame}_{facing}_{id(pil_image)}")
    return texture


class Player(arcade.Sprite):
    """Спрайт игрока с анимацией и здоровьем."""

    def __init__(self, x, y):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.scale = PLAYER_SCALE
        self.health = PLAYER_MAX_HEALTH
        self.invincible_timer = 0
        self.visible = True
        self.facing = 1
        self.on_ground = False

        self.textures_right = []
        self.textures_left = []
        for frame in range(4):
            self.textures_right.append(
                _make_player_texture(COLOR_PLAYER, COLOR_PLAYER_DARK, frame, 1)
            )
            self.textures_left.append(
                _make_player_texture(COLOR_PLAYER, COLOR_PLAYER_DARK, frame, -1)
            )

        self.jump_texture_right = self.textures_right[3]
        self.jump_texture_left = self.textures_left[3]
        self.anim_frame = 0
        self.anim_timer = 0
        self.texture = self.textures_right[0]

    def take_damage(self):
        """Нанести урон. Возвращает True если игрок погиб."""
        if self.invincible_timer > 0:
            return False
        self.health -= 1
        self.invincible_timer = INVINCIBLE_DURATION
        return self.health <= 0

    def update_animation(self, delta_time=1 / 60):
        """Обновить анимацию спрайта."""
        if self.invincible_timer > 0:
            self.invincible_timer -= 1
            self.visible = (self.invincible_timer // INVINCIBLE_BLINK_RATE) % 2 == 0
        else:
            self.visible = True

        if self.change_x > 0:
            self.facing = 1
        elif self.change_x < 0:
            self.facing = -1

        textures = self.textures_right if self.facing == 1 else self.textures_left

        if not self.on_ground:
            self.texture = (
                self.jump_texture_right if self.facing == 1 else self.jump_texture_left
            )
            return

        if abs(self.change_x) < 0.5:
            self.texture = textures[0]
            self.anim_timer = 0
            self.anim_frame = 0
            return

        self.anim_timer += 1
        if self.anim_timer >= 8:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame % 2) + 1
        self.texture = textures[self.anim_frame]


# ============================================================
#  ВРАГИ
# ============================================================

def _make_enemy_texture(frame=0, facing=1):
    """Создать текстуру слизня программно."""
    size = TILE_SIZE
    pil_image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(pil_image)
    cx = size // 2
    squish = 4 if frame == 1 else 0

    body_top = 20 + squish
    body_bottom = 56
    draw.ellipse([8, body_top, size - 8, body_bottom + 4], fill=COLOR_ENEMY_GREEN)
    draw.rectangle([8, body_bottom - 4, size - 8, body_bottom], fill=COLOR_ENEMY_GREEN)
    draw.ellipse([14, body_top + 10, size - 14, body_bottom], fill=COLOR_ENEMY_DARK)

    eye_y = body_top + 6
    if facing == 1:
        draw.ellipse([cx, eye_y, cx + 10, eye_y + 10], fill=(255, 255, 255))
        draw.ellipse([cx + 3, eye_y + 2, cx + 8, eye_y + 8], fill=(0, 0, 0))
        draw.ellipse([cx - 14, eye_y + 2, cx - 4, eye_y + 10], fill=(255, 255, 255))
        draw.ellipse([cx - 11, eye_y + 4, cx - 6, eye_y + 8], fill=(0, 0, 0))
    else:
        draw.ellipse([cx - 10, eye_y, cx, eye_y + 10], fill=(255, 255, 255))
        draw.ellipse([cx - 8, eye_y + 2, cx - 3, eye_y + 8], fill=(0, 0, 0))
        draw.ellipse([cx + 4, eye_y + 2, cx + 14, eye_y + 10], fill=(255, 255, 255))
        draw.ellipse([cx + 6, eye_y + 4, cx + 11, eye_y + 8], fill=(0, 0, 0))

    texture = arcade.Texture(pil_image, name=f"enemy_{frame}_{facing}_{id(pil_image)}")
    return texture


class Slime(arcade.Sprite):
    """Слизень — враг, патрулирующий между двумя точками."""

    def __init__(self, x, y, patrol_left, patrol_right):
        super().__init__()
        self.center_x = x
        self.center_y = y
        self.scale = ENEMY_SCALE
        self.patrol_left = patrol_left
        self.patrol_right = patrol_right
        self.change_x = ENEMY_SPEED
        self.facing = 1

        self.walk_textures_r = [_make_enemy_texture(0, 1), _make_enemy_texture(1, 1)]
        self.walk_textures_l = [_make_enemy_texture(0, -1), _make_enemy_texture(1, -1)]
        self.anim_frame = 0
        self.anim_timer = 0
        self.texture = self.walk_textures_r[0]

    def update(self):
        self.center_x += self.change_x
        if self.center_x >= self.patrol_right:
            self.change_x = -ENEMY_SPEED
            self.facing = -1
        elif self.center_x <= self.patrol_left:
            self.change_x = ENEMY_SPEED
            self.facing = 1

    def update_animation(self, delta_time=1 / 60):
        self.anim_timer += 1
        if self.anim_timer >= 15:
            self.anim_timer = 0
            self.anim_frame = (self.anim_frame + 1) % 2
        if self.facing == 1:
            self.texture = self.walk_textures_r[self.anim_frame]
        else:
            self.texture = self.walk_textures_l[self.anim_frame]


# ============================================================
#  ПОСТРОИТЕЛЬ УРОВНЕЙ
# ============================================================

def _make_wall_texture():
    size = TILE_SIZE
    img = Image.new("RGBA", (size, size), COLOR_WALL)
    draw = ImageDraw.Draw(img)
    random.seed(42)
    for _ in range(6):
        x1, y1 = random.randint(0, size), random.randint(0, size)
        x2, y2 = x1 + random.randint(-20, 20), y1 + random.randint(-20, 20)
        draw.line([(x1, y1), (x2, y2)], fill=COLOR_WALL_LIGHT, width=2)
    draw.rectangle([0, 0, size - 1, size - 1], outline=(70, 55, 40), width=2)
    return arcade.Texture(img, name=f"wall_{id(img)}")


def _make_crystal_texture(color):
    size = TILE_SIZE
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    points = [(cx, cy - 22), (cx + 14, cy), (cx, cy + 22), (cx - 14, cy)]
    draw.polygon(points, fill=color)
    highlight = tuple(min(255, c + 80) for c in color[:3]) + (180,)
    draw.polygon([(cx, cy - 16), (cx + 6, cy - 4), (cx, cy + 4), (cx - 6, cy - 4)], fill=highlight)
    return arcade.Texture(img, name=f"crystal_{color}_{id(img)}")


def _make_portal_texture():
    size = TILE_SIZE
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([8, 4, size - 8, size - 4], fill=(120, 40, 200, 200))
    draw.ellipse([16, 12, size - 16, size - 12], fill=(200, 120, 255, 220))
    draw.ellipse([24, 20, size - 24, size - 20], fill=(255, 220, 255, 240))
    return arcade.Texture(img, name=f"portal_{id(img)}")


def _make_heart_texture():
    size = TILE_SIZE
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    r = 10
    draw.ellipse([cx - r - 6, cy - r, cx - 6 + r, cy + r], fill=COLOR_HEART)
    draw.ellipse([cx + 6 - r, cy - r, cx + 6 + r, cy + r], fill=COLOR_HEART)
    draw.polygon([(cx - 18, cy + 2), (cx + 18, cy + 2), (cx, cy + 22)], fill=COLOR_HEART)
    return arcade.Texture(img, name=f"heart_{id(img)}")


def _make_lava_texture():
    size = TILE_SIZE
    img = Image.new("RGBA", (size, size), COLOR_LAVA)
    draw = ImageDraw.Draw(img)
    for i in range(0, size, 8):
        shade = (255, 120 + (i % 60), 20)
        draw.rectangle([i, 0, i + 4, size], fill=shade)
    draw.rectangle([0, 0, size - 1, 3], fill=(255, 220, 60))
    return arcade.Texture(img, name=f"lava_{id(img)}")


# Символьные карты уровней
# W=стена, C/B/G/R=кристаллы, E=враг, P=портал, H=сердце, S=старт, L=лава
LEVEL_MAPS = [
    # --- Уровень 1: Обучение ---
    [
        "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
        "W......................................W",
        "W......................................W",
        "W......................................W",
        "W...C..C..C............................W",
        "W..WWWWWWWWW....C...C......C..C........W",
        "W..............WWWWWW....WWWWWWWW......W",
        "W......................................W",
        "W..........................E...........W",
        "W.S...............E........WWWWW..P....W",
        "W.WWWW...WWWWW..WWWWWWW..........WWWWW.W",
        "W......................................W",
        "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    ],
    # --- Уровень 2: Опасные пещеры ---
    [
        "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
        "W......................................W",
        "W..B...B...G.........R.................W",
        "W.WWWWWWWWWWW.........................WW",
        "W......................C..C..C.........W",
        "W..................WWWWWWWWWWWWW.......W",
        "W.....E......H.........................W",
        "W...WWWWWW..WWW........................W",
        "W.....................E...E............W",
        "W.S................WWWWWWWWWWW...P.....W",
        "W.WWWW...WWWW..........................W",
        "WLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLW",
        "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    ],
    # --- Уровень 3: Финальное испытание ---
    [
        "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
        "W...........R.........R................W",
        "W..........WWW.......WWW...............W",
        "W......................................W",
        "W..B..G..B..G.........H................W",
        "W.WWWWWWWWWWWWW..WWWWWWWW..............W",
        "W........................E...E...E.....W",
        "W......................WWWWWWWWWWWWWW.WW",
        "W.............H........................W",
        "W.S...E......WWW.............P.........W",
        "W.WWWWWWWW.........WWWWW..WWWWWWWWWWWW.W",
        "WLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLw",
        "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    ],
]

# Кэш текстур
_wall_tex = None
_crystal_textures = {}
_portal_tex = None
_heart_tex = None
_lava_tex = None

_CRYSTAL_COLORS = {
    "C": COLOR_CRYSTAL_YELLOW, "B": COLOR_CRYSTAL_BLUE,
    "G": COLOR_CRYSTAL_GREEN, "R": COLOR_CRYSTAL_RED,
}


def _get_wall_tex():
    global _wall_tex
    if _wall_tex is None:
        _wall_tex = _make_wall_texture()
    return _wall_tex


def _get_crystal_tex(color):
    global _crystal_textures
    if color not in _crystal_textures:
        _crystal_textures[color] = _make_crystal_texture(color)
    return _crystal_textures[color]


def _get_portal_tex():
    global _portal_tex
    if _portal_tex is None:
        _portal_tex = _make_portal_texture()
    return _portal_tex


def _get_heart_tex():
    global _heart_tex
    if _heart_tex is None:
        _heart_tex = _make_heart_texture()
    return _heart_tex


def _get_lava_tex():
    global _lava_tex
    if _lava_tex is None:
        _lava_tex = _make_lava_texture()
    return _lava_tex


def build_level(level_num):
    """Построить уровень по номеру (1-based)."""
    if level_num < 1 or level_num > len(LEVEL_MAPS):
        raise ValueError(f"Уровень {level_num} не существует!")

    level_map = LEVEL_MAPS[level_num - 1]
    rows = len(level_map)

    walls = arcade.SpriteList(use_spatial_hash=True)
    crystals = arcade.SpriteList()
    enemies = arcade.SpriteList()
    hearts = arcade.SpriteList()
    portals = arcade.SpriteList()
    lava = arcade.SpriteList(use_spatial_hash=True)
    player_start = (128, 256)

    for row_i, row in enumerate(level_map):
        for col_i, char in enumerate(row):
            x = col_i * TILE_SIZE + TILE_SIZE // 2
            y = (rows - 1 - row_i) * TILE_SIZE + TILE_SIZE // 2

            if char in ("W", "w"):
                wall = arcade.Sprite(_get_wall_tex())
                wall.center_x, wall.center_y = x, y
                walls.append(wall)
            elif char in _CRYSTAL_COLORS:
                crystal = arcade.Sprite(_get_crystal_tex(_CRYSTAL_COLORS[char]))
                crystal.center_x, crystal.center_y = x, y
                crystal.properties = {"color": char}
                crystals.append(crystal)
            elif char == "E":
                enemy = Slime(x, y, x - ENEMY_PATROL_DISTANCE, x + ENEMY_PATROL_DISTANCE)
                enemies.append(enemy)
            elif char == "P":
                portal = arcade.Sprite(_get_portal_tex())
                portal.center_x, portal.center_y = x, y
                portals.append(portal)
            elif char == "H":
                heart = arcade.Sprite(_get_heart_tex())
                heart.center_x, heart.center_y = x, y
                hearts.append(heart)
            elif char == "L":
                lava_tile = arcade.Sprite(_get_lava_tex())
                lava_tile.center_x, lava_tile.center_y = x, y
                lava.append(lava_tile)
            elif char == "S":
                player_start = (x, y)

    return {
        "walls": walls, "crystals": crystals, "enemies": enemies,
        "hearts": hearts, "portals": portals, "lava": lava,
        "player_start": player_start,
    }


# ============================================================
#  СТАРТОВЫЙ ЭКРАН
# ============================================================

class FloatingCrystal:
    """Анимированный кристалл на фоне."""

    def __init__(self):
        self.x = random.randint(0, SCREEN_WIDTH)
        self.y = random.randint(0, SCREEN_HEIGHT)
        self.size = random.randint(8, 20)
        self.color = random.choice([COLOR_CRYSTAL_YELLOW, COLOR_CRYSTAL_BLUE, COLOR_CRYSTAL_GREEN])
        self.speed_x = random.uniform(-0.5, 0.5)
        self.speed_y = random.uniform(0.3, 1.0)
        self.phase = random.uniform(0, math.pi * 2)
        self.alpha = random.randint(80, 200)

    def update(self):
        self.y += self.speed_y
        self.x += self.speed_x + math.sin(self.phase) * 0.5
        self.phase += 0.02
        if self.y > SCREEN_HEIGHT + 30:
            self.y = -20
            self.x = random.randint(0, SCREEN_WIDTH)

    def draw(self):
        color_a = self.color[:3] + (self.alpha,)
        points = [
            (self.x, self.y - self.size), (self.x + self.size * 0.6, self.y),
            (self.x, self.y + self.size), (self.x - self.size * 0.6, self.y),
        ]
        arcade.draw_polygon_filled(points, color_a)


class StartView(arcade.View):
    """Стартовый экран игры."""

    def __init__(self):
        super().__init__()
        self.crystals = [FloatingCrystal() for _ in range(25)]
        self.time = 0.0
        self.high_scores = load_high_scores(5)
        self.blink_timer = 0

    def on_show_view(self):
        self.high_scores = load_high_scores(5)

    def on_update(self, delta_time):
        self.time += delta_time
        self.blink_timer += 1
        for c in self.crystals:
            c.update()

    def on_draw(self):
        self.clear()
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, COLOR_BG_DARK)

        for c in self.crystals:
            c.draw()

        scale = 1.0 + math.sin(self.time * 2) * 0.05
        ty = SCREEN_HEIGHT * 0.72

        arcade.draw_text("КРИСТАЛЬНЫЕ ПЕЩЕРЫ", SCREEN_WIDTH // 2 + 3, ty - 3,
                         (0, 0, 0, 150), font_size=int(48 * scale),
                         anchor_x="center", anchor_y="center", bold=True)
        arcade.draw_text("КРИСТАЛЬНЫЕ ПЕЩЕРЫ", SCREEN_WIDTH // 2, ty,
                         COLOR_TITLE, font_size=int(48 * scale),
                         anchor_x="center", anchor_y="center", bold=True)
        arcade.draw_text("Приключение шахтёра в магических пещерах",
                         SCREEN_WIDTH // 2, ty - 60, COLOR_TEXT_DIM,
                         font_size=18, anchor_x="center", anchor_y="center")

        if (self.blink_timer // 30) % 2 == 0:
            arcade.draw_text(">>> Нажмите ENTER чтобы начать <<<",
                             SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.42,
                             (255, 255, 200), font_size=22,
                             anchor_x="center", anchor_y="center", bold=True)

        arcade.draw_text("Управление: <- -> — движение | ПРОБЕЛ — прыжок | ESC — выход",
                         SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.30, COLOR_TEXT_DIM,
                         font_size=14, anchor_x="center", anchor_y="center")

        if self.high_scores:
            table_y = SCREEN_HEIGHT * 0.20
            arcade.draw_text("ТАБЛИЦА РЕКОРДОВ", SCREEN_WIDTH // 2, table_y,
                             COLOR_TITLE, font_size=18, anchor_x="center",
                             anchor_y="center", bold=True)
            for i, entry in enumerate(self.high_scores[:5]):
                y = table_y - 28 - i * 22
                text = f"{i+1}. {entry['name']} — {entry['score']} очков (ур. {entry['level']})"
                arcade.draw_text(text, SCREEN_WIDTH // 2, y, COLOR_TEXT,
                                 font_size=14, anchor_x="center", anchor_y="center")

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.RETURN, arcade.key.ENTER):
            gv = GameView()
            gv.setup(level=1)
            self.window.show_view(gv)
        elif key == arcade.key.ESCAPE:
            arcade.exit()


# ============================================================
#  ОСНОВНОЙ ИГРОВОЙ ЭКРАН
# ============================================================

class GameView(arcade.View):
    """Основной игровой вид."""

    def __init__(self):
        super().__init__()
        self.walls = self.crystals = self.enemies = None
        self.hearts = self.portals = self.lava = None
        self.player = None
        self.player_list = None
        self.physics_engine = None
        self.camera = self.gui_camera = None
        self.particle_system = None
        self.score = 0
        self.current_level = 1
        self.game_over = False
        self.sounds = {}
        self.sound_objects = {}
        self.left_pressed = self.right_pressed = False
        self.transition_alpha = 0
        self.transitioning = False
        self.transition_target = None
        self.transition_direction = "in"
        self.notification_text = ""
        self.notification_timer = 0

    def setup(self, level=1, score=0):
        """Настроить уровень."""
        self.current_level = level
        self.score = score
        self.game_over = False
        self.left_pressed = self.right_pressed = False
        self.transitioning = False
        self.transition_alpha = 255
        self.transition_direction = "out"

        if not self.sounds:
            sound_paths = generate_all_sounds()
            for name, path in sound_paths.items():
                try:
                    self.sound_objects[name] = arcade.load_sound(path)
                except Exception:
                    self.sound_objects[name] = None

        level_data = build_level(level)
        self.walls = level_data["walls"]
        self.crystals = level_data["crystals"]
        self.enemies = level_data["enemies"]
        self.hearts = level_data["hearts"]
        self.portals = level_data["portals"]
        self.lava = level_data["lava"]

        sx, sy = level_data["player_start"]
        self.player = Player(sx, sy)
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player)
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player, walls=self.walls, gravity_constant=GRAVITY,
        )
        self.camera = arcade.camera.Camera2D()
        self.gui_camera = arcade.camera.Camera2D()
        self.particle_system = ParticleSystem()
        self._show_notification(f"Уровень {self.current_level}")

    def _play_sound(self, name):
        snd = self.sound_objects.get(name)
        if snd:
            try:
                arcade.play_sound(snd, volume=0.5)
            except Exception:
                pass

    def _show_notification(self, text, duration=120):
        self.notification_text = text
        self.notification_timer = duration

    def on_update(self, delta_time):
        if self.game_over:
            return

        if self.transitioning:
            if self.transition_direction == "in":
                self.transition_alpha = min(255, self.transition_alpha + 8)
                if self.transition_alpha >= 255:
                    self._execute_transition()
            return
        else:
            if self.transition_alpha > 0:
                self.transition_alpha = max(0, self.transition_alpha - 5)

        self.player.change_x = 0
        if self.left_pressed:
            self.player.change_x = -PLAYER_MOVE_SPEED
        if self.right_pressed:
            self.player.change_x = PLAYER_MOVE_SPEED

        self.physics_engine.update()
        self.player.on_ground = self.physics_engine.can_jump()
        self.player.update_animation()

        for enemy in self.enemies:
            enemy.update()
            enemy.update_animation()

        self.particle_system.update()

        if self.notification_timer > 0:
            self.notification_timer -= 1

        # --- КОЛЛИЗИИ ---
        for crystal in arcade.check_for_collision_with_list(self.player, self.crystals):
            cc = crystal.properties.get("color", "C")
            mult = {"C": 1, "B": 2, "G": 2, "R": 5}.get(cc, 1)
            self.score += CRYSTAL_SCORE * mult
            self.particle_system.emit_crystal_burst(crystal.center_x, crystal.center_y)
            crystal.remove_from_sprite_lists()
            self._play_sound("collect")

        for heart in arcade.check_for_collision_with_list(self.player, self.hearts):
            if self.player.health < PLAYER_MAX_HEALTH:
                self.player.health += 1
                self._show_notification("Здоровье восстановлено!")
            else:
                self.score += 50
                self._show_notification("+50 очков!")
            heart.remove_from_sprite_lists()
            self._play_sound("heal")

        if arcade.check_for_collision_with_list(self.player, self.portals):
            self.score += LEVEL_COMPLETE_BONUS
            self._play_sound("portal")
            self.transition_target = "next_level" if self.current_level < TOTAL_LEVELS else "game_over_win"
            self.transitioning = True
            self.transition_direction = "in"
            return

        if arcade.check_for_collision_with_list(self.player, self.lava):
            self.particle_system.emit_lava_sparks(self.player.center_x, self.player.center_y)
            self._play_sound("lava")
            self.player.health = 0
            self.transition_target = "game_over_lose"
            self.transitioning = True
            self.transition_direction = "in"
            return

        for enemy in arcade.check_for_collision_with_list(self.player, self.enemies):
            if self.player.change_y < 0 and self.player.bottom > enemy.center_y:
                self.score += ENEMY_KILL_SCORE
                self.particle_system.emit_enemy_poof(enemy.center_x, enemy.center_y)
                enemy.remove_from_sprite_lists()
                self.player.change_y = PLAYER_JUMP_SPEED * 0.6
                self._play_sound("enemy_kill")
            else:
                if self.player.take_damage():
                    self.transition_target = "game_over_lose"
                    self.transitioning = True
                    self.transition_direction = "in"
                    return
                else:
                    self._show_notification(f"Урон! Осталось жизней: {self.player.health}")
                    if self.player.center_x < enemy.center_x:
                        self.player.change_x = -8
                    else:
                        self.player.change_x = 8
                    self.player.change_y = 6

        if self.player.center_y < -100:
            self.player.health = 0
            self.transition_target = "game_over_lose"
            self.transitioning = True
            self.transition_direction = "in"

        self._update_camera()

    def _update_camera(self):
        cam_x = max(0, self.player.center_x - SCREEN_WIDTH / 2)
        cam_y = max(0, self.player.center_y - SCREEN_HEIGHT / 2)
        self.camera.position = (cam_x + SCREEN_WIDTH / 2, cam_y + SCREEN_HEIGHT / 2)

    def _execute_transition(self):
        if self.transition_target == "next_level":
            self.setup(level=self.current_level + 1, score=self.score)
        elif self.transition_target in ("game_over_win", "game_over_lose"):
            won = self.transition_target == "game_over_win"
            self.window.show_view(GameOverView(self.score, self.current_level, won))

    def on_draw(self):
        self.clear()
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH * 3, 0, SCREEN_HEIGHT * 3, COLOR_BG_CAVE)

        self.camera.use()
        self.lava.draw()
        self.walls.draw()
        self.crystals.draw()
        self.hearts.draw()
        self.portals.draw()
        self.enemies.draw()
        self.player_list.draw()
        self.particle_system.draw()

        # --- HUD ---
        self.gui_camera.use()
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, SCREEN_HEIGHT - 50, SCREEN_HEIGHT, (0, 0, 0, 160))
        arcade.draw_text(f"Очки: {self.score}", 15, SCREEN_HEIGHT - 38,
                         COLOR_TITLE, font_size=20, bold=True)
        arcade.draw_text(f"Уровень: {self.current_level}/{TOTAL_LEVELS}",
                         SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT - 38, COLOR_TEXT, font_size=18)

        hx_start = SCREEN_WIDTH - 150
        arcade.draw_text("Жизни: ", hx_start, SCREEN_HEIGHT - 38, COLOR_TEXT, font_size=18)
        for i in range(self.player.health):
            hx = hx_start + 70 + i * 30
            hy = SCREEN_HEIGHT - 28
            arcade.draw_circle_filled(hx - 5, hy, 7, COLOR_HEART)
            arcade.draw_circle_filled(hx + 5, hy, 7, COLOR_HEART)
            arcade.draw_triangle_filled(hx - 12, hy - 2, hx + 12, hy - 2, hx, hy - 14, COLOR_HEART)

        if self.notification_timer > 0:
            alpha = min(255, self.notification_timer * 4)
            arcade.draw_text(self.notification_text, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 100,
                             (255, 255, 200, alpha), font_size=28,
                             anchor_x="center", anchor_y="center", bold=True)

        if self.transition_alpha > 0:
            arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT,
                                              (0, 0, 0, self.transition_alpha))

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.A):
            self.left_pressed = True
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.right_pressed = True
        elif key in (arcade.key.SPACE, arcade.key.UP, arcade.key.W):
            if self.physics_engine.can_jump():
                self.player.change_y = PLAYER_JUMP_SPEED
                self._play_sound("jump")
        elif key == arcade.key.ESCAPE:
            self.window.show_view(StartView())

    def on_key_release(self, key, modifiers):
        if key in (arcade.key.LEFT, arcade.key.A):
            self.left_pressed = False
        elif key in (arcade.key.RIGHT, arcade.key.D):
            self.right_pressed = False


# ============================================================
#  ФИНАЛЬНЫЙ ЭКРАН
# ============================================================

class GameOverView(arcade.View):
    """Финальный экран — результаты и таблица рекордов."""

    def __init__(self, score=0, level=1, won=False):
        super().__init__()
        self.final_score = score
        self.level_reached = level
        self.won = won
        self.time = 0.0
        self.high_scores = []
        self.score_saved = False
        self.blink_timer = 0
        self.bg_particles = []
        for _ in range(30):
            self.bg_particles.append({
                "x": random.randint(0, SCREEN_WIDTH),
                "y": random.randint(0, SCREEN_HEIGHT),
                "speed": random.uniform(0.2, 0.8),
                "size": random.randint(2, 6),
                "alpha": random.randint(40, 150),
            })

    def on_show_view(self):
        if not self.score_saved:
            save_score("Игрок", self.final_score, self.level_reached)
            self.score_saved = True
        self.high_scores = load_high_scores(5)

    def on_update(self, delta_time):
        self.time += delta_time
        self.blink_timer += 1
        for p in self.bg_particles:
            p["y"] += p["speed"]
            if p["y"] > SCREEN_HEIGHT + 10:
                p["y"] = -10
                p["x"] = random.randint(0, SCREEN_WIDTH)

    def on_draw(self):
        self.clear()
        bg = (15, 30, 60) if self.won else (40, 10, 10)
        arcade.draw_lrbt_rectangle_filled(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT, bg)

        for p in self.bg_particles:
            c = COLOR_CRYSTAL_YELLOW if self.won else COLOR_HEART
            arcade.draw_circle_filled(p["x"], p["y"], p["size"], c[:3] + (p["alpha"],))

        ty = SCREEN_HEIGHT * 0.78
        title = "ПОБЕДА!" if self.won else "ИГРА ОКОНЧЕНА"
        sub = f"Вы прошли все {TOTAL_LEVELS} уровней!" if self.won else "Шахтёр не смог выбраться из пещер..."
        scale = 1.0 + math.sin(self.time * 3) * 0.04
        tc = COLOR_TITLE if self.won else COLOR_HEART

        arcade.draw_text(title, SCREEN_WIDTH // 2, ty, tc, font_size=int(44 * scale),
                         anchor_x="center", anchor_y="center", bold=True)
        arcade.draw_text(sub, SCREEN_WIDTH // 2, ty - 50, COLOR_TEXT_DIM,
                         font_size=18, anchor_x="center", anchor_y="center")

        sy = SCREEN_HEIGHT * 0.52
        arcade.draw_text(f"Набрано очков: {self.final_score}", SCREEN_WIDTH // 2, sy,
                         COLOR_TITLE, font_size=28, anchor_x="center", anchor_y="center", bold=True)
        arcade.draw_text(f"Достигнут уровень: {self.level_reached} из {TOTAL_LEVELS}",
                         SCREEN_WIDTH // 2, sy - 40, COLOR_TEXT, font_size=20,
                         anchor_x="center", anchor_y="center")

        tbl_y = SCREEN_HEIGHT * 0.34
        arcade.draw_text("ТАБЛИЦА РЕКОРДОВ", SCREEN_WIDTH // 2, tbl_y, COLOR_TITLE,
                         font_size=20, anchor_x="center", anchor_y="center", bold=True)
        if self.high_scores:
            for i, entry in enumerate(self.high_scores):
                y = tbl_y - 30 - i * 24
                is_cur = entry["score"] == self.final_score and entry["level"] == self.level_reached
                clr = COLOR_CRYSTAL_YELLOW if is_cur else COLOR_TEXT
                mark = " <-- ВЫ" if is_cur else ""
                txt = f"{i+1}. {entry['name']} — {entry['score']} очков (ур. {entry['level']}){mark}"
                arcade.draw_text(txt, SCREEN_WIDTH // 2, y, clr, font_size=16,
                                 anchor_x="center", anchor_y="center")
        else:
            arcade.draw_text("Пока нет записей", SCREEN_WIDTH // 2, tbl_y - 30,
                             COLOR_TEXT_DIM, font_size=16, anchor_x="center", anchor_y="center")

        if (self.blink_timer // 30) % 2 == 0:
            arcade.draw_text("Нажмите ENTER для новой игры | ESC — выход",
                             SCREEN_WIDTH // 2, SCREEN_HEIGHT * 0.08,
                             (255, 255, 200), font_size=18,
                             anchor_x="center", anchor_y="center", bold=True)

    def on_key_press(self, key, modifiers):
        if key in (arcade.key.RETURN, arcade.key.ENTER):
            self.window.show_view(StartView())
        elif key == arcade.key.ESCAPE:
            arcade.exit()


# ============================================================
#  ТОЧКА ВХОДА
# ============================================================

def main():
    """Главная функция — создать окно и запустить игру."""
    window = arcade.Window(
        width=SCREEN_WIDTH, height=SCREEN_HEIGHT,
        title=SCREEN_TITLE, resizable=False,
    )
    window.show_view(StartView())
    arcade.run()


if __name__ == "__main__":
    main()
