import bpy

class BIMB_AddonPreferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    executable_path: bpy.props.StringProperty(
        name="Instant Meshes Executable",
        description="Path to the Instant Meshes application (.exe / .app)",
        subtype="FILE_PATH",
        default="",
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "executable_path")
        
        if not self.executable_path:
            layout.label(text="Please set the path to the Instant Meshes executable to use this add-on.", icon="ERROR")