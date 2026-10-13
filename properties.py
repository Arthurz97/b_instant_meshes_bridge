import bpy
from bpy.types import PropertyGroup
from bpy.props import IntProperty, BoolProperty

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
    crease_degree: IntProperty(
        name="Crease Degree",
        description="Dihedral angle threshold for creases",
        default=0,
        min=0,
        max=100,
    )
    deterministic: BoolProperty(
        name="Deterministic",
        description="Prefer (slower) deterministic algorithms",
        default=False,
    )
    dominant: BoolProperty(
        name="Dominant",
        description="Generate a tri/quad dominant mesh instead of a pure tri/quad mesh",
        default=False,
    )
    intrinsic: BoolProperty(
        name="Intrinsic",
        description="Intrinsic mode (extrinsic is the default)",
        default=False,
    )
    boundaries: BoolProperty(
        name="Boundaries",
        description="Align to boundaries (only applies when the mesh is not closed)",
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
    transfer_uvs: BoolProperty(
        name="Transfer UVs",
        description="Project original UV maps onto the new remeshed object",
        default=False,
    )
    hide_original: BoolProperty(
        name="Hide Original",
        description="Hide the original object from the viewport after remeshing",
        default=True,
    )
    open_ui: BoolProperty(
        name="Open in Instant Meshes",
        description="Opens the selected object in the Instant Meshes GUI. Import happens when you close the app",
        default=False,
    )