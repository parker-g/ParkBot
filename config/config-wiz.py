from tkinter import ttk
import tkinter as tk
import sys

# provide a GUI for users to enter the required information needed to setup the bot's configuration

class ConfigWizard:

    def __init__(self):
        pass

    def createConfigGUI(self):
        root = tk.Tk()
        self.frame = ttk.Frame(root, padding=10)
        self.frame.grid()

        # root = tk.Tk()
        # frm = frame
        # frm = ttk.Frame(root, padding=10)
        # frm.grid()
        # ttk.Label(frm, text="Hello World!").grid(column=0, row=0)
        # ttk.Button(frm, text="Quit", command=root.destroy).grid(column=1, row=0)
        # root.mainloop()