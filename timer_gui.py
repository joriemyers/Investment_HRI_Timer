"""
Investment_HRI_Timer
====================
Participant GUI with LSL bridge + Latin Square counterbalancing.

Participants : 101–110
Trials       : A (15 min), B (30 min), C (15 min), D (30 min)
Flow         : Login → Baseline (2 min) → Trial 1 → Trial 2 → Trial 3 → Trial 4 → Done

Latin Square:
  101, 105, 109 → A B D C
  102, 106, 110 → B C A D
  103, 107       → C D B A
  104, 108       → D A C B

Dependencies:
  pip install pylsl
"""

import tkinter as tk
import threading
import time

try:
    from pylsl import StreamInfo, StreamOutlet
    LSL_AVAILABLE = True
except ImportError:
    LSL_AVAILABLE = False
    print("[WARNING] pylsl not found — install with: pip install pylsl")


# ── Latin Square ───────────────────────────────────────────────────────────────

LATIN_SQUARE = [
    ["A", "B", "D", "C"],
    ["B", "C", "A", "D"],
    ["C", "D", "B", "A"],
    ["D", "A", "C", "B"],
]

TRIAL_DURATIONS = {"A": 900, "B": 1800, "C": 900, "D": 1800}
VALID_IDS = list(range(101, 111))

def get_trial_order(pid: int) -> list:
    row = (pid - 101) % len(LATIN_SQUARE)
    return LATIN_SQUARE[row]


# ── LSL ────────────────────────────────────────────────────────────────────────

def create_lsl_outlet():
    if not LSL_AVAILABLE:
        return None
    info = StreamInfo("HRI_Timer_Events", "Markers", 1, 0, "string", "InvestmentHRI_001")
    outlet = StreamOutlet(info)
    print("[LSL] Stream 'HRI_Timer_Events' is live.")
    return outlet

def push_marker(outlet, marker: str):
    if outlet:
        outlet.push_sample([marker])
    print(f"[LSL] {marker}")


# ── Palette ────────────────────────────────────────────────────────────────────

BG      = "#1e1e2e"
PANEL   = "#2a2a3e"
ACCENT  = "#89b4fa"
GREEN   = "#a6e3a1"
RED     = "#f38ba8"
YELLOW  = "#f9e2af"
PURPLE  = "#cba6f7"
SUBTEXT = "#7f849c"
WHITE   = "#ffffff"

TRIAL_COLORS = {"A": ACCENT, "B": GREEN, "C": YELLOW, "D": PURPLE}


# ── Helpers ────────────────────────────────────────────────────────────────────

def fmt(seconds: int) -> str:
    m, s = divmod(max(0, seconds), 60)
    return f"{m:02d}:{s:02d}"

def clear(frame):
    for w in frame.winfo_children():
        w.destroy()


# ── App ────────────────────────────────────────────────────────────────────────

class HRITimerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Investment HRI — Participant Timer")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.geometry("520x580")

        self.outlet      = create_lsl_outlet()
        self.pid         = None
        self.trial_order = []
        self.trial_index = -1

        self.container = tk.Frame(self, bg=BG)
        self.container.pack(expand=True, fill="both", padx=30, pady=20)

        self._show_login()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Screen 1: Login ────────────────────────────────────────────────────────

    def _show_login(self):
        clear(self.container)

        tk.Label(self.container, text="Investment HRI",
                 fg=ACCENT, bg=BG, font=("Segoe UI", 22, "bold")).pack(pady=(10, 2))
        tk.Label(self.container, text="Participant Timer System",
                 fg=SUBTEXT, bg=BG, font=("Segoe UI", 11)).pack()

        tk.Frame(self.container, bg=SUBTEXT, height=1).pack(fill="x", pady=18)

        tk.Label(self.container, text="Enter Participant ID",
                 fg=WHITE, bg=BG, font=("Segoe UI", 13, "bold")).pack(pady=(0, 4))
        tk.Label(self.container, text="(101 – 110)",
                 fg=SUBTEXT, bg=BG, font=("Segoe UI", 10)).pack()

        self.id_var = tk.StringVar()
        entry = tk.Entry(self.container, textvariable=self.id_var,
                         font=("Courier New", 30, "bold"), width=6,
                         justify="center", bg=PANEL, fg=WHITE,
                         insertbackground=WHITE, relief="flat", bd=0,
                         highlightthickness=2, highlightbackground=ACCENT)
        entry.pack(pady=14, ipady=10)
        entry.focus()
        entry.bind("<Return>", lambda e: self._login())

        self.error_var = tk.StringVar()
        tk.Label(self.container, textvariable=self.error_var,
                 fg=RED, bg=BG, font=("Segoe UI", 10)).pack(pady=2)

        lsl_color = GREEN if LSL_AVAILABLE else RED
        lsl_text  = "● LSL Active" if LSL_AVAILABLE else "● LSL Offline"
        tk.Label(self.container, text=lsl_text,
                 fg=lsl_color, bg=BG, font=("Segoe UI", 10)).pack(pady=(4, 14))

        self._btn(self.container, "Begin Session  ▶", ACCENT,
                  self._login).pack(ipadx=14, ipady=7)

    def _login(self):
        try:
            pid = int(self.id_var.get().strip())
        except ValueError:
            self.error_var.set("Please enter a number between 101 and 110.")
            return
        if pid not in VALID_IDS:
            self.error_var.set(f"{pid} is not valid. Use 101–110.")
            return
        self.pid         = pid
        self.trial_order = get_trial_order(pid)
        self.trial_index = -1
        push_marker(self.outlet, f"session_start_P{pid}")
        self._show_baseline()

    # ── Screen 2: Baseline ─────────────────────────────────────────────────────

    def _show_baseline(self):
        self._show_timer_screen(
            title      = "Baseline",
            subtitle   = f"Participant {self.pid}  •  Step 1 of 5",
            info       = "2-minute baseline period",
            duration   = 120,
            color      = "#89dceb",
            marker_pre = f"P{self.pid}_baseline",
            next_label = "Next: Trial 1  ▶",
            next_cmd   = self._advance,
        )

    # ── Screens 3–6: Trials ────────────────────────────────────────────────────

    def _advance(self):
        self.trial_index += 1
        if self.trial_index >= len(self.trial_order):
            self._show_done()
            return

        t     = self.trial_order[self.trial_index]
        step  = self.trial_index + 2
        mins  = TRIAL_DURATIONS[t] // 60
        is_last = self.trial_index == len(self.trial_order) - 1

        self._show_timer_screen(
            title      = f"Trial {self.trial_index + 1}  —  Condition {t}",
            subtitle   = f"Participant {self.pid}  •  Step {step} of 5",
            info       = f"Condition {t}  |  {mins}-minute task",
            duration   = TRIAL_DURATIONS[t],
            color      = TRIAL_COLORS[t],
            marker_pre = f"P{self.pid}_trial{self.trial_index + 1}_{t}",
            next_label = "Finish Session  ✔" if is_last else f"Next: Trial {self.trial_index + 2}  ▶",
            next_cmd   = self._advance,
        )

    # ── Generic timer screen ───────────────────────────────────────────────────

    def _show_timer_screen(self, title, subtitle, info, duration,
                           color, marker_pre, next_label, next_cmd):
        clear(self.container)

        self._running    = False
        self._elapsed    = 0
        self._duration   = duration
        self._stop_event = threading.Event()
        self._marker_pre = marker_pre

        # Header
        tk.Label(self.container, text=title,
                 fg=color, bg=BG, font=("Segoe UI", 18, "bold")).pack(pady=(4, 0))
        tk.Label(self.container, text=subtitle,
                 fg=SUBTEXT, bg=BG, font=("Segoe UI", 10)).pack()
        tk.Label(self.container, text=info,
                 fg=WHITE, bg=BG, font=("Segoe UI", 10, "italic")).pack(pady=(2, 4))

        tk.Frame(self.container, bg=SUBTEXT, height=1).pack(fill="x", pady=8)

        # Clock
        self._clock_var = tk.StringVar(value=fmt(duration))
        tk.Label(self.container, textvariable=self._clock_var,
                 fg=WHITE, bg=BG, font=("Courier New", 58, "bold")).pack(pady=(8, 4))

        # Progress bar
        self._prog = tk.Canvas(self.container, height=10, bg=BG, highlightthickness=0)
        self._prog.pack(fill="x", padx=10, pady=(0, 4))
        self._prog.update_idletasks()
        pw = self._prog.winfo_width() or 460
        self._prog.create_rectangle(0, 0, pw, 10, fill=PANEL, outline="", tags="bg")
        self._prog.create_rectangle(0, 0, 0, 10, fill=color, outline="", tags="bar")

        # Status
        self._status_var = tk.StringVar(value="Press Start when ready.")
        tk.Label(self.container, textvariable=self._status_var,
                 fg=SUBTEXT, bg=BG, font=("Segoe UI", 10, "italic")).pack(pady=(2, 8))

        # Timer buttons
        btn_row = tk.Frame(self.container, bg=BG)
        btn_row.pack()

        self._start_btn = self._btn(btn_row, "▶  Start", color, self._start_timer)
        self._start_btn.grid(row=0, column=0, padx=8)

        self._stop_btn = self._btn(btn_row, "■  Stop", RED, self._stop_timer, state="disabled")
        self._stop_btn.grid(row=0, column=1, padx=8)

        self._reset_btn = self._btn(btn_row, "↺  Reset", SUBTEXT, self._reset_timer)
        self._reset_btn.grid(row=0, column=2, padx=8)

        tk.Frame(self.container, bg=SUBTEXT, height=1).pack(fill="x", pady=12)

        # Next button — locked until timer finishes or is stopped
        self._next_btn = self._btn(self.container, next_label, PANEL,
                                   next_cmd, state="disabled", fg=SUBTEXT)
        self._next_btn.pack(ipadx=14, ipady=7)

    # ── Timer logic ────────────────────────────────────────────────────────────

    def _start_timer(self):
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        push_marker(self.outlet, f"{self._marker_pre}_start")
        self._start_btn.config(state="disabled")
        self._stop_btn.config(state="normal")
        self._status_var.set("Running…")
        threading.Thread(target=self._run_timer, daemon=True).start()

    def _stop_timer(self):
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        push_marker(self.outlet, f"{self._marker_pre}_stop")
        self._start_btn.config(state="normal")
        self._stop_btn.config(state="disabled")
        self._status_var.set(f"Stopped at {fmt(self._elapsed)}")
        self._unlock_next()

    def _reset_timer(self):
        if self._running:
            self._stop_timer()
        self._elapsed = 0
        self._clock_var.set(fmt(self._duration))
        self._prog.coords("bar", 0, 0, 0, 10)
        self._status_var.set("Press Start when ready.")
        self._start_btn.config(state="normal")
        self._stop_btn.config(state="disabled")
        self._next_btn.config(state="disabled", bg=PANEL, fg=SUBTEXT)

    def _run_timer(self):
        start = time.monotonic()
        base  = self._elapsed
        while not self._stop_event.is_set():
            now           = time.monotonic()
            self._elapsed = min(int(now - start) + base, self._duration)
            remaining     = self._duration - self._elapsed
            self.after(0, self._tick, remaining)
            if remaining <= 0:
                self.after(0, self._on_complete)
                break
            nxt = start + (self._elapsed - base + 1)
            gap = nxt - time.monotonic()
            if gap > 0:
                self._stop_event.wait(timeout=gap)

    def _tick(self, remaining):
        self._clock_var.set(fmt(remaining))
        pct = self._elapsed / self._duration
        w   = int((self._prog.winfo_width() or 460) * pct)
        self._prog.coords("bar", 0, 0, w, 10)

    def _on_complete(self):
        self._running = False
        push_marker(self.outlet, f"{self._marker_pre}_complete")
        self._clock_var.set("00:00")
        self._prog.coords("bar", 0, 0, self._prog.winfo_width() or 460, 10)
        self._status_var.set("✔  Timer complete!")
        self._start_btn.config(state="disabled")
        self._stop_btn.config(state="disabled")
        self._unlock_next()

    def _unlock_next(self):
        self._next_btn.config(state="normal", bg=GREEN, fg=BG,
                               activebackground=WHITE, activeforeground=BG)

    # ── Screen 7: Done ─────────────────────────────────────────────────────────

    def _show_done(self):
        clear(self.container)
        push_marker(self.outlet, f"session_end_P{self.pid}")

        tk.Label(self.container, text="Session Complete  ✔",
                 fg=GREEN, bg=BG, font=("Segoe UI", 20, "bold")).pack(pady=(20, 4))
        tk.Label(self.container, text=f"Participant {self.pid}",
                 fg=SUBTEXT, bg=BG, font=("Segoe UI", 12)).pack()

        tk.Frame(self.container, bg=SUBTEXT, height=1).pack(fill="x", pady=16)

        tk.Label(self.container, text="Trials completed in this order:",
                 fg=WHITE, bg=BG, font=("Segoe UI", 11, "bold")).pack(pady=(0, 6))

        for i, t in enumerate(self.trial_order):
            mins = TRIAL_DURATIONS[t] // 60
            tk.Label(self.container,
                     text=f"  Trial {i+1}  —  Condition {t}  ({mins} min)",
                     fg=TRIAL_COLORS[t], bg=BG,
                     font=("Segoe UI", 12)).pack(pady=3)

        tk.Frame(self.container, bg=SUBTEXT, height=1).pack(fill="x", pady=16)

        self._btn(self.container, "Start New Participant  ▶", ACCENT,
                  self._show_login).pack(ipadx=14, ipady=7)

    # ── Utility ────────────────────────────────────────────────────────────────

    def _btn(self, parent, text, bg, cmd, state="normal", fg=BG):
        return tk.Button(parent, text=text, command=cmd,
                         bg=bg, fg=fg, font=("Segoe UI", 11, "bold"),
                         relief="flat", cursor="hand2", state=state,
                         activebackground=WHITE, activeforeground=BG,
                         disabledforeground=SUBTEXT)

    def _on_close(self):
        push_marker(self.outlet, "app_closed")
        self.destroy()


if __name__ == "__main__":
    app = HRITimerApp()
    app.mainloop()
