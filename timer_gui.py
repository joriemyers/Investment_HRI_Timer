"""
Investment_HRI_Timer
====================
Participant GUI with LSL bridge + Latin Square counterbalancing + Event timing.

Participants : 101–110
Trials       : A (15 min), B (30 min), C (15 min), D (30 min)
Flow         : Login → Baseline (2 min) → Trial 1 → 2 → 3 → 4 → Done

Event buttons (trials only):
  1. Leak Check       — records time from trial Start → this press
  2. Visual Inspection — records time from Leak Check → this press
  3. Stop             — records time from Visual Inspection → this press
                        also stops the trial timer

Done screen shows all event times for every trial.

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
ORANGE  = "#fab387"
SUBTEXT = "#7f849c"
WHITE   = "#ffffff"

TRIAL_COLORS = {"A": ACCENT, "B": GREEN, "C": YELLOW, "D": PURPLE}


# ── Helpers ────────────────────────────────────────────────────────────────────

def fmt(seconds: int) -> str:
    m, s = divmod(max(0, seconds), 60)
    return f"{m:02d}:{s:02d}"

def fmt_f(seconds: float) -> str:
    """Format float seconds as MM:SS.t"""
    m  = int(seconds) // 60
    s  = seconds % 60
    return f"{m:02d}:{s:05.2f}"

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
        self.geometry("540x660")

        self.outlet      = create_lsl_outlet()
        self.pid         = None
        self.trial_order = []
        self.trial_index = -1

        # Stores event times per trial:
        # { trial_num: {"condition": "A",
        #               "leak_check": float,
        #               "visual_inspection": float,
        #               "stop": float } }
        self.event_log = {}

        self.container = tk.Frame(self, bg=BG)
        self.container.pack(expand=True, fill="both", padx=30, pady=20)

        self._show_login()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Screen 1: Login ────────────────────────────────────────────────────────

    def _show_login(self):
        clear(self.container)
        self.event_log = {}

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
        self.event_log   = {}
        push_marker(self.outlet, f"session_start_P{pid}")
        self._show_baseline()

    # ── Screen 2: Baseline (no event buttons) ─────────────────────────────────

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
            show_events= False,
        )

    # ── Screens 3–6: Trials ────────────────────────────────────────────────────

    def _advance(self):
        self.trial_index += 1
        if self.trial_index >= len(self.trial_order):
            self._show_done()
            return

        t       = self.trial_order[self.trial_index]
        step    = self.trial_index + 2
        mins    = TRIAL_DURATIONS[t] // 60
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
            show_events= True,
        )

    # ── Generic timer screen ───────────────────────────────────────────────────

    def _show_timer_screen(self, title, subtitle, info, duration,
                           color, marker_pre, next_label, next_cmd,
                           show_events=False):
        clear(self.container)

        self._running      = False
        self._elapsed      = 0
        self._duration     = duration
        self._stop_event   = threading.Event()
        self._marker_pre   = marker_pre
        self._show_events  = show_events
        self._trial_color  = color

        # Event timing state
        self._timer_start_wall = None   # wall-clock time.monotonic() when timer started
        self._last_event_wall  = None   # wall-clock time of last event press
        self._event_stage      = 0      # 0=none, 1=leak done, 2=visual done, 3=stop done

        # Header
        tk.Label(self.container, text=title,
                 fg=color, bg=BG, font=("Segoe UI", 18, "bold")).pack(pady=(4, 0))
        tk.Label(self.container, text=subtitle,
                 fg=SUBTEXT, bg=BG, font=("Segoe UI", 10)).pack()
        tk.Label(self.container, text=info,
                 fg=WHITE, bg=BG, font=("Segoe UI", 10, "italic")).pack(pady=(2, 4))

        tk.Frame(self.container, bg=SUBTEXT, height=1).pack(fill="x", pady=6)

        # Clock
        self._clock_var = tk.StringVar(value=fmt(duration))
        self._clock_lbl = tk.Label(self.container, textvariable=self._clock_var,
                                   fg=WHITE, bg=BG, font=("Courier New", 52, "bold"))
        self._clock_lbl.pack(pady=(6, 2))
        self._warned = False

        # Progress bar
        self._prog = tk.Canvas(self.container, height=10, bg=BG, highlightthickness=0)
        self._prog.pack(fill="x", padx=10, pady=(0, 4))
        self._prog.update_idletasks()
        pw = self._prog.winfo_width() or 480
        self._prog.create_rectangle(0, 0, pw, 10, fill=PANEL, outline="", tags="bg")
        self._prog.create_rectangle(0, 0, 0, 10, fill=color, outline="", tags="bar")

        # Status
        self._status_var = tk.StringVar(value="Press Start when ready.")
        tk.Label(self.container, textvariable=self._status_var,
                 fg=SUBTEXT, bg=BG, font=("Segoe UI", 10, "italic")).pack(pady=(2, 6))

        # Timer control buttons (Start / Reset only — Stop is an event button for trials)
        btn_row = tk.Frame(self.container, bg=BG)
        btn_row.pack()

        self._start_btn = self._btn(btn_row, "▶  Start", color, self._start_timer)
        self._start_btn.grid(row=0, column=0, padx=8)

        if not show_events:
            # Baseline: show a normal Stop button
            self._stop_btn = self._btn(btn_row, "■  Stop", RED, self._stop_timer, state="disabled")
            self._stop_btn.grid(row=0, column=1, padx=8)

        self._reset_btn = self._btn(btn_row, "↺  Reset", SUBTEXT, self._reset_timer)
        self._reset_btn.grid(row=0, column=2 if not show_events else 1, padx=8)

        # ── Event buttons (trials only) ────────────────────────────────────────
        if show_events:
            tk.Frame(self.container, bg=SUBTEXT, height=1).pack(fill="x", pady=8)
            tk.Label(self.container, text="Event Markers",
                     fg=SUBTEXT, bg=BG, font=("Segoe UI", 10, "bold")).pack()

            ev_frame = tk.Frame(self.container, bg=BG)
            ev_frame.pack(pady=6)

            self._leak_btn = self._btn(ev_frame, "🔍  Leak Check", ORANGE,
                                       self._event_leak, state="disabled")
            self._leak_btn.grid(row=0, column=0, padx=6, ipady=5, ipadx=4)

            self._visual_btn = self._btn(ev_frame, "👁  Visual Inspection", PURPLE,
                                         self._event_visual, state="disabled")
            self._visual_btn.grid(row=0, column=1, padx=6, ipady=5, ipadx=4)

            self._event_stop_btn = self._btn(ev_frame, "■  Stop", RED,
                                             self._event_stop, state="disabled")
            self._event_stop_btn.grid(row=0, column=2, padx=6, ipady=5, ipadx=4)

            # Live event time display
            self._ev_log_var = tk.StringVar(value="")
            tk.Label(self.container, textvariable=self._ev_log_var,
                     fg=GREEN, bg=BG, font=("Courier New", 10),
                     justify="left").pack(pady=(4, 0))

        tk.Frame(self.container, bg=SUBTEXT, height=1).pack(fill="x", pady=8)

        # Next button
        self._next_btn = self._btn(self.container, next_label, PANEL,
                                   next_cmd, state="disabled", fg=SUBTEXT)
        self._next_btn.pack(ipadx=14, ipady=7)

    # ── Event button handlers ──────────────────────────────────────────────────

    def _event_leak(self):
        now      = time.monotonic()
        elapsed  = now - self._timer_start_wall
        self._last_event_wall = now
        self._event_stage = 1

        trial_num = self.trial_index + 1
        cond      = self.trial_order[self.trial_index]
        if trial_num not in self.event_log:
            self.event_log[trial_num] = {"condition": cond}
        self.event_log[trial_num]["leak_check"] = elapsed

        push_marker(self.outlet, f"{self._marker_pre}_leak_check")
        self._leak_btn.config(state="disabled", bg=SUBTEXT)
        self._visual_btn.config(state="normal")
        self._update_ev_display(trial_num)

    def _event_visual(self):
        now      = time.monotonic()
        elapsed  = now - self._last_event_wall
        self._last_event_wall = now
        self._event_stage = 2

        trial_num = self.trial_index + 1
        self.event_log[trial_num]["visual_inspection"] = elapsed

        push_marker(self.outlet, f"{self._marker_pre}_visual_inspection")
        self._visual_btn.config(state="disabled", bg=SUBTEXT)
        self._event_stop_btn.config(state="normal")
        self._update_ev_display(trial_num)

    def _event_stop(self):
        now      = time.monotonic()
        elapsed  = now - self._last_event_wall
        self._event_stage = 3

        trial_num = self.trial_index + 1
        self.event_log[trial_num]["stop"] = elapsed

        push_marker(self.outlet, f"{self._marker_pre}_event_stop")
        self._event_stop_btn.config(state="disabled", bg=SUBTEXT)
        self._update_ev_display(trial_num)

        # Also stop the running timer
        self._stop_timer_silent()
        self._unlock_next()

    def _update_ev_display(self, trial_num):
        log  = self.event_log.get(trial_num, {})
        lines = []
        if "leak_check" in log:
            lines.append(f"  Leak Check:          {fmt_f(log['leak_check'])}  (from Start)")
        if "visual_inspection" in log:
            lines.append(f"  Visual Inspection:   {fmt_f(log['visual_inspection'])}  (from Leak Check)")
        if "stop" in log:
            lines.append(f"  Stop:                {fmt_f(log['stop'])}  (from Visual Inspection)")
        self._ev_log_var.set("\n".join(lines))

    # ── Timer logic ────────────────────────────────────────────────────────────

    def _start_timer(self):
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._timer_start_wall = time.monotonic()
        push_marker(self.outlet, f"{self._marker_pre}_start")
        self._start_btn.config(state="disabled")
        if not self._show_events:
            self._stop_btn.config(state="normal")
        else:
            self._leak_btn.config(state="normal")
        self._status_var.set("Running…")
        threading.Thread(target=self._run_timer, daemon=True).start()

    def _stop_timer(self):
        """Used by baseline Stop button."""
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        push_marker(self.outlet, f"{self._marker_pre}_stop")
        self._start_btn.config(state="normal")
        self._stop_btn.config(state="disabled")
        self._status_var.set(f"Stopped at {fmt(self._elapsed)}")
        self._unlock_next()

    def _stop_timer_silent(self):
        """Stop the timer without touching event buttons (called by event Stop)."""
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        push_marker(self.outlet, f"{self._marker_pre}_stop")
        self._start_btn.config(state="disabled")
        self._status_var.set(f"Stopped at {fmt(self._elapsed)}")

    def _reset_timer(self):
        if self._running:
            if self._show_events:
                self._stop_timer_silent()
            else:
                self._stop_timer()
        self._elapsed          = 0
        self._warned           = False
        self._timer_start_wall = None
        self._last_event_wall  = None
        self._event_stage      = 0
        self._clock_var.set(fmt(self._duration))
        self._clock_lbl.config(fg=WHITE)
        self._prog.coords("bar", 0, 0, 0, 10)
        self._status_var.set("Press Start when ready.")
        self._start_btn.config(state="normal")
        self._next_btn.config(state="disabled", bg=PANEL, fg=SUBTEXT)
        if not self._show_events:
            self._stop_btn.config(state="disabled")
        else:
            self._leak_btn.config(state="disabled", bg=ORANGE, fg=BG)
            self._visual_btn.config(state="disabled", bg=PURPLE, fg=BG)
            self._event_stop_btn.config(state="disabled", bg=RED, fg=BG)
            self._ev_log_var.set("")
            # Clear this trial's event log on reset
            trial_num = self.trial_index + 1
            self.event_log.pop(trial_num, None)

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
        w   = int((self._prog.winfo_width() or 480) * pct)
        self._prog.coords("bar", 0, 0, w, 10)
        if remaining <= 300 and not self._warned:
            self._warned = True
            self._clock_lbl.config(fg=RED)
            push_marker(self.outlet, f"{self._marker_pre}_5min_warning")

    def _on_complete(self):
        self._running = False
        push_marker(self.outlet, f"{self._marker_pre}_complete")
        self._clock_var.set("00:00")
        self._prog.coords("bar", 0, 0, self._prog.winfo_width() or 480, 10)
        self._status_var.set("✔  Timer complete!")
        if not self._show_events:
            self._start_btn.config(state="disabled")
            self._stop_btn.config(state="disabled")
            self._unlock_next()
        else:
            # Timer ran out — disable event buttons that haven't been pressed
            self._status_var.set("⚠  Time's up! Press remaining events or Next.")
            if self._event_stage < 3:
                self._unlock_next()

    def _unlock_next(self):
        self._next_btn.config(state="normal", bg=GREEN, fg=BG,
                               activebackground=WHITE, activeforeground=BG)

    # ── Screen 7: Done ─────────────────────────────────────────────────────────

    def _show_done(self):
        clear(self.container)
        push_marker(self.outlet, f"session_end_P{self.pid}")

        tk.Label(self.container, text="Session Complete  ✔",
                 fg=GREEN, bg=BG, font=("Segoe UI", 20, "bold")).pack(pady=(14, 2))
        tk.Label(self.container, text=f"Participant {self.pid}",
                 fg=SUBTEXT, bg=BG, font=("Segoe UI", 12)).pack()

        tk.Frame(self.container, bg=SUBTEXT, height=1).pack(fill="x", pady=10)

        # Event times summary
        tk.Label(self.container, text="Event Times by Trial",
                 fg=WHITE, bg=BG, font=("Segoe UI", 12, "bold")).pack(pady=(0, 6))

        for i, t in enumerate(self.trial_order):
            trial_num = i + 1
            color     = TRIAL_COLORS[t]
            mins      = TRIAL_DURATIONS[t] // 60
            log       = self.event_log.get(trial_num, {})

            # Trial header
            tk.Label(self.container,
                     text=f"Trial {trial_num}  —  Condition {t}  ({mins} min)",
                     fg=color, bg=BG, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=20)

            rows = [
                ("Leak Check",         log.get("leak_check"),         "from Start"),
                ("Visual Inspection",  log.get("visual_inspection"),  "from Leak Check"),
                ("Stop",               log.get("stop"),               "from Visual Inspection"),
            ]
            for label, val, ref in rows:
                display = fmt_f(val) if val is not None else "—"
                tk.Label(self.container,
                         text=f"    {label:<22} {display}   ({ref})",
                         fg=WHITE if val is not None else SUBTEXT,
                         bg=BG, font=("Courier New", 10)).pack(anchor="w", padx=30)

            tk.Frame(self.container, bg=PANEL, height=1).pack(fill="x", padx=20, pady=4)

        self._btn(self.container, "Start New Participant  ▶", ACCENT,
                  self._show_login).pack(ipadx=14, ipady=7, pady=(4, 0))

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
