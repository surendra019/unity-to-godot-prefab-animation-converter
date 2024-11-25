import tkinter as tk
from tkinter import filedialog, messagebox
import utils
from tkinter import ttk


prefab_parser_function = None
directory = None
reference_folder = None
progress_bar = None
window = None

# Create the main UI window
def create_ui():
    print(utils.get_reference_folder("C:/Users/DELL/AppData/Local/Programs/Python/Python312/python.exe"))

    global window
    window = tk.Tk()
    window.title("Unity to Godot Prefab Converter")

    # Create a button to load a prefab file
    load_button = tk.Button(window, text="Load Prefab", command=lambda: load_prefab())
    load_button.pack(pady=10)
    show_progress_bar(100)

    # Set the window size to 400x300 and center it
    center_window(window, 400, 300)
    # Start the UI loop
    window.mainloop()

# called from outside to show the progress bar.
def show_progress_bar(max_length: int):
    global progress_bar

    progress_bar = ttk.Progressbar(window, length=max_length, mode="determinate")
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


def center_window(window, width, height):
    # Get the screen width and height
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()

    # Calculate the position to center the window
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)

    # Set the window geometry (size and position)
    window.geometry(f"{width}x{height}+{x}+{y}")