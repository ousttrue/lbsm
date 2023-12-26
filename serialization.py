from typing import List, NamedTuple, Dict
import struct
import pathlib
import io
import json
import os
import mathutils
from . import vertex


from typing import TypedDict, List, Optional, Tuple


class Asset(TypedDict):
    version: str


class BufferView(TypedDict):
    name: str  # must unique !
    byteOffset: int
    byteLength: int


class Attribute(TypedDict):
    vertexAttribute: str  # position | normal | tangent | color | tex0 | tex1 | blendWeights | blendJoints
    format: str  # f32 | u16 | u32
    dimension: int  # 1 2 3 4


class Stream(TypedDict):
    bufferView: str
    attributes: List[Attribute]


class Indices(TypedDict):
    stride: int  # 2 | 4
    bufferView: str


class Mesh(TypedDict):
    name: str
    vertexCount: int
    vertexStreams: List[Stream]
    indices: Indices
    joints: List[int]


class Joint(TypedDict):
    name: str
    parent: Optional[int]
    head: Tuple[float, float, float]
    tail: Optional[Tuple[float, float, float]]
    is_connected: bool


class Root(TypedDict):
    asset: Asset
    bufferViews: List[BufferView]
    meshes: List[Mesh]
    joints: List[Joint]  # rig


class Bin:
    def __init__(self) -> None:
        self.stream = io.BytesIO()
        self.bufferViews: List[BufferView] = []
        self.offset = 0

    def push(self, name: str, data: memoryview):
        byteLength = len(data.tobytes())
        bufferView = BufferView(
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


class Serializer:
    def __init__(self):
        self.joints: List[Joint] = []
        self.joint_map: Dict[vertex.Joint, int] = {}

    def get_or_create_joint(
        self, joints: Dict[str, vertex.Joint], joint: vertex.Joint
    ) -> int:
        if joint in self.joint_map:
            return self.joint_map[joint]

        parent = -1
        if joint.parent:
            parent = self.get_or_create_joint(joints, joints[joint.parent])

        index = len(self.joints)
        self.joints.append(
            Joint(
                name=joint.name,
                parent=parent,
                head=joint.position,
                tail=None,
                is_connected=joint.is_connected,
            )
        )
        self.joint_map[joint] = index

        return index

    def serialize(self, dst: pathlib.Path, meshes: List[vertex.VertexBuffer]):
        # print(dst, meshes)

        bin = Bin()
        json_data = Root(
            asset=Asset(version="alpha"),
            bufferViews=bin.bufferViews,
            meshes=[],
            joints=self.joints,
        )
        for i, vb in enumerate(meshes):
            name = f"mesh{i}"
            bin.push(f"{name}.vert", vb.geometry)
            bin.push(f"{name}.tex", vb.colortex)
            bin.push(f"{name}.indx", vb.indices.indices)
            mesh = Mesh(
                name=name,
                vertexCount=vb.vertex_count,
                vertexStreams=[
                    Stream(
                        bufferView=f"{name}.vert",
                        attributes=[
                            Attribute(
                                vertexAttribute="position", format="f32", dimension=3
                            ),
                            Attribute(
                                vertexAttribute="normal", format="f32", dimension=3
                            ),
                            Attribute(
                                vertexAttribute="tangent", format="f32", dimension=4
                            ),
                        ],
                    ),
                    Stream(
                        bufferView=f"{name}.tex",
                        attributes=[
                            Attribute(
                                vertexAttribute="color", format="f32", dimension=4
                            ),
                            Attribute(
                                vertexAttribute="tex0", format="f32", dimension=2
                            ),
                            Attribute(
                                vertexAttribute="tex1", format="f32", dimension=2
                            ),
                        ],
                    ),
                ],
                indices=Indices(
                    stride=vb.indices.stride,
                    bufferView=f"{name}.indx",
                ),
                joints=[],
            )

            if vb.skinning:
                joint_map = {joint.name: joint for joint in vb.skinning.joints}
                bin.push(f"{name}.skin", vb.skinning.skinning)
                mesh["vertexStreams"].append(
                    Stream(
                        bufferView=f"{name}.skin",
                        attributes=[
                            Attribute(
                                vertexAttribute="blendWeights",
                                format="f32",
                                dimension=4,
                            ),
                            Attribute(
                                vertexAttribute="blendIndices",
                                format="u16",
                                dimension=4,
                            ),
                        ],
                    )
                )
                mesh["joints"] = [
                    self.get_or_create_joint(joint_map, joint)
                    for joint in vb.skinning.joints
                ]

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


def serialize(dst: pathlib.Path, meshes: List[vertex.VertexBuffer]):
    s = Serializer()
    s.serialize(dst, meshes)
