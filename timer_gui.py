"""
Investment_HRI_Timer
====================
A Python-based participant GUI with Lab Streaming Layer (LSL) bridge.

Timers:
  - Baseline  : 2 minutes  (120 s)
  - Task A    : 15 minutes (900 s)
  - Task B    : 30 minutes (1800 s)

LSL stream name : "HRI_Timer_Events"
LSL stream type : "Markers"
Markers sent    : "baseline_start", "baseline_stop",
                  "task15_start",   "task15_stop",
                  "task30_start",   "task30_stop",
                  "timer_complete_<name>"

Dependencies:
  pip install pylsl
  (tkinter ships with Python on Windows)
"""

import tkinter as tk
from tkinter import font as tkfont
import threading
import time

try:
    from pylsl import StreamInfo, StreamOutlet
    LSL_AVAILABLE = True
except ImportError:
    LSL_AVAILABLE = False
    print("[WARNING] pylsl not found. LSL streaming disabled.")
    print("          Install with:  pip install pylsl")


# ── LSL Setup ──────────────────────────────────────────────────────────────────

def create_lsl_outlet():
    if not LSL_AVAILABLE:
        return None
    info = StreamInfo(
        name="HRI_Timer_Events",
        type="Markers",
        channel_count=1,
        nominal_srate=0,          # irregular rate (event-driven)
        channel_format="string",
        source_id="InvestmentHRI_001"
    )
    outlet = StreamOutlet(info)
    print("[LSL] Stream 'HRI_Timer_Events' is live.")
    return outlet


def push_marker(outlet, marker: str):
    if outlet is not None:
        outlet.push_sample([marker])
    print(f"[LSL] Marker: {marker}")


# ── Colour palette ─────────────────────────────────────────────────────────────

BG         = "#1e1e2e"
PANEL_BG   = "#2a2a3e"
ACCENT     = "#89b4fa"
GREEN      = "#a6e3a1"
RED        = "#f38ba8"
YELLOW     = "#f9e2af"
TEXT       = "#cdd6f4"
SUBTEXT    = "#7f849c"
WHITE      = "#ffffff"

TIMER_CONFIGS = [
    {"label": "Baseline",      "duration": 120,  "marker_prefix": "baseline", "color": ACCENT},
    {"label": "15-min Task",   "duration": 900,  "marker_prefix": "task15",   "color": GREEN},
    {"label": "30-min Task",   "duration": 1800, "marker_prefix": "task30",   "color": YELLOW},
]


# ── Timer block widget ─────────────────────────────────────────────────────────

class TimerBlock(tk.Frame):
    def __init__(self, parent, config: dict, outlet, **kwargs):
        super().__init__(parent, bg=PANEL_BG, bd=0, relief="flat",
                         highlightthickness=2, highlightbackground=SUBTEXT,
                         **kwargs)
        self.outlet       = outlet
        self.duration     = config["duration"]
        self.prefix       = config["marker_prefix"]
        self.color        = config["color"]
        self.label_text   = config["label"]

        self.running      = False
        self.elapsed      = 0
        self._thread      = None
        self._stop_event  = threading.Event()

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 18, "pady": 6}

        # Title
        self.title_lbl = tk.Label(self, text=self.label_text,
                                  fg=self.color, bg=PANEL_BG,
                                  font=("Segoe UI", 14, "bold"))
        self.title_lbl.pack(pady=(18, 2))

        # Duration hint
        mins = self.duration // 60
        hint = f"{mins} minute{'s' if mins > 1 else ''}"
        tk.Label(self, text=hint, fg=SUBTEXT, bg=PANEL_BG,
                 font=("Segoe UI", 10)).pack()

        # Big clock
        self.clock_var = tk.StringVar(value=self._fmt(self.duration))
        self.clock_lbl = tk.Label(self, textvariable=self.clock_var,
                                  fg=WHITE, bg=PANEL_BG,
                                  font=("Courier New", 36, "bold"))
        self.clock_lbl.pack(pady=10)

        # Progress bar (canvas)
        self.progress_canvas = tk.Canvas(self, height=8, bg=PANEL_BG,
                                         highlightthickness=0, width=260)
        self.progress_canvas.pack(padx=18, fill="x")
        self.progress_canvas.create_rectangle(0, 0, 260, 8,
                                              fill=SUBTEXT, outline="", tags="bg")
        self.progress_bar = self.progress_canvas.create_rectangle(
            0, 0, 0, 8, fill=self.color, outline="", tags="bar")

        # Status
        self.status_var = tk.StringVar(value="Ready")
        self.status_lbl = tk.Label(self, textvariable=self.status_var,
                                   fg=SUBTEXT, bg=PANEL_BG,
                                   font=("Segoe UI", 10, "italic"))
        self.status_lbl.pack(pady=(6, 2))

        # Buttons
        btn_frame = tk.Frame(self, bg=PANEL_BG)
        btn_frame.pack(pady=(8, 18))

        self.start_btn = tk.Button(
            btn_frame, text="▶  Start",
            command=self.start,
            bg=self.color, fg=BG,
            font=("Segoe UI", 11, "bold"),
            relief="flat", padx=16, pady=6, cursor="hand2",
            activebackground=WHITE, activeforeground=BG)
        self.start_btn.grid(row=0, column=0, padx=6)

        self.stop_btn = tk.Button(
            btn_frame, text="■  Stop",
            command=self.stop,
            bg=PANEL_BG, fg=RED,
            font=("Segoe UI", 11, "bold"),
            relief="flat", padx=16, pady=6, cursor="hand2",
            highlightthickness=1, highlightbackground=RED,
            state="disabled",
            activebackground=RED, activeforeground=WHITE)
        self.stop_btn.grid(row=0, column=1, padx=6)

        self.reset_btn = tk.Button(
            btn_frame, text="↺",
            command=self.reset,
            bg=PANEL_BG, fg=SUBTEXT,
            font=("Segoe UI", 12),
            relief="flat", padx=10, pady=4, cursor="hand2",
            activebackground=PANEL_BG, activeforeground=TEXT)
        self.reset_btn.grid(row=0, column=2, padx=2)

    # ── helpers ──

    @staticmethod
    def _fmt(seconds: int) -> str:
        m, s = divmod(max(0, seconds), 60)
        return f"{m:02d}:{s:02d}"

    def _update_progress(self):
        pct  = self.elapsed / self.duration
        w    = int(self.progress_canvas.winfo_width() * pct)
        self.progress_canvas.coords("bar", 0, 0, w, 8)

    # ── controls ──

    def start(self):
        if self.running:
            return
        self.running = True
        self._stop_event.clear()

        push_marker(self.outlet, f"{self.prefix}_start")

        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_var.set("Running…")
        self.status_lbl.config(fg=GREEN)
        self.config(highlightbackground=self.color)

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        if not self.running:
            return
        self._stop_event.set()
        self.running = False

        push_marker(self.outlet, f"{self.prefix}_stop")

        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_var.set(f"Stopped at {self._fmt(self.elapsed)}")
        self.status_lbl.config(fg=YELLOW)
        self.config(highlightbackground=SUBTEXT)

    def reset(self):
        if self.running:
            self.stop()
        self.elapsed = 0
        self.clock_var.set(self._fmt(self.duration))
        self.progress_canvas.coords("bar", 0, 0, 0, 8)
        self.status_var.set("Ready")
        self.status_lbl.config(fg=SUBTEXT)
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.config(highlightbackground=SUBTEXT)

    def _run(self):
        start_time  = time.monotonic()
        base_elapsed = self.elapsed

        while not self._stop_event.is_set():
            now          = time.monotonic()
            self.elapsed = min(int(now - start_time) + base_elapsed,
                               self.duration)
            remaining    = self.duration - self.elapsed

            # Update UI from main thread
            self.after(0, self._refresh_ui, remaining)

            if remaining <= 0:
                self.after(0, self._on_complete)
                break

            # Sleep until next second boundary
            next_tick = start_time + (self.elapsed - base_elapsed + 1)
            sleep_dur = next_tick - time.monotonic()
            if sleep_dur > 0:
                self._stop_event.wait(timeout=sleep_dur)

    def _refresh_ui(self, remaining):
        self.clock_var.set(self._fmt(remaining))
        self._update_progress()

    def _on_complete(self):
        self.running = False
        push_marker(self.outlet, f"timer_complete_{self.prefix}")
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="disabled")
        self.status_var.set("✔ Complete!")
        self.status_lbl.config(fg=GREEN)
        self.clock_var.set("00:00")
        self.config(highlightbackground=GREEN)
        self._update_progress()


# ── Main application window ────────────────────────────────────────────────────

class HRITimerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Investment HRI — Participant Timer")
        self.configure(bg=BG)
        self.resizable(False, False)

        self.outlet = create_lsl_outlet()

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=24, pady=(20, 8))

        tk.Label(header, text="Investment HRI", fg=ACCENT, bg=BG,
                 font=("Segoe UI", 20, "bold")).pack(side="left")

        lsl_color = GREEN if LSL_AVAILABLE else RED
        lsl_text  = "● LSL Active" if LSL_AVAILABLE else "● LSL Offline"
        tk.Label(header, text=lsl_text, fg=lsl_color, bg=BG,
                 font=("Segoe UI", 10)).pack(side="right", pady=6)

        tk.Label(self, text="Participant Timer Console",
                 fg=SUBTEXT, bg=BG,
                 font=("Segoe UI", 11)).pack()

        # Separator
        tk.Frame(self, bg=SUBTEXT, height=1).pack(fill="x", padx=24, pady=10)

        # Timer blocks
        timer_row = tk.Frame(self, bg=BG)
        timer_row.pack(padx=24, pady=8)

        for cfg in TIMER_CONFIGS:
            block = TimerBlock(timer_row, cfg, self.outlet)
            block.pack(side="left", padx=10, pady=4, fill="y")

        # Footer
        tk.Frame(self, bg=SUBTEXT, height=1).pack(fill="x", padx=24, pady=(10, 0))
        tk.Label(self, text="Stream: HRI_Timer_Events  |  Type: Markers",
                 fg=SUBTEXT, bg=BG,
                 font=("Segoe UI", 9)).pack(pady=(4, 14))

    def _on_close(self):
        push_marker(self.outlet, "session_end")
        self.destroy()


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = HRITimerApp()
    app.mainloop()
