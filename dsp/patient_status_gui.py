"""Live person/robot detection display (legacy filename kept for existing imports)."""

import tkinter as tk
from tkinter import ttk


class DetectionStatusGUI:
    STATUS_COLORS = {
        "Person detected": "#65d6a4",
        "Robot detected": "#69b7ff",
        "Nothing detected": "#b1bac8",
    }

    def __init__(self, location_label="RIS Corner", placeholder_mode=True):
        self.root = tk.Tk()
        self.root.title("RIS Corner - Live detection")
        self.root.geometry("820x560")
        self.root.minsize(640, 480)
        self.root.configure(bg="#0d1117")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Escape>", self.exit_fullscreen)
        self.is_open = True
        self.stop_requested = False

        container = tk.Frame(self.root, bg="#0d1117", padx=36, pady=28)
        container.pack(fill="both", expand=True)
        self._label(container, location_label.upper(), 12, "#8b98ab").pack(anchor="w")
        self._label(container, "Live radar detection", 24, "#f6f7fb", "bold").pack(
            anchor="w", pady=(4, 12)
        )
        if placeholder_mode:
            self._label(
                container, "Placeholder model - results are for interface testing", 11, "#e4bd71"
            ).pack(anchor="w")

        result = tk.Frame(container, bg="#161d29", padx=20, pady=20)
        result.pack(fill="both", expand=True, pady=24)
        self.status_text = tk.Label(
            result, text="\u2014", bg="#161d29", fg="#b1bac8", font=("Segoe UI", 32, "bold")
        )
        self.status_text.pack(expand=True)
        self.result_detail = tk.Label(
            result, text="Waiting for the first prediction", bg="#161d29",
            fg="#8b98ab", font=("Segoe UI", 11)
        )
        self.result_detail.pack(pady=(0, 8))

        legend = tk.Frame(container, bg="#0d1117")
        legend.pack(fill="x")
        for status, color in self.STATUS_COLORS.items():
            self._label(legend, status, 11, color).pack(side="left", expand=True)

        self.recording_text = self._label(container, "Ready to record", 11, "#b1bac8")
        self.recording_text.pack(anchor="w", pady=(24, 6))
        self.progress = ttk.Progressbar(container, mode="determinate")
        self.progress.pack(fill="x")
        self.stop_button = tk.Button(
            container, text="Stop recording", command=self.request_stop,
            bg="#26364b", fg="#f6f7fb", activebackground="#334966",
            activeforeground="#ffffff", relief="flat", padx=16, pady=8,
            font=("Segoe UI", 11), cursor="hand2"
        )
        self.stop_button.pack(anchor="e", pady=(16, 0))

    @staticmethod
    def _label(parent, text, size, color, weight="normal"):
        return tk.Label(
            parent, text=text, bg="#0d1117", fg=color,
            font=("Segoe UI", size, weight), anchor="w"
        )

    def update_status(self, status):
        if status not in self.STATUS_COLORS:
            raise ValueError(f"Unsupported detection status: {status}")
        if self.is_open:
            self.status_text.configure(text=status, fg=self.STATUS_COLORS[status])
            self.result_detail.configure(text="Latest result from recent radar frames")

    def update_progress(self, frame_count, total_frames):
        if self.is_open:
            self.progress.configure(maximum=total_frames, value=frame_count)
            self.recording_text.configure(text=f"Recording frame {frame_count} / {total_frames}")

    def set_recording_status(self, message):
        if self.is_open:
            self.recording_text.configure(text=message)

    def finish(self, message):
        """Keep the last detection visible after acquisition ends."""
        if self.is_open:
            self.set_recording_status(message)
            self.result_detail.configure(text="Recording ended - result is no longer live")
            self.stop_button.configure(text="Close", command=self.close, state="normal")

    def request_stop(self):
        self.stop_requested = True
        if self.is_open:
            self.stop_button.configure(text="Stopping...", state="disabled")

    def pump(self):
        if self.is_open:
            try:
                self.root.update_idletasks()
                self.root.update()
            except tk.TclError:
                self.is_open = False
                self.stop_requested = True

    def wait_until_closed(self):
        if self.is_open:
            self.root.mainloop()

    def close(self):
        self.stop_requested = True
        self.is_open = False
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def exit_fullscreen(self, event=None):
        self.root.attributes("-fullscreen", False)


# Keep the previous import name available to callers of this module.
PatientStatusGUI = DetectionStatusGUI
