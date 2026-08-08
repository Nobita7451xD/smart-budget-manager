import customtkinter as ctk
from utils.theme import *

class SplashScreen:

    def __init__(self):

        self.root = ctk.CTk()
        self.root.title("Smart Budget Manager")
        self.root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(fg_color=BG_COLOR)

        # ---------------- Title ---------------- #

        ctk.CTkLabel(
            self.root,
            text="💰",
            font=("Segoe UI Emoji", 80)
        ).pack(pady=(130, 20))

        ctk.CTkLabel(
            self.root,
            text="SMART BUDGET",
            font=TITLE_FONT,
            text_color="white"
        ).pack()

        ctk.CTkLabel(
            self.root,
            text="Personal Finance Manager",
            font=NORMAL_FONT,
            text_color=TEXT_SECONDARY
        ).pack(pady=10)

        # ---------------- Progress ---------------- #

        self.progress = ctk.CTkProgressBar(
            self.root,
            width=500,
            height=15
        )
        self.progress.pack(pady=60)

        self.progress.set(0)
        self.value = 0

        self.load()

        self.root.mainloop()

    def load(self):

        if self.value < 100:

            self.progress.set(self.value / 100)
            self.value += 2

            self.root.after(40, self.load)

        else:

            self.root.destroy()

            from modules.login import LoginPage
            LoginPage()