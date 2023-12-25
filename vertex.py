import ctypes
import bpy
import mathutils
from typing import Optional, Tuple


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


class Vertex(ctypes.Structure):
    _fields_ = [
        ("position", Float3),
        ("normal", Float3),
        ("uv", Float2),
    ]

    def __str__(self) -> str:
        return f"[pos: {self.position}, nom: {self.normal}, uv: {self.uv}]"

    @staticmethod
    def from_mesh(
        mesh: bpy.types.Mesh, mat: mathutils.Matrix
    ) -> Tuple[memoryview, memoryview]:
        mesh.transform(mat)
        if mat.is_negative:
            mesh.flip_normals()
        mesh.calc_loop_triangles()

        vertices = (Vertex * len(mesh.loops))()
        indexCount = len(mesh.loop_triangles) * 3
        if len(vertices) > 65535:
            indices = (ctypes.c_uint * indexCount)()
        else:
            indices = (ctypes.c_ushort * indexCount)()

        i = 0
        uv_layer = mesh.uv_layers and mesh.uv_layers[0]
        for tri in mesh.loop_triangles:
            for loop_index in tri.loops:
                dst = vertices[loop_index]
                v = mesh.vertices[mesh.loops[loop_index].vertex_index]
                dst.position = Float3.from_vector(v.co)
                if tri.use_smooth:
                    dst.normal = Float3.from_vector(v.normal)
                else:
                    dst.normal = Float3.from_vector(tri.normal)
                if isinstance(uv_layer, bpy.types.MeshUVLoopLayer):
                    dst.uv = Float2.from_vector(uv_layer.data[loop_index].uv)
                indices[i] = loop_index
                i += 1

        return (memoryview(vertices), memoryview(indices))

    @staticmethod
    def from_object(
        ob: bpy.types.Object, matrix: mathutils.Matrix, *, use_mesh_modifiers=False
    ) -> Optional[Tuple[memoryview, memoryview]]:
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

            mat = matrix @ ob.matrix_world
            return Vertex.from_mesh(mesh, mat)

        except RuntimeError:
            return
        finally:
            mesh_owner.to_mesh_clear()
