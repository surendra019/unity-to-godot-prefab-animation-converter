# Unity Prefab to Godot Scene Converter

This tool converts Unity `.prefab` animations into Godot scenes with an `AnimationPlayer`, supporting Godot versions 4.x up to 4.3 (and likely higher versions).

## Features
- Converts `.prefab` animations with `GameObject` and `SpriteRenderer` components into Godot scenes.
- Generates `.tscn` files with animations that can be played in Godot.
- Easy-to-use interface for folder selection and loading prefabs.

## Usage Conditions
1. The `.prefab` scene must only contain `GameObject` and `SpriteRenderer` components.
2. All related animation files must be stored in **the same folder**, including:
   - `.png`
   - `.png.meta`
   - `.anim`
   - `.anim.meta`
   - `.prefab`
   - `.controller`
3. The folder must be two levels deep within the Godot project directory. Example:
   `res://Assets/PandaAnimation/`, This is a valid directory structure for the tool to work.

## How to Use
1. Open the tool and access the interface:  
![Tool Interface Screenshot](#) <!-- Replace with actual screenshot -->

2. Select the folder containing all the animation files:  
![Folder Selection Screenshot](#) <!-- Replace with actual screenshot -->

3. Follow these steps:
   - Click the **Load Prefab** button.
   - Choose the folder containing your animation files (e.g., `res://Assets/PandaAnimation/`).
   - Wait 1-20 seconds for the `.tscn` file to be generated.
   - Select the folder where the `.tscn` file should be saved (this must be inside the Godot project directory, e.g., `res://Scenes/`).

4. The `.tscn` file is now ready to be used in your Godot project.

## Example Directory Structure
Ensure your files are organized as follows:

## Notes
   - Ensure all necessary files are present and properly organized before using the tool.
   - The tool supports Godot 4.x versions up to 4.3 (and likely higher versions).

---

## License
[Insert License Here, e.g., MIT License]


