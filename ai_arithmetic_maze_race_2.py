"""
AI Arithmetic Maze Race — A* (Click-to-Move Edition)
=====================================================
RULES
-----
* Both Player (blue) and AI (red) start at same cell (top-left).
* A question appears.  Solve it correctly → your token GLOWS and you
  may click any highlighted neighbour cell to move ONE step.
* After your move (or after the timer expires) the AI takes ONE step
  along its A* path.  Turns alternate 1-for-1.
* Wrong answer → new question immediately; AI does NOT move.
* First to reach the GREEN GOAL wins.

MOVEMENT
--------
* Click-to-move — no arrow keys needed (works on every OS/keyboard).
* Valid neighbour cells are highlighted in YELLOW when it is your turn.
* You have 12 seconds to click a cell; otherwise the AI moves and a
  new question appears.
"""

import tkinter as tk
from tkinter import messagebox
import heapq, time, os
from typing import List, Tuple, Dict, Optional, Set, Generator

# ── Config ────────────────────────────────────────────────────────────────────
GRID_ROWS    = 7
GRID_COLS    = 7
# Reduced cell size to make the window smaller on screen
CELL_SIZE    = 50
MOVE_TIME_S  = 12        # seconds player has to click after correct answer
SEARCH_STEP_MS = 40      # A* animation speed

START = (0, 0)
GOAL  = (6, 6)
WALL_PROB = 0.22

Cell = Tuple[int, int]

DIRS = [(-1,0),(1,0),(0,-1),(0,1)]

def manhattan(a: Cell, b: Cell) -> int:
    return abs(a[0]-b[0]) + abs(a[1]-b[1])


# Lightweight, secure helpers to avoid depending on a possibly-shadowed
# `random` symbol in the environment (some systems have a conflicting
# module named `random` that makes `random.random()` fail). We use
# `secrets` which is available in the stdlib and suitable for game
# randomness here.
def _rand_real() -> float:
    # 53 bits of randomness -> float in [0,1)
    r = int.from_bytes(os.urandom(7), "big") >> 1
    return r / (1 << 53)

def _rand_int(a: int, b: int) -> int:
    # simple modulo reduction using 64 bits (sufficient for game use)
    width = b - a + 1
    r = int.from_bytes(os.urandom(8), "big")
    return a + (r % width)

def _rand_choice(seq):
    return seq[_rand_int(0, len(seq)-1)]


# ── Main class ────────────────────────────────────────────────────────────────
class MazeRace:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("AI Arithmetic Maze Race — A*")
        self.root.resizable(False, False)

        # ── game state ──
        self.player_pos: Cell = START
        self.ai_pos:     Cell = START
        self.maze:  List[List[int]] = []
        self.game_over  = False
        self.started    = False
        self.can_move   = False      # True after correct answer
        self.move_deadline = 0.0

        # ── stats ──
        self.player_score    = 0
        self.player_moves    = 0
        self.ai_moves        = 0
        self.correct_answers = 0
        self.wrong_answers   = 0
        self.total_attempts  = 0
        self.start_time: Optional[float] = None
        self.player_win_time: Optional[float] = None
        self.ai_win_time:     Optional[float] = None

        # ── A* ──
        self.ai_path: List[Cell] = []
        self.astar_gen: Optional[Generator] = None
        self.astar_running = False
        self._astar_vis: Dict = {}

        # ── timer job ──
        self._timer_job: Optional[str] = None
        self._ai_pending = False     # AI is waiting for its turn

        self.current_question: Tuple = (1,"+",1,2)

        self._build_ui()
        self.generate_maze()
        self.draw()

    # ══════════════════════════════════════════════════════════════════════════
    # UI
    # ══════════════════════════════════════════════════════════════════════════
    def _build_ui(self):
        W = GRID_COLS * CELL_SIZE
        H = GRID_ROWS * CELL_SIZE

        # canvas
        self.canvas = tk.Canvas(self.root, width=W, height=H,
                                bg="#e8e8e8", highlightthickness=0,
                                cursor="hand2")
        self.canvas.grid(row=0, column=0, columnspan=5, padx=6, pady=6)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        # question row
        tk.Label(self.root, text="Question:", font=("Arial",13)
                 ).grid(row=1, column=0, sticky="w", padx=8, pady=4)
        self.q_label = tk.Label(self.root, text="",
                                font=("Arial",15,"bold"), width=14, anchor="w")
        self.q_label.grid(row=1, column=1, sticky="w")

        self.entry = tk.Entry(self.root, font=("Arial",14), width=7)
        self.entry.grid(row=1, column=2, padx=4)
        self.entry.bind("<Return>", lambda e: self._submit())

        self.submit_btn = tk.Button(self.root, text="Submit ↵",
                                    font=("Arial",12), command=self._submit,
                                    state=tk.DISABLED, bg="#2196F3", fg="white")
        self.submit_btn.grid(row=1, column=3, padx=6)

        # status
        self.status = tk.Label(self.root, text="Press START to begin",
                               font=("Arial",11), fg="#1565C0", anchor="w")
        self.status.grid(row=2, column=0, columnspan=3, sticky="w", padx=8)
        self.score_lbl = tk.Label(self.root, text="Score: 0",
                                  font=("Arial",11,"bold"))
        self.score_lbl.grid(row=2, column=3, columnspan=2, sticky="e", padx=8)

        # timer bar
        self.timer_canvas = tk.Canvas(self.root, width=W, height=14,
                                      bg="#dddddd", highlightthickness=0)
        self.timer_canvas.grid(row=3, column=0, columnspan=5, padx=6)

        # start button
        self.start_btn = tk.Button(self.root, text="▶  START GAME",
                                   font=("Arial",12,"bold"),
                                   bg="#4CAF50", fg="white",
                                   command=self._start)
        self.start_btn.grid(row=4, column=0, columnspan=5, pady=10, ipadx=20)

        # legend
        tk.Label(self.root,
                 text="🔵 You   🔴 AI   🟩 GOAL   🟡 Click yellow cell to move",
                 font=("Arial",10), fg="#555"
                 ).grid(row=5, column=0, columnspan=5, pady=(0,6))

    # ══════════════════════════════════════════════════════════════════════════
    # DRAWING
    # ══════════════════════════════════════════════════════════════════════════
    def draw(self):
        self.canvas.delete("all")

        valid_moves: Set[Cell] = set()
        if self.can_move and not self.game_over:
            valid_moves = self._valid_neighbours(self.player_pos)

        for r in range(GRID_ROWS):
            for c in range(GRID_COLS):
                x1,y1 = c*CELL_SIZE, r*CELL_SIZE
                x2,y2 = x1+CELL_SIZE, y1+CELL_SIZE
                if self.maze[r][c] == 1:
                    fill = "#1a1a1a"
                elif (r,c) == GOAL:
                    fill = "#2e7d32"
                elif (r,c) in valid_moves:
                    fill = "#ffe066"          # bright yellow = clickable
                elif self.astar_running and self._astar_vis:
                    info = self._astar_vis
                    if (r,c) in info.get("closed",set()):
                        fill = "#c8dfff"
                    elif (r,c) in info.get("open",set()):
                        fill = "#a8efff"
                    else:
                        fill = "#f5f5e8"
                else:
                    fill = "#f5f5e8"
                self.canvas.create_rectangle(x1,y1,x2,y2,
                                             fill=fill, outline="#bbb")

        # A* current node highlight
        if self.astar_running and self._astar_vis:
            cur = self._astar_vis.get("current")
            if cur and self.maze[cur[0]][cur[1]] == 0:
                self._fill(cur[0],cur[1],"#70b8ff")

        # AI planned path (orange, behind agents)
        for (r,c) in self.ai_path[1:]:
            self._fill(r,c,"#ffd98a")

        # GOAL label
        gr,gc = GOAL
        self.canvas.create_text(
            gc*CELL_SIZE+CELL_SIZE//2, gr*CELL_SIZE+CELL_SIZE//2,
            text="GOAL", fill="white", font=("Arial",11,"bold"))

        # agents
        self._draw_agent(self.ai_pos,     "#C62828", "AI")
        self._draw_agent(self.player_pos, "#1565C0", "YOU")

        # glow ring when player can move
        if self.can_move and not self.game_over:
            r,c = self.player_pos
            cx = c*CELL_SIZE+CELL_SIZE//2
            cy = r*CELL_SIZE+CELL_SIZE//2
            rad = CELL_SIZE//3 + 6
            self.canvas.create_oval(cx-rad,cy-rad,cx+rad,cy+rad,
                                    outline="#FFD700", width=4)

    def _fill(self,r,c,color):
        p=3
        self.canvas.create_rectangle(
            c*CELL_SIZE+p, r*CELL_SIZE+p,
            (c+1)*CELL_SIZE-p, (r+1)*CELL_SIZE-p,
            fill=color, outline="")

    def _draw_agent(self, pos, fill, label):
        r,c = pos
        cx = c*CELL_SIZE+CELL_SIZE//2
        cy = r*CELL_SIZE+CELL_SIZE//2
        rad = CELL_SIZE//3
        self.canvas.create_oval(cx-rad,cy-rad,cx+rad,cy+rad,
                                fill=fill, outline="white", width=2)
        self.canvas.create_text(cx,cy,text=label,fill="white",
                                font=("Arial",8,"bold"))

    def _draw_timer_bar(self, fraction: float):
        W = GRID_COLS * CELL_SIZE
        self.timer_canvas.delete("all")
        if fraction > 0:
            color = "#4CAF50" if fraction > 0.4 else (
                    "#FF9800" if fraction > 0.2 else "#f44336")
            self.timer_canvas.create_rectangle(
                0,0, int(W*fraction),14, fill=color, outline="")

    # ══════════════════════════════════════════════════════════════════════════
    # CLICK-TO-MOVE
    # ══════════════════════════════════════════════════════════════════════════
    def _on_canvas_click(self, event):
        if not self.started or self.game_over or not self.can_move:
            return
        c = event.x // CELL_SIZE
        r = event.y // CELL_SIZE
        clicked: Cell = (r, c)

        if clicked not in self._valid_neighbours(self.player_pos):
            self.status.config(text="⚠️  Click a yellow highlighted cell!")
            return

        self._do_player_move(clicked)

    def _valid_neighbours(self, pos: Cell) -> Set[Cell]:
        r,c = pos
        result = set()
        for dr,dc in DIRS:
            nr,nc = r+dr,c+dc
            if 0<=nr<GRID_ROWS and 0<=nc<GRID_COLS and self.maze[nr][nc]==0:
                result.add((nr,nc))
        return result

    def _do_player_move(self, dest: Cell):
        self._cancel_timer()
        self.can_move     = False
        self.player_pos   = dest
        self.player_moves += 1
        self._draw_timer_bar(0)
        self.draw()

        if self._check_winner():
            return

        # AI takes its ONE step after the player moved
        self._ai_take_step()

        if not self.game_over:
            self._new_question()

    # ══════════════════════════════════════════════════════════════════════════
    # QUESTIONS & SUBMIT
    # ══════════════════════════════════════════════════════════════════════════
    def _new_question(self):
        a  = _rand_int(1,12)
        b  = _rand_int(1,12)
        op = _rand_choice(["+","-","*"])
        ans = a+b if op=="+" else (a-b if op=="-" else a*b)
        self.current_question = (a,op,b,ans)
        self.q_label.config(text=f"{a} {op} {b} = ?")
        self.entry.delete(0,tk.END)
        self.entry.focus_set()
        self.status.config(text="🤔 Solve the question to earn a move!")
        self.can_move = False
        self._draw_timer_bar(0)
        self.draw()

    def _submit(self):
        if self.game_over or not self.started: return
        raw = self.entry.get().strip()
        try: val = int(raw)
        except ValueError:
            messagebox.showerror("Invalid","Enter a whole number."); return

        _,_,_,ans = self.current_question
        self.total_attempts += 1
        self.entry.delete(0,tk.END)

        if val == ans:
            self.correct_answers += 1
            self.player_score    += 1
            self.score_lbl.config(text=f"Score: {self.player_score}")
            self.can_move = True
            self.status.config(
                text="✅ Correct!  Click a YELLOW cell to move  ⬆⬇⬅➡")
            self._start_move_timer()
            self.draw()   # show yellow neighbours + glow
        else:
            self.wrong_answers += 1
            self.status.config(text="❌ Wrong!  New question coming…")
            # Wrong answer: AI does NOT move, just get new question
            self._new_question()

    # ══════════════════════════════════════════════════════════════════════════
    # MOVE TIMER
    # ══════════════════════════════════════════════════════════════════════════
    def _start_move_timer(self):
        self._cancel_timer()
        self.move_deadline = time.time() + MOVE_TIME_S

        def tick():
            if self.game_over or not self.started or not self.can_move:
                self._draw_timer_bar(0); return
            remaining = self.move_deadline - time.time()
            frac = max(0.0, remaining / MOVE_TIME_S)
            self._draw_timer_bar(frac)
            if remaining <= 0:
                self._time_expired()
            else:
                self._timer_job = self.root.after(100, tick)
        tick()

    def _cancel_timer(self):
        if self._timer_job:
            try: self.root.after_cancel(self._timer_job)
            except: pass
            self._timer_job = None

    def _time_expired(self):
        self._cancel_timer()
        if self.game_over or not self.started: return
        self.can_move = False
        self._draw_timer_bar(0)
        self.status.config(text="⏰ Time's up!  AI moves, new question for you.")
        # Time expired: AI gets its step, player gets new question
        self._ai_take_step()
        if not self.game_over:
            self._new_question()

    # ══════════════════════════════════════════════════════════════════════════
    # AI — one step per player turn
    # ══════════════════════════════════════════════════════════════════════════
    def _ai_take_step(self):
        """Move the AI exactly ONE step along its A* path."""
        if self.game_over: return

        # Recompute path if stale
        if not self.ai_path or self.ai_path[0] != self.ai_pos:
            self.ai_path = self._astar(self.ai_pos, GOAL)

        if len(self.ai_path) > 1:
            self.ai_pos  = self.ai_path[1]
            self.ai_moves += 1
            self.ai_path   = self.ai_path[1:]
            self.draw()
            self._check_winner()
        else:
            self.status.config(text="🤖 AI has no path!")

        # Re-run animated A* so search vis stays fresh
        self._run_astar_animated()

    # ══════════════════════════════════════════════════════════════════════════
    # A* ALGORITHM
    # ══════════════════════════════════════════════════════════════════════════
    def _astar(self, start, goal) -> List[Cell]:
        heap = [(manhattan(start,goal),0,start)]
        parent: Dict[Cell,Optional[Cell]] = {start:None}
        g: Dict[Cell,int] = {start:0}
        closed: Set[Cell] = set()
        while heap:
            f,cost,cur = heapq.heappop(heap)
            if cur in closed: continue
            if cur == goal:
                path,node = [],cur
                while node is not None: path.append(node); node=parent[node]
                return path[::-1]
            closed.add(cur)
            for dr,dc in DIRS:
                nr,nc = cur[0]+dr,cur[1]+dc
                nb = (nr,nc)
                if 0<=nr<GRID_ROWS and 0<=nc<GRID_COLS and self.maze[nr][nc]==0:
                    ng = cost+1
                    if ng < g.get(nb,10**9):
                        parent[nb]=cur; g[nb]=ng
                        heapq.heappush(heap,(ng+manhattan(nb,goal),ng,nb))
        return []

    def _astar_generator(self, start, goal):
        heap = [(manhattan(start,goal),0,start)]
        parent: Dict[Cell,Optional[Cell]] = {start:None}
        g: Dict[Cell,int] = {start:0}
        closed: Set[Cell] = set()
        while heap:
            openset = {item[2] for item in heap}
            yield {"open":set(openset),"closed":set(closed),"current":None}
            f,cost,cur = heapq.heappop(heap)
            if cur in closed: continue
            yield {"open":set(openset),"closed":set(closed),"current":cur}
            if cur == goal:
                path,node = [],cur
                while node is not None: path.append(node); node=parent.get(node)
                self.ai_path = path[::-1]; return
            closed.add(cur)
            for dr,dc in DIRS:
                nr,nc = cur[0]+dr,cur[1]+dc
                nb=(nr,nc)
                if 0<=nr<GRID_ROWS and 0<=nc<GRID_COLS and self.maze[nr][nc]==0:
                    ng=cost+1
                    if nb not in closed and ng<g.get(nb,10**9):
                        parent[nb]=cur; g[nb]=ng
                        heapq.heappush(heap,(ng+manhattan(nb,goal),ng,nb))
        self.ai_path = []

    def _run_astar_animated(self):
        if self.astar_running: return
        self.astar_gen     = self._astar_generator(self.ai_pos, GOAL)
        self.astar_running = True
        self._astar_vis    = {}
        self._astar_step()

    def _astar_step(self):
        if not self.started: self.astar_running=False; return
        try:
            self._astar_vis = next(self.astar_gen)
            self.draw()
            self.root.after(SEARCH_STEP_MS, self._astar_step)
        except StopIteration:
            self.astar_running = False
            self.astar_gen     = None
            self._astar_vis    = {}
            self.draw()

    # ══════════════════════════════════════════════════════════════════════════
    # MAZE GENERATION
    # ══════════════════════════════════════════════════════════════════════════
    def generate_maze(self):
        while True:
            grid = [[0 if _rand_real()>WALL_PROB else 1
                     for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]
            grid[START[0]][START[1]] = 0
            grid[GOAL[0]][GOAL[1]]   = 0
            # open neighbours of start so player always has a first move
            for dr,dc in DIRS:
                nr,nc = START[0]+dr,START[1]+dc
                if 0<=nr<GRID_ROWS and 0<=nc<GRID_COLS:
                    grid[nr][nc] = 0
            self.maze = grid
            if self._astar(START,GOAL):
                self.player_pos = START
                self.ai_pos     = START
                self.ai_path    = self._astar(START,GOAL)
                return

    # ══════════════════════════════════════════════════════════════════════════
    # WIN CHECK
    # ══════════════════════════════════════════════════════════════════════════
    def _check_winner(self) -> bool:
        if self.player_pos == GOAL and not self.game_over:
            self.player_win_time = time.time()
            self.game_over = True
            self._end("player"); return True
        if self.ai_pos == GOAL and not self.game_over:
            self.ai_win_time = time.time()
            self.game_over = True
            self._end("ai"); return True
        return False

    def _end(self, winner):
        self.started = False
        self._cancel_timer()

        pt = (self.player_win_time - self.start_time
              if self.player_win_time and self.start_time else None)
        at = (self.ai_win_time - self.start_time
              if self.ai_win_time  and self.start_time else None)

        dlg = tk.Toplevel(self.root)
        dlg.title("Challenge Complete!")
        dlg.resizable(False,False)

        msg  = "🎉  YOU WIN!" if winner=="player" else "🤖  AI WINS!"
        col  = "#2e7d32"     if winner=="player" else "#c62828"
        tk.Label(dlg, text="🏁  Challenge Complete!",
                 font=("Arial",18,"bold")).pack(pady=10)
        tk.Label(dlg, text=msg,
                 font=("Arial",15,"bold"), fg=col).pack(pady=4)

        frame = tk.Frame(dlg); frame.pack(padx=24, pady=8)
        stats = [
            ("Your moves",     self.player_moves,   "AI moves",      self.ai_moves),
            ("Correct answers",self.correct_answers, "Wrong answers", self.wrong_answers),
            ("Total attempts", self.total_attempts,  "",              ""),
        ]
        if pt: stats.append(("Your time", f"{pt:.1f}s",
                              "AI time",   f"{at:.1f}s" if at else "—"))
        for i,(la,va,lb,vb) in enumerate(stats):
            tk.Label(frame,text=f"{la}: {va}",font=("Arial",12),anchor="w"
                     ).grid(row=i,column=0,sticky="w",padx=10,pady=3)
            if lb:
                tk.Label(frame,text=f"{lb}: {vb}",font=("Arial",12),anchor="e"
                         ).grid(row=i,column=1,sticky="e",padx=10)

        bf = tk.Frame(dlg); bf.pack(pady=14)
        tk.Button(bf, text="Play Again", width=13,
                  command=lambda:(dlg.destroy(),self._reset())
                  ).pack(side="left",padx=8)
        tk.Button(bf, text="Quit", width=13,
                  command=self.root.destroy).pack(side="left",padx=8)

        dlg.transient(self.root); dlg.grab_set()
        self.root.wait_window(dlg)

    # ══════════════════════════════════════════════════════════════════════════
    # LIFECYCLE
    # ══════════════════════════════════════════════════════════════════════════
    def _start(self):
        if self.started: return
        self.started    = True
        self.game_over  = False
        self.can_move   = False
        self.start_btn.config(state=tk.DISABLED)
        self.submit_btn.config(state=tk.NORMAL)
        self.start_time = time.time()

        self.player_win_time = self.ai_win_time = None
        self.player_score = self.player_moves = self.ai_moves = 0
        self.correct_answers = self.wrong_answers = self.total_attempts = 0
        self.score_lbl.config(text="Score: 0")

        self.generate_maze()
        self._run_astar_animated()
        self._new_question()
        self.entry.focus_set()

    def _reset(self):
        self._cancel_timer()
        self.game_over = self.started = self.can_move = False
        self.astar_running = False; self.astar_gen = None; self._astar_vis = {}
        self.player_score = self.player_moves = self.ai_moves = 0
        self.correct_answers = self.wrong_answers = self.total_attempts = 0
        self.player_win_time = self.ai_win_time = self.start_time = None
        self.score_lbl.config(text="Score: 0")
        self.start_btn.config(state=tk.NORMAL)
        self.submit_btn.config(state=tk.DISABLED)
        self.q_label.config(text="")
        self.status.config(text="Press START to begin")
        self._draw_timer_bar(0)
        self.generate_maze()
        self.draw()


def main():
    root = tk.Tk()
    MazeRace(root)
    root.mainloop()

if __name__ == "__main__":
    main()