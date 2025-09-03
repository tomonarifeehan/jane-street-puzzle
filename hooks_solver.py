import tkinter as tk
from tkinter import ttk
from typing import Tuple, List, Set, Optional
import random
import math

GRID_SIZE = 9
BOLD_WIDTH = 6
GRID_WIDTH = 1
OUTER_BORDER_WIDTH = 6

# Prefilled non-editable numbers (0-indexed row, col) -> digit
GIVENS = {
    (0, 4): 5,
    (1, 3): 4,
    (4, 4): 1,
    (7, 5): 8,
    (8, 4): 9,
}

# High-contrast "highlighter" palette + white
COLOR_CHOICES = [
    ("White", "#ffffff"),
    ("Neon Yellow", "#FFF200"),
    ("Electric Lime", "#C6FF00"),
    ("Electric Cyan", "#00E5FF"),
    ("Hot Pink", "#FF2D95"),
    ("Safety Orange", "#FF5E00"),
    ("Vivid Purple", "#A100FF"),
]

# Fixed color assignment (indices into COLOR_CHOICES) per pentomino
# These remain constant across button clicks in this session.
PENTOMINO_COLORS = {
    "I": 1,  # Neon Yellow
    "N": 2,  # Electric Lime
    "Z": 3,  # Electric Cyan
    "U": 4,  # Hot Pink
    "X": 5,  # Safety Orange
    "V": 6,  # Vivid Purple
}

class GridEditor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("9×9 Grid Editor")
        self.minsize(920, 660)

        # --- model ---
        self.colors = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]  # index into COLOR_CHOICES
        self.digits = [["" for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]  # "", "0".."9"
        # sides[r][c] = [top, right, bottom, left] booleans
        self.sides = [[[False, False, False, False] for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        # number color: 0 = black, 1 = red
        self.num_color = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        # locked (non-editable) cells
        self.locked = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        for (r, c), d in GIVENS.items():
            if 0 <= r < GRID_SIZE and 0 <= c < GRID_SIZE and 0 <= d <= 9:
                self.digits[r][c] = str(d)
                self.locked[r][c] = True
                self.num_color[r][c] = 0  # force black for givens

        # position of the '1'
        self.one_pos = self.find_one_position()
        self.ensure_one_bold()

        # track the 3-cell L around '1'
        self.core_L_cells: Optional[Set[Tuple[int, int]]] = None

        self.selected = (0, 0)

        # --- UI layout ---
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        main = ttk.Frame(self)
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(main, bg="white", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        side = ttk.Frame(main)
        side.grid(row=0, column=1, sticky="ns", padx=(0, 10), pady=10)
        for i in range(10):
            side.rowconfigure(i, weight=0)
        side.rowconfigure(99, weight=1)  # spacer

        # --- Color palette ---
        ttk.Label(side, text="Background").grid(row=0, column=0, sticky="w", pady=(0, 4))
        for idx, (name, hx) in enumerate(COLOR_CHOICES):
            b = tk.Button(side, text=name, width=18, relief="raised", bg=hx, activebackground=hx,
                          command=lambda i=idx: self.apply_color(i))
            b.grid(row=1+idx, column=0, sticky="ew", pady=2)

        ttk.Button(side, text="Clear Background", command=lambda: self.apply_color(0)).grid(row=1+len(COLOR_CHOICES), column=0, sticky="ew", pady=(4, 10))

        # --- Border toggles ---
        sep1 = ttk.Separator(side, orient="horizontal")
        sep1.grid(row=18, column=0, sticky="ew", pady=(6,6))

        ttk.Label(side, text="Bold Sides").grid(row=20, column=0, sticky="w", pady=(0, 4))
        self.var_top = tk.IntVar(value=0)
        self.var_right = tk.IntVar(value=0)
        self.var_bottom = tk.IntVar(value=0)
        self.var_left = tk.IntVar(value=0)
        self.chk_top = ttk.Checkbutton(side, text="Top (T)", variable=self.var_top, command=lambda: self.toggle_side("top"))
        self.chk_right = ttk.Checkbutton(side, text="Right (R)", variable=self.var_right, command=lambda: self.toggle_side("right"))
        self.chk_bottom = ttk.Checkbutton(side, text="Bottom (B)", variable=self.var_bottom, command=lambda: self.toggle_side("bottom"))
        self.chk_left = ttk.Checkbutton(side, text="Left (L)", variable=self.var_left, command=lambda: self.toggle_side("left"))
        self.chk_top.grid(row=21, column=0, sticky="w")
        self.chk_right.grid(row=22, column=0, sticky="w")
        self.chk_bottom.grid(row=23, column=0, sticky="w")
        self.chk_left.grid(row=24, column=0, sticky="w")

        ttk.Button(side, text="Clear Sides", command=self.clear_sides).grid(row=25, column=0, sticky="ew", pady=(4, 6))

        # --- Single-button generator ---
        ttk.Button(side, text="Build Pattern (single click)", command=self.generate_core_and_complement).grid(row=26, column=0, sticky="ew", pady=(0, 10))

        # NEW: Pentomino placement button
        ttk.Button(side, text="Place Pentominoes", command=self.place_random_pentominoes).grid(row=27, column=0, sticky="ew", pady=(0, 10))

        # --- Digits ---
        sep2 = ttk.Separator(side, orient="horizontal")
        sep2.grid(row=28, column=0, sticky="ew", pady=(6,6))

        ttk.Label(side, text="Digit").grid(row=40, column=0, sticky="w", pady=(0, 4))
        digits_frame = ttk.Frame(side)
        digits_frame.grid(row=41, column=0, sticky="ew")
        for n in range(10):
            r = n // 5
            c = n % 5
            b = ttk.Button(digits_frame, text=str(n), width=3, command=lambda ch=str(n): self.apply_digit(ch))
            b.grid(row=r, column=c, padx=2, pady=2)
        ttk.Button(side, text="Clear Digit (Del)", command=lambda: self.apply_digit("")).grid(row=42, column=0, sticky="ew", pady=(4, 10))

        # --- Number color ---
        sep3 = ttk.Separator(side, orient="horizontal")
        sep3.grid(row=43, column=0, sticky="ew", pady=(6,6))

        ttk.Label(side, text="Number Color").grid(row=44, column=0, sticky="w")
        nc_frame = ttk.Frame(side)
        nc_frame.grid(row=45, column=0, sticky="ew", pady=(2, 10))
        ttk.Button(nc_frame, text="Black", command=lambda: self.apply_num_color(0), width=7).grid(row=0, column=0, padx=2)
        ttk.Button(nc_frame, text="Red", command=lambda: self.apply_num_color(1), width=7).grid(row=0, column=1, padx=2)
        ttk.Button(nc_frame, text="Toggle (X)", command=self.toggle_num_color).grid(row=0, column=2, padx=2)

        # --- Help ---
        help_text = (
            "Shortcuts:\\n"
            " • Click: select cell\\n"
            " • Arrow keys: move selection\\n"
            " • 0–9: set digit, Delete to clear\\n"
            " • T/R/B/L: toggle bold Top/Right/Bottom/Left\\n"
            " • C: cycle background color\\n"
            " • X: toggle digit color (black/red)\\n"
            " • '1' cell is always bold and cannot be changed\\n"
            " • 'Build Pattern (single click)' places a 3-cell L touching '1' and a complementary 5-cell L.\\n"
            " • 'Place Pentominoes' colors I,N,Z,U,X,V with fixed bright colors, and enforces:\\n"
            "     - row targets for each piece, and\\n"
            "     - every 2×2 region contains at least one white cell.\\n"
        )
        ttk.Label(side, text=help_text, justify="left").grid(row=99, column=0, sticky="s")

        # bindings
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<Button-1>", self.on_click)
        self.bind("<Key>", self.on_key)

        self.redraw()
        self.update_side_vars_from_selection()

    # ---- helpers ----
    def find_one_position(self) -> Optional[Tuple[int, int]]:
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.digits[r][c] == "1":
                    return (r, c)
        return None

    def board_bbox(self) -> Tuple[float, float, float, float]:
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        size = min(w, h) - 20  # padding
        size = max(size, 100)
        cell = size / GRID_SIZE
        x0 = (w - size) / 2
        y0 = (h - size) / 2
        self.cell = cell
        self.offset_x = x0
        self.offset_y = y0
        return x0, y0, x0 + size, y0 + size

    def cell_bbox(self, r: int, c: int) -> Tuple[float, float, float, float]:
        x0, y0, _, _ = self.board_bbox()
        cx0 = x0 + c * self.cell
        cy0 = y0 + r * self.cell
        return cx0, cy0, cx0 + self.cell, cy0 + self.cell

    # ---- UI actions ----
    def on_resize(self, _event=None):
        self.redraw()

    def on_click(self, event):
        r, c = self.rc_from_xy(event.x, event.y)
        if r is not None:
            self.selected = (r, c)
            self.update_side_vars_from_selection()
            self.redraw()

    def on_key(self, event):
        r, c = self.selected
        if event.char in "0123456789":
            self.apply_digit(event.char)
            return
        if event.keysym in ("BackSpace", "Delete"):
            self.apply_digit("")
            return
        if event.char.lower() == "c":
            self.apply_color((self.colors[r][c] + 1) % len(COLOR_CHOICES))
            return
        if event.char.lower() == "x":
            self.toggle_num_color()
            return
        if event.char.lower() in ("t", "r", "b", "l"):
            mapping = {"t": "top", "r": "right", "b": "bottom", "l": "left"}
            self.toggle_side(mapping[event.char.lower()])
            return
        # arrow navigation
        if event.keysym in ("Left", "Right", "Up", "Down"):
            dr = dc = 0
            if event.keysym == "Left": dc = -1
            elif event.keysym == "Right": dc = 1
            elif event.keysym == "Up": dr = -1
            elif event.keysym == "Down": dr = 1
            nr = max(0, min(GRID_SIZE-1, r + dr))
            nc = max(0, min(GRID_SIZE-1, c + dc))
            self.selected = (nr, nc)
            self.update_side_vars_from_selection()
            self.redraw()

    def rc_from_xy(self, x, y):
        x0, y0, x1, y1 = self.board_bbox()
        if not (x0 <= x <= x1 and y0 <= y <= y1):
            return None, None
        c = int((x - x0) // self.cell)
        r = int((y - y0) // self.cell)
        r = max(0, min(GRID_SIZE-1, r))
        c = max(0, min(GRID_SIZE-1, c))
        return r, c

    def apply_color(self, color_index: int):
        r, c = self.selected
        self.colors[r][c] = color_index
        self.redraw()

    def apply_digit(self, ch: str):
        r, c = self.selected
        if self.locked[r][c]:
            self.bell()
            return
        self.digits[r][c] = ch
        self.redraw()

    def apply_num_color(self, color_flag: int):
        r, c = self.selected
        if self.locked[r][c]:
            self.bell()
            return
        self.num_color[r][c] = 1 if color_flag else 0
        self.redraw()

    def toggle_num_color(self):
        r, c = self.selected
        if self.locked[r][c]:
            self.bell()
            return
        self.num_color[r][c] = 1 - self.num_color[r][c]
        self.redraw()

    def toggle_side(self, which: str):
        r, c = self.selected
        idx = {"top": 0, "right": 1, "bottom": 2, "left": 3}[which]
        self.sides[r][c][idx] = not self.sides[r][c][idx]
        self.update_side_vars_from_selection()
        self.redraw()

    def clear_sides(self):
        # clear everything except keep the '1' cell fully bold
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.sides[r][c] = [False, False, False, False]
        
        self.update_side_vars_from_selection()
        self.redraw()

    def ensure_one_bold(self):
        if getattr(self, 'one_pos', None) is not None:
            r1, c1 = self.one_pos
            self.sides[r1][c1] = [True, True, True, True]

    # ---- 3-cell L (around '1') ----
    def available_L_shapes(self) -> List[Set[Tuple[int,int]]]:
        """Return list of 3-cell L sets touching the '1' cell, within bounds."""
        res: List[Set[Tuple[int,int]]] = []
        if self.one_pos is None:
            return res
        r, c = self.one_pos
        orientations = [
            { (r-1, c), (r, c-1), (r-1, c-1) },  # NW
            { (r-1, c), (r, c+1), (r-1, c+1) },  # NE
            { (r+1, c), (r, c-1), (r+1, c-1) },  # SW
            { (r+1, c), (r, c+1), (r+1, c+1) },  # SE
        ]
        for cells in orientations:
            ok = True
            for (rr, cc) in cells:
                if not (0 <= rr < GRID_SIZE and 0 <= cc < GRID_SIZE):
                    ok = False
                    break
            if ok:
                res.append(cells)
        return res

    def core_block4(self) -> Optional[Set[Tuple[int,int]]]:
        """Return the 4-cell square: the '1' cell plus the chosen 3-cell L."""
        if self.one_pos is None or self.core_L_cells is None:
            return None
        block = set(self.core_L_cells)
        block.add(self.one_pos)
        return block

    def core_orientation(self) -> Optional[str]:
        """Return 'NW','NE','SW','SE' for the 3-cell L relative to the '1' cell."""
        if self.one_pos is None or self.core_L_cells is None:
            return None
        r, c = self.one_pos
        cells = self.core_L_cells
        if {(r-1, c), (r, c-1), (r-1, c-1)}.issubset(cells):
            return "NW"
        if {(r-1, c), (r, c+1), (r-1, c+1)}.issubset(cells):
            return "NE"
        if {(r+1, c), (r, c-1), (r+1, c-1)}.issubset(cells):
            return "SW"
        if {(r+1, c), (r, c+1), (r+1, c+1)}.issubset(cells):
            return "SE"
        return None

    def complement_L_cells(self, orient: str) -> Optional[Set[Tuple[int,int]]]:
        """Return the 5-cell '3x3-L' that complements the 2x2 block to make a 3x3 (in spirit)."""
        if self.one_pos is None or self.core_L_cells is None:
            return None
        r, c = self.one_pos
        if orient == "NW":
            R = range(r-2, r+1)
            C = range(c-2, c+1)
            block2x2 = {(r-1, c-1), (r-1, c), (r, c-1), (r, c)}
        elif orient == "NE":
            R = range(r-2, r+1)
            C = range(c, c+3)
            block2x2 = {(r-1, c), (r-1, c+1), (r, c), (r, c+1)}
        elif orient == "SW":
            R = range(r, r+3)
            C = range(c-2, c+1)
            block2x2 = {(r, c-1), (r, c), (r+1, c-1), (r+1, c)}
        elif orient == "SE":
            R = range(r, r+3)
            C = range(c, c+3)
            block2x2 = {(r, c), (r, c+1), (r+1, c), (r+1, c+1)}
        else:
            return None

        for rr in R:
            for cc in C:
                if not (0 <= rr < GRID_SIZE and 0 <= cc < GRID_SIZE):
                    return None

        region = {(rr, cc) for rr in R for cc in C}
        comp = region - block2x2
        if len(comp) != 5:
            return None
        return comp

    def outline_cells(self, cells: Set[Tuple[int,int]], do_redraw: bool = True):
        """Set bold sides outlining the union of cells (no internal bold lines).
           NOTE: This clears previous sides (except keeps '1' bold)."""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.sides[r][c] = [False, False, False, False]
        
        self.add_outline_cells(cells, do_redraw=False)
        if do_redraw:
            self.redraw()

    def add_outline_cells(self, cells: Set[Tuple[int,int]], do_redraw: bool = True):
        """Add bold sides outlining given cells on top of existing sides (no clearing)."""
        cells_set = set(cells)
        for (r, c) in cells_set:
            if r-1 < 0 or (r-1, c) not in cells_set:
                self.sides[r][c][0] = True
            if c+1 >= GRID_SIZE or (r, c+1) not in cells_set:
                self.sides[r][c][1] = True
            if r+1 >= GRID_SIZE or (r+1, c) not in cells_set:
                self.sides[r][c][2] = True
            if c-1 < 0 or (r, c-1) not in cells_set:
                self.sides[r][c][3] = True

        self.redraw() if do_redraw else None

    # ---- Single-click: core + complementary 5-cell L ----
    def generate_core_and_complement(self):
        """Single-click: place a random 3-cell L touching '1', then independently choose one of
        the four possible 3×3 placements whose complement (5-cell L) plus the 2×2 block fills that 3×3.
        Update off-screen; draw once at the end."""
        options = self.available_L_shapes()
        if not options:
            self.bell(); return
        core_choice = random.choice(options)
        self.core_L_cells = set(core_choice)

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.sides[r][c] = [False, False, False, False]
        self.ensure_one_bold()
        self.add_outline_cells(self.core_L_cells, do_redraw=False)

        if self.one_pos is None:
            self.one_pos = self.find_one_position()
        if self.one_pos is None:
            self.redraw(); return
        block4 = set(self.core_L_cells)
        block4.add(self.one_pos)

        min_r = min(r for r, _ in block4)
        min_c = min(c for _, c in block4)

        tl_candidates = [
            (min_r,     min_c),
            (min_r,     min_c - 1),
            (min_r - 1, min_c),
            (min_r - 1, min_c - 1),
        ]

        valid_tl = []
        for tr, tc in tl_candidates:
            if 0 <= tr <= GRID_SIZE - 3 and 0 <= tc <= GRID_SIZE - 3:
                valid_tl.append((tr, tc))
        if not valid_tl:
            self.redraw(); return

        tr, tc = random.choice(valid_tl)
        region = {(rr, cc) for rr in range(tr, tr+3) for cc in range(tc, tc+3)}
        comp = region - block4
        if len(comp) != 5:
            others = [tl for tl in valid_tl if tl != (tr, tc)]
            for tr2, tc2 in others:
                region2 = {(rr, cc) for rr in range(tr2, tr2+3) for cc in range(tc2, tc2+3)}
                comp2 = region2 - block4
                if len(comp2) == 5:
                    comp = comp2
                    tr, tc = tr2, tc2
                    break
            else:
                self.redraw(); return

        self.add_outline_cells(comp, do_redraw=False)

        tl4_candidates = [
            (tr,     tc),
            (tr-1,   tc),
            (tr,     tc-1),
            (tr-1,   tc-1),
        ]
        tl4_valid = [(r4, c4) for (r4, c4) in tl4_candidates if 0 <= r4 <= GRID_SIZE-4 and 0 <= c4 <= GRID_SIZE-4]
        if tl4_valid:
            r4, c4 = random.choice(tl4_valid)
            region4 = {(rr, cc) for rr in range(r4, r4+4) for cc in range(c4, c4+4)}
            l7 = region4 - region
            if len(l7) == 7:
                self.add_outline_cells(l7, do_redraw=False)

        tl5_candidates = [
            (r4,   c4),
            (r4-1, c4),
            (r4,   c4-1),
            (r4-1, c4-1),
        ]
        tl5_valid = [(r5, c5) for (r5, c5) in tl5_candidates if 0 <= r5 <= GRID_SIZE-5 and 0 <= c5 <= GRID_SIZE-5]
        if tl5_valid:
            r5, c5 = random.choice(tl5_valid)
            region5 = {(rr, cc) for rr in range(r5, r5+5) for cc in range(c5, c5+5)}
            l9 = region5 - region4
            if len(l9) == 9:
                self.add_outline_cells(l9, do_redraw=False)

        tl6_candidates = [
            (r5,   c5),
            (r5-1, c5),
            (r5,   c5-1),
            (r5-1, c5-1),
        ]
        tl6_valid = [(r6, c6) for (r6, c6) in tl6_candidates if 0 <= r6 <= GRID_SIZE-6 and 0 <= c6 <= GRID_SIZE-6]
        if tl6_valid:
            r6, c6 = random.choice(tl6_valid)
            region6 = {(rr, cc) for rr in range(r6, r6+6) for cc in range(c6, c6+6)}
            l11 = region6 - region5
            if len(l11) == 11:
                self.add_outline_cells(l11, do_redraw=False)

        tl7_candidates = [
            (r6,   c6),
            (r6-1, c6),
            (r6,   c6-1),
            (r6-1, c6-1),
        ]
        tl7_valid = [(r7, c7) for (r7, c7) in tl7_candidates if 0 <= r7 <= GRID_SIZE-7 and 0 <= c7 <= GRID_SIZE-7]
        if tl7_valid:
            r7, c7 = random.choice(tl7_valid)
            region7 = {(rr, cc) for rr in range(r7, r7+7) for cc in range(c7, c7+7)}
            l13 = region7 - region6
            if len(l13) == 13:
                self.add_outline_cells(l13, do_redraw=False)

        tl8_candidates = [
            (r7,   c7),
            (r7-1, c7),
            (r7,   c7-1),
            (r7-1, c7-1),
        ] if 'r7' in locals() else []
        tl8_valid = [(r8, c8) for (r8, c8) in tl8_candidates if 0 <= r8 <= GRID_SIZE-8 and 0 <= c8 <= GRID_SIZE-8]
        if tl8_valid:
            r8, c8 = random.choice(tl8_valid)
            region8 = {(rr, cc) for rr in range(r8, r8+8) for cc in range(c8, c8+8)}
            l15 = region8 - region7
            if len(l15) == 15:
                self.add_outline_cells(l15, do_redraw=False)

        tl9_candidates = [
            (r8,   c8),
            (r8-1, c8),
            (r8,   c8-1),
            (r8-1, c8-1),
        ] if 'r8' in locals() else []
        tl9_valid = [(r9, c9) for (r9, c9) in tl9_candidates if 0 <= r9 <= GRID_SIZE-9 and 0 <= c9 <= GRID_SIZE-9]
        if tl9_valid:
            r9, c9 = random.choice(tl9_valid)
            region9 = {(rr, cc) for rr in range(r9, r9+9) for cc in range(c9, c9+9)}
            l17 = region9 - region8
            if len(l17) == 17:
                self.add_outline_cells(l17, do_redraw=False)
        self.redraw()

    def update_side_vars_from_selection(self):
        r, c = self.selected
        t, rgt, btm, lft = self.sides[r][c]
        self.var_top.set(1 if t else 0)
        self.var_right.set(1 if rgt else 0)
        self.var_bottom.set(1 if btm else 0)
        self.var_left.set(1 if lft else 0)

    # ---- drawing ----
    def redraw(self):
        self.canvas.delete("all")
        x0, y0, x1, y1 = self.board_bbox()

        # fill cells
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                bx0, by0, bx1, by1 = self.cell_bbox(r, c)
                _, hx = COLOR_CHOICES[self.colors[r][c]]
                self.canvas.create_rectangle(bx0, by0, bx1, by1, fill=hx, outline="")

        # base grid
        for i in range(GRID_SIZE + 1):
            x = x0 + i * self.cell
            y = y0 + i * self.cell
            self.canvas.create_line(x0, y, x1, y, width=GRID_WIDTH, fill="#000000")
            self.canvas.create_line(x, y0, x, y1, width=GRID_WIDTH, fill="#000000")

        # outer border (always thick)
        self.canvas.create_rectangle(x0, y0, x1, y1, width=OUTER_BORDER_WIDTH, outline="#000000")

        # bold sides — canonical ownership for interior edges
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                bx0, by0, bx1, by1 = self.cell_bbox(r, c)

                # Top edge
                if r == 0:
                    if self.sides[r][c][0]:
                        self.canvas.create_line(bx0, by0, bx1, by0, width=BOLD_WIDTH, fill="#000000")
                else:
                    if self.sides[r][c][0] or self.sides[r-1][c][2]:
                        self.canvas.create_line(bx0, by0, bx1, by0, width=BOLD_WIDTH, fill="#000000")

                # Left edge
                if c == 0:
                    if self.sides[r][c][3]:
                        self.canvas.create_line(bx0, by0, bx0, by1, width=BOLD_WIDTH, fill="#000000")
                else:
                    if self.sides[r][c][3] or self.sides[r][c-1][1]:
                        self.canvas.create_line(bx0, by0, bx0, by1, width=BOLD_WIDTH, fill="#000000")

                # Right outer boundary
                if c == GRID_SIZE - 1 and self.sides[r][c][1]:
                    self.canvas.create_line(bx1, by0, bx1, by1, width=BOLD_WIDTH, fill="#000000")

                # Bottom outer boundary
                if r == GRID_SIZE - 1 and self.sides[r][c][2]:
                    self.canvas.create_line(bx0, by1, bx1, by1, width=BOLD_WIDTH, fill="#000000")

        # digits
        font_size = int(self.cell * 0.45)
        if font_size < 6:
            font_size = 6
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                ch = self.digits[r][c]
                if ch != "":
                    bx0, by0, bx1, by1 = self.cell_bbox(r, c)
                    if self.locked[r][c]:
                        fill = "#000000"  # forced black for givens
                    else:
                        fill = "red" if self.num_color[r][c] == 1 else "#000000"
                    self.canvas.create_text((bx0 + bx1)/2, (by0 + by1)/2, text=ch, fill=fill, font=("Helvetica", font_size, "bold"))

        # selection highlight
        sr, sc = self.selected
        sx0, sy0, sx1, sy1 = self.cell_bbox(sr, sc)
        pad = max(2, int(self.cell * 0.06))
        self.canvas.create_rectangle(
            sx0+pad, sy0+pad, sx1-pad, sy1-pad,
            outline="#0077ff", width=2, dash=(4, 2)
        )

    # ---------- Pentomino placement ----------
    def place_random_pentominoes(self):
        """
        Randomly place pentominoes I, N, Z, U, X, V (5 adjacent cells each)
        on the 9x9 grid such that:
          - I has at least one cell in row 0
          - N has at least one cell in row 5
          - Z has at least one cell in row 8
          - U has at least one cell in row 0
          - X has at least one cell in row 3
          - V has at least one cell in row 8
        Uses background colors only; no changes to digits/sides.
        Clears all backgrounds first.
        Additionally enforces: every 2x2 region of the grid must contain at least one white cell.
        """
        shapes = ["I", "N", "Z", "U", "X", "V"]
        row_target = {"I": 0, "N": 5, "Z": 8, "U": 0, "X": 3, "V": 8}

        # Clear all backgrounds to white
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                self.colors[r][c] = 0  # White

        # Precompute all orientations for each shape
        all_orients = {name: self._pentomino_orientations(name) for name in shapes}

        # Backtracking with MRV (fewest candidates first), randomized
        occupied: Set[Tuple[int,int]] = set()
        assignment = {}

        random.shuffle(shapes)

        def violates_2x2_all_filled(occ: Set[Tuple[int,int]]) -> bool:
            """Return True if any 2x2 window is fully occupied (no white cell)."""
            for r in range(GRID_SIZE - 1):
                for c in range(GRID_SIZE - 1):
                    w = {(r, c), (r+1, c), (r, c+1), (r+1, c+1)}
                    if w.issubset(occ):
                        return True
            return False

        def gen_candidates(name, occ):
            """Generate all non-overlapping placements for a shape that meet its row constraint and don't immediately violate the 2x2 rule."""
            target = row_target[name]
            placements = []
            for orient in all_orients[name]:
                rows = [r for r, _ in orient]
                cols = [c for _, c in orient]
                h = max(rows) + 1
                w = max(cols) + 1

                possible_trs = set()
                for r0 in rows:
                    tr = target - r0
                    if 0 <= tr <= GRID_SIZE - h:
                        possible_trs.add(tr)
                if not possible_trs:
                    continue

                valid_tcs = range(0, GRID_SIZE - w + 1)

                for tr in possible_trs:
                    for tc in valid_tcs:
                        placed = {(r + tr, c + tc) for (r, c) in orient}
                        if not all((0 <= rr < GRID_SIZE and 0 <= cc < GRID_SIZE) for rr, cc in placed):
                            continue
                        if placed & occ:
                            continue
                        occ2 = occ | placed
                        # Early prune if any 2x2 window becomes fully colored
                        if violates_2x2_all_filled(occ2):
                            continue
                        placements.append(placed)
            random.shuffle(placements)
            return placements

        def choose_next(shapes_left, occ):
            """Pick the next shape using MRV (fewest candidates)."""
            best_shape = None
            best_cands = None
            best_len = None
            for s in shapes_left:
                cands = gen_candidates(s, occ)
                n = len(cands)
                if n == 0:
                    return s, []
                if best_len is None or n < best_len:
                    best_len = n
                    best_shape = s
                    best_cands = cands
                    if n == 1:
                        break
            return best_shape, best_cands

        def backtrack(shapes_left, occ):
            if not shapes_left:
                # Final safety: ensure 2x2 rule holds
                return not violates_2x2_all_filled(occ)
            s, candidates = choose_next(shapes_left, occ)
            if not candidates:
                return False
            for placed in candidates:
                assignment[s] = placed
                occ2 = occ | placed
                rest = [x for x in shapes_left if x != s]
                if backtrack(rest, occ2):
                    return True
                del assignment[s]
            return False

        success = False
        for _ in range(40):  # a few restarts for variety
            assignment.clear()
            occupied.clear()
            random.shuffle(shapes)
            if backtrack(shapes, occupied):
                success = True
                break

        if not success:
            self.bell()
            self.redraw()
            return

        # Color the placed shapes using fixed mapping
        for name, cells in assignment.items():
            col_idx = PENTOMINO_COLORS[name]
            for (r, c) in cells:
                self.colors[r][c] = col_idx

        self.redraw()

    # ---- Pentomino geometry helpers ----
    def _pentomino_orientations(self, name):
        """Return a set of orientations; each orientation is a frozenset of (r,c) with min r=c=0."""
        base = self._pentomino_base(name)
        seen = set()
        for rot in range(4):
            shape = self._normalize(self._rotate(base, rot))
            seen.add(frozenset(shape))
            refl = self._normalize(self._reflect_h(self._rotate(base, rot)))
            seen.add(frozenset(refl))
        return [set(cells) for cells in seen]

    def _pentomino_base(self, name):
        """Base shapes (not normalized after transforms). Coordinates are adjacent 4-neighborhood."""
        if name == "I":
            return {(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)}
        if name == "N":
            return {(0, 0), (1, 0), (1, 1), (2, 1), (3, 1)}
        if name == "Z":
            return {(0, 0), (0, 1), (1, 1), (1, 2), (2, 2)}
        if name == "U":
            return {(0, 0), (0, 2), (1, 0), (1, 1), (1, 2)}
        if name == "X":
            return {(0, 1), (1, 0), (1, 1), (1, 2), (2, 1)}
        if name == "V":
            return {(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)}
        raise ValueError(f"Unknown pentomino: {name}")

    def _rotate(self, cells, times90):
        """Rotate 0/90/180/270 degrees around origin."""
        times90 %= 4
        pts = set(cells)
        for _ in range(times90):
            pts = {(c, -r) for (r, c) in pts}
        return pts

    def _reflect_h(self, cells):
        """Reflect across vertical axis (y-axis): (r,c)->(r,-c)."""
        return {(r, -c) for (r, c) in cells}

    def _normalize(self, cells):
        """Shift so min r = 0 and min c = 0."""
        min_r = min(r for r, _ in cells)
        min_c = min(c for _, c in cells)
        return {(r - min_r, c - min_c) for (r, c) in cells}


if __name__ == "__main__":
    app = GridEditor()
    app.mainloop()
