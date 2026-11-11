import bpy
import os

def select_only(context, obj):
    """Clears selection and makes the given object the only selected and active one."""
    for scene_obj in context.scene.objects:
        scene_obj.select_set(False)
    
    obj.select_set(True)
    context.view_layer.objects.active = obj

def get_bundled_executable_path():
    """Path of the Instant Meshes executable bundled with the add-on (bin/)."""
    return os.path.join(os.path.dirname(__file__), "bin", "Instant Meshes.exe")

def get_executable_path(prefs):
    """Resolves the executable: user preference first, bundled bin/ fallback, else None."""
    if prefs.executable_path:
        user_path = bpy.path.abspath(prefs.executable_path)
        if os.path.isfile(user_path):
            return user_path
    bundled_path = get_bundled_executable_path()
    if os.path.isfile(bundled_path):
        return bundled_path
    return None