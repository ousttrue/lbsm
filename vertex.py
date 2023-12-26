import ctypes
import pathlib
from typing import Optional, Tuple, List, NamedTuple, Dict
import bpy
import mathutils


def to_tuple(v: mathutils.Vector):
    return (v.x, v.y, v.z)


class Float2(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
    ]

    def __str__(self) -> str:
        return f"({self.x},{self.y})"

    @staticmethod
    def from_vector(v: mathutils.Vector) -> "Float2":
        return Float2(v.x, v.y)


class Float3(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
    ]

    def __str__(self) -> str:
        return f"({self.x},{self.y},{self.z})"

    @staticmethod
    def from_vector(v: mathutils.Vector) -> "Float3":
        return Float3(v.x, v.y, v.z)


class Float4(ctypes.Structure):
    _fields_ = [
        ("x", ctypes.c_float),
        ("y", ctypes.c_float),
        ("z", ctypes.c_float),
        ("w", ctypes.c_float),
    ]


class VertexGeometry(ctypes.Structure):
    _fields_ = [
        ("position", Float3),
        ("normal", Float3),
        ("tangent", Float4),
    ]


class VertexColorTex(ctypes.Structure):
    _fields_ = [
        ("color", Float4),
        ("tex0", Float2),
        ("tex1", Float2),
    ]


class VertexSkin(ctypes.Structure):
    _fields_ = [
        ("weights", (ctypes.c_float * 4)),
        ("joints", (ctypes.c_ushort * 4)),
    ]


def get_armature(ob: bpy.types.Object) -> Optional[bpy.types.Object]:
    for m in ob.modifiers:
        if m.type == "ARMATURE":
            return m.object


class Joint(NamedTuple):
    name: str
    position: Tuple[float, float, float]
    is_connected: bool
    parent: Optional[str]  # armature bone name is unique


class Skinning(NamedTuple):
    joints: List[Joint]
    skinning: memoryview


class Indices(NamedTuple):
    stride: int  # 2 or 4
    indices: memoryview


class VertexBuffer(NamedTuple):
    indices: Indices
    vertex_count: int
    geometry: memoryview
    colortex: memoryview
    skinning: Optional[Skinning]


def from_mesh(
    matrix: mathutils.Matrix,
    ob: bpy.types.Object,
    mesh: bpy.types.Mesh,
) -> VertexBuffer:
    mat = matrix @ ob.matrix_world
    mesh.transform(mat)
    if mat.is_negative:
        mesh.flip_normals()
    mesh.calc_loop_triangles()

    geometry = (VertexGeometry * len(mesh.loops))()
    colortex = (VertexColorTex * len(mesh.loops))()
    indexCount = len(mesh.loop_triangles) * 3
    if len(geometry) > 65535:
        index_stride = 4
        indices = (ctypes.c_uint * indexCount)()
    else:
        index_stride = 2
        indices = (ctypes.c_ushort * indexCount)()

    i = 0
    uv_layer = mesh.uv_layers and mesh.uv_layers[0]

    skinWeights = None
    armatureOb = get_armature(ob)
    armature = None
    if armatureOb:
        armature = armatureOb.data
        skinWeights = (VertexSkin * len(mesh.loops))()
        jointNames = [g.name for g in ob.vertex_groups]

    for tri in mesh.loop_triangles:
        for loop_index in tri.loops:
            dst_geom = geometry[loop_index]
            dst_tex = colortex[loop_index]
            v = mesh.vertices[mesh.loops[loop_index].vertex_index]

            # geom
            dst_geom.position = Float3.from_vector(v.co)
            if tri.use_smooth:
                dst_geom.normal = Float3.from_vector(v.normal)
            else:
                dst_geom.normal = Float3.from_vector(tri.normal)

            # color tex
            if isinstance(uv_layer, bpy.types.MeshUVLoopLayer):
                dst_tex.tex0 = Float2.from_vector(uv_layer.data[loop_index].uv)

            # skin
            if skinWeights:
                dst_skin = skinWeights[loop_index]

                def set_joint_weight(index: int, vg: bpy.types.VertexGroupElement):
                    dst_skin.joints[index] = vg.group
                    dst_skin.weights[index] = vg.weight

                for j, vg in enumerate(v.groups[:4]):
                    set_joint_weight(j, vg)

            indices[i] = loop_index
            i += 1

    skinning = None
    if skinWeights:
        mat = matrix @ armatureOb.matrix_world

        def create_joint(name: str):
            position = (0, 0, 0)
            bone = armature.bones[name]
            if bone:
                head_local = mat @ bone.head_local
                position = to_tuple(head_local)

            parent = None
            if bone.parent:
                parent = bone.parent.name

            return Joint(
                name=name, position=position, is_connected=bone.use_connect, parent=parent
            )

        skinning = Skinning(
            [create_joint(name) for name in jointNames],
            memoryview(skinWeights),
        )

    return VertexBuffer(
        Indices(index_stride, memoryview(indices)),
        len(mesh.loops),
        memoryview(geometry),
        memoryview(colortex),
        skinning,
    )


def from_object(
    ob: bpy.types.Object,
    matrix: mathutils.Matrix,
    *,
    use_mesh_modifiers=False,
) -> Optional[VertexBuffer]:
    if ob.mode == "EDIT":
        ob.update_from_editmode()

    if use_mesh_modifiers:
        # get the modifiers
        depsgraph = bpy.context.evaluated_depsgraph_get()
        mesh_owner = ob.evaluated_get(depsgraph)
    else:
        mesh_owner = ob

    # Object.to_mesh() is not guaranteed to return a mesh.
    try:
        mesh = mesh_owner.to_mesh()
        if not isinstance(mesh, bpy.types.Mesh):
            return

        return from_mesh(matrix, ob, mesh)

    except RuntimeError:
        raise
    finally:
        mesh_owner.to_mesh_clear()


def export_objects(
    objects: List[bpy.types.Object], matrix: mathutils.Matrix
) -> List[VertexBuffer]:
    meshes = []
    for ob in objects:
        if isinstance(ob.data, bpy.types.Mesh):
            mesh = from_object(ob, matrix)
            meshes.append(mesh)
    return meshes


def export_glb(path: pathlib.Path, matrix: mathutils.Matrix) -> List[VertexBuffer]:
    # clear scene
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # load glb
    bpy.ops.import_scene.gltf(filepath=str(path))

    return export_objects(bpy.context.scene.objects, matrix)
