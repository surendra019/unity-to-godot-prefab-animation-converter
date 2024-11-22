import re
import string
import os
import math
import random

texture_insert_position = -1
resource_ids = []


# extracts id value from a line string.
def extract_id(input_string):
    # Use a regular expression to find the id value
    match = re.search(r'id="([^"]+)"', input_string)
    if match:
        return match.group(1)  # Return the captured group (the id value)
    return None  # Return None if no match is found


# finds the line in the scene which has some substring.
def find_line_with_substring(complete_string, substring):
    # Split the complete string into lines
    lines = complete_string.splitlines()
    
    # Search for the substring in each line
    for line in lines:
        if substring in line:
            return line
    
    return False

# returns the index in the file to add line for sub_resource.
def get_insert_index_after_sub_resources(godot_scene: str) -> int:
    # Split the scene content into lines
    lines = godot_scene.splitlines(keepends=True)  # keepends=True retains newline characters
    last_ext_resource_index = -1
    cumulative_index = 0

    for i, line in enumerate(lines):
        cumulative_index += len(line)

        if line.strip().startswith('sub_resource'):
            last_ext_resource_index = cumulative_index  # Keep track of the start index in the string

    if last_ext_resource_index == -1:
        global texture_insert_position
        # If no ext_resource lines, insert at the position
        last_ext_resource_index = texture_insert_position
        

    # Return the index in the file string to insert after the last ext_resource
    return last_ext_resource_index



# returns the index in the file to add line for sub_resource.
def get_insert_index_after_ext_resources(godot_scene: str) -> int:
    # Split the scene content into lines
    lines = godot_scene.splitlines(keepends=True)  # keepends=True retains newline characters
    last_ext_resource_index = -1
    cumulative_index = 0

    for i, line in enumerate(lines):
        cumulative_index += len(line)

        if line.strip().startswith('[ext_resource'):
            last_ext_resource_index = cumulative_index  # Keep track of the start index in the string

    if last_ext_resource_index == -1:
        global texture_insert_position
        # If no ext_resource lines, insert at the position
        last_ext_resource_index = texture_insert_position

    # Return the index in the file string to insert after the last ext_resource
    return last_ext_resource_index



# inserts a string at index in the original_string and then returns the result.
def insert_at_index(original_string, index, substring):
    # Split the string into two parts: before and after the index
    # print("left -----------------------------------------------")
    # print(original_string[:index])
    # print("right-----------------------------------------------")
    # print(original_string[index:])
    return original_string[:index] + substring + original_string[index:]


        
# scans all the files with suffix (extension) in the passed directory.
def get_all_files(directory, suffix):
    png_meta_files = []  # Use a different variable name for the result list
    try:
        # Walk through the directory and subdirectories
        for root, _, files in os.walk(directory):
            for file in files:
                # Check for .png.meta extension
                if file.endswith(suffix):
                    file_path = os.path.join(root, file)
                    png_meta_files.append(file_path)
                    # print(file_path)  # Print the file path if needed
    except Exception as e:
        print(f"An error occurred: {e}")
    return png_meta_files



# convert the path to Godot's project relative path.
def convert_to_res_path(file_path, reference_folder):
    try:
        # Normalize the file path to handle both Windows and UNIX style paths
        file_path = os.path.normpath(file_path)

        # Get the absolute path of the reference folder
        reference_folder_path = os.path.normpath(reference_folder)
        
        # Check if the file path contains the reference folder
        if reference_folder_path not in file_path:
            print(f"Error: The file is not inside the reference folder '{reference_folder}'")
            return None

        # Find the position of the reference folder in the file_path
        reference_folder_pos = file_path.find(reference_folder_path)

        # If the reference folder exists, create a relative path from there
        if reference_folder_pos != -1:
            # Extract the relative path by removing the reference folder and the part before it
            relative_path = file_path[reference_folder_pos+len(reference_folder_path):]
            # Clean up the relative path to make sure it's in the correct format
            relative_path = relative_path.replace(os.sep, "/").lstrip("/")
            res_path = f"res://{reference_folder}/{relative_path}"

            return res_path
        else:
            print(f"Error: '{reference_folder}' not found in the file path.")
            return None

    except Exception as e:
        print(f"Error: {e}")
        return None


# convert degrees to radians. 
def degrees_to_radians(degrees):
    """Convert degrees to radians."""
    return degrees * math.pi / 180



# generate a random resource id.
def generate_unique_id():
    # Define the possible characters for the ID
    characters = string.ascii_letters + string.digits
    
    while True:
        # Generate a random 10-character ID
        random_id = ''.join(random.choice(characters) for _ in range(10))
        global resource_ids
        # Check if the ID is already in the id_list
        if random_id not in resource_ids:
            resource_ids.append(random_id)  # Add the new ID to the list
            return random_id  # Return the unique ID



# convert rotation in quaternion to radian.
def quaternion_to_radians(q_x, q_y, q_z, q_w):

    # Convert quaternion to Euler angles (in radians), focusing on the Z-axis (yaw)
    yaw = math.atan2(2.0 * (q_w * q_z + q_x * q_y), 1.0 - 2.0 * (q_y * q_y + q_z * q_z))
    
    # Return the rotation in radians
    return yaw


# returns the track string line by adding the values.
def get_track_string(animation_track_idx: int, node_path: string, times_string: string, transition_string: string, values_string: string, property: string):
    track = (
        f"tracks/{animation_track_idx}/type = \"value\"\n"
        f"tracks/{animation_track_idx}/imported = false\n"
        f"tracks/{animation_track_idx}/enabled = true\n"
        f"tracks/{animation_track_idx}/path = NodePath(\"{node_path}:{property}\")\n"
        f"tracks/{animation_track_idx}/interp = 1\n"
        f"tracks/{animation_track_idx}/loop_wrap = true\n"
        f"tracks/{animation_track_idx}/keys = "
        f"{{\n"
        f"\"times\": {times_string},\n"
        f"\"transitions\": {transition_string},\n"
        f"\"update\": 0,\n"
        f"\"values\": {values_string}\n"
        f"}}\n"
    )
    return track

# returns the reference folder path with respect to the .prefab file.

def get_reference_folder(file_path: str):
    # Normalize the path separator to ensure compatibility
    normalized_path = file_path.replace("\\", "/")
    
    # Extract the directory part
    directory = os.path.dirname(normalized_path)
    
    # Split the directory into parts
    parts = directory.split("/")
    
    # Get the last two folders
    previous_two_folders = "/".join(parts[-2:])

    return previous_two_folders

# returns the directory path from the file_path.
def get_directory_path(file_path):
    # Extract the directory part of the path
    directory = os.path.dirname(file_path)
    
    # Split the directory into parts
    parts = directory.split(os.sep)
    
    # Join the last three parts to get the desired path
    return os.sep.join(parts[-3:]) + os.sep




# print all the attributes of a class.
def print_entry_attributes(entry):
    # Get the attributes of the entry as a dictionary
    attributes = vars(entry)
    
    # Iterate through the attributes and print them
    for attribute, value in attributes.items():
        print(f"{attribute}: {value}")