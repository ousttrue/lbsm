import bpy
import struct
from typing import List, Tuple, NamedTuple
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
            "byteOffset": self.offset,
            "byteLength": byteLength,
        }
        self.bufferViews.append(bufferView)
        self.stream.write(data)
        self.offset += byteLength
        return bufferView


class Chunk(NamedTuple):
    chunkType: bytes
    data: bytes


def write_chunks(dst: pathlib.Path, *chunks: Chunk):
    # header size
    #
    # magic: char[4]
    # version: uint
    # byteLength: uint
    byteLength = 12
    for chunk in chunks:
        byteLength += 8 + len(chunk.data)

    with dst.open("wb") as w:
        # little endian binary format
        # magic
        w.write(b"LBSM")
        # version
        w.write(struct.pack("I", 1))
        # fileTotalLength
        w.write(struct.pack("I", byteLength))

        for chunk in chunks:
            # chunkDataLength
            w.write(struct.pack("I", len(chunk.data)))
            # chunkType
            if len(chunk.chunkType) != 4:
                raise Exception("must 4")
            w.write(chunk.chunkType)
            # chunkData
            w.write(chunk.data)

        return byteLength


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

    print(json.dumps(json_data, indent=2))
    json_chunk = json.dumps(json_data).encode("utf-8")

    # glb like format
    calcSize = write_chunks(
        dst,
        Chunk(b"JSON", json_chunk),
        Chunk(b"BIN\0", bin.stream.getvalue()),
    )

    result = dst.read_bytes()
    assert (len(result) == calcSize, "write size")


if __name__ == "__main__":
    meshes = []
    for ob in bpy.context.scene.objects:
        if isinstance(ob.data, bpy.types.Mesh):
            mesh = Vertex.from_object(ob, mathutils.Matrix())
            meshes.append(mesh)

    dst = HERE / "tmp.lbsm"
    export(dst, meshes)
