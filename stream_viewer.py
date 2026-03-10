"""
HRI Stream Viewer
=================
A simple live viewer for the HRI_Timer_Events LSL stream.
Shows incoming markers in real time as the timer GUI runs.

Usage:
  1. Make sure timer_gui.py is already running
  2. Open a second PowerShell window
  3. cd into your Investment_HRI_Timer folder
  4. Run: python stream_viewer.py

Dependencies: pylsl (already installed), tkinter (built into Python)
"""

import tkinter as tk
from tkinter import scrolledtext
import threading

try:
    from pylsl import StreamInlet, resolve_stream
    LSL_AVAILABLE = True
except ImportError:
    LSL_AVAILABLE = False


# ── Palette ────────────────────────────────────────────────────────────────────

BG      = "#1e1e2e"
PANEL   = "#2a2a3e"
ACCENT  = "#89b4fa"
GREEN   = "#a6e3a1"
RED     = "#f38ba8"
YELLOW  = "#f9e2af"
SUBTEXT = "#7f849c"
WHITE   = "#ffffff"


class StreamViewerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("HRI Stream Viewer — HRI_Timer_Events")
        self.configure(bg=BG)
        self.geometry("660x500")
        self.resizable(True, True)

        self._inlet    = None
        self._running  = False
        self._thread   = None
        self._start_ts = None
        self._count    = 0

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        if not LSL_AVAILABLE:
            self._log("ERROR: pylsl is not installed. Run: pip install pylsl\n", RED)
        else:
            self._log("Ready. Click Connect to search for the HRI_Timer_Events stream.\n", SUBTEXT)

    # ── UI ─────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = tk.Frame(self, bg=BG)
        header.pack(fill="x", padx=20, pady=(16, 4))

        tk.Label(header, text="HRI Stream Viewer",
                 fg=ACCENT, bg=BG, font=("Segoe UI", 16, "bold")).pack(side="left")

        self._status_var = tk.StringVar(value="● Disconnected")
        self._status_lbl = tk.Label(header, textvariable=self._status_var,
                                    fg=RED, bg=BG, font=("Segoe UI", 10))
        self._status_lbl.pack(side="right", pady=4)

        # Controls
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(fill="x", padx=20, pady=(0, 8))

        self._connect_btn = tk.Button(
            ctrl, text="Connect",
            command=self._connect,
            bg=GREEN, fg=BG, font=("Segoe UI", 10, "bold"),
            relief="flat", padx=12, pady=4, cursor="hand2",
            activebackground=WHITE, activeforeground=BG)
        self._connect_btn.pack(side="left", padx=(0, 8))

        self._disconnect_btn = tk.Button(
            ctrl, text="Disconnect",
            command=self._disconnect,
            bg=PANEL, fg=RED, font=("Segoe UI", 10, "bold"),
            relief="flat", padx=12, pady=4, cursor="hand2",
            state="disabled",
            activebackground=RED, activeforeground=WHITE)
        self._disconnect_btn.pack(side="left", padx=(0, 8))

        self._clear_btn = tk.Button(
            ctrl, text="Clear",
            command=self._clear,
            bg=PANEL, fg=SUBTEXT, font=("Segoe UI", 10),
            relief="flat", padx=12, pady=4, cursor="hand2",
            activebackground=WHITE, activeforeground=BG)
        self._clear_btn.pack(side="left")

        self._count_var = tk.StringVar(value="Markers received: 0")
        tk.Label(ctrl, textvariable=self._count_var,
                 fg=SUBTEXT, bg=BG, font=("Segoe UI", 10)).pack(side="right")

        # Separator
        tk.Frame(self, bg=SUBTEXT, height=1).pack(fill="x", padx=20, pady=(4, 6))

        # Column header
        tk.Label(self, text=f"  {'Time (s)':<14}Marker",
                 fg=SUBTEXT, bg=BG, font=("Courier New", 10, "bold")).pack(anchor="w", padx=20)

        # Scrollable log area
        self._log_box = scrolledtext.ScrolledText(
            self, bg=PANEL, fg=WHITE,
            font=("Courier New", 10),
            relief="flat", bd=0,
            state="disabled",
            wrap="word",
            padx=10, pady=8)
        self._log_box.pack(fill="both", expand=True, padx=20, pady=(4, 16))

        # Color tags for different marker types
        self._log_box.tag_config("start",    foreground=GREEN)
        self._log_box.tag_config("stop",     foreground=RED)
        self._log_box.tag_config("complete", foreground=ACCENT)
        self._log_box.tag_config("warning",  foreground=YELLOW)
        self._log_box.tag_config("session",  foreground=YELLOW)
        self._log_box.tag_config("default",  foreground=WHITE)
        self._log_box.tag_config("dim",      foreground=SUBTEXT)

    # ── Logging ────────────────────────────────────────────────────────────────

    def _log(self, text, color=None):
        self._log_box.config(state="normal")
        tag = "default"
        if color == SUBTEXT: tag = "dim"
        elif color == RED:   tag = "stop"
        elif color == GREEN: tag = "start"
        self._log_box.insert("end", text, tag)
        self._log_box.see("end")
        self._log_box.config(state="disabled")

    def _log_marker(self, time_s, marker):
        # Pick color based on marker content
        m = marker.lower()
        if "complete" in m:         tag = "complete"
        elif "start" in m:          tag = "start"
        elif "stop" in m:           tag = "stop"
        elif "warning" in m:        tag = "warning"
        elif "session" in m:        tag = "session"
        else:                       tag = "default"

        line = f"  {time_s:<14.3f}{marker}\n"
        self._log_box.config(state="normal")
        self._log_box.insert("end", line, tag)
        self._log_box.see("end")
        self._log_box.config(state="disabled")

    def _clear(self):
        self._log_box.config(state="normal")
        self._log_box.delete("1.0", "end")
        self._log_box.config(state="disabled")
        self._count = 0
        self._count_var.set("Markers received: 0")

    # ── Connection ─────────────────────────────────────────────────────────────

    def _connect(self):
        if not LSL_AVAILABLE:
            return
        self._connect_btn.config(state="disabled")
        self._status_var.set("● Searching…")
        self._status_lbl.config(fg=YELLOW)
        self._log("Searching for HRI_Timer_Events stream (up to 10 seconds)…\n", SUBTEXT)
        threading.Thread(target=self._find_stream, daemon=True).start()

    def _find_stream(self):
        try:
            streams = resolve_stream("name", "HRI_Timer_Events", 1, 10)
            if not streams:
                self.after(0, self._on_not_found)
                return
            self._inlet = StreamInlet(streams[0])
            self._start_ts = None
            self.after(0, self._on_connected)
        except Exception as e:
            self.after(0, self._on_error, str(e))

    def _on_connected(self):
        self._running = True
        self._status_var.set("● Connected")
        self._status_lbl.config(fg=GREEN)
        self._connect_btn.config(state="disabled")
        self._disconnect_btn.config(state="normal")
        self._log("Connected to HRI_Timer_Events! Waiting for markers…\n", GREEN)
        self._thread = threading.Thread(target=self._read_loop, daemon=True)
        self._thread.start()

    def _on_not_found(self):
        self._status_var.set("● Disconnected")
        self._status_lbl.config(fg=RED)
        self._connect_btn.config(state="normal")
        self._log("Stream not found. Make sure timer_gui.py is running, then try again.\n", RED)

    def _on_error(self, msg):
        self._status_var.set("● Error")
        self._status_lbl.config(fg=RED)
        self._connect_btn.config(state="normal")
        self._log(f"Error: {msg}\n", RED)

    def _disconnect(self):
        self._running = False
        self._inlet   = None
        self._status_var.set("● Disconnected")
        self._status_lbl.config(fg=RED)
        self._connect_btn.config(state="normal")
        self._disconnect_btn.config(state="disabled")
        self._log("Disconnected.\n", SUBTEXT)

    # ── Read loop ──────────────────────────────────────────────────────────────

    def _read_loop(self):
        while self._running and self._inlet:
            try:
                sample, timestamp = self._inlet.pull_sample(timeout=1.0)
                if sample:
                    if self._start_ts is None:
                        self._start_ts = timestamp
                    relative = timestamp - self._start_ts
                    self._count += 1
                    self.after(0, self._log_marker, relative, sample[0])
                    self.after(0, self._count_var.set,
                               f"Markers received: {self._count}")
            except Exception:
                break

    # ── Close ──────────────────────────────────────────────────────────────────

    def _on_close(self):
        self._running = False
        self.destroy()


if __name__ == "__main__":
    app = StreamViewerApp()
    app.mainloop()
