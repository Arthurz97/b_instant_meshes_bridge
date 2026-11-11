import bpy
import os

from .utils import get_bundled_executable_path

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

        if self.executable_path and os.path.isfile(bpy.path.abspath(self.executable_path)):
            return  # user path valido: nenhum aviso

        if os.path.isfile(get_bundled_executable_path()):
            layout.label(text="Using bundled executable. You can set a custom path above if you prefer.", icon="INFO")
        else:
            layout.label(text="Executable not found. Please set a custom path above or ensure 'Instant Meshes.exe' is inside the bundled 'bin' folder.", icon="ERROR")