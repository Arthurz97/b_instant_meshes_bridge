import bpy
import shutil
import tempfile
import subprocess
import mathutils
from pathlib import Path
from .utils import select_only, get_executable_path, clear_last_visited_mru

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

        executable_path = get_executable_path(prefs)
        if executable_path is None:
            self.report({"ERROR"}, "Instant Meshes executable not found. Configure it in Preferences.")
            return {"CANCELLED"}

        source_obj = context.active_object
        original_selection = list(context.selected_objects)
        original_active = context.view_layer.objects.active

        # Captura as matrizes originais antes de qualquer processamento (Lógica BPyMeshLab)
        orig_matrix = source_obj.matrix_world.copy()
        orig_rot = source_obj.rotation_euler.copy()
        orig_scale = source_obj.scale.copy()

        if settings.open_ui:
            return self._execute_gui(
                context, settings, executable_path, source_obj,
                original_selection, original_active, orig_matrix, orig_rot, orig_scale,
            )

        finished_import = None
        with tempfile.TemporaryDirectory(prefix="bimb_") as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "input.obj"
            output_path = temp_path / "output.obj"

            try:
                # 1. Export Original Mesh
                self._export_active_mesh(context, source_obj, input_path, settings)

                # 2. Build and Execute Command (CLI)
                command = [
                    str(executable_path),
                    "-S", str(settings.smooth_iterations),
                    "-o", str(output_path)
                ]
                if settings.deterministic: command.insert(1, "-d")
                if not settings.pure_quad_mesh: command.insert(1, "-D")
                if not settings.extrinsic: command.insert(1, "-i")
                if settings.sharp_creases:
                    command.insert(1, str(settings.crease_angle))
                    command.insert(1, "-c")
                if settings.align_to_boundaries: command.insert(1, "-b")
                if settings.remesh_as == "TRIANGLES":
                    rosy, posy = "6", "6"
                elif settings.remesh_as == "QUADS_24":
                    rosy, posy = "2", "4"
                else:  # QUADS_44 (default)
                    rosy, posy = "4", "4"
                command.insert(1, posy); command.insert(1, "-p")
                command.insert(1, rosy); command.insert(1, "-r")

                if settings.resolution_mode == "VERTICES":
                    res_flag, res_value = "-v", str(settings.vertex_count)
                elif settings.resolution_mode == "FACES":
                    res_flag, res_value = "-f", str(settings.face_count)
                else:  # SCALE
                    res_flag, res_value = "-s", str(settings.edge_scale)
                command.insert(1, res_value); command.insert(1, res_flag)
                command.append(str(input_path))

                subprocess.run(command, capture_output=True, text=True, check=False)

                if not output_path.is_file():
                    self.report({"ERROR"}, "Instant Meshes did not generate an output file.")
                    return {"CANCELLED"}

                # 3. Import Result + fluxo pós-remesh
                imported = self._finalize_import(
                    context, source_obj, output_path, settings,
                    orig_matrix, orig_rot, orig_scale,
                )
                finished_import = imported
                self.report({"INFO"}, "Instant Meshes remeshing completed.")

                return {"FINISHED"}

            finally:
                if finished_import is None:
                    self._restore_selection(context, original_selection, original_active)

    # ------------------------------------------------------------------
    # Modo GUI (bloqueante): espera o usuário completar o ciclo no exe
    # ------------------------------------------------------------------

    def _execute_gui(self, context, settings, executable_path, source_obj, original_selection, original_active, orig_matrix, orig_rot, orig_scale):
        """Modo GUI (bloqueante): abre o exe com out.obj e importa o resultado quando ele fecha."""
        if not bpy.data.is_saved:
            self.report({"ERROR"}, "Save the .blend file first — the GUI flow stores the exchange files next to it.")
            return {"CANCELLED"}

        temp_dir = Path(bpy.data.filepath).parent / "instantmeshes_temp"
        temp_dir.mkdir(exist_ok=True)
        input_path = temp_dir / "original.obj"
        output_path = temp_dir / "out.obj"

        try:
            # 1. Export Original Mesh + cópia que o exe abre
            self._export_active_mesh(context, source_obj, input_path, settings)
            shutil.copy2(input_path, output_path)
        except Exception as exc:
            shutil.rmtree(temp_dir, ignore_errors=True)
            self.report({"ERROR"}, f"Export to Instant Meshes failed: {exc}")
            return {"CANCELLED"}

        # 2. Espera o usuário completar o ciclo no exe (UI travada por design).
        # Sem entrada 'last visited' utilizável no registro, a ComDlg32 usa o
        # fallback documentado (cwd com arquivos do filtro *.obj) = pasta temp.
        launch_mtime = output_path.stat().st_mtime
        self.report({"INFO"}, "Waiting for Instant Meshes GUI to close...")
        clear_last_visited_mru(executable_path)
        command = [str(executable_path)]
        if settings.gui_fullscreen:
            command.append("-F")
        command.append(str(output_path))
        subprocess.run(command, cwd=str(temp_dir), check=False)

        # 3. Importa somente se o usuário salvou (out.obj mudou desde o launch)
        saved = False
        try:
            saved = output_path.is_file() and output_path.stat().st_mtime != launch_mtime
        except OSError:
            saved = False

        if not saved:
            shutil.rmtree(temp_dir, ignore_errors=True)
            self._restore_selection(context, original_selection, original_active)
            self.report({"WARNING"}, "Instant Meshes closed without saving out.obj — import skipped.")
            return {"CANCELLED"}

        try:
            self._finalize_import(
                context, source_obj, output_path, settings,
                orig_matrix, orig_rot, orig_scale,
            )
        except Exception as exc:
            # Mantém a pasta temp para import manual em caso de falha
            self.report({"ERROR"}, f"Import of the Instant Meshes result failed: {exc} — files kept in '{temp_dir}'")
            return {"CANCELLED"}

        shutil.rmtree(temp_dir, ignore_errors=True)
        self.report({"INFO"}, "Instant Meshes remeshing completed.")
        return {"FINISHED"}

    # ------------------------------------------------------------------
    # Fluxo compartilhado
    # ------------------------------------------------------------------

    def _finalize_import(self, context, source_obj, output_path, settings, orig_matrix, orig_rot, orig_scale):
        """Importa o resultado e aplica o fluxo pós-remesh (compartilhado entre CLI e GUI)."""
        # Guarda de modo: o usuário pode ter clicado o botão dentro de edit mode
        if context.object is not None and context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        imported = self._import_result(context, output_path)

        # Evita o efeito cascata _remesh_remesh_remesh (Lógica do BPyMeshLab)
        base_name = source_obj.name.split("_remesh")[0]
        imported.name = f"{base_name}_remesh"

        base_data_name = source_obj.data.name.split("_remesh")[0]
        imported.data.name = f"{base_data_name}_remesh"

        # 4. Process Workflow Toggles
        self._copy_materials(source_obj, imported)

        if settings.hide_original:
            source_obj.hide_set(True)

        # 5. Clean up mesh data (flat/smooth shading, clear sharp edges)
        self._cleanup_mesh(context, imported, settings)

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

        return imported

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

    def _cleanup_mesh(self, context, imported, settings):
        select_only(context, imported)

        for edge in imported.data.edges:
            edge.use_edge_sharp = False

        if settings.shade_smooth:
            bpy.ops.object.shade_smooth()
        else:
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
