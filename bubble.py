import tkinter as tk
import json
import os
import winsound
import threading
from datetime import datetime
import time
import math

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reminders.json")

def load_reminders():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_reminders(reminders):
    with open(DATA_FILE, "w") as f:
        json.dump(reminders, f, indent=2)

def play_sound():
    try:
        winsound.MessageBeep(winsound.MB_OK)
        threading.Timer(0.12, lambda: winsound.Beep(523, 200)).start()
        threading.Timer(0.26, lambda: winsound.Beep(659, 250)).start()
        threading.Timer(0.42, lambda: winsound.Beep(784, 350)).start()
    except:
        pass


class ReminderBubble:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ReminderBubble")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="black")
        self.root.wm_attributes("-transparentcolor", "black")

        self.bubble_size = 64
        self.glow_pad = 42
        self.canvas_size = self.bubble_size + self.glow_pad * 2
        self.center = self.canvas_size // 2
        self.r = self.bubble_size // 2

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.bx = sw - 102
        self.by = sh - 132
        self.root.geometry(f"{self.canvas_size}x{self.canvas_size}+{self.bx}+{self.by}")

        self.drag_data = {"x": 0, "y": 0}
        self.panel_open = False
        self.pulse_phase = 0.0

        self.canvas = tk.Canvas(
            self.root,
            width=self.canvas_size,
            height=self.canvas_size,
            bg="black",
            highlightthickness=0,
        )
        self.canvas.pack()

        self.build_bubble()
        self.bind_events()

        self.panel = None
        self.reminders = load_reminders()
        self.check_thread_active = True
        self.start_checker()

        self.pulse_loop()

        self.root.mainloop()

    def where(self, k):
        return self.center - self.r - k, self.center - self.r - k, self.center + self.r + k, self.center + self.r + k

    def build_bubble(self):
        # ---- soft aura (fake "box-shadow" glow) ----
        layers = [
            (30,  "#20134a", "gray50"),
            (22,  "#2c1b5e", "gray50"),
            (15,  "#3b2676", "gray50"),
            (9,   "#4c3394", "gray50"),
            (4,   "#5b3fb0", "gray50"),
        ]
        for k, col, st in layers:
            self.canvas.create_oval(*self.where(k), fill=col, outline="", stipple=st)

        # ---- gradient circle (fake #6366f1 -> #8b5cf6) ----
        self.canvas.create_oval(*self.where(0), fill="#6d4bd8", outline="", tags="bubble")
        self.canvas.create_oval(*self.where(0), fill="#8b5cf6", outline="", tags="bubble")
        self.canvas.create_oval(*self.where(0), fill="#a78bfa", outline="", tags="bubble")

        self.canvas.create_oval(
            self.center - self.r, self.center - self.r,
            self.center + self.r, self.center + self.r,
            fill="", outline="#c4b5fd", width=2.5, tags="bubble",
        )

        # soft white highlight on the top-left (fake gloss)
        hi_x = self.center - self.r * 0.45
        hi_y = self.center - self.r * 0.5
        self.canvas.create_oval(
            hi_x - 6, hi_y - 4, hi_x + 14, hi_y + 10,
            fill="#ffffff", outline="", stipple="gray50", tags="bubble",
        )

        self.excl = self.canvas.create_text(
            self.center, self.center,
            text="!", fill="white", font=("Segoe UI", 24, "bold"), tags="bubble",
        )

    def bind_events(self):
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.show_menu)
        self.root.bind("<Escape>", lambda e: self.quit_app())

    # ---------- the one expanding ring (like the CSS pulse) ----------
    def pulse_loop(self):
        self.pulse_phase += 0.05
        if self.pulse_phase > math.pi * 2:
            self.pulse_phase -= math.pi * 2

        progress = self.pulse_phase / (math.pi * 2)          # 0 -> 1
        expand = 0.6 + 1.0 * progress                         # 0.6 -> 1.6
        fade = 0.85 * (1 - progress)                          # 0.85 -> 0

        k = (self.r + 4) * expand - self.r
        color_r, color_g, color_b = 196, 182, 253
        rgb = [max(0, int(c * fade)) for c in (color_r, color_g, color_b)]
        color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

        self.canvas.delete("pulse")
        self.canvas.create_oval(
            *self.where(k), fill="", outline=color, width=3, tags="pulse",
        )

        # pulse ring always behind the bubble
        self.canvas.tag_lower("pulse")
        self.canvas.tag_raise("bubble")
        self.canvas.tag_raise("glow_front")

        self.root.after(30, self.pulse_loop)

    # ---------- drag anywhere ----------
    def on_press(self, event):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.drag_data["moved"] = False
        self.drag_data["was_on_bubble"] = self.clicked_on_bubble(event)

    def clicked_on_bubble(self, event):
        dx = event.x - self.center
        dy = event.y - self.center
        return (dx * dx + dy * dy) <= self.r * self.r

    def on_drag(self, event):
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        if abs(dx) > 3 or abs(dy) > 3:
            self.drag_data["moved"] = True
        self.bx += dx
        self.by += dy
        self.root.geometry(f"+{self.bx}+{self.by}")

    def on_release(self, event):
        if (not self.drag_data["moved"]) and self.drag_data["was_on_bubble"]:
            self.toggle_panel()

    # ---------- right-click menu ----------
    def show_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0, bg="#1e293b", fg="#e2e8f0",
                       activebackground="#6d4bd8", activeforeground="white",
                       font=("Segoe UI", 10), relief="flat")
        menu.add_command(label="Open reminders", command=self.toggle_panel)
        menu.add_separator()
        menu.add_command(label="Quit", command=self.quit_app)
        menu.tk_popup(event.x_root, event.y_root)

    def quit_app(self):
        self.check_thread_active = False
        if self.panel:
            self.panel.destroy()
        self.root.destroy()

    def toggle_panel(self):
        play_sound()
        if self.panel_open:
            self.close_panel()
        else:
            self.open_panel()

    # ---------- reminders panel ----------
    def open_panel(self):
        if self.panel:
            self.close_panel()

        self.panel = tk.Toplevel(self.root)
        self.panel.overrideredirect(True)
        self.panel.attributes("-topmost", True)
        self.panel.configure(bg="#1e293b")

        pw, ph = 340, 420
        px = min(self.bx - pw - 10, self.root.winfo_screenwidth() - pw - 10)
        px = max(px, 10)
        py = max(self.by - ph, 10)
        self.panel.geometry(f"{pw}x{ph}+{px}+{py}")

        top = tk.Frame(self.panel, bg="#1e293b")
        top.pack(fill="x", padx=14, pady=(12, 0))

        tk.Label(top, text="Reminders", bg="#1e293b", fg="#e2e8f0",
                 font=("Segoe UI", 15, "bold"), anchor="w").pack(side="left")

        close_btn = tk.Label(top, text="\u2715", bg="#1e293b", fg="#94a3b8",
                             font=("Segoe UI", 13), cursor="hand2")
        close_btn.pack(side="right")
        close_btn.bind("<Button-1>", lambda e: self.close_panel())

        quit_btn = tk.Label(top, text="Quit", bg="#1e293b", fg="#f87171",
                            font=("Segoe UI", 9), cursor="hand2")
        quit_btn.pack(side="right", padx=(0, 10))
        quit_btn.bind("<Button-1>", lambda e: self.quit_app())

        sub = tk.Label(self.panel, text="Click + to add, circle to close",
                       bg="#1e293b", fg="#64748b", font=("Segoe UI", 9), anchor="w")
        sub.pack(fill="x", padx=14, pady=(2, 6))

        add_frame = tk.Frame(self.panel, bg="#1e293b")
        add_frame.pack(fill="x", padx=14, pady=(0, 8))

        self.entry_text = tk.Entry(add_frame, bg="#0f172a", fg="#e2e8f0",
                                   insertbackground="#e2e8f0", font=("Segoe UI", 11),
                                   relief="flat", bd=0)
        self.entry_text.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 6))
        self.entry_text.bind("<Return>", lambda e: self.add_reminder())

        self.entry_time = tk.Entry(add_frame, bg="#0f172a", fg="#94a3b8",
                                   font=("Segoe UI", 10), relief="flat", bd=0, width=7)
        self.entry_time.pack(side="left", ipady=6, padx=(0, 6))
        self.entry_time.insert(0, "14:30")
        self.entry_time.bind("<FocusIn>", lambda e: (
            self.entry_time.delete(0, "end") if self.entry_time.get() == "14:30" else None))
        self.entry_time.bind("<FocusOut>", lambda e: (
            self.entry_time.insert(0, "14:30") if not self.entry_time.get() else None))

        add_btn = tk.Label(add_frame, text="+", bg="#6d4bd8", fg="white",
                           font=("Segoe UI", 14, "bold"), cursor="hand2", padx=10)
        add_btn.pack(side="left", ipady=2)
        add_btn.bind("<Button-1>", lambda e: self.add_reminder())

        sep = tk.Frame(self.panel, bg="#334155", height=1)
        sep.pack(fill="x", padx=14, pady=(0, 6))

        self.list_frame = tk.Frame(self.panel, bg="#1e293b")
        self.list_frame.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        self.render_list()
        self.panel_open = True

    def close_panel(self):
        if self.panel:
            self.panel.destroy()
            self.panel = None
        self.panel_open = False

    def render_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        now_str = datetime.now().strftime("%H:%M")

        if not self.reminders:
            tk.Label(self.list_frame, text="No reminders yet.\nAdd one above!",
                     bg="#1e293b", fg="#64748b", font=("Segoe UI", 10),
                     justify="center").pack(pady=40)
            return

        for i, r in enumerate(self.reminders):
            bg_color = "#0f172a"
            if r.get("time") and r["time"] == now_str:
                bg_color = "#1e1b4b"

            frame = tk.Frame(self.list_frame, bg=bg_color, padx=10, pady=6)
            frame.pack(fill="x", pady=3)

            left = tk.Frame(frame, bg=bg_color)
            left.pack(side="left", fill="x", expand=True)

            tk.Label(left, text=r["text"], bg=bg_color,
                     fg="#e2e8f0", font=("Segoe UI", 11), anchor="w", wraplength=220).pack(anchor="w")

            if r.get("time"):
                tk.Label(left, text=f"Due {r['time']}", bg=bg_color,
                         fg="#94a3b8", font=("Segoe UI", 8), anchor="w").pack(anchor="w")

            del_btn = tk.Label(frame, text="\u2715", bg=bg_color, fg="#f87171",
                               font=("Segoe UI", 12), cursor="hand2")
            del_btn.pack(side="right", padx=(6, 0))
            del_btn.bind("<Button-1>", lambda e, idx=i: self.delete_reminder(idx))

    def add_reminder(self):
        text = self.entry_text.get().strip()
        time_val = self.entry_time.get().strip()
        if not text:
            return
        if time_val:
            try:
                datetime.strptime(time_val, "%H:%M")
            except ValueError:
                return
        self.reminders.append({"text": text, "time": time_val, "last_fired": ""})
        save_reminders(self.reminders)
        self.entry_text.delete(0, "end")
        self.entry_time.delete(0, "end")
        self.entry_time.insert(0, "14:30")
        self.render_list()

    def delete_reminder(self, idx):
        if 0 <= idx < len(self.reminders):
            self.reminders.pop(idx)
            save_reminders(self.reminders)
            self.render_list()

    def fire_reminder(self, r, idx):
        now_str = datetime.now().strftime("%H:%M")
        self.reminders[idx]["last_fired"] = now_str
        save_reminders(self.reminders)
        play_sound()
        self.blink_bubble()

    def blink_bubble(self):
        for k in range(6):
            delay = k * 150
            self.root.after(delay, lambda k=k: self._flash_ring(k))

    def _flash_ring(self, k):
        pad = 8 + k * 6
        flash = self.canvas.create_oval(
            *self.where(pad), fill="", outline="#fbbf24", width=4, tags="flash",
        )
        self.canvas.tag_lower("flash")
        self.canvas.tag_lower("pulse")
        self.root.after(100, lambda f=flash: self.canvas.delete(f))

    def start_checker(self):
        def check():
            while self.check_thread_active:
                now_str = datetime.now().strftime("%H:%M")
                for i, r in enumerate(self.reminders):
                    if r.get("time") and r["time"] == now_str and r.get("last_fired") != now_str:
                        self.root.after(0, lambda idx=i: self.fire_reminder(self.reminders[idx], idx))
                time.sleep(20)
        t = threading.Thread(target=check, daemon=True)
        t.start()


if __name__ == "__main__":
    ReminderBubble()