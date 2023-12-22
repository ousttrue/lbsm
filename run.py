import bpy
from typing import List, Tuple
import mathutils
import ctypes
from vertex import Vertex
import pathlib
import io
import json

HERE = pathlib.Path(__file__).absolute().parent


class Bin:
    def __init__(self) -> None:
        self.stream = io.BytesIO()
        self.bufferViews = []
        self.offset = 0

    def push(self, name: str, data: memoryview):
        byteLength = len(data.tobytes())
        bufferView = {
            "name": name,
            "offset": self.offset,
            "byteLength": byteLength,
        }
        self.bufferViews.append(bufferView)
        self.stream.write(data)
        self.offset += byteLength
        return bufferView


def export(dst: pathlib.Path, meshes: List[Tuple[memoryview, memoryview]]):
    print(dst, meshes)

    bin = Bin()
    json_data = {
        "asset": {
            "version": "alpha",
        },
        "bufferViews": bin.bufferViews,
        "meshes": [],
    }
    for i, (vertices, indices) in enumerate(meshes):
        name = f"mesh{i}"
        bin.push(f"{name}.vert", vertices)

        bin.push(f"{name}.indx", indices)
        json_data["meshes"].append(
            {
                "name": name,
                "vertices": f"{name}.vert",
                "indices": f"{name}.indx",
            }
        )

    # glb like format
    print(json.dumps(json_data, indent=2))
    json_chunk = json.dumps(json_data)


if __name__ == "__main__":

    meshes = []
    for ob in bpy.context.scene.objects:
        if isinstance(ob.data, bpy.types.Mesh):
            mesh = Vertex.from_object(ob, mathutils.Matrix())
            meshes.append(mesh)

    dst = HERE / "tmp.lbsm"
    export(dst, meshes)
