import pathlib
import bpy
import mathutils


class Exporter:
    def __init__(self, matrix: mathutils.Matrix, use_mesh_modifiers: bool) -> None:
        self.matrix = matrix
        self.use_mesh_modifiers = use_mesh_modifiers

    def push_object(self, ob: bpy.types.Object):
        print("export", ob)

        # faces = itertools.chain.from_iterable(
        #     faces_from_mesh(ob, global_matrix, self.use_mesh_modifiers)
        # )
        # get the editmode data
        if ob.mode == "EDIT":
            ob.update_from_editmode()

        # get the modifiers
        if self.use_mesh_modifiers:
            depsgraph = bpy.context.evaluated_depsgraph_get()
            mesh_owner = ob.evaluated_get(depsgraph)
        else:
            mesh_owner = ob

        # Object.to_mesh() is not guaranteed to return a mesh.
        try:
            mesh = mesh_owner.to_mesh()
        except RuntimeError:
            return

        if not isinstance(mesh, bpy.types.Mesh):
            return

        mat = self.matrix @ ob.matrix_world
        self.push_mesh(mesh, mat)

        mesh_owner.to_mesh_clear()

    def push_mesh(self, mesh: bpy.types.Mesh, mat: mathutils.Matrix):
        mesh.transform(mat)
        if mat.is_negative:
            mesh.flip_normals()
        mesh.calc_loop_triangles()

        # POS & NORMAL
        print(f"{len(mesh.vertices)} verts")
        for i, v in enumerate(mesh.vertices):
            pass
        
        # MeshLoopTriangle
        if mesh.uv_layers:
            uv_layer = mesh.uv_layers[0]
            def get_uv(i):
                return uv_layer.data[i].uv
        else:
            def get_uv(i):
                return None

        for i, tri in enumerate(mesh.loop_triangles):
            print(i, [get_uv(l) for l in tri.loops])
            # polygon = mesh.polygons[tri.polygon_index]
            # print(i, polygon, [i for i in tri.vertices])
        #     yield [vertices[index] for index in tri.vertices]
            
        # uv
            
        # VertexGroup joint, weight

    def write(self, filepath: pathlib.Path):
        # print([f for f in faces])
        print(filepath)
