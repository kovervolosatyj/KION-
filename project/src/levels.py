"""Уровни и логика игры (без pygame) — можно тестировать отдельно.

Легенда карты:
  .  обычный тайл            (пробел) — пустое место
  P R B Y   старт героя (P - фиолетовый, R - голубой, B - зелёный, Y - Амипат)
  p r b g   финиш этого героя (g - «выход» Амипат / зелёная клетка)
  m h a     предметы: m - зеркало (синий), h - конь/подкова (фиолетовый), a - яблоко (красный)
"""
from dataclasses import dataclass, field

ITEM_OWNER = {"m": "B", "h": "P", "a": "R"}
ITEM_NAME = {"m": "mirror", "h": "horse", "a": "apple"}
END_OWNER = {"p": "P", "r": "R", "b": "B", "g": "Y"}
START_CHARS = "PRBY"

TUTORIAL = [
    " Y  ",
    " ...",
    "....",
    "....",
    " g  ",
]

L4 = [
    "...R ",
    ".....",
    " .. .",
    ".....",
    ".. ..",
    " ...r",
]

SIMPLE = [
    TUTORIAL,
    [
        " PRB ",
        " ..m.",
        "h....",
        "...a.",
        "p.rb.",
    ],
    [
        " P.RB..",
        ".......",
        ".......",
        "  ....b",
        "  p..r ",
    ],
    [
        ".P  R.",
        "...  .",
        "p.....",
        " .....",
        "   r..",
    ],
    L4,
]

# ----------------------------------------------------------------------------
@dataclass
class Hero:
    id: str
    start: tuple
    end: tuple = None
    item: tuple = None          # клетка с предметом (или None)
    item_kind: str = None       # "mirror" / "horse" / "apple"


@dataclass
class Level:
    tiles: set
    heroes: list
    rows: int
    cols: int
    items: dict = field(default_factory=dict)   # клетка -> (hero_id, kind)


def parse_level(rows):
    w = max(len(r) for r in rows)
    tiles, heroes, items = set(), {}, {}
    ends = {}
    for r, line in enumerate(rows):
        for c, ch in enumerate(line.ljust(w)):
            if ch == " ":
                continue
            tiles.add((r, c))
            if ch in START_CHARS:
                heroes[ch] = Hero(ch, (r, c))
            elif ch in END_OWNER:
                ends[END_OWNER[ch]] = (r, c)
            elif ch in ITEM_OWNER:
                items[(r, c)] = (ITEM_OWNER[ch], ITEM_NAME[ch])
    for hid, pos in ends.items():
        heroes[hid].end = pos
    for pos, (hid, kind) in items.items():
        heroes[hid].item, heroes[hid].item_kind = pos, kind
    order = [h for h in "PRBY" if h in heroes]
    return Level(tiles, [heroes[h] for h in order], len(rows), w, items)


NEIGH = ((1, 0), (-1, 0), (0, 1), (0, -1))


def adjacent(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1]) == 1


class Board:
    """Состояние прохождения одного уровня."""

    def __init__(self, level):
        self.level = level
        self.reset()

    def reset(self):
        self.paths = {h.id: [h.start] for h in self.level.heroes}
        self.hero = {h.id: h for h in self.level.heroes}
        self.active = None
        self.started = False

    # --- запросы -----------------------------------------------------------
    def owner_of(self, cell):
        for hid, p in self.paths.items():
            if cell in p:
                return hid
        return None

    def covered(self):
        return sum(len(p) for p in self.paths.values())

    def hero_done(self, hid):
        return self.paths[hid][-1] == self.hero[hid].end

    def item_collected(self, hid):
        h = self.hero[hid]
        return h.item is not None and h.item in self.paths[hid]

    def is_complete(self):
        return (self.covered() == len(self.level.tiles)
                and all(self.hero_done(h.id) for h in self.level.heroes))

    def can_enter(self, hid, cell):
        if cell not in self.level.tiles or self.owner_of(cell):
            return False
        for h in self.level.heroes:                      # чужой финиш закрыт
            if h.id != hid and h.end == cell:
                return False
        it = self.level.items.get(cell)                   # чужой предмет не годится
        if it and it[0] != hid:
            return False
        return True

    # --- ввод --------------------------------------------------------------
    def press(self, cell):
        """Нажатие на клетку: выбираем линию героя (обрезаем её до этой клетки)."""
        hid = self.owner_of(cell)
        if hid is None:
            self.active = None
            return False
        p = self.paths[hid]
        del p[p.index(cell) + 1:]
        self.active = hid
        self.started = True
        return True

    def release(self):
        self.active = None

    def step(self, cell):
        """Перетаскивание через клетку. Возвращает список событий."""
        events = []
        hid = self.active
        if hid is None:
            return events
        p = self.paths[hid]
        if cell == p[-1]:
            return events
        if cell in p:                                     # возврат по своей линии
            del p[p.index(cell) + 1:]
            return events
        if not adjacent(p[-1], cell) or self.hero_done(hid):
            return events
        if not self.can_enter(hid, cell):
            return events
        p.append(cell)
        h = self.hero[hid]
        if h.item and cell == h.item:
            events.append(("item", hid))
        if self.hero_done(hid):
            events.append(("done", hid))
        if self.is_complete():
            events.append(("win", None))
        return events


# ----------------------------------------------------------------------------
def solve(level, limit=200000):
    """Поиск решения (для проверки уровней и подсказки-«пальчика»).
    Возвращает {hero_id: [клетки]} или None."""
    heroes = level.heroes
    occ = {h.start for h in heroes}
    paths = {h.id: [h.start] for h in heroes}
    ends = {h.end for h in heroes}
    total = len(level.tiles)
    budget = [limit]

    def allowed(h, cell):
        if cell not in level.tiles or cell in occ:
            return False
        if cell in ends and cell != h.end:
            return False
        it = level.items.get(cell)
        return not (it and it[0] != h.id)

    def feasible(idx):
        free = [c for c in level.tiles if c not in occ]
        access = set()
        cur = heroes[idx]
        if paths[cur.id][-1] != cur.end:
            access.add(paths[cur.id][-1])
        for h in heroes[idx + 1:]:
            access.add(h.start)
        freeset = set(free)
        for c in free:
            n = 0
            for d in NEIGH:
                q = (c[0] + d[0], c[1] + d[1])
                if q in freeset or q in access:
                    n += 1
            if n < (1 if c in ends else 2):
                return False
        seen = set()
        for c in free:
            if c in seen:
                continue
            comp, st, touch = {c}, [c], False
            seen.add(c)
            while st:
                x = st.pop()
                for d in NEIGH:
                    q = (x[0] + d[0], x[1] + d[1])
                    if q in access:
                        touch = True
                    if q in freeset and q not in seen:
                        seen.add(q); comp.add(q); st.append(q)
            if not touch:
                return False
        return True

    def dfs(idx):
        budget[0] -= 1
        if budget[0] < 0:
            return False
        h = heroes[idx]
        head = paths[h.id][-1]
        if head == h.end:
            if idx == len(heroes) - 1:
                return len(occ) == total
            return feasible(idx + 1) and dfs(idx + 1)
        for d in NEIGH:
            q = (head[0] + d[0], head[1] + d[1])
            if allowed(h, q):
                occ.add(q); paths[h.id].append(q)
                if feasible(idx) and dfs(idx):
                    return True
                occ.discard(q); paths[h.id].pop()
        return False

    return {k: list(v) for k, v in paths.items()} if dfs(0) else None
