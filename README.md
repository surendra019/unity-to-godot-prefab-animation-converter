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
