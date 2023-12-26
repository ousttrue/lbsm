import pathlib
import bpy
import mathutils
from bpy.props import (
    StringProperty,
    BoolProperty,
    FloatProperty,
)
from bpy_extras.io_utils import (
    ExportHelper,
    orientation_helper,
    axis_conversion,
)
from bpy.types import (
    Operator,
)


bl_info = {
    "name": "LinearBlendSkinningModel Exporter",
    "version": (0, 0, 1),
    "blender": (4, 0, 0),
    "location": "File > Import-Export",
    "description": "Import-Export lbsm files",
    "category": "Import-Export",
}


from . import serialization
from . import vertex


@orientation_helper(axis_forward="Z", axis_up="Y")
class ExportLBSM(Operator, ExportHelper):
    bl_idname = "export_mesh.lbsm"
    bl_label = "Export lbsm"
    bl_description = """Save LinearBlendSkinningModel data"""

    filename_ext = ".lbsm"
    filter_glob: StringProperty(default="*.lbsm", options={"HIDDEN"})

    use_selection: BoolProperty(
        name="Selection Only",
        description="Export selected objects only",
        default=False,
    )
    global_scale: FloatProperty(
        name="Scale",
        min=0.01,
        max=1000.0,
        default=1.0,
    )
    use_scene_unit: BoolProperty(
        name="Scene Unit",
        description="Apply current scene's unit (as defined by unit scale) to exported data",
        default=False,
    )
    use_mesh_modifiers: BoolProperty(
        name="Apply Modifiers",
        description="Apply the modifiers before saving",
        default=True,
    )

    def execute(self, context):
        import os
        import itertools
        from mathutils import Matrix

        keywords = self.as_keywords(
            ignore=(
                "axis_forward",
                "axis_up",
                "use_selection",
                "global_scale",
                "check_existing",
                "filter_glob",
                "use_scene_unit",
                "use_mesh_modifiers",
                "batch_mode",
                "global_space",
            ),
        )

        scene = context.scene
        if self.use_selection:
            data_seq = context.selected_objects
        else:
            data_seq = scene.objects

        # Take into account scene's unit scale, so that 1 inch in Blender gives 1 inch elsewhere! See T42000.
        global_scale = self.global_scale
        if scene.unit_settings.system != "NONE" and self.use_scene_unit:
            global_scale *= scene.unit_settings.scale_length

        global_matrix = axis_conversion(
            to_forward=self.axis_forward,
            to_up=self.axis_up,
        ).to_4x4() @ Matrix.Scale(global_scale, 4)

        meshes = vertex.export_objects(data_seq, global_matrix)
        serialization.serialize(pathlib.Path(keywords["filepath"]), meshes)

        return {"FINISHED"}

    def draw(self, context):
        pass


class LBSM_PT_export_main(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = ""
    bl_parent_id = "FILE_PT_operator"
    bl_options = {"HIDE_HEADER"}

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_MESH_OT_lbsm"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "ascii")
        layout.prop(operator, "batch_mode")


class LBSM_PT_export_include(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_MESH_OT_lbsm"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "use_selection")


class LBSM_PT_export_transform(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Transform"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_MESH_OT_lbsm"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "global_scale")
        layout.prop(operator, "use_scene_unit")

        layout.prop(operator, "axis_forward")
        layout.prop(operator, "axis_up")


class LBSM_PT_export_geometry(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Geometry"
    bl_parent_id = "FILE_PT_operator"

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname == "EXPORT_MESH_OT_lbsm"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False  # No animation.

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator, "use_mesh_modifiers")


# def menu_import(self, context):
#     self.layout.operator(ImportSTL.bl_idname, text="Stl (.stl)")


def menu_export(self, context):
    self.layout.operator(ExportLBSM.bl_idname, text="Lbsm (.lbsm)")


classes = (
    ExportLBSM,
    LBSM_PT_export_main,
    LBSM_PT_export_include,
    LBSM_PT_export_geometry,
    LBSM_PT_export_transform,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    # bpy.types.TOPBAR_MT_file_import.append(menu_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_export)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    # bpy.types.TOPBAR_MT_file_import.remove(menu_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_export)


if __name__ == "__main__":
    register()
