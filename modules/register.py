import customtkinter as ctk
from tkinter import messagebox
import sqlite3

from utils.theme import *


class RegisterPage:

    def __init__(self):

        self.root = ctk.CTk()
        self.root.title("Create Account")
        self.root.geometry(f"{APP_WIDTH}x{APP_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(fg_color=BG_COLOR)

        # ================= LEFT =================

        left = ctk.CTkFrame(
            self.root,
            width=500,
            fg_color=PRIMARY,
            corner_radius=0
        )

        left.pack(side="left", fill="both")

        ctk.CTkLabel(
            left,
            text="📝",
            font=("Segoe UI Emoji", 80)
        ).pack(pady=(120,20))

        ctk.CTkLabel(
            left,
            text="CREATE\nACCOUNT",
            font=("Segoe UI",36,"bold"),
            justify="center"
        ).pack()

        ctk.CTkLabel(
            left,
            text="Smart Budget Manager",
            font=("Segoe UI",16)
        ).pack(pady=20)

        # ================= RIGHT =================

        right = ctk.CTkFrame(
            self.root,
            fg_color=BG_COLOR,
            corner_radius=0
        )

        right.pack(side="right", fill="both", expand=True)

        ctk.CTkLabel(
            right,
            text="Create Your Account",
            font=("Segoe UI",28,"bold")
        ).pack(pady=(80,20))

        self.username = ctk.CTkEntry(
            right,
            width=320,
            height=45,
            placeholder_text="Username"
        )

        self.username.pack(pady=10)

        self.password = ctk.CTkEntry(
            right,
            width=320,
            height=45,
            placeholder_text="Password",
            show="*"
        )

        self.password.pack(pady=10)

        self.confirm = ctk.CTkEntry(
            right,
            width=320,
            height=45,
            placeholder_text="Confirm Password",
            show="*"
        )

        self.confirm.pack(pady=10)

        ctk.CTkButton(
            right,
            text="Create Account",
            width=320,
            height=45,
            command=self.register
        ).pack(pady=25)

        ctk.CTkButton(
            right,
            text="Back to Login",
            width=320,
            height=45,
            fg_color="transparent",
            border_width=2,
            command=self.back_login
        ).pack()

        self.root.mainloop()

    def register(self):

        username = self.username.get()
        password = self.password.get()
        confirm = self.confirm.get()

        if username == "" or password == "" or confirm == "":
            messagebox.showerror("Error", "All fields are required.")
            return

        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        conn = sqlite3.connect("finance.db")
        cursor = conn.cursor()

        try:

            cursor.execute(
                "INSERT INTO users(username,password) VALUES(?,?)",
                (username, password)
            )

            conn.commit()

            messagebox.showinfo("Success", "Account Created Successfully!")

            self.root.destroy()

            from modules.login import LoginPage
            LoginPage()

        except sqlite3.IntegrityError:

            messagebox.showerror(
                "Error",
                "Username already exists."
            )

        conn.close()

    def back_login(self):

        self.root.destroy()

        from modules.login import LoginPage

        LoginPage()