import bpy
import os
from .operator import BIMB_OT_remesh_active

class BIMB_PT_panel(bpy.types.Panel):
    bl_label = "BInstantMeshes"
    bl_idname = "BIMB_PT_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "BInstantMeshes"

    def draw(self, context):
        layout = self.layout
        settings = context.scene.bimb_settings
        prefs = context.preferences.addons[__package__].preferences

        # -- Open in UI (Topo) --
        col_top = layout.column(align=True)
        col_top.prop(settings, "open_ui", icon="WINDOW")

        # -- Workflow Toggles --
        box_work = layout.box()
        box_work.label(text="Workflow:", icon="MODIFIER")
        col_work = box_work.column(align=True)
        col_work.prop(settings, "preserve_transforms")
        col_work.prop(settings, "apply_modifiers")
        col_work.prop(settings, "transfer_uvs")
        col_work.prop(settings, "hide_original")

        # -- Algorithm Toggles --
        box_algo = layout.box()
        box_algo.label(text="Algorithm:", icon="MESH_DATA")
        col_algo = box_algo.column(align=True)
        col_algo.prop(settings, "deterministic")
        col_algo.prop(settings, "dominant")
        col_algo.prop(settings, "intrinsic")
        col_algo.prop(settings, "boundaries")

        # -- Parameters --
        box_params = layout.box()
        box_params.label(text="Parameters:", icon="TOOL_SETTINGS")
        col_params = box_params.column(align=True)
        col_params.use_property_split = True
        col_params.use_property_decorate = False
        
        col_params.prop(settings, "smooth_iterations")
        col_params.prop(settings, "crease_degree")
        col_params.prop(settings, "vertex_count")
        
        layout.separator(factor=0.5) 

        # -- Execution Button --
        col_exec = layout.column(align=True)
        col_exec.scale_y = 1.5
        col_exec.operator(BIMB_OT_remesh_active.bl_idname, text="Remesh", icon="VIEW_PERSPECTIVE")

        # Warning if executable is not set
        executable = bpy.path.abspath(prefs.executable_path)
        if not executable or not os.path.isfile(executable):
            layout.separator()
            layout.label(text="Executable not configured!", icon="ERROR")