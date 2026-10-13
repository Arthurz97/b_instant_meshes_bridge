import bpy
from . import preferences
from . import properties
from . import panel
from . import operator

classes = (
    preferences.BIMB_AddonPreferences,
    properties.BIMB_Settings,
    operator.BIMB_OT_remesh_active,
    panel.BIMB_PT_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register the properties inside the Scene
    bpy.types.Scene.bimb_settings = bpy.props.PointerProperty(type=properties.BIMB_Settings)

def unregister():
    del bpy.types.Scene.bimb_settings
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)