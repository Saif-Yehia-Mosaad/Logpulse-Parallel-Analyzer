import tkinter as tk
from tkinter import filedialog, ttk
import threading

import sequential
import parallel

BG     = "#0d0d0d"
PANEL  = "#111111"
CARD   = "#1a1a1a"
BORDER = "#2a2a2a"
TEXT   = "#ffffff"
MUTED  = "#888888"
GREEN  = "#00ff9c"
RED    = "#ff4444"
ACCENT = "#ffffff"


class Dashboard:
    def __init__(self, root, run_seq=None, run_par=None):
        self.root    = root
        self.run_seq = run_seq or sequential.run_sequential
        self.run_par = run_par or parallel.run_parallel

        self.root.title("Logpulse Analyzer Dashboard")
        self.root.geometry("1100x700")
        self.root.configure(bg=BG)
        self.root.resizable(True, True)

        self.files   = []
        self._running = False

        self._build_ui()

    # ─────────────────────────────────────────
    #  UI BUILD
    # ─────────────────────────────────────────
    def _build_ui(self):
        self._build_topbar()
        self._build_subbar()
        self._build_panels()
        self._build_bottom()

    # ── Top bar ──────────────────────────────
    def _build_topbar(self):
        bar = tk.Frame(self.root, bg=BG, height=48)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # ← Return
        tk.Button(
            bar, text="← Return", bg=BG, fg=MUTED,
            relief="flat", activebackground=BG, activeforeground=TEXT,
            font=("Segoe UI", 10), cursor="hand2",
            command=self.root.destroy
        ).pack(side="left", padx=14, pady=10)

        # Status (right)
        self.status_lbl = tk.Label(
            bar, text="Status: Idle",
            bg=BG, fg=GREEN, font=("Segoe UI", 10, "bold")
        )
        self.status_lbl.pack(side="right", padx=14)

        # Start Analysis button (right)
        self.start_btn = tk.Button(
            bar, text="Start Analysis",
            bg=ACCENT, fg="#000000",
            relief="flat", activebackground="#cccccc",
            font=("Segoe UI", 10, "bold"),
            padx=16, pady=4, cursor="hand2",
            command=self._start
        )
        self.start_btn.pack(side="right", padx=6)

        # Halt button (right)
        self.halt_btn = tk.Button(
            bar, text="Halt",
            bg=BG, fg=MUTED,
            relief="flat", activebackground=BORDER, activeforeground=TEXT,
            font=("Segoe UI", 10),
            padx=12, pady=4, cursor="hand2",
            command=self._halt
        )
        self.halt_btn.pack(side="right", padx=2)

    # ── Sub bar (upload + file count) ────────
    def _build_subbar(self):
        bar = tk.Frame(self.root, bg=BG)
        bar.pack(fill="x", padx=14, pady=(0, 6))

        tk.Button(
            bar, text="Upload Logs",
            bg=BG, fg=TEXT,
            relief="solid", bd=1,
            highlightbackground=BORDER,
            font=("Segoe UI", 9),
            padx=10, pady=3, cursor="hand2",
            command=self._upload
        ).pack(side="left")

        self.file_lbl = tk.Label(
            bar, text="0 logs staged",
            bg=BG, fg=MUTED, font=("Segoe UI", 9)
        )
        self.file_lbl.pack(side="left", padx=10)

    # ── Two result panels ─────────────────────
    def _build_panels(self):
        container = tk.Frame(self.root, bg=BG)
        container.pack(fill="both", expand=True, padx=10)

        # خلي الأعمدة تتمدد بالتساوي
        container.columnconfigure(0, weight=1)
        container.columnconfigure(1, weight=1)
        container.rowconfigure(0, weight=1)

        self.seq_panel = self._make_panel(container, "Sequential System Results")
        self.seq_panel["frame"].grid(row=0, column=0, sticky="nsew", padx=(0, 5))

        self.par_panel = self._make_panel(container, "Parallel System Results")
        self.par_panel["frame"].grid(row=0, column=1, sticky="nsew", padx=(5, 0))

    def _make_panel(self, parent, title):
        outer = tk.Frame(parent, bg=BORDER, bd=1)

        inner = tk.Frame(outer, bg=PANEL)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        # Title
        tk.Label(
            inner, text=title,
            bg=PANEL, fg=TEXT,
            font=("Segoe UI", 11, "bold"),
            anchor="w"
        ).pack(fill="x", padx=14, pady=(10, 4))

        # Progress bar
        style_name = f"p{id(outer)}.Horizontal.TProgressbar"
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            style_name,
            troughcolor=CARD,
            background=GREEN,
            thickness=6
        )
        pbar = ttk.Progressbar(
            inner, style=style_name,
            orient="horizontal", mode="determinate", maximum=100
        )
        pbar.pack(fill="x", padx=14, pady=(0, 10))

        # Time + Errors row
        metrics_row = tk.Frame(inner, bg=PANEL)
        metrics_row.pack(fill="x", padx=14, pady=(0, 10))

        time_card  = self._metric_card(metrics_row, "Total Time",   "0.00 sec", GREEN)
        time_card["frame"].pack(side="left", fill="both", expand=True, padx=(0, 6))

        err_card   = self._metric_card(metrics_row, "Total Errors", "0",        RED)
        err_card["frame"].pack(side="left", fill="both", expand=True)

        # Common + Freq row
        boxes_row = tk.Frame(inner, bg=PANEL)
        boxes_row.pack(fill="both", expand=True, padx=14, pady=(0, 12))

        common_frame = self._text_box(boxes_row, "Most Common Errors")
        common_frame["frame"].pack(side="left", fill="both", expand=True, padx=(0, 6))

        freq_frame = self._text_box(boxes_row, "Errors Per Minute")
        freq_frame["frame"].pack(side="left", fill="both", expand=True)

        return {
            "frame":   outer,
            "pbar":    pbar,
            "time":    time_card["value"],
            "errors":  err_card["value"],
            "common":  common_frame["text"],
            "freq":    freq_frame["text"],
        }

    def _metric_card(self, parent, label, default, color):
        card = tk.Frame(parent, bg=CARD, bd=1, relief="flat",
                        highlightbackground=BORDER, highlightthickness=1)

        tk.Label(
            card, text=label,
            bg=CARD, fg=MUTED,
            font=("Segoe UI", 8, "bold"),
            anchor="w"
        ).pack(fill="x", padx=10, pady=(8, 0))

        val = tk.Label(
            card, text=default,
            bg=CARD, fg=color,
            font=("Segoe UI", 22, "bold"),
            anchor="w"
        )
        val.pack(fill="x", padx=10, pady=(2, 10))

        return {"frame": card, "value": val}

    def _text_box(self, parent, title):
        frame = tk.Frame(parent, bg=CARD,
                         highlightbackground=BORDER, highlightthickness=1)

        tk.Label(
            frame, text=title,
            bg=CARD, fg=TEXT,
            font=("Segoe UI", 9, "bold"),
            anchor="w"
        ).pack(fill="x", padx=8, pady=(6, 2))

        txt = tk.Text(
            frame,
            bg="#0a0a0a", fg="#cccccc",
            font=("Consolas", 8),
            relief="flat", bd=0,
            selectbackground=BORDER,
            insertbackground=TEXT,
            wrap="word"
        )
        txt.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        return {"frame": frame, "text": txt}

    # ── Bottom conclusion bar ─────────────────
    def _build_bottom(self):
        bottom = tk.Frame(self.root, bg=CARD,
                          highlightbackground=BORDER, highlightthickness=1)
        bottom.pack(fill="x", padx=10, pady=(4, 10))

        tk.Label(
            bottom, text="Performance Conclusion",
            bg=CARD, fg=TEXT,
            font=("Segoe UI", 9, "bold"),
            anchor="w"
        ).pack(fill="x", padx=14, pady=(8, 2))

        self.conclusion = tk.Label(
            bottom, text="Run an analysis to see results.",
            bg=CARD, fg=MUTED,
            font=("Segoe UI", 10),
            anchor="w"
        )
        self.conclusion.pack(fill="x", padx=14, pady=(0, 10))

    # ─────────────────────────────────────────
    #  LOGIC
    # ─────────────────────────────────────────
    def _upload(self):
        files = filedialog.askopenfilenames(filetypes=[("Log Files", "*.log")])
        if files:
            self.files = list(files)
            self.file_lbl.config(text=f"{len(self.files)} logs staged")

    def _halt(self):
        # إشارة للـ background thread — في الإصدار ده بيغيّر الـ status بس
        self._running = False
        self.status_lbl.config(text="Status: Halted", fg=RED)
        self.start_btn.config(state="normal")

    def _start(self):
        if not self.files or self._running:
            return

        self._running = True
        self.start_btn.config(state="disabled")
        self.status_lbl.config(text="Status: Running...", fg=GREEN)

        # reset progress bars
        self.seq_panel["pbar"]["value"] = 0
        self.par_panel["pbar"]["value"] = 0

        threading.Thread(target=self._run_background, daemon=True).start()

    def _run_background(self):
        # Sequential
        self.root.after(0, lambda: self.seq_panel["pbar"].config(value=50))
        seq = self.run_seq(self.files)
        self.root.after(0, lambda: self.seq_panel["pbar"].config(value=100))

        if not self._running:
            return

        # Parallel
        self.root.after(0, lambda: self.par_panel["pbar"].config(value=50))
        par = self.run_par(self.files)
        self.root.after(0, lambda: self.par_panel["pbar"].config(value=100))

        self.root.after(0, self._finish_ui, seq, par)

    def _finish_ui(self, seq, par):
        self._update_panel(self.seq_panel, seq)
        self._update_panel(self.par_panel, par)

        s_t = seq["time"]
        p_t = par["time"]
        diff = s_t - p_t
        pct  = (diff / s_t * 100) if s_t else 0

        if pct > 0:
            verdict = f"Parallel engine is {pct:.1f}% faster! ✓"
            color   = GREEN
        else:
            verdict = f"Sequential was {abs(pct):.1f}% faster this time."
            color   = RED

        self.conclusion.config(
            text=(
                f"Sequential Time: {s_t:.2f} s      "
                f"Parallel Time: {p_t:.2f} s      "
                f"Difference: {abs(diff):.2f} s      "
                f"{verdict}"
            ),
            fg=color
        )

        self.status_lbl.config(text="Status: Analysis Complete!", fg=GREEN)
        self.start_btn.config(state="normal")
        self._running = False

    def _update_panel(self, panel, data):
        panel["time"].config(text=f"{data['time']:.2f} sec")
        panel["errors"].config(text=str(data["total"]))

        panel["common"].config(state="normal")
        panel["common"].delete("1.0", tk.END)
        for msg, cnt in data["common"].items():
            panel["common"].insert(tk.END, f"► {msg}\n   Count: {cnt}\n\n")

        panel["freq"].config(state="normal")
        panel["freq"].delete("1.0", tk.END)
        for k, v in data["freq"].items():
            panel["freq"].insert(tk.END, f"[{k}]: {v} errors\n")


# ── Standalone run ────────────────────────────
if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()

    root = tk.Tk()
    Dashboard(root)
    root.mainloop()