import customtkinter as ctk
from tkinter import messagebox
import sqlite3

from utils.theme import *


class LoginPage:

    def __init__(self):

        self.root = ctk.CTk()
        self.root.title("Smart Budget Manager")
        self.root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(fg_color=BG_COLOR)

        # LEFT PANEL
        left = ctk.CTkFrame(
            self.root,
            width=500,
            fg_color=PRIMARY,
            corner_radius=0
        )
        left.pack(side="left", fill="both")

        ctk.CTkLabel(
            left,
            text="💰",
            font=("Segoe UI Emoji", 80)
        ).pack(pady=(130, 20))

        ctk.CTkLabel(
            left,
            text="SMART\nBUDGET",
            font=("Segoe UI", 36, "bold"),
            justify="center"
        ).pack()

        ctk.CTkLabel(
            left,
            text="Personal Finance Manager",
            font=("Segoe UI", 16)
        ).pack(pady=20)

        # RIGHT PANEL
        right = ctk.CTkFrame(
            self.root,
            fg_color=BG_COLOR,
            corner_radius=0
        )
        right.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(
            right,
            text="Welcome Back 👋",
            font=("Segoe UI", 30, "bold")
        ).pack(pady=(120, 15))

        ctk.CTkLabel(
            right,
            text="Login to continue",
            font=("Segoe UI", 15)
        ).pack()

        self.username = ctk.CTkEntry(
            right,
            width=320,
            height=45,
            placeholder_text="Username"
        )
        self.username.pack(pady=(40, 15))

        self.password = ctk.CTkEntry(
            right,
            width=320,
            height=45,
            placeholder_text="Password",
            show="*"
        )
        self.password.pack()

        # Pressing Enter in either input field signs the user in.
        self.username.bind("<Return>", lambda event: self.login())
        self.password.bind("<Return>", lambda event: self.login())

        self.show = ctk.CTkCheckBox(
            right,
            text="Show Password",
            command=self.toggle_password
        )
        self.show.pack(pady=15)

        ctk.CTkButton(
            right,
            text="Login",
            width=320,
            height=45,
            command=self.login
        ).pack(pady=15)

        ctk.CTkButton(
            right,
            text="Create Account",
            width=320,
            height=45,
            fg_color="transparent",
            border_width=2,
            command=self.open_register
        ).pack()

        # Let the user start typing immediately when the page opens.
        self.username.focus_set()

        self.root.mainloop()

    def toggle_password(self):

        if self.show.get():
            self.password.configure(show="")
        else:
            self.password.configure(show="*")

    def login(self):

        username = self.username.get()
        password = self.password.get()

        conn = sqlite3.connect("finance.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cursor.fetchone()
        conn.close()

        if user:
            self.root.destroy()

            from modules.dashboard import Dashboard
            Dashboard(username)

        else:
            messagebox.showerror(
                "Login Failed",
                "Wrong Username or Password"
            )

    def open_register(self):

        self.root.destroy()

        from modules.register import RegisterPage
        RegisterPage()
