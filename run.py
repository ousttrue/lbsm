import bpy
import mathutils
from vertex import Vertex
import pathlib

HERE = pathlib.Path(__file__).absolute().parent


if __name__ == "__main__":

    for ob in bpy.context.scene.objects:
        if isinstance(ob.data, bpy.types.Mesh):
            vertices = Vertex.from_object(ob, mathutils.Matrix())
            print(vertices)

    dst = HERE / "tmp.lbsm"
