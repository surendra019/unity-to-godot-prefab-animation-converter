from tkinter import filedialog, messagebox
import unityparser
import ui
import utils
import os


godot_scene = ""
parent_name = ""
sub_resource_target_position = -1
second_node_insert_position = -1


# Function to parse Unity prefab and convert to Godot .tscn scene
def parse_unity_prefab_to_godot(prefab_path):
    try:
        unity_doc = unityparser.UnityDocument.load_yaml(prefab_path)

        # Get all entries in the Unity prefab (these are Unity components)
        entries = unity_doc.entries
        
        # Initialize scene structure for Godot .tscn 
        # format=2 for godoto 3.x else 3 for 4.x
        global godot_scene

        godot_scene = "[gd_scene load_steps=2 format=3]\n"
      
        global second_node_insert_position

        
        utils.texture_insert_position = len(godot_scene)


        parent_node = find_parent(entries)
        godot_scene += f"\n\n[node name=\"{parent_node.m_Name}\" type=\"Node2D\"]\n"
        second_node_insert_position = len(f"\n\n[node name=\"{parent_node.m_Name}\" type=\"Node2D\"]\n")

        add_children(entries, get_transform_object_by_game_object(entries, parent_node))

        add_animation_player(entries)
    

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
                if hasattr(transform, 'm_GameObject'):                    
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



# returns the node path from the GameObject's name.
def get_complete_node_path_from_game_object_name(entries, name):

    game_object = get_game_object_from_name(entries, name)
    if game_object == None:
        return None
    result = ""
    entry = get_transform_object_by_game_object(entries, game_object)
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
    rotation = f"{-1 * utils.quaternion_to_radians(float(transform.m_LocalRotation['x']), float(transform.m_LocalRotation['y']), float(transform.m_LocalRotation['z']), float(transform.m_LocalRotation['w']))}"
    scale = f"Vector2({float(transform.m_LocalScale['x'])}, {float(transform.m_LocalScale['y'])})"

    global godot_scene
    godot_scene += f"position = {position}\n"
    godot_scene += f"rotation = {rotation}\n"
    godot_scene += f"scale = {scale}\n"

# assigns the texture.
def assign_texture(entries, game_object):
    path = get_png_image_path(entries, game_object)
    if path != None:
        godot_relative_path = utils.convert_to_res_path(path, ui.reference_folder)
        global godot_scene
        random_id = utils.generate_unique_id()
        line = f"\n[ext_resource type=\"Texture2D\"  path=\"{godot_relative_path}\" id=\"{random_id}\"]\n"
        godot_scene = utils.insert_at_index(godot_scene, utils.texture_insert_position, line)
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
            z_index = _class.m_SortingOrder
            z_index_string = f"z_index = {z_index}"

            godot_scene += z_index_string
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
    animation_files = utils.get_all_files(ui.directory, ".anim")
    global godot_scene
    insert_idx = utils.get_insert_index_after_ext_resources(godot_scene)
    animation_name_to_id = {}

    files = [animation_files[24]]
    print(len(animation_files))

    for file in files:
        print(animation_files.index(file) + 1)
        unity_doc = unityparser.UnityDocument.load_yaml(file)
        
        if len(unity_doc.data[0].m_EulerCurves) == 0 and len(unity_doc.data[0].m_PositionCurves) == 0 and len(unity_doc.data[0].m_ScaleCurves) == 0:
            continue

        file_path = file  # The file path
        file_name = os.path.basename(file_path)  # Extract "ter.anim"
        name_without_extension = os.path.splitext(file_name)[0]  # Extract "ter"


        anim_length = float(unity_doc.data[0].m_EulerCurves[0]['curve']['m_Curve'][-1]['time'])

        animation_id = utils.generate_unique_id()
        animation_text = f"\n[sub_resource type=\"Animation\" id=\"{animation_id}\"]\nresource_name = \"{name_without_extension}\"\nlength = {anim_length}\n"




        godot_scene = utils.insert_at_index(godot_scene, insert_idx, animation_text)
        insert_idx += len(animation_text)


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
                        values_string += str(-1 * utils.degrees_to_radians(float(value))) + ','
                        transition_string += str(1) + ','
                    else:
                        times_string += time
                        values_string += str(-1 * utils.degrees_to_radians(float(value)))
                        transition_string += str(1)
                
                times_string += ')'
                values_string += ']'
                transition_string += ')'

                node_path = '.'

                full_path = keyframes['path']  # The file path
                node_name = os.path.basename(full_path)  # Extract "ter.anim"



                if get_complete_node_path_from_game_object_name(entries, node_name) == None:
                    continue
                elif get_complete_node_path_from_game_object_name(entries, node_name) != "":
                    node_path = get_complete_node_path_from_game_object_name(entries, node_name)[:-1]

                
                track = utils.get_track_string(animation_track_idx, node_path, times_string, transition_string, values_string, "rotation")

                godot_scene = utils.insert_at_index(godot_scene, insert_idx, track)
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

                if get_complete_node_path_from_game_object_name(entries, node_name) == None:
                    continue
                elif get_complete_node_path_from_game_object_name(entries, node_name) != "":
                    node_path = get_complete_node_path_from_game_object_name(entries, node_name)[:-1]

                
                track = utils.get_track_string(animation_track_idx, node_path, times_string, transition_string, values_string, "position")


                godot_scene = utils.insert_at_index(godot_scene, insert_idx, track)
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

                if get_complete_node_path_from_game_object_name(entries, node_name) == None:
                    continue
                elif get_complete_node_path_from_game_object_name(entries, node_name) != "":
                    node_path = get_complete_node_path_from_game_object_name(entries, node_name)[:-1]


                
                track = utils.get_track_string(animation_track_idx, node_path, times_string, transition_string, values_string, "scale")


                godot_scene = utils.insert_at_index(godot_scene, insert_idx, track)
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

                            if get_complete_node_path_from_game_object_name(entries, node_name) == None:
                                continue
                            elif get_complete_node_path_from_game_object_name(entries, node_name) != "":
                                node_path = get_complete_node_path_from_game_object_name(entries, node_name)[:-1]

                            
                            track = utils.get_track_string(animation_track_idx, node_path, times_string, transition_string, values_string, "visible")


                            godot_scene = utils.insert_at_index(godot_scene, insert_idx, track)
                            insert_idx += len(track)
                            animation_track_idx += 1
                    case '1':
                        if i['attribute'] == 'm_IsActive':
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

                            if get_complete_node_path_from_game_object_name(entries, node_name) == None:
                                continue
                            elif get_complete_node_path_from_game_object_name(entries, node_name) != "":
                                node_path = get_complete_node_path_from_game_object_name(entries, node_name)[:-1]


                            
                            track = utils.get_track_string(animation_track_idx, node_path, times_string, transition_string, values_string, "visible")

                            godot_scene = utils.insert_at_index(godot_scene, insert_idx, track)
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

                                if 'guid' in j['value']:
                                    if get_png_image_path(entries, None, j['value']['guid']) == None:
                                        continue
                                    if get_png_ext_resource_line(entries, j['value']['guid']) != False:

                                        keyframe['value'] = f"ExtResource(\"{utils.extract_id(get_png_ext_resource_line(entries, j['value']['guid']))}\")"
                                    else:
                                        godot_relative_path = utils.convert_to_res_path(get_png_image_path(entries, None, j['value']['guid']), ui.reference_folder)
                                        random_id = utils.generate_unique_id()
                                        line = f"\n[ext_resource type=\"Texture2D\"  path=\"{godot_relative_path}\" id=\"{random_id}\"]\n"
                                        godot_scene = utils.insert_at_index(godot_scene, utils.texture_insert_position, line)
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


                            if get_complete_node_path_from_game_object_name(entries, node_name) == None:
                                continue
                            elif get_complete_node_path_from_game_object_name(entries, node_name) != "":
                                node_path = get_complete_node_path_from_game_object_name(entries, node_name)[:-1]

                            
                            track = utils.get_track_string(animation_track_idx, node_path, times_string, transition_string, values_string, "texture")


                            godot_scene = utils.insert_at_index(godot_scene, insert_idx, track)
                            insert_idx += len(track)
                            animation_track_idx += 1
                
    animation_library_id = utils.generate_unique_id()
    animation_library_string = f"\n[sub_resource type=\"AnimationLibrary\" id=\"{animation_library_id}\"]\n"

    animation_data_string = f"_data = {{"
    for i in animation_name_to_id:
        if list(animation_name_to_id.keys()).index(i) != len(list(animation_name_to_id.keys())) - 1:
            animation_data_string += f"\"{i}\" : SubResource(\"{animation_name_to_id[i]}\"),\n"
        else:
            animation_data_string += f"\"{i}\" : SubResource(\"{animation_name_to_id[i]}\")\n"
    
    animation_data_string += '}\n'

    godot_scene = utils.insert_at_index(godot_scene, insert_idx, animation_library_string)
    insert_idx += len(animation_library_string)

    godot_scene = utils.insert_at_index(godot_scene, insert_idx, animation_data_string)
    insert_idx += len(animation_data_string)

    animation_player_string = f"\n[node name=\"AnimationPlayer\" type=\"AnimationPlayer\" parent=\".\"]\n"
    libraries_string = (f"libraries = {{\n"
                        f"\"\": SubResource(\"{animation_library_id}\")\n"
                        f"}}\n")
    global second_node_insert_position
    target_idx = second_node_insert_position + insert_idx
    godot_scene = utils.insert_at_index(godot_scene, target_idx, animation_player_string)
    target_idx += len(animation_player_string)

    godot_scene = utils.insert_at_index(godot_scene, target_idx, libraries_string)
    target_idx += len(libraries_string)
               
            


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
                        all_png_meta_files = utils.get_all_files(ui.directory, ".png.meta")
                        for file in all_png_meta_files:
                            unity_doc = unityparser.UnityDocument.load_yaml(file)
                            for entry in unity_doc.entries:
                                if guid == entry['guid']:
                                    return file.removesuffix('.meta')
                    else:
                        return None
                            # print_entry_attributes(entry)
    if guid != None:
        all_png_meta_files = utils.get_all_files(ui.directory, ".png.meta")
        for file in all_png_meta_files:
            unity_doc = unityparser.UnityDocument.load_yaml(file)
            for entry in unity_doc.entries:
                if guid == entry['guid']:
                    return file.removesuffix('.meta')

                    


# checks if a png resource is already imported in the scene.
def get_png_ext_resource_line(entries, guid):
    global_path = get_png_image_path(entries, None, guid)
    global godot_scene
    if global_path != '':
        relative_path = utils.convert_to_res_path(global_path, ui.reference_folder)
        line = utils.find_line_with_substring(godot_scene, relative_path)
        return line





if __name__ == "__main__":
    ui.prefab_parser_function = parse_unity_prefab_to_godot
    ui.create_ui()
    
