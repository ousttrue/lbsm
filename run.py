import pathlib
import os
import bpy
import mathutils


HERE = pathlib.Path(__file__).absolute().parent


if __name__ == "__main__":
    # export_objects(bpy.context.scene.objects)
    glb = (
        pathlib.Path(os.environ["GLTF_SAMPLE_MODELS"])
        / "2.0/CesiumMan/glTF-Binary/CesiumMan.glb"
    )

    zup_to_yup = mathutils.Matrix(
        [
            [-1.0000, 0.0000, 0.0000, 0.0000],
            [0.0000, 0.0000, 1.0000, 0.0000],
            [0.0000, 1.0000, 0.0000, 0.0000],
            [0.0000, 0.0000, 0.0000, 1.0000],
        ],
    )
    from lbsm import vertex

    meshes = vertex.export_glb(glb, zup_to_yup)

    dst = HERE / "tmp.lbsm"
    from lbsm import serialization

    serialization.serialize(dst, meshes)
