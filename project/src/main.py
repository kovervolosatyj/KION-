
import asyncio
import math
import os
import sys
import webbrowser

import pygame

from levels import SIMPLE, Board, parse_level, solve

CONTINUE_URL = ""
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PUBLIC_DIR = os.path.join(os.path.dirname(BASE_DIR), "public")
FONT_NAMES = (
    "GRECHA.ttf",
    "GRECHA.otf",
    "Grecha.ttf",
    "Grecha.otf",
    "grecha.ttf",
    "grecha.otf",
    "font.ttf",
)

FONT_DIRS = (
    PUBLIC_DIR,
    os.path.join(BASE_DIR, "assets"),
    os.path.join(BASE_DIR, "fonts"),
    BASE_DIR,
)

FONT_CANDIDATES = [
    os.path.join(folder, name)
    for folder in FONT_DIRS
    for name in FONT_NAMES
]

FONT_PATH = next(
    (path for path in FONT_CANDIDATES if os.path.isfile(path)),
    None
)

print("GRECHA path:", FONT_PATH)


HERO_START_TILES = {
    "P": "tile_start_purple.png",  # фиолетовый
    "R": "tile_start (2).png",     # красный
    "B": "tile_start_blue.png",    # голубой
    "Y": "tile_start_green.png",   # зелёный
}
HERO_END_TILES = {
    "P": "tile_end_purple.png",
    "R": "tile_end (2).png",
    "B": "tile_end_blue.png",
    "Y": "tile_end_green.png",
}

ITEM_IMAGES = {
    "mirror": "mirror.png",
    "horse": "horse.png",
    "apple": "apple.png",
}
POPUP_IMAGE = "textblock.png"
BACKGROUND_DESKTOP = "background_desktop.png"
BACKGROUND_MOBILE = "background_mobile.png"
MUSIC_PATH = os.path.join(PUBLIC_DIR, "music", "game.mp3")

BG = (12, 12, 15)
TILE = (40, 40, 47)
TILE_EDGE = (92, 92, 104)
CREAM = (241, 236, 226)
INK = (14, 14, 16)
GREY = (120, 118, 126)
HERO_COL = {
    "P": (139, 92, 255),
    "R": (220, 55, 65),
    "B": (79, 198, 235),
    "Y": (104, 211, 142),
}
EXIT_COL = HERO_COL["Y"]

INTRO = ("Амипат, юная красавица, когда-то полюбила сразу троих друзей, а они — ее. "
         "И решили они положить конец сомнениям, назначив ей встречу…")

START_STORY = {
    0: [INTRO,
        "Амипат спешит к друзьям. Проведи девушку через улочки аула: проложи её путь "
        "непрерывной тропой, не пропустив ни одного закоулка."],
    1: ["Друзья отправились на рынок за подарками для Амипат: кто принесет лучший, тому она и достанется.",
        "Всяк из трех молодцев присмотрел для Амипат особенный подарок. Да только каждому под силу "
        "унести лишь один — и чужой ему не годится!",
        "Помоги друзьям обойти рынок: проведи каждого через ярмарку своим путем и не забудь прихватить подарки."],
    2: ["Встретились друзья, заглянули в зеркало и увидели, что Амипат умирает.",
        "Приведи молодцев обратно к возлюбленной!"],
    3: ["Спешили друзья к Амипат, да знали, что не каждого она выберет."],
}
ITEM_TEXT = {
    "B": "Зеркало, в котором всегда видно любимую.",
    "P": "Конь, который быстрее ветра домчит до любимой.",
    "R": "Яблоко, которое может дарить жизнь.",
}
END_STORY = [
    "Откусив яблоко, Амипат ожила. Мудрец в ауле рассудил, что она должна достаться тому, кто принес яблоко. "
    "Так и вышло.",
    "Спустя время совместной жизни муж Амипат вдруг умирает при странных обстоятельствах. От горя она "
    "отправляется искать способ вернуть любимого на тот же рынок, где было куплено яблоко.",
    "У одной старухи находится то, что нужно Амипат: дудочка, способная воскресить мертвеца. "
    "Амипат спрашивает цену, но деньги старуху не интересуют…",
]
FINAL_BUTTON = "ЧИТАТЬ ПРОДОЛЖЕНИЕ"
LEVEL_TITLES = ["Обучение", "Уровень 1", "Уровень 2", "Уровень 3", "Уровень 4"]
DEMO_LEVELS = (0, 1)


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


_fonts = {}
_assets = {}
_original_assets = {}


def original_asset(name):

    if name not in _original_assets:
        path = os.path.join(PUBLIC_DIR, name)
        if not os.path.exists(path):
            _original_assets[name] = None
        else:
            try:
                _original_assets[name] = pygame.image.load(path).convert_alpha()
            except pygame.error:
                _original_assets[name] = None
    return _original_assets[name]


def draw_cover_background(surf, name):

    image = original_asset(name)
    if image is None:
        return False
    W, H = surf.get_size()
    iw, ih = image.get_size()
    scale = max(W / iw, H / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    scaled = pygame.transform.smoothscale(image, (nw, nh))
    left, top = (nw - W) // 2, (nh - H) // 2
    surf.blit(scaled, (0, 0), pygame.Rect(left, top, W, H))
    return True


def draw_asset(surf, name, rect, color=None):
    image = asset(name, rect.size)
    if image is None:
        return False
    surf.blit(image, rect)
    if color is not None:
        tint = pygame.Surface(rect.size, pygame.SRCALPHA)
        tint.fill((*color, 82))
        surf.blit(tint, rect, special_flags=pygame.BLEND_RGBA_ADD)
    return True


def asset(name, size):
    key = (name, int(size[0]), int(size[1]))
    if key not in _assets:
        path = os.path.join(PUBLIC_DIR, name)
        if not os.path.exists(path):
            return None
        image = pygame.image.load(path).convert_alpha()
        _assets[key] = pygame.transform.smoothscale(image, key[1:])
    return _assets[key]


def font(size, bold=False):
    key = (size, bold)

    if key not in _fonts:
        if FONT_PATH is not None:
            loaded_font = pygame.font.Font(FONT_PATH, size)
            if bold:
                loaded_font.set_bold(True)
            _fonts[key] = loaded_font
        else:
            print("ОШИБКА: GRECHA не найдена!")
            print("Проверь папку и расширение файла шрифта.")
            _fonts[key] = pygame.font.SysFont("arial", size, bold=bold)

    return _fonts[key]


def wrap(text, fnt, max_w):
    lines, cur = [], ""
    for word in text.split():
        test = (cur + " " + word).strip()
        if fnt.size(test)[0] <= max_w or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_text(surf, text, fnt, color, center=None, topleft=None,
              midleft=None, letter_spacing=1):
    if letter_spacing == 0:
        img = fnt.render(text, True, color)
        r = img.get_rect()
        if center:
            r.center = center
        elif topleft:
            r.topleft = topleft
        elif midleft:
            r.midleft = midleft
        surf.blit(img, r)
        return r

    widths = [fnt.size(char)[0] for char in text]
    total_width = sum(widths) + letter_spacing * (len(text) - 1)
    height = fnt.get_height()

    img = pygame.Surface((max(1, total_width), height), pygame.SRCALPHA)
    x = 0

    for char, width in zip(text, widths):
        char_img = fnt.render(char, True, color)
        img.blit(char_img, (x, 0))
        x += width + letter_spacing

    r = img.get_rect()
    if center:
        r.center = center
    elif topleft:
        r.topleft = topleft
    elif midleft:
        r.midleft = midleft

    surf.blit(img, r)
    return r


_mandalas = {}


def mandala(radius):

    radius = int(radius)
    if radius not in _mandalas:
        s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        c = (radius, radius)
        col = (*CREAM, 40)
        for k in (0.97, 0.8, 0.55, 0.3):
            pygame.draw.circle(s, col, c, int(radius * k), 2)
        for i in range(24):
            a = i * math.tau / 24
            p1 = (c[0] + math.cos(a) * radius * 0.3, c[1] + math.sin(a) * radius * 0.3)
            p2 = (c[0] + math.cos(a) * radius * 0.8, c[1] + math.sin(a) * radius * 0.8)
            pygame.draw.line(s, col, p1, p2, 2)
            pygame.draw.circle(s, col, (int(c[0] + math.cos(a) * radius * 0.9),
                                        int(c[1] + math.sin(a) * radius * 0.9)), max(2, radius // 40))
        _mandalas[radius] = s
    return _mandalas[radius]


def draw_icon(surf, kind, c, s, color):

    x, y = c
    w = max(2, int(s * 0.09))
    if kind == "mirror":
        pygame.draw.circle(surf, color, (int(x), int(y - s * 0.06)), int(s * 0.2), w)
        pygame.draw.line(surf, color, (x, y + s * 0.14), (x, y + s * 0.3), w)
    elif kind == "horse":
        r = pygame.Rect(0, 0, s * 0.42, s * 0.42)
        r.center = (x, y + s * 0.02)
        pygame.draw.arc(surf, color, r, math.pi, math.tau, w)
        pygame.draw.line(surf, color, (x - s * 0.21, y + s * 0.02), (x - s * 0.21, y - s * 0.17), w)
        pygame.draw.line(surf, color, (x + s * 0.21, y + s * 0.02), (x + s * 0.21, y - s * 0.17), w)
    elif kind == "apple":
        pygame.draw.circle(surf, color, (int(x), int(y + s * 0.04)), int(s * 0.19))
        pygame.draw.line(surf, color, (x, y - s * 0.14), (x + s * 0.04, y - s * 0.28), w)
        pygame.draw.ellipse(surf, color, pygame.Rect(x + s * 0.03, y - s * 0.3, s * 0.15, s * 0.08))


class Geom:
    def __init__(self, pitch, ox, oy):
        self.pitch, self.ox, self.oy = pitch, ox, oy

    def center(self, cell):
        return (self.ox + (cell[1] + 0.5) * self.pitch, self.oy + (cell[0] + 0.5) * self.pitch)



class Game:
    def __init__(self):
        self.level_idx = 0
        self.seen_start = set()
        self.shown_items = set()
        self.popups = []
        self.popup_t = 0.0
        self.then = None
        self.trans = None
        self.final = False
        self.win_timer = None
        self.toast = ("", 0.0)
        self.demo_t = 0.0
        self.last_pos = None
        self.ui = {}
        self._solutions = {}
        self.load_level(0)
        self.start_story(0)


    @property
    def sets(self):
        return SIMPLE

    def load_level(self, idx):
        self.level_idx = idx
        self.level = parse_level(self.sets[idx])
        self.board = Board(self.level)
        self.win_timer = None
        self.demo_t = 0.0
        key = idx
        if key not in self._solutions:
            self._solutions[key] = solve(self.level)
        self.solution = self._solutions[key]

    def restart(self):
        self.board.reset()
        self.win_timer = None
        self.demo_t = 0.0

    def start_story(self, idx):
        if idx in START_STORY and idx not in self.seen_start:
            self.seen_start.add(idx)
            self.show(START_STORY[idx])


    def show(self, texts, then=None):
        self.popups = list(texts)
        self.popup_t = 0.0
        self.then = then

    def close_popup(self):
        if not self.popups:
            return
        self.popups.pop(0)
        self.popup_t = 0.0
        if not self.popups and self.then:
            cb, self.then = self.then, None
            cb()


    def level_complete(self):
        if self.level_idx == len(self.sets) - 1:
            self.show(END_STORY, then=lambda: setattr(self, "final", True))
            return
        size = pygame.display.get_surface().get_size()
        old = pygame.Surface(size)
        self.draw_scene(old)
        self.load_level(self.level_idx + 1)
        new = pygame.Surface(size)
        self.draw_scene(new)
        self.trans = {"old": old, "new": new, "t": 0.0}


    def handle(self, e):
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_SPACE, pygame.K_RETURN) and self.popups and self.popup_t > 0.15:
                self.close_popup()
            elif e.key == pygame.K_r and not self.popups and not self.trans:
                self.restart()

        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.on_press(e.pos)
        elif e.type == pygame.MOUSEBUTTONUP and e.button == 1:
            self.board.release()
            self.last_pos = None
        elif e.type == pygame.MOUSEMOTION and e.buttons[0]:
            self.on_drag(e.pos)

    def on_press(self, pos):
        if self.final:
            if self.ui.get("final") and self.ui["final"].collidepoint(pos):
                if CONTINUE_URL:
                    webbrowser.open(CONTINUE_URL)
                else:
                    self.toast = ("Здесь будет ссылка на продолжение новеллы", 3.0)
            return
        if self.popups:
            if self.popup_t > 0.15:
                self.close_popup()
            return
        if self.trans or self.win_timer is not None:
            return
        if self.ui.get("restart") and self.ui["restart"].collidepoint(pos):
            self.restart()
            return
        cell = self.cell_at(pos)
        if cell and self.board.press(cell):
            self.last_pos = pos

    def on_drag(self, pos):
        if self.popups or self.trans or self.win_timer is not None or self.board.active is None:
            return
        g = self.geom(pygame.display.get_surface().get_size())
        a = self.last_pos or pos
        dist = math.hypot(pos[0] - a[0], pos[1] - a[1])
        n = max(1, int(dist / (g.pitch * 0.25)))
        for i in range(1, n + 1):          # «досчитываем» клетки при быстром движении пальца
            p = (a[0] + (pos[0] - a[0]) * i / n, a[1] + (pos[1] - a[1]) * i / n)
            cell = self.cell_at(p)
            if cell:
                self.apply(self.board.step(cell))
        self.last_pos = pos

    def apply(self, events):
        for ev, hid in events:
            if ev == "done" and self.board.item_collected(hid):
                key = (self.level_idx, hid)
                if key not in self.shown_items and hid in ITEM_TEXT:
                    self.shown_items.add(key)
                    self.show([ITEM_TEXT[hid]])
            elif ev == "win":
                self.win_timer = 0.7


    def update(self, dt):
        if self.popups:
            self.popup_t += dt
        if self.toast[1] > 0:
            self.toast = (self.toast[0], self.toast[1] - dt)
        if self.trans:
            self.trans["t"] += dt / 0.9
            if self.trans["t"] >= 1:
                self.trans = None
                self.start_story(self.level_idx)
            return
        if self.win_timer is not None and not self.popups:
            self.win_timer -= dt
            if self.win_timer <= 0:
                self.win_timer = None
                self.level_complete()
        self.demo_t = self.demo_t + dt if self.demo_active() else 0.0

    def demo_active(self):
        return (self.level_idx in DEMO_LEVELS and self.solution and not self.popups and not self.trans
                and not self.final and not self.board.started and self.win_timer is None)


    @staticmethod
    def unit(size):
        return max(0.7, min(size[0] / 480, size[1] / 800))

    def geom(self, size):
        W, H = size
        u = self.unit(size)
        hud = int(104 * u)
        pad = int(18 * u)
        pitch = min((W - 2 * pad) / self.level.cols, (H - hud - 2 * pad) / self.level.rows, 150 * u)
        bw, bh = pitch * self.level.cols, pitch * self.level.rows
        return Geom(pitch, (W - bw) / 2, hud + (H - hud - bh) / 2)

    def cell_at(self, pos):
        g = self.geom(pygame.display.get_surface().get_size())
        c, r = (pos[0] - g.ox) / g.pitch, (pos[1] - g.oy) / g.pitch
        ci, ri = math.floor(c), math.floor(r)
        if (ri, ci) not in self.level.tiles:
            return None
        if max(abs(c - ci - 0.5), abs(r - ri - 0.5)) > 0.46:
            return None
        return (ri, ci)


    def draw(self, screen):
        W, H = screen.get_size()
        if self.trans:
            e = ease(self.trans["t"])
            screen.fill(BG)
            screen.blit(self.trans["old"], (0, -H * e))
            screen.blit(self.trans["new"], (0, H - H * e))
            return
        self.draw_scene(screen)
        u = self.unit((W, H))
        if self.final:
            self.draw_final(screen, u)
        elif self.popups:
            self.draw_popup(screen, u)
        if self.toast[1] > 0:
            r = draw_text(screen, self.toast[0], font(int(16 * u)), CREAM, center=(W // 2, H - int(40 * u)))
            pygame.draw.rect(screen, CREAM, r.inflate(24, 14), 1, border_radius=10)

    def draw_scene(self, surf):
        W, H = surf.get_size()
        u = self.unit((W, H))

        bg_name = BACKGROUND_MOBILE if H > W else BACKGROUND_DESKTOP
        has_bg = draw_cover_background(surf, bg_name)
        if not has_bg and bg_name != BACKGROUND_DESKTOP:
            has_bg = draw_cover_background(surf, BACKGROUND_DESKTOP)
        if has_bg:
            shade = pygame.Surface((W, H), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 112))
            surf.blit(shade, (0, 0))
        else:
            surf.fill(BG)
            surf.blit(mandala(min(W * 0.55, 260 * u)), (W / 2 - min(W * 0.55, 260 * u), -min(W * 0.55, 260 * u) * 0.9))

        bar_h = int(H * 0.035)
        x, i = 0, 0
        while x < W:
            bw = int(5 * u) + (i * 7 % 4) * int(2 * u)
            pygame.draw.rect(surf, (30, 30, 36), (x, H - bar_h, bw, bar_h))
            x += bw + int(9 * u)
            i += 1
        self.draw_hud(surf, u)
        self.draw_board(surf, self.geom((W, H)), u)

    def draw_hud(self, surf, u):
        W, H = surf.get_size()
        pad = int(18 * u)
        draw_text(surf, LEVEL_TITLES[self.level_idx], font(int(28 * u), True), CREAM, midleft=(pad, int(32 * u)))

        ids = ["Y"] if self.level_idx == 0 else ["P", "R", "B"]
        present = {h.id for h in self.level.heroes}
        rad = int(9 * u)
        x = W - pad - int(52 * u) - len(ids) * int(26 * u)
        for hid in ids:
            c = (x, int(32 * u))
            if hid in present:
                pygame.draw.circle(surf, HERO_COL[hid], c, rad)
            else:
                pygame.draw.circle(surf, mix(HERO_COL[hid], BG, 0.7), c, rad, 2)
            x += int(26 * u)
        # кнопка «заново»
        r = pygame.Rect(0, 0, int(40 * u), int(40 * u))
        r.center = (W - pad - int(20 * u), int(32 * u))
        pygame.draw.rect(surf, CREAM, r, 2, border_radius=int(12 * u))
        cx, cy, rr = r.centerx, r.centery, int(8 * u)
        pygame.draw.arc(surf, CREAM, pygame.Rect(cx - rr, cy - rr, rr * 2, rr * 2), 0.7, 5.8, 2)
        ax, ay = cx + math.cos(0.7) * rr, cy - math.sin(0.7) * rr
        pygame.draw.polygon(surf, CREAM, [(ax - 5 * u, ay - 4 * u), (ax + 5 * u, ay - 4 * u), (ax + 1 * u, ay + 5 * u)])
        self.ui["restart"] = r


        if self.level_idx == 1:
            collected = [(hid, self.board.hero[hid].item_kind)
                         for hid in ("P", "R", "B")
                         if hid in self.board.hero and self.board.item_collected(hid)]
            thumb = max(18, int(27 * u))
            tx, ty = pad, int(66 * u)
            for hid, kind in collected:
                rc = pygame.Rect(tx, ty, thumb, thumb)
                pygame.draw.rect(surf, (20, 20, 25, 180), rc, border_radius=max(3, int(5 * u)))
                if not draw_asset(surf, ITEM_IMAGES.get(kind, ""), rc):
                    draw_icon(surf, kind, rc.center, thumb, CREAM)
                pygame.draw.rect(surf, HERO_COL[hid], rc, max(1, int(2 * u)), border_radius=max(3, int(5 * u)))
                tx += thumb + int(7 * u)

    def draw_board(self, surf, g, u):
        lv, bd = self.level, self.board
        pitch = g.pitch
        size = pitch * 0.88
        rad = int(pitch * 0.18)
        occ = {cell: hid for hid, p in bd.paths.items() for cell in p}
        starts = {h.start: h for h in lv.heroes}
        ends = {h.end: h for h in lv.heroes}

        def rect_of(cell):
            cx, cy = g.center(cell)
            return pygame.Rect(cx - size / 2, cy - size / 2, size, size)

        for cell in lv.tiles:
            rc = rect_of(cell)
            hid = occ.get(cell)
            if cell in starts:
                hero = starts[cell]

                if self.level_idx == 0:
                    image_name = "tile_start_green.png"
                    if not draw_asset(surf, image_name, rc):
                        draw_asset(surf, "tile_start.png", rc)
                else:
                    image_name = HERO_START_TILES.get(hero.id, "tile_start_green.png")
                    if not draw_asset(surf, image_name, rc):
                        draw_asset(surf, "tile_start.png", rc)
            elif cell in ends:
                hero = ends[cell]
                if self.level_idx == 0:
                    image_name = "tile_end_green.png"
                    if not draw_asset(surf, image_name, rc):
                        draw_asset(surf, "tile_end.png", rc)
                else:
                    image_name = HERO_END_TILES.get(hero.id, "tile_end.png")
                    if not draw_asset(surf, image_name, rc):
                        draw_asset(surf, "tile_end.png", rc)
            elif hid:
                col = HERO_COL[hid]
                name = "tile1.png" if (cell[0] + cell[1]) % 2 else "tile2.png"

                if not draw_asset(surf, name, rc):
                    pygame.draw.rect(surf, TILE, rc, border_radius=rad)


                pad = max(2, int(pitch * 0.005))
                overlay_size = (rc.width + pad * 2, rc.height + pad * 2)

                overlay = pygame.Surface(overlay_size, pygame.SRCALPHA)
                tint = (*col, 65)

                pygame.draw.rect(
                    overlay,
                    tint,
                    overlay.get_rect().inflate(-pad, -pad),
                    border_radius=rad
                )


                small = (
                    max(1, overlay_size[0] // 5),
                    max(1, overlay_size[1] // 5)
                )
                overlay = pygame.transform.smoothscale(overlay, small)
                overlay = pygame.transform.smoothscale(overlay, overlay_size)

                surf.blit(overlay, (rc.x - pad, rc.y - pad))
            else:
                name = "tile1.png" if (cell[0] + cell[1]) % 2 else "tile2.png"
                if not draw_asset(surf, name, rc):
                    pygame.draw.rect(surf, TILE, rc, border_radius=rad)
                    pygame.draw.rect(surf, TILE_EDGE, rc, 2, border_radius=rad)


        for h in lv.heroes:
            pts = [g.center(c) for c in bd.paths[h.id]]
            self.draw_trail(surf, pts, HERO_COL[h.id], pitch)
            if pts and (bd.active == h.id or len(pts) > 1):
                hx, hy = pts[-1]
                lw = max(3, int(pitch * 0.17))
                pygame.draw.circle(surf, CREAM, (int(hx), int(hy)), int(lw * 0.78))
                pygame.draw.circle(surf, mix(HERO_COL[h.id], INK, 0.62), (int(hx), int(hy)), int(lw * 0.57))


        for cell, (hid, kind) in lv.items.items():
            cx, cy = g.center(cell)
            col = HERO_COL[hid]
            got = bd.item_collected(hid)
            d = pitch * 0.34
            poly = [(cx, cy - d), (cx + d, cy), (cx, cy + d), (cx - d, cy)]
            pygame.draw.polygon(surf, col if got else INK, poly)
            pygame.draw.polygon(surf, CREAM if got else col, poly, max(2, int(pitch * 0.045)))
            icon_size = max(8, int(pitch * 0.48))
            icon_rect = pygame.Rect(0, 0, icon_size, icon_size)
            icon_rect.center = (int(cx), int(cy))
            if not draw_asset(surf, ITEM_IMAGES.get(kind, ""), icon_rect):
                draw_icon(surf, kind, (cx, cy), pitch, INK if got else CREAM)

        if self.demo_active():
            self.draw_demo(surf, g, u)

    @staticmethod
    def draw_trail(surf, pts, hero_color, pitch, alpha=255):

        if len(pts) < 2:
            return
        layer = surf
        if alpha < 255:
            layer = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        width = max(3, int(pitch * 0.17))
        outline = width + max(2, int(pitch * 0.045))
        white = (255, 255, 255, alpha) if layer is not surf else CREAM
        pygame.draw.lines(layer, white, False, pts, outline)

        segments = len(pts) - 1
        for i in range(segments):
            t = (i + 1) / max(1, segments)
            dark = mix(hero_color, INK, 0.48 + 0.42 * t)
            color = (*dark, alpha) if layer is not surf else dark
            pygame.draw.line(layer, color, pts[i], pts[i + 1], width)
            pygame.draw.circle(layer, color, (int(pts[i + 1][0]), int(pts[i + 1][1])), width // 2)
        if layer is not surf:
            surf.blit(layer, (0, 0))

    def draw_demo(self, surf, g, u):

        hid = self.level.heroes[0].id
        path = self.solution[hid]
        pts = [g.center(c) for c in path]
        per_tile, hold, fade, pause = 0.16, 1.3, 0.5, 2.0
        draw_t = per_tile * (len(pts) - 1)
        t = self.demo_t % (draw_t + hold + fade + pause)
        if t < draw_t:
            f = t / per_tile
            alpha = 255
        elif t < draw_t + hold:
            f, alpha = len(pts) - 1, 255
        elif t < draw_t + hold + fade:
            f, alpha = len(pts) - 1, int(255 * (1 - (t - draw_t - hold) / fade))
        else:
            return
        i = min(int(f), len(pts) - 2)
        k = f - i
        cur = (pts[i][0] + (pts[i + 1][0] - pts[i][0]) * k, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * k)
        line = pts[:i + 1] + [cur]
        ov = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
        self.draw_trail(ov, line, HERO_COL[hid], g.pitch, alpha=alpha)
        if t < draw_t + hold:
            r = int(g.pitch * 0.26)
            pygame.draw.circle(ov, (255, 255, 255, 190), (int(cur[0]), int(cur[1])), r)
            pygame.draw.circle(ov, (255, 255, 255, 255), (int(cur[0]), int(cur[1])), int(r * 1.6), 3)
        surf.blit(ov, (0, 0))

    def draw_popup(self, surf, u):
        W, H = surf.get_size()

        # Затемнение игрового поля
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 150))
        surf.blit(dim, (0, 0))

        text = self.popups[0]


        pw = min(int(W * 0.92), int(620 * u))
        ph = min(int(H * 0.60), int(390 * u))


        popup_bg = asset(POPUP_IMAGE, (pw, ph))

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)

        if popup_bg is not None:
            panel.blit(popup_bg, (0, 0))
        else:
            pygame.draw.rect(
                panel, (32, 30, 37),
                (0, 0, pw, ph),
                border_radius=int(18 * u)
            )
            pygame.draw.rect(
                panel, CREAM,
                (6, 6, pw - 12, ph - 12),
                width=max(1, int(2 * u)),
                border_radius=int(14 * u)
            )


        pad_x = int(pw * 0.13)
        text_top = int(ph * 0.16)
        text_bottom = int(ph * 0.22)
        available_h = ph - text_top - text_bottom
        available_w = pw - pad_x * 2

        font_size = max(12, int(18 * u))

        while font_size > 11:
            fnt = font(font_size)
            lines = wrap(text, fnt, available_w)
            line_h = fnt.get_linesize() + max(2, int(3 * u))

            if line_h * len(lines) <= available_h:
                break

            font_size -= 1

        fnt = font(font_size)
        lines = wrap(text, fnt, available_w)
        line_h = fnt.get_linesize() + max(2, int(3 * u))


        total_h = line_h * len(lines)
        y = text_top + (available_h - total_h) // 2

        for line in lines:
            draw_text(
                panel,
                line,
                fnt,
                (255, 255, 255),
                center=(pw // 2, y + line_h // 2)
            )
            y += line_h

        # Подсказка всегда находится внизу подложки
        hint_font = font(max(15, int(12 * u)))
        draw_text(
            panel,
            "нажмите, чтобы продолжить",
            hint_font,
            (255, 255, 255),
            center=(pw // 2, ph - int(120 * u))
        )


        e = ease(self.popup_t / 0.25)
        panel.set_alpha(int(255 * e))

        panel_y = (H - ph) // 2 - int(20 * u * (1 - e))
        surf.blit(panel, ((W - pw) // 2, panel_y))

    def draw_final(self, surf, u):
        W, H = surf.get_size()
        dim = pygame.Surface((W, H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 200))
        surf.blit(dim, (0, 0))
        draw_text(surf, "Продолжение следует…", font(int(30 * u), True), CREAM, center=(W // 2, H // 2 - int(70 * u)))
        r = pygame.Rect(0, 0, min(int(W * 0.84), int(420 * u)), int(64 * u))
        r.center = (W // 2, H // 2 + int(10 * u))
        pygame.draw.rect(surf, CREAM, r, border_radius=int(14 * u))
        draw_text(surf, FINAL_BUTTON, font(int(20 * u), True), INK, center=r.center)
        self.ui["final"] = r



async def main():
    pygame.init()
    pygame.mixer.music.load(
        os.path.join(PUBLIC_DIR, "Circassian Breeze.mp3")
    )
    pygame.mixer.music.set_volume(0.3)
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(0.3) 
    pygame.mixer.music.play(-1) 
    if os.path.exists(MUSIC_PATH):
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(MUSIC_PATH)
            pygame.mixer.music.set_volume(0.42)
            pygame.mixer.music.play(-1)
        except pygame.error:
            pass
    pygame.display.set_caption("Амипат — Песни земли")
    screen = pygame.display.set_mode((460, 800), pygame.RESIZABLE)

    # Заставка
    splash_path = os.path.join(PUBLIC_DIR, "kion_desktop.png")
    splash = pygame.image.load(splash_path).convert()
    clock_splash = pygame.time.Clock()

    start_time = pygame.time.get_ticks()

    while pygame.time.get_ticks() - start_time < 2000:
        elapsed = pygame.time.get_ticks() - start_time

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        screen.fill((0, 0, 0))

        if elapsed < 1000:
            splash.set_alpha(255)
        else:
            alpha = int(255 * (2000 - elapsed) / 1000)
            splash.set_alpha(max(0, alpha))

        scaled_splash = pygame.transform.smoothscale(
            splash, screen.get_size()
        )
        screen.blit(scaled_splash, (0, 0))
        pygame.display.flip()
        clock_splash.tick(60)

    splash.set_alpha(255)


    clock = pygame.time.Clock()
    game = Game()

    clock = pygame.time.Clock()
    game = Game()
    while True:
        dt = clock.tick(60) / 1000
        for e in pygame.event.get():
            game.handle(e)
        game.update(dt)
        game.draw(pygame.display.get_surface())
        pygame.display.flip()
        await asyncio.sleep(0)


if __name__ == "__main__":
    asyncio.run(main())


