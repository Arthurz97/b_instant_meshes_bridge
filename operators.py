import bpy
import os
import shutil
import tempfile
import subprocess
import mathutils
from pathlib import Path
from .utils import select_only

class BIMB_OT_remesh_active(bpy.types.Operator):
    bl_idname = "object.bimb_remesh_active"
    bl_label = "Instant Meshes Remesh"
    bl_description = "Run Instant Meshes on the active mesh and import the result as a new object"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.type == "MESH"

    def execute(self, context):
        settings = context.scene.bimb_settings
        prefs = context.preferences.addons[__package__].preferences
        
        executable_path = bpy.path.abspath(prefs.executable_path)
        if not executable_path or not os.path.isfile(executable_path):
            self.report({"ERROR"}, "Instant Meshes executable not found. Configure it in Preferences.")
            return {"CANCELLED"}

        source_obj = context.active_object
        original_selection = list(context.selected_objects)
        original_active = context.view_layer.objects.active
        finished_import = None
        
        # Captura as matrizes originais antes de qualquer processamento (Lógica BPyMeshLab)
        orig_matrix = source_obj.matrix_world.copy()
        orig_rot = source_obj.rotation_euler.copy()
        orig_scale = source_obj.scale.copy()

        with tempfile.TemporaryDirectory(prefix="bimb_") as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "input.obj"
            output_path = temp_path / "output.obj"

            try:
                # 1. Export Original Mesh
                self._export_active_mesh(context, source_obj, input_path, settings)

                # 2. Build and Execute Command
                if settings.open_ui:
                    shutil.copy2(input_path, output_path)
                    command = [str(executable_path), str(output_path)]
                    
                    self.report({"INFO"}, "Waiting for Instant Meshes GUI to close...")
                    subprocess.run(command, check=False)
                else:
                    command = [
                        str(executable_path),
                        "-c", str(settings.crease_degree),
                        "-v", str(settings.vertex_count),
                        "-S", str(settings.smooth_iterations),
                        "-o", str(output_path)
                    ]
                    if settings.deterministic: command.insert(1, "-d")
                    if settings.dominant: command.insert(1, "-D")
                    if settings.intrinsic: command.insert(1, "-i")
                    if settings.boundaries: command.insert(1, "-b")
                    command.append(str(input_path))
                    
                    subprocess.run(command, capture_output=True, text=True, check=False)

                if not output_path.is_file():
                    self.report({"ERROR"}, "Instant Meshes did not generate an output file.")
                    return {"CANCELLED"}

                # 3. Import Result
                imported = self._import_result(context, output_path)
                
                # Evita o efeito cascata _remesh_remesh_remesh (Lógica do BPyMeshLab)
                base_name = source_obj.name.split("_remesh")[0]
                imported.name = f"{base_name}_remesh"
                
                base_data_name = source_obj.data.name.split("_remesh")[0]
                imported.data.name = f"{base_data_name}_remesh"
                
                # 4. Process Workflow Toggles
                self._copy_materials(source_obj, imported)
                
                if settings.transfer_uvs and source_obj.data.uv_layers:
                    self._transfer_uvs(context, source_obj, imported)
                
                if settings.hide_original:
                    source_obj.hide_set(True)

                # 5. Clean up mesh data (flat shading, clear sharp edges)
                self._cleanup_mesh(context, imported)

                # 6. Apply Transforms and Restore Pivot (Lógica baseada no BPyMeshLab)
                select_only(context, imported)
                
                # Reseta tudo do importador OBJ garantindo que a malha seja "Pura" no World Space (0,0,0)
                bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

                if settings.preserve_transforms:
                    imported.data.transform(orig_matrix.inverted())
                    imported.matrix_world = orig_matrix.copy()
                    imported.rotation_euler = orig_rot.copy()
                    imported.scale = orig_scale.copy()
                else:
                    loc = orig_matrix.translation
                    new_matrix = mathutils.Matrix.Translation(loc)
                    imported.data.transform(new_matrix.inverted())
                    imported.matrix_world = new_matrix

                finished_import = imported
                self.report({"INFO"}, "Instant Meshes remeshing completed.")
                
                return {"FINISHED"}
            
            finally:
                if finished_import is None:
                    self._restore_selection(context, original_selection, original_active)

    def _export_active_mesh(self, context, source_obj, input_path, settings):
        select_only(context, source_obj)
        bpy.ops.wm.obj_export(
            filepath=str(input_path),
            check_existing=False,
            export_selected_objects=True,
            apply_modifiers=settings.apply_modifiers,
            export_normals=True,
            export_uv=True,
            forward_axis="NEGATIVE_Z",
            up_axis="Y",
        )

    def _import_result(self, context, output_path):
        before = set(bpy.data.objects)
        bpy.ops.wm.obj_import(
            filepath=str(output_path),
            use_split_objects=False,
            use_split_groups=False,
            forward_axis="NEGATIVE_Z",
            up_axis="Y",
        )
        created = [obj for obj in bpy.data.objects if obj not in before]
        if not created:
            raise RuntimeError("Blender did not import any object.")
        return created[0]

    def _copy_materials(self, source_obj, imported):
        imported.data.materials.clear()
        for material in source_obj.data.materials:
            imported.data.materials.append(material)

    def _transfer_uvs(self, context, source_obj, imported):
        select_only(context, imported)
        source_obj.select_set(True)
        context.view_layer.objects.active = source_obj
        try:
            bpy.ops.object.data_transfer(
                data_type="UV",
                use_create=True,
                vert_mapping="NEAREST",
                edge_mapping="NEAREST",
                loop_mapping="NEAREST_POLYNOR",
                poly_mapping="NEAREST",
                use_object_transform=True,
                layers_select_src="ACTIVE",
                layers_select_dst="ACTIVE",
                mix_mode="REPLACE",
                mix_factor=1.0,
            )
        except Exception as exc:
            self.report({"WARNING"}, f"Remesh done, but UV transfer failed: {exc}")

    def _cleanup_mesh(self, context, imported):
        select_only(context, imported)
        
        for edge in imported.data.edges:
            edge.use_edge_sharp = False
            
        bpy.ops.object.shade_flat()
        bpy.ops.mesh.customdata_custom_splitnormals_clear()

    def _restore_selection(self, context, selected_objects, active_object):
        for scene_obj in context.scene.objects:
            scene_obj.select_set(False)
        for obj in selected_objects:
            if context.scene.objects.get(obj.name):
                obj.select_set(True)
        if active_object and context.scene.objects.get(active_object.name):
            context.view_layer.objects.active = active_object