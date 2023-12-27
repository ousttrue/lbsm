from typing import List, NamedTuple, Dict, Tuple
import struct
import pathlib
import io
import json
from . import vertex


from typing import TypedDict, List, Optional, Tuple


class Axes(TypedDict):
    x: str
    y: str
    z: str


class Asset(TypedDict):
    version: str
    axes: Axes


class BufferView(TypedDict):
    name: str  # must unique !
    byteOffset: int
    byteLength: int


class Attribute(TypedDict):
    vertexAttribute: str  # position | normal | tangent | color | tex0 | tex1 | blendWeights | blendJoints
    format: str  # f32 | u16 | u32
    dimension: int  # 1 2 3 4


class Stream(TypedDict):
    bufferView: int
    attributes: List[Attribute]


class Indices(TypedDict):
    stride: int  # 2 | 4
    bufferView: int


class SubMesh(TypedDict):
    material: int
    drawCount: int


class Mesh(TypedDict):
    name: str
    vertexCount: int
    vertexStreams: List[Stream]
    indices: Indices
    subMeshes: List[SubMesh]
    joints: List[int]


class Bone(TypedDict):
    name: str
    parent: Optional[int]
    head: Tuple[float, float, float]
    tail: Optional[Tuple[float, float, float]]
    is_connected: bool


class Texture(TypedDict):
    bufferView: int


class Material(TypedDict):
    name: str
    color: Tuple[float, float, float, float]
    colorTexture: int


class Root(TypedDict):
    asset: Asset
    bufferViews: List[BufferView]
    tetures: List[Texture]
    materials: List[Material]
    meshes: List[Mesh]
    bones: List[Bone]  # rig


class Bin:
    def __init__(self) -> None:
        self.stream = io.BytesIO()
        self.bufferViews: List[BufferView] = []
        self.offset = 0

    def push(self, name: str, data: memoryview) -> int:
        index = len(self.bufferViews)
        byteLength = len(data.tobytes())
        bufferView = BufferView(
            name=name,
            byteOffset=self.offset,
            byteLength=byteLength,
        )
        self.bufferViews.append(bufferView)
        self.stream.write(data)
        self.offset += byteLength
        return index


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
        self.bones: List[Bone] = []
        self.joint_map: Dict[vertex.Joint, int] = {}

    def get_or_create_joint(
        self, joints: Dict[str, vertex.Joint], joint: vertex.Joint
    ) -> int:
        if joint in self.joint_map:
            return self.joint_map[joint]

        parent = -1
        if joint.parent:
            parent = self.get_or_create_joint(joints, joints[joint.parent])

        index = len(self.bones)
        self.bones.append(
            Bone(
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
            asset=Asset(
                version="alpha",
                axes=Axes(
                    x="right",
                    y="up",
                    z="back",
                ),
            ),
            bufferViews=bin.bufferViews,
            textures=[],
            materials=[Material(name="tmp", color=(1, 1, 1, 1), colorTexture=-1)],
            meshes=[],
            bones=self.bones,
        )
        for i, vb in enumerate(meshes):
            name = f"mesh{i}"
            vert = bin.push(f"{name}.vert", vb.geometry)
            tex = bin.push(f"{name}.tex", vb.colortex)
            indx = bin.push(f"{name}.indx", vb.indices.indices)
            mesh = Mesh(
                name=name,
                vertexCount=vb.vertex_count,
                vertexStreams=[
                    Stream(
                        bufferView=vert,
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
                        bufferView=tex,
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
                    bufferView=indx,
                ),
                subMeshes=[SubMesh(material=0, drawCount=vb.indices.get_draw_count())],
                joints=[],
            )

            if vb.skinning:
                joint_map = {joint.name: joint for joint in vb.skinning.joints}
                skin = bin.push(f"{name}.skin", vb.skinning.skinning)
                mesh["vertexStreams"].append(
                    Stream(
                        bufferView=skin,
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
