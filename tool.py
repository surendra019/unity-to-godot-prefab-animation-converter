import tkinter as tk
from tkinter import filedialog, messagebox
import unityparser
import math
import random
import string
import os
import re

# TODO: check if the animation track of changing Sprite has guid when the Sprite is not assigned in some keyframe to enter "null" there.

godot_scene = ""
parent_name = ""
directory_input = None
reference_folder_input = None
texture_insert_position = -1
sub_resource_target_position = -1
second_node_insert_position = -1

resource_ids = []

# Function to parse Unity prefab and convert to Godot .tscn scene
def parse_unity_prefab_to_godot(prefab_path, text_widget):
    try:
        # Load the Unity YAML prefab file into a UnityDocument object
        unity_doc = unityparser.UnityDocument.load_yaml(prefab_path)
        
        # Clear the text widget before adding new data
        text_widget.delete(1.0, tk.END)

        # Get all entries in the Unity prefab (these are Unity components)
        entries = unity_doc.entries
        
        if not entries:
            text_widget.insert(tk.END, "No entries found in the prefab.\n")
        
        # Initialize scene structure for Godot .tscn 
        # format=2 for godoto 3.x else 3 for 4.x
        global godot_scene

        godot_scene = "[gd_scene load_steps=2 format=3]\n"
      
        global second_node_insert_position

        global texture_insert_position
        texture_insert_position = len(godot_scene)

        # print(type(get_class_by_anchor(entries, "5367279928316716526").m_Component[0]['component']['fileID']))
        # print(find_parent(entries).m_Name)

        parent_node = find_parent(entries)
        godot_scene += f"\n\n[node name=\"{parent_node.m_Name}\" type=\"Node2D\"]\n"
        second_node_insert_position = len(f"\n\n[node name=\"{parent_node.m_Name}\" type=\"Node2D\"]\n")

        add_children(entries, get_transform_object_by_game_object(entries, parent_node))

        add_animation_player(entries)
        # Display the Godot scene structure in the text widget
        text_widget.insert(tk.END, godot_scene)

        # Optionally, save the generated scene to a .tscn file
        save_path = filedialog.asksaveasfilename(defaultextension=".tscn", filetypes=[("Godot Scene", "*.tscn")])
        if save_path:
            with open(save_path, 'w') as scene_file:
                scene_file.write(godot_scene)
            messagebox.showinfo("Success", f"Godot scene saved to {save_path}")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to parse prefab: {e}")


# finds the parent from the YAML string.
def find_parent(entries):
    """
    Finds the parent GameObject of a prefab in Unity.

    Parameters:
    - entries: List of all entries (classes) in the Unity prefab (i.e. UnityDocument).

    Returns:
    - The parent GameObject (if found), or None if no parent is found.
    """
    # Traverse all the entries (classes) in the Unity document
    for entry in entries:
        class_name = entry.__class__.__name__

        # Focus on Transform components to find the parent
        if class_name == 'Transform':
            transform = entry
            # Check if this Transform has m_Father: {fileID: 0}, indicating no parent
            if hasattr(transform, 'm_Father') and transform.m_Father['fileID'] == '0':
                # m_Father is {fileID: 0}, so this Transform is a child of the GameObject
                # Now, find the related GameObject using m_GameObject
                # print(transform)
                if hasattr(transform, 'm_GameObject'):
                    # print(transform.m_GameObject['fileID'])
                    
                    game_object_file_id = transform.m_GameObject['fileID']
                    
                    # # Search for the GameObject with the matching fileID (anchor)
                    parent_game_object = get_class_by_anchor(entries, game_object_file_id)

                    global parent_name
                    parent_name = parent_game_object.m_Name
                    return parent_game_object

    # If no parent was found, return None
    return None



# helper function to return transform object using the class_id.
def get_class_by_anchor(entries, anchor):
    # Iterate over all the entries in the prefab
    for entry in entries:
        # Check if the entry has a class_id and if it matches the given class_id
        if hasattr(entry, 'anchor') and entry.anchor == anchor:
            return entry
    return None  # Return None if no matching transform is found


# returns the GameObject from its Transform's anchor.
def get_game_object_by_transform_anchor(entries, anchor):
    transform = get_class_by_anchor(entries, anchor)
    if hasattr(transform, "m_GameObject"):
        game_obj_anchor = transform.m_GameObject['fileID']

        # Iterate over all the entries in the prefab
        for entry in entries:
            # Check if the entry has a class_id and if it matches the given class_id
            if hasattr(entry, 'anchor') and entry.anchor == game_obj_anchor:
                return entry
    return None  # Return None if no matching transform is found


# returns the transform object from a GameObject.
def get_transform_object_by_game_object(entries, game_object):
    if hasattr(game_object, "m_Component"):
        for i in game_object.m_Component:
            _class = get_class_by_anchor(entries, i['component']['fileID'])
            if _class.__class__.__name__ == 'Transform':
                return _class
    return None



# print all the attributes of a class.
def print_entry_attributes(entry):
    # Get the attributes of the entry as a dictionary
    attributes = vars(entry)
    
    # Iterate through the attributes and print them
    for attribute, value in attributes.items():
        print(f"{attribute}: {value}")

# returns the node path from the GameObject's name.
def get_complete_node_path_from_game_object_name(entries, name):
    result = ""
    entry = get_transform_object_by_game_object(entries, get_game_object_from_name(entries, name))
    if entry.__class__.__name__ == "Transform":
        if hasattr(entry, "m_Father"):
            current_transform = entry
            while current_transform != None:
                top = get_game_object_by_transform_anchor(entries, current_transform.anchor)
                result = top.m_Name + '/' + result
                current_transform = get_class_by_anchor(entries, current_transform.m_Father['fileID'])
    index = result.find('/')  # Find the first occurrence of the character

    return result[index + 1:]

# helper function to return the GameObject from its name.
def get_game_object_from_name(entries, name):
    for entry in entries:
        if entry.__class__.__name__ == 'GameObject':
            if entry.m_Name == name:
                return entry
            

# returns the complete node path from the current transform to the top of the tree.
def get_node_path_from_current_node(entries, entry):
    result = ""
    if entry.__class__.__name__ == "Transform":
        if hasattr(entry, "m_Father"):
            current_transform = entry
            while current_transform != None:
                top = get_game_object_by_transform_anchor(entries, current_transform.anchor)
                result = top.m_Name + '/' + result
                current_transform = get_class_by_anchor(entries, current_transform.m_Father['fileID'])
    index = result.find('/')  # Find the first occurrence of the character

    return result[index + 1:]


# currently returns the type of node from the GameObjects and its components. 
def get_node_type_from_game_object(entries, game_object):
    result = ""
    if hasattr(game_object, "m_Component"):
        for i in game_object.m_Component:
            _class = get_class_by_anchor(entries, i['component']['fileID'])
            if _class.__class__.__name__ == 'SpriteRenderer':
                result = 'Sprite2D'
            elif _class.__class__.__name__ == 'Transform':
                result = 'Node2D'
    if result == '':
        result = 'Node'
    return result


# assign the GameObject's properties to the Godot Nodes.
def assign_properties(entries, node_type, game_object):
    match node_type:
        case 'Node2D':
            assign_transform(entries, game_object)
        case 'Sprite2D':
            assign_transform(entries, game_object)
            assign_texture(entries, game_object)
    assign_other_properties(entries, game_object)
            # godot_scene += f"z_index = + "

# assigns transform of the GameObject to the respective node.
def assign_transform(entries, game_object):
    transform = get_transform_object_by_game_object(entries, game_object)
    position = f"Vector2({float(transform.m_LocalPosition['x']) * 100}, {-1 * float(transform.m_LocalPosition['y']) * 100})"
    rotation = f"{-1 * quaternion_to_radians(float(transform.m_LocalRotation['x']), float(transform.m_LocalRotation['y']), float(transform.m_LocalRotation['z']), float(transform.m_LocalRotation['w']))}"
    scale = f"Vector2({float(transform.m_LocalScale['x'])}, {float(transform.m_LocalScale['y'])})"

    z_index = 100 - math.ceil(float(transform.m_LocalPosition['z']))

    global godot_scene
    godot_scene += f"position = {position}\n"
    godot_scene += f"rotation = {rotation}\n"
    godot_scene += f"scale = {scale}\n"
    godot_scene += f"z_index = {z_index}\n"

# assigns the texture.
def assign_texture(entries, game_object):
    path = get_png_image_path(entries, game_object)
    if path != None:
        godot_relative_path = convert_to_res_path(path)
        global godot_scene
        random_id = generate_unique_id()
        line = f"\n[ext_resource type=\"Texture2D\"  path=\"{godot_relative_path}\" id=\"{random_id}\"]\n"
        godot_scene = insert_at_index(godot_scene, texture_insert_position, line)
        global sub_resource_target_position
        sub_resource_target_position = godot_scene.find(line) + len(line) + 1
        godot_scene += f"texture = ExtResource(\"{random_id}\")\n"

# assigns other properties based on the assigned components to a GameObject.
def assign_other_properties(entries, game_object):
    is_game_object_active = True
    has_visibility_set = False
    if hasattr(game_object, 'm_IsActive'):
        enabled = game_object.m_IsActive
        is_game_object_active = True if enabled == '1' else False
    global godot_scene
    for i in game_object.m_Component:
        _class = get_class_by_anchor(entries, i['component']['fileID'])
        if _class.__class__.__name__ == 'SpriteRenderer':
            enabled = True if _class.m_Enabled == '1' else False
            enabled_string = f"visible = {'true' if (enabled and is_game_object_active) else 'false'}"
            godot_scene += enabled_string
            has_visibility_set = True
    
    if not has_visibility_set:
        enabled_string = f"visible = {'true' if (is_game_object_active) else 'false'}"
        godot_scene += enabled_string
    
  

    








# adds all the children into the Godot Scene.
def add_children(entries, entry):
    if hasattr(entry, "m_Children"):
        if len(entry.m_Children) == 0:
            return
        for i in entry.m_Children:
            anchor = i['fileID']
            _class = get_game_object_by_transform_anchor(entries, anchor)
            if hasattr(_class, "m_Name"):
                global godot_scene
                parent_path = "."
                if get_node_path_from_current_node(entries, entry) != "":
                    parent_path = get_node_path_from_current_node(entries, entry)
              
                node_type = get_node_type_from_game_object(entries, _class)
                godot_scene += f"\n[node name=\"{_class.m_Name}\" type=\"{node_type}\" parent=\"{parent_path}\"]\n"
                assign_properties(entries, node_type, _class)

            add_children(entries, get_class_by_anchor(entries, anchor))
    else:
        return

# adds animation player with all the animations.
def add_animation_player(entries):
    animation_files = get_all_files(directory_input.get(), ".anim")
    global godot_scene
    insert_idx = get_insert_index_after_ext_resources(godot_scene)
    animation_name_to_id = {}

    files = animation_files

    for file in files:
        unity_doc = unityparser.UnityDocument.load_yaml(file)
        
        if len(unity_doc.data[0].m_EulerCurves) == 0 and len(unity_doc.data[0].m_PositionCurves) == 0 and len(unity_doc.data[0].m_ScaleCurves) == 0:
            continue

        file_path = file  # The file path
        file_name = os.path.basename(file_path)  # Extract "ter.anim"
        name_without_extension = os.path.splitext(file_name)[0]  # Extract "ter"


        anim_length = float(unity_doc.data[0].m_EulerCurves[0]['curve']['m_Curve'][-1]['time'])

        animation_id = generate_unique_id()
        animation_text = f"\n[sub_resource type=\"Animation\" id=\"{animation_id}\"]\nresource_name = \"{name_without_extension}\"\nlength = {anim_length}\n"




        godot_scene = insert_at_index(godot_scene, insert_idx, animation_text)
        insert_idx += len(animation_text)

        # # for getting the animation length.
        # for i in unity_doc.data[0].m_EulerCurves:
        #     times = []

        #     for j in i['curve']['m_Curve']:
        #         times.append(float(j['time']))


        animation_name_to_id[name_without_extension] = animation_id

        animation_track_idx = 0

        if hasattr(unity_doc.data[0], 'm_EulerCurves'):
            for i in unity_doc.data[0].m_EulerCurves:
                keyframes = {}
                keyframe_array = []

                for j in i['curve']['m_Curve']:
                    keyframe = {}
                    keyframe['time'] = j['time']
                    keyframe['value'] = j['value']['z']
                    keyframe_array.append(keyframe)
                keyframes['keyframes'] = keyframe_array
                keyframes['path'] = i['path']

                times_string = "PackedFloat32Array("
                values_string = "["
                transition_string = "PackedFloat32Array("

                for i in keyframes['keyframes']:
                    time = i['time']
                    value = i['value']
                    if keyframes['keyframes'].index(i) != len(keyframes['keyframes']) - 1:
                        times_string += time + ','
                        values_string += str(-1 * degrees_to_radians(float(value))) + ','
                        transition_string += str(1) + ','
                    else:
                        times_string += time
                        values_string += str(-1 * degrees_to_radians(float(value)))
                        transition_string += str(1)
                
                times_string += ')'
                values_string += ']'
                transition_string += ')'

                node_path = '.'

                full_path = keyframes['path']  # The file path
                node_name = os.path.basename(full_path)  # Extract "ter.anim"

                if get_complete_node_path_from_game_object_name(entries, node_name) != "":
                    node_path = get_complete_node_path_from_game_object_name(entries, node_name)[:-1]

                
                track = (
                    f"tracks/{animation_track_idx}/type = \"value\"\n"
                    f"tracks/{animation_track_idx}/imported = false\n"
                    f"tracks/{animation_track_idx}/enabled = true\n"
                    f"tracks/{animation_track_idx}/path = NodePath(\"{node_path}:rotation\")\n"
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

                godot_scene = insert_at_index(godot_scene, insert_idx, track)
                insert_idx += len(track)
                animation_track_idx += 1
        if hasattr(unity_doc.data[0], 'm_PositionCurves'):
            for i in unity_doc.data[0].m_PositionCurves:
                keyframes = {}
                keyframe_array = []
                for j in i['curve']['m_Curve']:
                    keyframe = {}
                    keyframe['time'] = j['time']
                    keyframe['value'] = f"Vector2({float(j['value']['x']) * 100}, {float(j['value']['y']) * -100})"
                    keyframe_array.append(keyframe)
                keyframes['keyframes'] = keyframe_array
                keyframes['path'] = i['path']

                times_string = "PackedFloat32Array("
                values_string = "["
                transition_string = "PackedFloat32Array("

                for j in keyframes['keyframes']:
                    time = j['time']
                    value = j['value']

                    if keyframes['keyframes'].index(j) != len(keyframes['keyframes']) - 1:
                        times_string += time + ','
                        values_string += value + ','
                        transition_string += str(1) + ','
                    else:
                        times_string += time
                        values_string += value
                        transition_string += str(1)
                
                times_string += ')'
                values_string += ']'
                transition_string += ')'
                
                node_path = '.'

                full_path = keyframes['path']  # The file path
                node_name = os.path.basename(full_path)  # Extract "ter.anim"

                if get_complete_node_path_from_game_object_name(entries, node_name) != "":
                    node_path = get_complete_node_path_from_game_object_name(entries, node_name)[:-1]


                
                track = (
                    f"tracks/{animation_track_idx}/type = \"value\"\n"
                    f"tracks/{animation_track_idx}/imported = false\n"
                    f"tracks/{animation_track_idx}/enabled = true\n"
                    f"tracks/{animation_track_idx}/path = NodePath(\"{node_path}:position\")\n"
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

                godot_scene = insert_at_index(godot_scene, insert_idx, track)
                insert_idx += len(track)
                animation_track_idx += 1
        if hasattr(unity_doc.data[0], 'm_ScaleCurves'):
            for i in unity_doc.data[0].m_ScaleCurves:
                keyframes = {}
                keyframe_array = []
                for j in i['curve']['m_Curve']:
                    keyframe = {}
                    keyframe['time'] = j['time']
                    keyframe['value'] = f"Vector2({float(j['value']['x'])}, {float(j['value']['y'])})"
                    keyframe_array.append(keyframe)
                keyframes['keyframes'] = keyframe_array
                keyframes['path'] = i['path']


                times_string = "PackedFloat32Array("
                values_string = "["
                transition_string = "PackedFloat32Array("

                for j in keyframes['keyframes']:
                    time = j['time']
                    value = j['value']

                    if keyframes['keyframes'].index(j) != len(keyframes['keyframes']) - 1:
                        times_string += time + ','
                        values_string += value + ','
                        transition_string += str(1) + ','
                    else:
                        times_string += time
                        values_string += value
                        transition_string += str(1)
                
                times_string += ')'
                values_string += ']'
                transition_string += ')'
                
                node_path = '.'

                full_path = keyframes['path']  # The file path
                node_name = os.path.basename(full_path)  # Extract "ter.anim"

                if get_complete_node_path_from_game_object_name(entries, node_name) != "":
                    node_path = get_complete_node_path_from_game_object_name(entries, node_name)[:-1]


                
                track = (
                    f"tracks/{animation_track_idx}/type = \"value\"\n"
                    f"tracks/{animation_track_idx}/imported = false\n"
                    f"tracks/{animation_track_idx}/enabled = true\n"
                    f"tracks/{animation_track_idx}/path = NodePath(\"{node_path}:scale\")\n"
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

                godot_scene = insert_at_index(godot_scene, insert_idx, track)
                insert_idx += len(track)
                animation_track_idx += 1

        if hasattr(unity_doc.data[0], 'm_FloatCurves'):
            for i in unity_doc.data[0].m_FloatCurves:
                keyframes = {}
                keyframe_array = []
      
                match i['classID']:
                    case '212':
                        if i['attribute'] == 'm_Enabled':
                            for j in i['curve']['m_Curve']:
                                keyframe = {}
                                keyframe['time'] = j['time']
                                keyframe['value'] = j['value']
                                keyframe_array.append(keyframe)

                            keyframes['keyframes'] = keyframe_array
                            keyframes['path'] = i['path']
                            times_string = "PackedFloat32Array("
                            values_string = "["
                            transition_string = "PackedFloat32Array("

                            for j in keyframes['keyframes']:
                                time = j['time']
                                value = j['value']

                                if keyframes['keyframes'].index(j) != len(keyframes['keyframes']) - 1:
                                    times_string += time + ','
                                    values_string += value + ','
                                    transition_string += str(1) + ','
                                else:
                                    times_string += time
                                    values_string += value
                                    transition_string += str(1)
                            
                            times_string += ')'
                            values_string += ']'
                            transition_string += ')'
                            
                            node_path = '.'

                            full_path = keyframes['path']  # The file path
                            node_name = os.path.basename(full_path)  # Extract "ter.anim"

                            if get_complete_node_path_from_game_object_name(entries, node_name) != "":
                                node_path = get_complete_node_path_from_game_object_name(entries, node_name)[:-1]


                            
                            track = (
                                f"tracks/{animation_track_idx}/type = \"value\"\n"
                                f"tracks/{animation_track_idx}/imported = false\n"
                                f"tracks/{animation_track_idx}/enabled = true\n"
                                f"tracks/{animation_track_idx}/path = NodePath(\"{node_path}:visible\")\n"
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

                            godot_scene = insert_at_index(godot_scene, insert_idx, track)
                            insert_idx += len(track)
                            animation_track_idx += 1
        if hasattr(unity_doc.data[0], 'm_PPtrCurves'):
            for i in unity_doc.data[0].m_PPtrCurves:
                keyframes = {}
                keyframe_array = []
                match i['classID']:
                    case '212':
                        if i['attribute'] == 'm_Sprite':
                            for j in i['curve']:
                                keyframe = {}
                                keyframe['time'] = j['time']

                                # print(get_png_ext_resource_line(entries, j['value']['guid']))
                                
                                if 'guid' in j['value']:
                                    if get_png_image_path(entries, None, j['value']['guid']) == None:
                                        continue
                                    if get_png_ext_resource_line(entries, j['value']['guid']) != False:
                                        keyframe['value'] = f"ExtResource(\"{extract_id(get_png_ext_resource_line(entries, j['value']['guid']))}\")"
                                    else:
                                        godot_relative_path = convert_to_res_path(get_png_image_path(entries, None, j['value']['guid']))
                                        random_id = generate_unique_id()
                                        line = f"\n[ext_resource type=\"Texture2D\"  path=\"{godot_relative_path}\" id=\"{random_id}\"]\n"
                                        godot_scene = insert_at_index(godot_scene, texture_insert_position, line)
                                        insert_idx += len(line)
                                        keyframe['value'] = f"ExtResource(\"{random_id}\")"
                                else:
                                    keyframe['value'] = 'null'

                                keyframe_array.append(keyframe)
                            keyframes['keyframes'] = keyframe_array
                            keyframes['path'] = i['path']
                            
                            times_string = "PackedFloat32Array("
                            values_string = "["
                            transition_string = "PackedFloat32Array("


                            for j in keyframes['keyframes']:
                                time = j['time']
                                value = j['value']

                                if keyframes['keyframes'].index(j) != len(keyframes['keyframes']) - 1:
                                    times_string += time + ','
                                    values_string += value + ','
                                    transition_string += str(1) + ','
                                else:
                                    times_string += time
                                    values_string += value
                                    transition_string += str(1)
                            
                            times_string += ')'
                            values_string += ']'
                            transition_string += ')'
                            
                            node_path = '.'

                            full_path = keyframes['path']  # The file path
                            node_name = os.path.basename(full_path)  # Extract "ter.anim"


                            if get_complete_node_path_from_game_object_name(entries, node_name) != "":
                                node_path = get_complete_node_path_from_game_object_name(entries, node_name)[:-1]

                            
                            track = (
                                f"tracks/{animation_track_idx}/type = \"value\"\n"
                                f"tracks/{animation_track_idx}/imported = false\n"
                                f"tracks/{animation_track_idx}/enabled = true\n"
                                f"tracks/{animation_track_idx}/path = NodePath(\"{node_path}:texture\")\n"
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

                            godot_scene = insert_at_index(godot_scene, insert_idx, track)
                            insert_idx += len(track)
                            animation_track_idx += 1
                
    animation_library_id = generate_unique_id()
    animation_library_string = f"\n[sub_resource type=\"AnimationLibrary\" id=\"{animation_library_id}\"]\n"

    animation_data_string = f"_data = {{"
    for i in animation_name_to_id:
        if list(animation_name_to_id.keys()).index(i) != len(list(animation_name_to_id.keys())) - 1:
            animation_data_string += f"\"{i}\" : SubResource(\"{animation_name_to_id[i]}\"),\n"
        else:
            animation_data_string += f"\"{i}\" : SubResource(\"{animation_name_to_id[i]}\")\n"
    
    animation_data_string += '}\n'

    godot_scene = insert_at_index(godot_scene, insert_idx, animation_library_string)
    insert_idx += len(animation_library_string)

    godot_scene = insert_at_index(godot_scene, insert_idx, animation_data_string)
    insert_idx += len(animation_data_string)

    animation_player_string = f"\n[node name=\"AnimationPlayer\" type=\"AnimationPlayer\" parent=\".\"]\n"
    libraries_string = (f"libraries = {{\n"
                        f"\"\": SubResource(\"{animation_library_id}\")\n"
                        f"}}\n")
    global second_node_insert_position
    target_idx = second_node_insert_position + insert_idx
    godot_scene = insert_at_index(godot_scene, target_idx, animation_player_string)
    target_idx += len(animation_player_string)

    godot_scene = insert_at_index(godot_scene, target_idx, libraries_string)
    target_idx += len(libraries_string)
               
            

# Function to open a file dialog and load the prefab
def load_prefab(text_widget):
    if directory_input and directory_input.get() == "" or reference_folder_input and reference_folder_input.get() == "":
        messagebox.showerror("Error", "Enter a directory!")
        return

    # Open a file dialog to select the Unity prefab file
    prefab_path = filedialog.askopenfilename(title="Select a Unity Prefab", filetypes=[("Prefab Files", "*.prefab")])
    
    if prefab_path:
        parse_unity_prefab_to_godot(prefab_path, text_widget)

# Create the main UI window
def create_ui():
    window = tk.Tk()
    window.title("Unity to Godot Prefab Converter")

    # Create a button to load a prefab file
    load_button = tk.Button(window, text="Load Prefab", command=lambda: load_prefab(text_widget))
    load_button.pack(pady=10)
    
    # Add a label
    label = tk.Label(window, text="Enter meta directory:")
    label.pack(pady=1)

    # Add an input box
    input_box = tk.Entry(window)
    input_box.pack(pady=10)

     
    # Add a label
    refernece_folder_label = tk.Label(window, text="Enter reference folder path(in '/')")
    refernece_folder_label.pack(pady=1)

    # Add an input box
    refernece_folder_in= tk.Entry(window)
    refernece_folder_in.pack(pady=10)


    global directory_input
    directory_input = input_box

    global reference_folder_input
    reference_folder_input = refernece_folder_in

    # Create a text widget to display the prefab details
    text_widget = tk.Text(window, height=20, width=80)
    text_widget.pack(padx=10, pady=10)

    # Create a scroll bar for the text widget
    scroll_bar = tk.Scrollbar(window, command=text_widget.yview)
    scroll_bar.pack(side=tk.RIGHT, fill=tk.Y)
    text_widget.config(yscrollcommand=scroll_bar.set)



    # Start the UI loop
    window.mainloop()

# returns the image's path if the passed GameObject has a SpriteRenderer and it further has an image assigned on it.
def get_png_image_path(entries, game_object = None, guid = None):
    # path = ''
    if game_object != None:
        if hasattr(game_object, "m_Component"):
            for i in game_object.m_Component:
                _class = get_class_by_anchor(entries, i['component']['fileID'])
                if _class.__class__.__name__ == 'SpriteRenderer':
                    if 'guid' in _class.m_Sprite:
                        guid = _class.m_Sprite['guid']
                        all_png_meta_files = get_all_files(directory_input.get(), ".png.meta")
                        for file in all_png_meta_files:
                            unity_doc = unityparser.UnityDocument.load_yaml(file)
                            for entry in unity_doc.entries:
                                if guid == entry['guid']:
                                    return file.removesuffix('.meta')
                    else:
                        return None
                            # print_entry_attributes(entry)
    if guid != None:
        all_png_meta_files = get_all_files(directory_input.get(), ".png.meta")
        for file in all_png_meta_files:
            unity_doc = unityparser.UnityDocument.load_yaml(file)
            for entry in unity_doc.entries:
                if guid == entry['guid']:
                    return file.removesuffix('.meta')

                    
        
# scans all the files with suffix (extension) in the passed directory.
def get_all_files(directory, suffix):
    """
    Scans the given directory and returns all .png.meta files.

    Args:
        directory (str): The directory to scan.

    Returns:
        list: A list of full paths to .png.meta files.
    """
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
def convert_to_res_path(file_path):
    """
    Converts a given file path to a res:// path, using the specified reference folder.

    Args:
        file_path (str): The absolute file path to convert.
        reference_folder (str): The folder to treat as the root (default is "Meta").

    Returns:
        str: The converted res:// path, or None if the path does not start with the reference folder.
    """
    reference_folder = reference_folder_input.get()
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

def quaternion_to_radians(q_x, q_y, q_z, q_w):
    """
    Converts a Unity quaternion to a rotation angle in radians (around the Z-axis).
    
    Parameters:
        q_x (float): The x component of the quaternion.
        q_y (float): The y component of the quaternion.
        q_z (float): The z component of the quaternion.
        q_w (float): The w component of the quaternion.
        
    Returns:
        float: The rotation angle in radians.
    """
    # Convert quaternion to Euler angles (in radians), focusing on the Z-axis (yaw)
    yaw = math.atan2(2.0 * (q_w * q_z + q_x * q_y), 1.0 - 2.0 * (q_y * q_y + q_z * q_z))
    
    # Return the rotation in radians
    return yaw

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

def insert_at_index(original_string, index, substring):
    # Split the string into two parts: before and after the index
    # print("left -----------------------------------------------")
    # print(original_string[:index])
    # print("right-----------------------------------------------")
    # print(original_string[index:])
    return original_string[:index] + substring + original_string[index:]


def degrees_to_radians(degrees):
    """Convert degrees to radians."""
    return degrees * math.pi / 180


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


# checks if a png resource is already imported in the scene.
def get_png_ext_resource_line(entries, guid):
    global_path = get_png_image_path(entries, None, guid)
    global godot_scene
    if global_path != '':
        relative_path = convert_to_res_path(global_path)
        line = find_line_with_substring(godot_scene, relative_path)
        return line

# finds the line in the scene which has some substring.
def find_line_with_substring(complete_string, substring):
    # Split the complete string into lines
    lines = complete_string.splitlines()
    
    # Search for the substring in each line
    for line in lines:
        if substring in line:
            return line
    
    return False

def extract_id(input_string):
    # Use a regular expression to find the id value
    match = re.search(r'id="([^"]+)"', input_string)
    if match:
        return match.group(1)  # Return the captured group (the id value)
    return None  # Return None if no match is found


if __name__ == "__main__":
    create_ui()
