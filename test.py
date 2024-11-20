import unityparser
from tkinter import filedialog
import os

string = "hello\n\ntoo"
track = (
    f"tracks/{0}/type = \"value\"\n"
    f"tracks/{0}/imported = false\n"
    f"tracks/{0}/enabled = true\n"
    f"tracks/{0}/path = NodePath(\"{0}:rotation\")\n"
    f"tracks/{0}/interp = 1\n"
    f"tracks/{0}/loop_wrap = true\n"
    f"tracks/{0}/keys = "
    f"{{\n"
    f"\"times\": {0},\n"
    f"\"transitions\": {0},\n"
    f"\"update\": 0,\n"
    f"\"values\": {0}\n"
    f"}}\n"
)
def insert_at_index(original_string, index, substring):
    # Split the string into two parts: before and after the index
    return original_string[:index] + substring + original_string[index:]

idx = 6
string = insert_at_index(string, idx, track)
idx += len(track)
string = insert_at_index(string, idx, track)
idx += len(track)
string = insert_at_index(string, idx, track)



print(string)