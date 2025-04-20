import customtkinter as ctk
import threading
from tkinter import END

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

import journey_companion

gui_textbox = None

def write_to_gui(message):
    global gui_textbox
    if gui_textbox:
        gui_textbox.configure(state="normal")         # Make it editable temporarily
        gui_textbox.insert("end", message + "\n")     # Add new message at the bottom
        gui_textbox.configure(state="disabled")       # Make it read-only again
        gui_textbox.see("end")     

def run_assistant():
    journey_companion.main(write_to_gui)

def start_assistant():
    log_textbox.insert(END, "Assistant starting...\n")
    log_textbox.see(END)
    assistant_thread = threading.Thread(target=run_assistant)
    assistant_thread.start()


app = ctk.CTk()
app.geometry("600x400")
app.title("Journey Companion - Voice Assistant")

title_label = ctk.CTkLabel(app, text="Journey Companion", font=ctk.CTkFont(size=24, weight="bold"))
title_label.pack(pady=20)

start_button = ctk.CTkButton(app, text="Start Assistant", command=start_assistant)
start_button.pack(pady=10)

log_textbox = ctk.CTkTextbox(app, height=200, width=500)
log_textbox.pack(pady=10)
log_textbox.insert(END, "Welcome to Journey Companion!\n")

gui_textbox = log_textbox  # 🔗 Connect the global variable to your actual textbox


app.mainloop()
