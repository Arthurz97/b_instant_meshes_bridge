import bpy
from .operators import BIMB_OT_remesh_active
from .utils import get_executable_path

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

        col_mode = col_algo.row()
        col_mode.use_property_split = True
        col_mode.use_property_decorate = False
        col_mode.prop(settings, "remesh_as")

        col_algo.prop(settings, "deterministic")

        row_purequad = col_algo.row()
        row_purequad.enabled = (settings.remesh_as != "TRIANGLES")
        row_purequad.prop(settings, "pure_quad_mesh")

        col_algo.prop(settings, "extrinsic")
        col_algo.prop(settings, "align_to_boundaries")

        # -- Parameters --
        box_params = layout.box()
        box_params.label(text="Parameters:", icon="TOOL_SETTINGS")
        box_params.prop(settings, "sharp_creases")

        col_params = box_params.column(align=True)
        col_params.use_property_split = True
        col_params.use_property_decorate = False

        col_params.prop(settings, "smooth_iterations")

        col_crease = col_params.column(align=True)
        col_crease.enabled = settings.sharp_creases
        col_crease.prop(settings, "crease_angle")

        col_params.prop(settings, "resolution_mode")

        if settings.resolution_mode == "VERTICES":
            col_params.prop(settings, "vertex_count")
        elif settings.resolution_mode == "FACES":
            col_params.prop(settings, "face_count")
        else:  # SCALE
            col_params.prop(settings, "edge_scale")
        
        layout.separator(factor=0.5) 

        # -- Execution Button --
        col_exec = layout.column(align=True)
        col_exec.scale_y = 1.5
        col_exec.operator(BIMB_OT_remesh_active.bl_idname, text="Remesh", icon="VIEW_PERSPECTIVE")

        # Warning if no executable can be resolved (user path or bundled bin/)
        executable = get_executable_path(prefs)
        if executable is None:
            layout.separator()
            layout.label(text="Executable not configured!", icon="ERROR")