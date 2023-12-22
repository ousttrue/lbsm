import bpy
import mathutils
from lbsm import Exporter
import pathlib

HERE = pathlib.Path(__file__).absolute().parent


if __name__ == "__main__":
    exporter = Exporter(mathutils.Matrix(), False)

    for ob in bpy.context.scene.objects:
        exporter.push_object(ob)

    dst = HERE / "tmp.lbsm"
    exporter.write(dst)

