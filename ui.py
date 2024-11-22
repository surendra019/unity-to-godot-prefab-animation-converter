import tkinter as tk
from tkinter import filedialog, messagebox
import utils
from tkinter import ttk


prefab_parser_function = None
directory = None
reference_folder = None
progress_bar = None

# Create the main UI window
def create_ui():
    window = tk.Tk()
    window.title("Unity to Godot Prefab Converter")

    # Create a button to load a prefab file
    load_button = tk.Button(window, text="Load Prefab", command=lambda: load_prefab())
    load_button.pack(pady=10)
    
    global progress_bar
    # Create a progress bar
    progress_bar = ttk.Progressbar(window, length=200, mode="determinate")
    # Start the UI loop
    window.mainloop()

# called from outside to show the progress bar.
def show_progress_bar():
    progress_bar.pack(pady=20)



# Function to open a file dialog and load the prefab
def load_prefab():
    # Open a file dialog to select the Unity prefab file
    prefab_path = filedialog.askopenfilename(title="Select a Unity Prefab", filetypes=[("Prefab Files", "*.prefab")])

    global reference_folder
    reference_folder = utils.get_reference_folder(prefab_path)

    global directory
    directory = utils.get_directory_path(prefab_path)

    if prefab_path and prefab_parser_function:
        prefab_parser_function(prefab_path)
