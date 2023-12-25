import bpy
import struct
from typing import List, Tuple, NamedTuple, TypedDict
import mathutils
import ctypes
import vertex
import pathlib
import io
import json
import os
import jsontype


HERE = pathlib.Path(__file__).absolute().parent


# class BoneBinding(NamedTuple):
#     name: str
#     weight: float


# class VertexBinding(NamedTuple):
#     b0: BoneBinding
#     b1: BoneBinding
#     b2: BoneBinding
#     b3: BoneBinding


class Bin:
    def __init__(self) -> None:
        self.stream = io.BytesIO()
        self.bufferViews: List[jsontype.BufferView] = []
        self.offset = 0

    def push(self, name: str, data: memoryview):
        byteLength = len(data.tobytes())
        bufferView = jsontype.BufferView(
            name=name,
            byteOffset=self.offset,
            byteLength=byteLength,
        )
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


def export(dst: pathlib.Path, meshes: List[vertex.VertexBuffer]):
    print(dst, meshes)

    bin = Bin()
    json_data = jsontype.Root(
        asset=jsontype.Asset(version="alpha"),
        bufferViews=bin.bufferViews,
        meshes=[],
    )
    for i, vb in enumerate(meshes):
        name = f"mesh{i}"
        bin.push(f"{name}.vert", vb.geometry)
        bin.push(f"{name}.tex", vb.colortex)
        bin.push(f"{name}.indx", vb.indices.indices)
        mesh = jsontype.Mesh(
            name=name,
            vertexCount=vb.vertex_count,
            vertexStreams=[
                jsontype.Stream(
                    bufferView=f"{name}.vert",
                    attributes=[
                        jsontype.Attribute(
                            vertexAttribute="position", format="f32", dimension=3
                        ),
                        jsontype.Attribute(
                            vertexAttribute="normal", format="f32", dimension=3
                        ),
                        jsontype.Attribute(
                            vertexAttribute="tangent", format="f32", dimension=4
                        ),
                    ],
                ),
                jsontype.Stream(
                    bufferView=f"{name}.tex",
                    attributes=[
                        jsontype.Attribute(
                            vertexAttribute="color", format="f32", dimension=4
                        ),
                        jsontype.Attribute(
                            vertexAttribute="tex0", format="f32", dimension=2
                        ),
                        jsontype.Attribute(
                            vertexAttribute="tex1", format="f32", dimension=2
                        ),
                    ],
                ),
            ],
            indices=jsontype.Indices(
                stride=vb.indices.stride,
                bufferView=f"{name}.indx",
            ),
            joints=[],
        )
        if vb.skinning:
            bin.push(f"{name}.skin", vb.skinning.skinning)
            mesh["vertexStreams"].append(
                jsontype.Stream(
                    bufferView=f"{name}.skin",
                    attributes=[
                        jsontype.Attribute(
                            vertexAttribute="blendWeights", format="f32", dimension=4
                        ),
                        jsontype.Attribute(
                            vertexAttribute="blendIndices", format="u16", dimension=4
                        ),
                    ],
                )
            )
            mesh["joints"] = vb.skinning.joints

        json_data["meshes"].append(mesh)

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


def export_objects(objects: List[bpy.types.Object]):
    meshes = []
    for ob in objects:
        if isinstance(ob.data, bpy.types.Mesh):
            mesh = vertex.from_object(ob, mathutils.Matrix())
            meshes.append(mesh)

    dst = HERE / "tmp.lbsm"
    export(dst, meshes)


def export_glb(path: pathlib.Path):
    # clear scene
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    # load glb
    print(path, path.exists())
    bpy.ops.import_scene.gltf(filepath=str(path))

    export_objects(bpy.context.scene.objects)


if __name__ == "__main__":
    # export_objects(bpy.context.scene.objects)

    glb = (
        pathlib.Path(os.environ["GLTF_SAMPLE_MODELS"])
        / "2.0/CesiumMan/glTF-Binary/CesiumMan.glb"
    )
    export_glb(glb)
