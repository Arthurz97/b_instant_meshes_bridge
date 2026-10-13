import bpy

def select_only(context, obj):
    """Clears selection and makes the given object the only selected and active one."""
    for scene_obj in context.scene.objects:
        scene_obj.select_set(False)
    
    obj.select_set(True)
    context.view_layer.objects.active = obj