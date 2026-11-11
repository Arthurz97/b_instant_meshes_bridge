import bpy
from bpy.types import PropertyGroup
from bpy.props import IntProperty, FloatProperty, BoolProperty, EnumProperty

class BIMB_Settings(PropertyGroup):
    vertex_count: IntProperty(
        name="Vertex Count",
        description="Desired vertex count of the output mesh",
        default=2000,
        min=10,
        soft_max=50000,
    )
    smooth_iterations: IntProperty(
        name="Smooth Iterations",
        description="Number of smoothing & ray tracing reprojection steps",
        default=2,
        min=0,
        max=10,
    )
    crease_angle: IntProperty(
        name="Crease angle",
        description="Dihedral angle threshold for creases",
        default=20,
        min=0,
        max=180,
    )
    sharp_creases: BoolProperty(
        name="Sharp creases",
        description="Don't smooth discontinuous surface normals in CAD models and similar input data",
        default=True,
    )
    remesh_as: EnumProperty(
        name="Remesh as",
        items=[
            ("TRIANGLES", "Triangles (6-RoSy, 6-PoSy)", ""),
            ("QUADS_24", "Quads (2-RoSy, 4-PoSy)", ""),
            ("QUADS_44", "Quads (4-RoSy, 4-PoSy)", ""),
        ],
        default="QUADS_44",
    )
    resolution_mode: EnumProperty(
        name="Resolution Mode",
        items=[
            ("VERTICES", "Vertex Count", "Desired vertex count of the output mesh"),
            ("FACES", "Face Count", "Desired face count of the output mesh"),
            ("SCALE", "Edge Scale", "Desired world space length of edges in the output"),
        ],
        default="VERTICES",
    )
    face_count: IntProperty(
        name="Face Count",
        description="Desired face count of the output mesh",
        default=2000,
        min=10,
    )
    edge_scale: FloatProperty(
        name="Edge Scale",
        description="Desired world space length of edges in the output",
        default=1.0,
        min=0.01,
        subtype="DISTANCE",
    )
    deterministic: BoolProperty(
        name="Deterministic",
        description="Prefer (slower) deterministic algorithms",
        default=False,
    )
    pure_quad_mesh: BoolProperty(
        name="Pure quad mesh",
        description="Apply one step of subdivision to extract a pure quad mesh",
        default=True,
    )
    extrinsic: BoolProperty(
        name="Extrinsic",
        description="Use an extrinsic smoothness energy with automatic parameter-free alignment to geometric features",
        default=True,
    )
    align_to_boundaries: BoolProperty(
        name="Align to boundaries",
        description="Align to boundaries (only applies to open / non-manifold meshes)",
        default=False,
    )
    preserve_transforms: BoolProperty(
        name="Preserve Transforms",
        description="Restores the original Rotation and Scale to the final object. If unchecked, applied transforms are used",
        default=False,
    )
    apply_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply all modifiers before sending the mesh to Instant Meshes",
        default=False,
    )
    shade_smooth: BoolProperty(
        name="Shade Smooth",
        description="Render and display faces smooth, using interpolated vertex normals.",
        default=False,
    )
    hide_original: BoolProperty(
        name="Hide Original",
        description="Hide the original object from the viewport after remeshing",
        default=True,
    )
    open_ui: BoolProperty(
        name="Use GUI Mode",
        description="Opens the object in the Instant Meshes GUI. IMPORTANT: Export overwriting the 'out.obj' file and close the app to import the result automatically",
        default=False,
    )