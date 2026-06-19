"""
Hamilton AI — Floating Desktop Overlay
Always-on-top floating orb → click to expand panel
Shows: status, history, quick controls, mic toggle
"""

import tkinter as tk
from tkinter import font as tkfont
import threading
import time
import json
import os
import sys
from datetime import datetime

# ─────────────────────────────────────────────
# HISTORY FILE
# ─────────────────────────────────────────────
HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hamilton_history.json")

def load_history():
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return []

def save_history(history):
    try:
        with open(HISTORY_FILE, "w") as f:
            json.dump(history[-100:], f, indent=2)  # keep last 100
    except Exception:
        pass

def add_to_history(role, text):
    history = load_history()
    history.append({
        "role": role,
        "text": text,
        "time": datetime.now().strftime("%H:%M:%S"),
        "date": datetime.now().strftime("%Y-%m-%d")
    })
    save_history(history)

# ─────────────────────────────────────────────
# COLORS & THEME
# ─────────────────────────────────────────────
C = {
    "bg":           "#0a0a0f",
    "panel":        "#0f0f1a",
    "panel_border": "#1e1e3a",
    "card":         "#131320",
    "card_hover":   "#1a1a2e",
    "accent":       "#00d4ff",
    "accent2":      "#7b2fff",
    "accent_dim":   "#004455",
    "text":         "#e8e8f0",
    "text_dim":     "#6666aa",
    "text_muted":   "#333355",
    "green":        "#00ff9d",
    "red":          "#ff4466",
    "yellow":       "#ffd700",
    "orb_idle":     "#00d4ff",
    "orb_listen":   "#00ff9d",
    "orb_think":    "#ffd700",
    "orb_speak":    "#7b2fff",
}

# ─────────────────────────────────────────────
# STATE
# ─────────────────────────────────────────────
class HamiltonState:
    def __init__(self):
        self.status       = "idle"      # idle | listening | thinking | speaking
        self.is_listening = False
        self.is_running   = True
        self.last_command = ""
        self.last_response= ""
        self.agent_thread = None
        self.on_command_cb= None        # callback → run_agent(text)

state = HamiltonState()

# ─────────────────────────────────────────────
# MAIN GUI
# ─────────────────────────────────────────────
class HamiltonUI:
    def __init__(self, root):
        self.root = root
        self.root.withdraw()

        # ── Floating orb window ──────────────────
        self.orb_win = tk.Toplevel(root)
        self.orb_win.overrideredirect(True)
        self.orb_win.attributes("-topmost", True)
        self.orb_win.attributes("-alpha", 0.92)
        self.orb_win.configure(bg="#000000")

        # Position: bottom-right corner
        sw = self.orb_win.winfo_screenwidth()
        sh = self.orb_win.winfo_screenheight()
        self.orb_x = sw - 90
        self.orb_y = sh - 140
        self.orb_win.geometry(f"70x70+{self.orb_x}+{self.orb_y}")

        # Make background transparent (Windows)
        try:
            self.orb_win.wm_attributes("-transparentcolor", "#000000")
        except Exception:
            pass

        self.orb_canvas = tk.Canvas(
            self.orb_win, width=70, height=70,
            bg="#000000", highlightthickness=0
        )
        self.orb_canvas.pack()
        self._draw_orb(C["orb_idle"], pulse=False)

        # Drag support
        self._drag_x = 0
        self._drag_y = 0
        self.orb_canvas.bind("<ButtonPress-1>",   self._orb_drag_start)
        self.orb_canvas.bind("<B1-Motion>",        self._orb_drag_move)
        self.orb_canvas.bind("<ButtonRelease-1>",  self._orb_click)

        # ── Panel window (hidden) ────────────────
        self.panel_visible = False
        self.panel_win = None
        self._build_panel()

        # ── Pulse animation ──────────────────────
        self._pulse_phase  = 0
        self._animate()

        # ── Status update loop ───────────────────
        self._update_status_loop()

    # ─────────────────────────────────────────
    # ORB DRAWING
    # ─────────────────────────────────────────
    def _draw_orb(self, color, pulse=False, radius_extra=0):
        c = self.orb_canvas
        c.delete("all")
        cx, cy = 35, 35
        r = 28 + radius_extra

        # Outer glow rings
        for i in range(4, 0, -1):
            alpha_hex = ["22","33","44","66"][4 - i]
            try:
                c.create_oval(
                    cx - r - i*4, cy - r - i*4,
                    cx + r + i*4, cy + r + i*4,
                    fill="", outline=color + alpha_hex,
                    width=1
                )
            except Exception:
                pass

        # Shadow
        c.create_oval(cx-r+3, cy-r+3, cx+r+3, cy+r+3,
                      fill="#000000", outline="")

        # Main orb gradient simulation (two overlapping ovals)
        c.create_oval(cx-r, cy-r, cx+r, cy+r,
                      fill=C["bg"], outline=color, width=2)

        # Inner glow
        c.create_oval(cx-r+8, cy-r+8, cx+r-8, cy+r-8,
                      fill=color, outline="", stipple="gray25")

        # Center dot
        c.create_oval(cx-6, cy-6, cx+6, cy+6,
                      fill=color, outline="")

        # "H" letter
        c.create_text(cx, cy, text="H",
                      fill="#ffffff", font=("Georgia", 11, "bold"))

    # ─────────────────────────────────────────
    # DRAG
    # ─────────────────────────────────────────
    def _orb_drag_start(self, e):
        self._drag_x = e.x
        self._drag_y = e.y
        self._dragged = False

    def _orb_drag_move(self, e):
        dx = e.x - self._drag_x
        dy = e.y - self._drag_y
        if abs(dx) > 3 or abs(dy) > 3:
            self._dragged = True
        x = self.orb_win.winfo_x() + dx
        y = self.orb_win.winfo_y() + dy
        self.orb_win.geometry(f"+{x}+{y}")
        self.orb_x = x
        self.orb_y = y
        if self.panel_visible and self.panel_win:
            self._reposition_panel()

    def _orb_click(self, e):
        if not getattr(self, "_dragged", False):
            self._toggle_panel()

    # ─────────────────────────────────────────
    # PANEL BUILD
    # ─────────────────────────────────────────
    def _build_panel(self):
        if self.panel_win:
            try:
                self.panel_win.destroy()
            except Exception:
                pass

        self.panel_win = tk.Toplevel(self.root)
        self.panel_win.overrideredirect(True)
        self.panel_win.attributes("-topmost", True)
        self.panel_win.attributes("-alpha", 0.96)
        self.panel_win.configure(bg=C["panel_border"])
        self.panel_win.withdraw()

        W, H = 340, 540
        self._panel_w = W
        self._panel_h = H

        # Outer border frame
        outer = tk.Frame(self.panel_win, bg=C["panel_border"], padx=1, pady=1)
        outer.pack(fill="both", expand=True)

        main = tk.Frame(outer, bg=C["panel"], width=W-2, height=H-2)
        main.pack(fill="both", expand=True)
        main.pack_propagate(False)

        self._build_header(main)
        self._build_status_bar(main)
        self._build_tabs(main)
        self._build_footer(main)

    def _build_header(self, parent):
        hdr = tk.Frame(parent, bg=C["panel"], pady=12)
        hdr.pack(fill="x", padx=16)

        # Logo + name
        logo_frame = tk.Frame(hdr, bg=C["panel"])
        logo_frame.pack(side="left")

        logo_canvas = tk.Canvas(logo_frame, width=36, height=36,
                                bg=C["panel"], highlightthickness=0)
        logo_canvas.pack(side="left")
        logo_canvas.create_oval(2, 2, 34, 34, fill=C["bg"],
                                outline=C["accent"], width=1)
        logo_canvas.create_text(18, 18, text="H",
                                fill=C["accent"], font=("Georgia", 14, "bold"))

        name_frame = tk.Frame(logo_frame, bg=C["panel"])
        name_frame.pack(side="left", padx=8)

        tk.Label(name_frame, text="HAMILTON",
                 bg=C["panel"], fg=C["text"],
                 font=("Georgia", 13, "bold")).pack(anchor="w")
        tk.Label(name_frame, text="AI Desktop Agent",
                 bg=C["panel"], fg=C["text_dim"],
                 font=("Courier", 7)).pack(anchor="w")

        # Close button
        close_btn = tk.Label(hdr, text="✕",
                             bg=C["panel"], fg=C["text_dim"],
                             font=("Arial", 12), cursor="hand2")
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self._toggle_panel())
        close_btn.bind("<Enter>",    lambda e: close_btn.config(fg=C["red"]))
        close_btn.bind("<Leave>",    lambda e: close_btn.config(fg=C["text_dim"]))

        # Divider
        tk.Frame(parent, bg=C["panel_border"], height=1).pack(fill="x")

    def _build_status_bar(self, parent):
        self.status_frame = tk.Frame(parent, bg=C["card"], pady=8)
        self.status_frame.pack(fill="x", padx=12, pady=(10, 0))

        inner = tk.Frame(self.status_frame, bg=C["card"])
        inner.pack(padx=12)

        # Status indicator dot
        self.status_dot = tk.Canvas(inner, width=10, height=10,
                                    bg=C["card"], highlightthickness=0)
        self.status_dot.pack(side="left", pady=2)
        self.status_dot.create_oval(1, 1, 9, 9, fill=C["green"], outline="")

        self.status_label = tk.Label(inner, text="● Ready",
                                     bg=C["card"], fg=C["green"],
                                     font=("Courier", 9, "bold"))
        self.status_label.pack(side="left", padx=6)

        self.status_text = tk.Label(inner, text="Waiting for command...",
                                    bg=C["card"], fg=C["text_dim"],
                                    font=("Courier", 8))
        self.status_text.pack(side="left")

    def _build_tabs(self, parent):
        # Tab bar
        tab_bar = tk.Frame(parent, bg=C["panel"])
        tab_bar.pack(fill="x", padx=12, pady=(12, 0))

        self.tab_frames = {}
        self.tab_btns   = {}
        self.active_tab = tk.StringVar(value="history")

        tabs = [("history", "History"), ("controls", "Controls"), ("settings", "Settings")]

        for tid, tlabel in tabs:
            btn = tk.Label(tab_bar, text=tlabel,
                           bg=C["panel"], fg=C["text_dim"],
                           font=("Courier", 8, "bold"),
                           cursor="hand2", padx=10, pady=5)
            btn.pack(side="left")
            self.tab_btns[tid] = btn
            btn.bind("<Button-1>", lambda e, t=tid: self._switch_tab(t))

        # Tab content area
        self.tab_area = tk.Frame(parent, bg=C["panel"])
        self.tab_area.pack(fill="both", expand=True, padx=12, pady=8)

        self._build_history_tab()
        self._build_controls_tab()
        self._build_settings_tab()
        self._switch_tab("history")

    def _switch_tab(self, tab_id):
        self.active_tab.set(tab_id)
        for tid, frame in self.tab_frames.items():
            frame.pack_forget()
        for tid, btn in self.tab_btns.items():
            if tid == tab_id:
                btn.config(fg=C["accent"],
                           relief="flat",
                           borderwidth=0)
            else:
                btn.config(fg=C["text_dim"])
        self.tab_frames[tab_id].pack(fill="both", expand=True)
        if tab_id == "history":
            self._refresh_history()

    # ── HISTORY TAB ──────────────────────────
    def _build_history_tab(self):
        frame = tk.Frame(self.tab_area, bg=C["panel"])
        self.tab_frames["history"] = frame

        # Scrollable list
        container = tk.Frame(frame, bg=C["panel_border"], pady=1, padx=1)
        container.pack(fill="both", expand=True)

        inner = tk.Frame(container, bg=C["panel"])
        inner.pack(fill="both", expand=True)

        scrollbar = tk.Scrollbar(inner, bg=C["panel"],
                                 troughcolor=C["bg"],
                                 width=6)
        scrollbar.pack(side="right", fill="y")

        self.history_canvas = tk.Canvas(inner, bg=C["panel"],
                                        highlightthickness=0,
                                        yscrollcommand=scrollbar.set)
        self.history_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.history_canvas.yview)

        self.history_inner = tk.Frame(self.history_canvas, bg=C["panel"])
        self.history_canvas_window = self.history_canvas.create_window(
            (0, 0), window=self.history_inner, anchor="nw"
        )
        self.history_inner.bind("<Configure>", self._on_history_configure)
        self.history_canvas.bind("<Configure>", self._on_canvas_configure)

        # Clear button
        clear_row = tk.Frame(frame, bg=C["panel"])
        clear_row.pack(fill="x", pady=(6, 0))

        clear_btn = tk.Label(clear_row, text="Clear History",
                             bg=C["panel"], fg=C["text_muted"],
                             font=("Courier", 7), cursor="hand2")
        clear_btn.pack(side="right")
        clear_btn.bind("<Button-1>", lambda e: self._clear_history())
        clear_btn.bind("<Enter>",    lambda e: clear_btn.config(fg=C["red"]))
        clear_btn.bind("<Leave>",    lambda e: clear_btn.config(fg=C["text_muted"]))

    def _on_history_configure(self, e):
        self.history_canvas.configure(
            scrollregion=self.history_canvas.bbox("all")
        )

    def _on_canvas_configure(self, e):
        self.history_canvas.itemconfig(
            self.history_canvas_window, width=e.width
        )

    def _refresh_history(self):
        for w in self.history_inner.winfo_children():
            w.destroy()

        history = load_history()
        if not history:
            tk.Label(self.history_inner,
                     text="No history yet.\nStart talking to Hamilton!",
                     bg=C["panel"], fg=C["text_muted"],
                     font=("Courier", 8), justify="center"
                     ).pack(pady=30)
            return

        for item in reversed(history[-20:]):
            role  = item.get("role", "user")
            text  = item.get("text", "")
            ts    = item.get("time", "")

            is_user = role == "user"
            bg_col  = C["card"] if is_user else C["bg"]
            fg_col  = C["accent"] if is_user else C["text"]
            prefix  = "YOU" if is_user else " AI"
            prefix_col = C["accent"] if is_user else C["accent2"]

            row = tk.Frame(self.history_inner, bg=bg_col,
                           pady=6, padx=8)
            row.pack(fill="x", pady=1)

            top = tk.Frame(row, bg=bg_col)
            top.pack(fill="x")

            tk.Label(top, text=prefix,
                     bg=bg_col, fg=prefix_col,
                     font=("Courier", 7, "bold")).pack(side="left")
            tk.Label(top, text=ts,
                     bg=bg_col, fg=C["text_muted"],
                     font=("Courier", 7)).pack(side="right")

            # Word-wrap text
            display = text[:120] + ("..." if len(text) > 120 else "")
            tk.Label(row, text=display,
                     bg=bg_col, fg=fg_col,
                     font=("Courier", 8),
                     wraplength=270, justify="left",
                     anchor="w").pack(fill="x", pady=(2, 0))

        # Scroll to top (most recent)
        self.history_canvas.yview_moveto(0)

    def _clear_history(self):
        save_history([])
        self._refresh_history()

    # ── CONTROLS TAB ─────────────────────────
    def _build_controls_tab(self):
        frame = tk.Frame(self.tab_area, bg=C["panel"])
        self.tab_frames["controls"] = frame

        sections = [
            ("🎤 Voice", [
                ("Start Listening",  self._start_listening,  C["green"]),
                ("Stop Listening",   self._stop_listening,   C["red"]),
            ]),
            ("🪟 Window", [
                ("Minimize",         lambda: self._quick("minimize"),    C["accent"]),
                ("Maximize",         lambda: self._quick("maximize"),    C["accent"]),
                ("Show Desktop",     lambda: self._quick("show_desktop"),C["accent"]),
                ("Task View",        lambda: self._quick("task_view"),   C["accent"]),
            ]),
            ("🔊 Volume", [
                ("Volume Up",        lambda: self._quick("volume_up"),   C["yellow"]),
                ("Volume Down",      lambda: self._quick("volume_down"), C["yellow"]),
                ("Mute / Unmute",    lambda: self._quick("mute"),        C["yellow"]),
            ]),
            ("📸 Capture", [
                ("Screenshot",       lambda: self._quick("screenshot"),  C["accent2"]),
                ("Snip Tool",        lambda: self._quick("snip"),        C["accent2"]),
            ]),
            ("⚙️ System", [
                ("Lock Screen",      lambda: self._quick("lock"),        C["text_dim"]),
                ("Task Manager",     lambda: self._quick("task_manager"),C["text_dim"]),
            ]),
        ]

        scroll_frame = tk.Frame(frame, bg=C["panel"])
        scroll_frame.pack(fill="both", expand=True)

        for section_name, buttons in sections:
            tk.Label(scroll_frame, text=section_name,
                     bg=C["panel"], fg=C["text_dim"],
                     font=("Courier", 7, "bold")).pack(anchor="w", pady=(8, 2))

            btn_row = tk.Frame(scroll_frame, bg=C["panel"])
            btn_row.pack(fill="x")

            for label, cmd, color in buttons:
                self._make_btn(btn_row, label, cmd, color)

    def _make_btn(self, parent, label, command, color):
        btn = tk.Label(parent, text=label,
                       bg=C["card"], fg=color,
                       font=("Courier", 8),
                       padx=8, pady=5,
                       cursor="hand2",
                       relief="flat")
        btn.pack(side="left", padx=2, pady=2)
        btn.bind("<Button-1>", lambda e, c=command: c())
        btn.bind("<Enter>",    lambda e: btn.config(bg=C["card_hover"]))
        btn.bind("<Leave>",    lambda e: btn.config(bg=C["card"]))

    def _quick(self, action):
        """Fire a quick action directly."""
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from actions import (
                minimize_window, maximize_window, minimize_all,
                show_all_windows, volume_up, volume_down, mute,
                screenshot, snip, lock, open_task_manager
            )
            import pyautogui

            action_map = {
                "minimize":     minimize_window,
                "maximize":     maximize_window,
                "show_desktop": minimize_all,
                "task_view":    show_all_windows,
                "volume_up":    volume_up,
                "volume_down":  volume_down,
                "mute":         mute,
                "screenshot":   screenshot,
                "snip":         snip,
                "lock":         lock,
                "task_manager": open_task_manager,
            }
            fn = action_map.get(action)
            if fn:
                threading.Thread(target=fn, daemon=True).start()
                self._set_status("thinking", f"Running: {action}")
        except Exception as e:
            self._set_status("idle", f"Error: {e}")

    # ── SETTINGS TAB ─────────────────────────
    def _build_settings_tab(self):
        frame = tk.Frame(self.tab_area, bg=C["panel"])
        self.tab_frames["settings"] = frame

        self.always_top_var = tk.BooleanVar(value=True)
        self.opacity_var    = tk.DoubleVar(value=0.92)

        def row(parent, label, widget_fn):
            r = tk.Frame(parent, bg=C["card"], pady=8, padx=10)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=label, bg=C["card"], fg=C["text"],
                     font=("Courier", 8)).pack(side="left")
            widget_fn(r)

        def always_top_toggle(parent):
            cb = tk.Checkbutton(parent, variable=self.always_top_var,
                                bg=C["card"], fg=C["accent"],
                                activebackground=C["card"],
                                selectcolor=C["bg"],
                                command=self._apply_always_top)
            cb.pack(side="right")

        def opacity_slider(parent):
            s = tk.Scale(parent, variable=self.opacity_var,
                         from_=0.5, to=1.0, resolution=0.05,
                         orient="horizontal", length=120,
                         bg=C["card"], fg=C["text"],
                         troughcolor=C["bg"],
                         highlightthickness=0,
                         command=self._apply_opacity)
            s.pack(side="right")

        tk.Label(frame, text="SETTINGS",
                 bg=C["panel"], fg=C["text_dim"],
                 font=("Courier", 7, "bold")).pack(anchor="w", pady=(4, 8))

        row(frame, "Always on top",  always_top_toggle)
        row(frame, "Opacity",        opacity_slider)

        # Version info
        info = tk.Frame(frame, bg=C["panel"])
        info.pack(fill="x", pady=(20, 0))

        tk.Label(info, text="Hamilton AI  v1.0",
                 bg=C["panel"], fg=C["text_muted"],
                 font=("Courier", 7)).pack()
        tk.Label(info, text="Desktop Automation Agent",
                 bg=C["panel"], fg=C["text_muted"],
                 font=("Courier", 7)).pack()

        # Quit button
        quit_btn = tk.Label(frame, text="Quit Hamilton",
                            bg=C["panel"], fg=C["text_muted"],
                            font=("Courier", 8), cursor="hand2")
        quit_btn.pack(pady=(16, 0))
        quit_btn.bind("<Button-1>", lambda e: self._quit())
        quit_btn.bind("<Enter>",    lambda e: quit_btn.config(fg=C["red"]))
        quit_btn.bind("<Leave>",    lambda e: quit_btn.config(fg=C["text_muted"]))

    def _apply_always_top(self):
        val = self.always_top_var.get()
        self.orb_win.attributes("-topmost", val)
        if self.panel_win:
            self.panel_win.attributes("-topmost", val)

    def _apply_opacity(self, val=None):
        v = self.opacity_var.get()
        self.orb_win.attributes("-alpha", v)
        if self.panel_win:
            self.panel_win.attributes("-alpha", min(v + 0.04, 1.0))

    # ── FOOTER ───────────────────────────────
    def _build_footer(self, parent):
        tk.Frame(parent, bg=C["panel_border"], height=1).pack(fill="x")

        footer = tk.Frame(parent, bg=C["panel"], pady=8)
        footer.pack(fill="x", padx=16)

        # Mic button
        self.mic_btn = tk.Label(footer, text="🎤  LISTEN",
                                bg=C["card"], fg=C["green"],
                                font=("Courier", 8, "bold"),
                                padx=14, pady=6, cursor="hand2")
        self.mic_btn.pack(side="left")
        self.mic_btn.bind("<Button-1>", lambda e: self._toggle_listen())
        self.mic_btn.bind("<Enter>",    lambda e: self.mic_btn.config(bg=C["card_hover"]))
        self.mic_btn.bind("<Leave>",    lambda e: self.mic_btn.config(bg=C["card"]))

        # Last command display
        self.last_cmd_label = tk.Label(footer, text="",
                                       bg=C["panel"], fg=C["text_dim"],
                                       font=("Courier", 7),
                                       wraplength=180, justify="left")
        self.last_cmd_label.pack(side="left", padx=10)

    # ─────────────────────────────────────────
    # PANEL SHOW / HIDE
    # ─────────────────────────────────────────
    def _toggle_panel(self):
        if self.panel_visible:
            self.panel_win.withdraw()
            self.panel_visible = False
        else:
            self._reposition_panel()
            self.panel_win.deiconify()
            self.panel_visible = True
            if self.active_tab.get() == "history":
                self._refresh_history()

    def _reposition_panel(self):
        sw  = self.orb_win.winfo_screenwidth()
        ox  = self.orb_win.winfo_x()
        oy  = self.orb_win.winfo_y()
        W   = self._panel_w
        H   = self._panel_h

        # Place panel to the left of orb, aligned vertically
        px = ox - W - 10
        py = oy + 35 - H

        # Keep on screen
        if px < 0:
            px = ox + 80
        if py < 0:
            py = 10
        if py + H > self.orb_win.winfo_screenheight():
            py = self.orb_win.winfo_screenheight() - H - 10

        self.panel_win.geometry(f"{W}x{H}+{px}+{py}")

    # ─────────────────────────────────────────
    # STATUS
    # ─────────────────────────────────────────
    def _set_status(self, status, text=""):
        state.status = status
        color_map = {
            "idle":      C["green"],
            "listening": C["green"],
            "thinking":  C["yellow"],
            "speaking":  C["accent2"],
            "error":     C["red"],
        }
        label_map = {
            "idle":      "● Ready",
            "listening": "◉ Listening",
            "thinking":  "◌ Thinking",
            "speaking":  "◈ Speaking",
            "error":     "✕ Error",
        }
        color = color_map.get(status, C["text_dim"])
        label = label_map.get(status, "● Ready")

        try:
            self.status_label.config(text=label, fg=color)
            if text:
                short = text[:38] + ("..." if len(text) > 38 else "")
                self.status_text.config(text=short)

            # Update orb color
            orb_color = {
                "idle":      C["orb_idle"],
                "listening": C["orb_listen"],
                "thinking":  C["orb_think"],
                "speaking":  C["orb_speak"],
            }.get(status, C["orb_idle"])
            self._draw_orb(orb_color)
        except Exception:
            pass

    def _update_status_loop(self):
        """Sync GUI status with agent state every 500ms."""
        try:
            self._set_status(state.status,
                             state.last_command or "Waiting for command...")
            if state.last_command:
                short = state.last_command[:30] + ("..." if len(state.last_command) > 30 else "")
                self.last_cmd_label.config(text=f'"{short}"')
        except Exception:
            pass
        self.root.after(500, self._update_status_loop)

    # ─────────────────────────────────────────
    # ANIMATION
    # ─────────────────────────────────────────
    def _animate(self):
        self._pulse_phase = (self._pulse_phase + 1) % 60
        extra = int(abs(self._pulse_phase - 30) / 30 * 3)  # 0-3px pulse

        color_map = {
            "idle":      C["orb_idle"],
            "listening": C["orb_listen"],
            "thinking":  C["orb_think"],
            "speaking":  C["orb_speak"],
        }
        color = color_map.get(state.status, C["orb_idle"])

        # Only pulse when active
        pulse_extra = extra if state.status != "idle" else 0
        try:
            self._draw_orb(color, radius_extra=pulse_extra)
        except Exception:
            pass

        self.root.after(50, self._animate)  # 20fps

    # ─────────────────────────────────────────
    # LISTEN TOGGLE
    # ─────────────────────────────────────────
    def _toggle_listen(self):
        if state.is_listening:
            self._stop_listening()
        else:
            self._start_listening()

    def _start_listening(self):
        state.is_listening = True
        state.status = "listening"
        try:
            self.mic_btn.config(text="⏹  STOP", fg=C["red"])
        except Exception:
            pass

        def listen_loop():
            try:
                sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
                from voice import start_listening as voice_listen
                from main import run_agent

                for goal in voice_listen():
                    if not state.is_listening:
                        break
                    if not goal:
                        continue
                    if "exit" in goal or "stop" in goal:
                        break

                    state.last_command = goal
                    state.status = "thinking"
                    add_to_history("user", goal)

                    try:
                        run_agent(goal)
                        add_to_history("ai", f"Executed: {goal}")
                    except Exception as e:
                        add_to_history("ai", f"Error: {e}")

                    state.status = "idle"

            except Exception as e:
                print(f"Listen loop error: {e}")
                state.status = "error"
            finally:
                state.is_listening = False
                state.status = "idle"
                try:
                    self.mic_btn.config(text="🎤  LISTEN", fg=C["green"])
                except Exception:
                    pass

        state.agent_thread = threading.Thread(target=listen_loop, daemon=True)
        state.agent_thread.start()

    def _stop_listening(self):
        state.is_listening = False
        state.status = "idle"
        try:
            self.mic_btn.config(text="🎤  LISTEN", fg=C["green"])
        except Exception:
            pass

    # ─────────────────────────────────────────
    # QUIT
    # ─────────────────────────────────────────
    def _quit(self):
        state.is_running   = False
        state.is_listening = False
        try:
            self.root.quit()
            self.root.destroy()
        except Exception:
            pass
        os._exit(0)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
def launch_ui():
    root = tk.Tk()
    root.withdraw()
    app = HamiltonUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_ui()
