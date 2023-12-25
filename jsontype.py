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


class Joint(TypedDict):
    name: str
    position: Tuple[float, float, float]


class Indices(TypedDict):
    stride: int  # 2 | 4
    bufferView: str


class Mesh(TypedDict):
    name: str
    vertexCount: int
    vertexStreams: List[Stream]
    indices: Indices
    joints: List[Joint]


class Root(TypedDict):
    asset: Asset
    bufferViews: List[BufferView]
    meshes: List[Mesh]
