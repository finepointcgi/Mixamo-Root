
'''
    Copyright (C) 2022  Richard Perry
    Copyright (C) Johngoss725 (Average Godot Enjoyer)

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Note that Johngoss725's original contributions were published under a 
    Creative Commons 1.0 Universal License (CC0-1.0) located at
    <https://github.com/Johngoss725/Mixamo-To-Godot>.
'''

bl_info = {
    "name": "Mixamo Root",
    "author": "Richard Perry, Johngoss725",
    "version": (1, 2, 2),
    "blender": (2, 80, 0),
    "location": "3D View > UI (Right Panel) > Mixamo Tab",
    "description": ("Script to bake insert root motion bone for Mixamo Animations"),
    "warning": "",  # used for warning icon and text in addons panel
    "wiki_url": "https://github.com/RichardPerry/mixamo_root_bones/wiki",
    "tracker_url": "https://github.com/enziop/mixamo_root_bones/issues" ,
    "category": "Animation"
}

import bpy

try:
    from . import mixamoroot
except SystemError:
    import mixamoroot

if "bpy" in locals():
    from importlib import reload
    if "mixamoroot" in locals():
        reload(mixamoroot)

class MixamoPropertyGroup(bpy.types.PropertyGroup):
    '''Property container for options and paths of Mixamo Root'''
    hip_name: bpy.props.StringProperty(
        name="Hip Bone Name",
        description="Name to identify the hip bone if not MixamoRig:Hips",
        maxlen = 256,
        default = "Hips",
        subtype='NONE')
    root_name: bpy.props.StringProperty(
        name="Root Bone Name",
        description="Name to save the root bone, default is Root",
        maxlen = 256,
        default = "Root",
        subtype='NONE')
    name_prefix: bpy.props.StringProperty(
        name="Name Prefix",
        description="Prefix of mixamo armature components to help identification, if not default of 'mixamorig:'",
        maxlen = 256,
        default = "mixamorig:",
        subtype='NONE')
    source_directory: bpy.props.StringProperty(
        name="Source Directory",
        description="Path to directory containing mixamo animation files (.fbx)",
        maxlen = 256,
        default = "",
        subtype='DIR_PATH')
    remove_prefix: bpy.props.BoolProperty(
        name="Remove Prefix",
        description="Remove prefix from armature component names",
        default=False)
    insert_root: bpy.props.BoolProperty(
        name="Insert Root",
        description="Inserts a root bone at the base of the model aligned with the hip's horizontal plane coordinates",
        default=False)
    delete_armatures: bpy.props.BoolProperty(
        name="Delete Armatures",
        description="Deletes all but one imported armature in the blend file. This assumes you've imported mixamo armatures for animations all applied to the same model",
        default=False)
    delete_applied_armatures: bpy.props.BoolProperty(
        name="Delete Armatures",
        description="Deletes all armatures for applied animations after the process is complete",
        default=False)
    push_nla: bpy.props.BoolProperty(
        name="Push To NLA",
        description="Pushes all the actions created for the control rig to the NLA",
        default=False)

class OBJECT_OT_ImportAnimations(bpy.types.Operator):
    '''Operator for importing animations and inserting root bones'''
    bl_idname = "mixamo.importanim"
    bl_label = "Import Animations"
    bl_description = "Imports all mixamo animations from the [Source Directory], insert root bones, and merges into a single armature"

    def execute(self, context):
        mixamo = context.scene.mixamo
        source_directory = mixamo.source_directory
        hip_name = mixamo.hip_name
        root_name = mixamo.root_name
        name_prefix = mixamo.name_prefix
        remove_prefix = mixamo.remove_prefix
        insert_root = mixamo.insert_root
        delete_armatures = mixamo.delete_armatures
        if source_directory == '':
            self.report({'ERROR_INVALID_INPUT'}, "Error: no Source Directory set.")
            return{ 'CANCELLED'}
        if hip_name == '':
            self.report({'ERROR_INVALID_INPUT'}, "Error: no Hip Bone Name set.")
            return{ 'CANCELLED'}
        if root_name == '':
            self.report({'ERROR_INVALID_INPUT'}, "Error: no Root Bone Name set.")
            return{ 'CANCELLED'}
        if remove_prefix == True:
            self.report({'WARNING'}, "Remove Prefix set to true, armature components will have their mixamo prefix removed.")
        if delete_armatures == True:
            self.report({'WARNING'}, "Delete Armatures set to true, imported animation armatures will be removed.")
        mixamoroot.get_all_anims(
            bpy.path.abspath(source_directory),
            root_bone_name=root_name,
            hip_bone_name=hip_name,
            remove_prefix=remove_prefix, name_prefix=name_prefix, insert_root=insert_root, delete_armatures=delete_armatures)
        return{ 'FINISHED'}

class OBJECT_OT_ApplyAnimations(bpy.types.Operator):
    '''Operator for applying all imported animations to a target control rig'''
    bl_idname = "mixamo.applyanims"
    bl_label = "Apply Animations"
    bl_description = "Applies all the imported mixamo animations, to a single mixamo control rig. ONLY for mixamo control rigs generated with mixamo addon"

    def execute(self, context):
        mixamo = context.scene.mixamo
        mixamo_control_rig = context.scene.mixamo_control_rig
        delete_applied_armatures = mixamo.delete_applied_armatures
        control_rig = mixamo_control_rig
        push_nla = mixamo.push_nla
        if control_rig == '' or control_rig == None or bpy.data.objects[control_rig.name].type != "ARMATURE":
            self.report({'ERROR_INVALID_INPUT'}, "Error: No valid control rig armature selected")
            return{ 'CANCELLED'}
        if delete_applied_armatures == True:
            self.report({'WARNING'}, "Delete Armatures set to true, imported animation armatures will be removed.")
        mixamoroot.apply_all_anims(delete_applied_armatures=delete_applied_armatures, control_rig=control_rig, push_nla=push_nla)
        return{ 'FINISHED'}

class OBJECT_OT_AddRootNLA(bpy.types.Operator):
    '''Operator for adding a root bone to all animations to in the NLA, including keyframes'''
    bl_idname = "mixamo.addrootnla"
    bl_label = "Add Root"
    bl_description = "Adds a root bone to all animation strips in the NLA for the selected armature, iterating through every keyframe and copying the hip position. Sets the Z coordinate to a minimum of 0"

    # Works on the selected armature only
    def execute(self, context):
        mixamo = context.scene.mixamo
        hip_name = mixamo.hip_name
        root_name = mixamo.root_name
        name_prefix = mixamo.name_prefix
        if hip_name == '':
            self.report({'ERROR_INVALID_INPUT'}, "Error: no Hip Bone Name set.")
            return{ 'CANCELLED'}
        if root_name == '':
            self.report({'ERROR_INVALID_INPUT'}, "Error: no Root Bone Name set.")
            return{ 'CANCELLED'}
        mixamoroot.add_root_bone_nla(root_bone_name=root_name, hip_bone_name=hip_name, name_prefix=name_prefix)
        return{ 'FINISHED'}

class MIXAMOCONV_VIEW_3D_PT_mixamoroot(bpy.types.Panel):
    """Creates a Tab in the Toolshelve in 3D_View"""
    bl_label = "Mixamo Root"
    bl_idname = "MIXAMOCONV_VIEW_3D_PT_mixamoroot"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Mixamo"

    def draw(self, context):
        layout = self.layout

        scene = bpy.context.scene

        box = layout.box()
        box.label(text="Import Helpers")
        # Options for how to do the conversion
        row = box.row()
        row.prop(scene.mixamo, "insert_root", toggle=True)
        row = box.row()
        row.prop(scene.mixamo, "remove_prefix", toggle=True)
        row.prop(scene.mixamo, "delete_armatures", toggle=True)
        row = box.row()
        box.prop(scene.mixamo, "hip_name")
        row = box.row()
        box.prop(scene.mixamo, "root_name")
        row = box.row()
        box.prop(scene.mixamo, "name_prefix")
        # Button for conversion of single Selected rig
        box = layout.box()
        box.label(text="Animation Files")
        row = box.row()
        row.prop(scene.mixamo, "source_directory")
        # button to start batch conversion
        row = box.row()
        row.scale_y = 2.0
        row.operator("mixamo.importanim")
        status_row = box.row()
        box = layout.box()
        box.label(text="Animation Helpers")
        row = box.row()
        box.label(text="Control Rig:")
        row = box.row()
        row.prop(scene, "mixamo_control_rig")
        row = box.row()
        row.prop(scene.mixamo, "delete_applied_armatures", toggle=True) # todo delete_applied_armatures
        row.prop(scene.mixamo, "push_nla", toggle=True)
        row = box.row()
        # box.prop(scene.mixamo, "mixamo.applyanims") # todo
        row.operator("mixamo.applyanims")
        row = box.row()
        row.scale_y = 2.0
        row.operator("mixamo.addrootnla")
        status_row = box.row()
        # status_row = box.row()

classes = (
    OBJECT_OT_ImportAnimations,
    OBJECT_OT_ApplyAnimations,
    OBJECT_OT_AddRootNLA,
    MIXAMOCONV_VIEW_3D_PT_mixamoroot,
)

def register():
    bpy.utils.register_class(MixamoPropertyGroup)
    bpy.types.Scene.mixamo_control_rig = bpy.props.PointerProperty(
                                            type=bpy.types.Object,
                                            name="",
                                            description="The control rig generated by mixamo, used as target for the animation application function")
    bpy.types.Scene.mixamo = bpy.props.PointerProperty(type=MixamoPropertyGroup)
    for cls in classes:
        bpy.utils.register_class(cls)
    '''
    bpy.utils.register_class(OBJECT_OT_ImportAnimations)
    bpy.utils.register_class(OBJECT_OT_ApplyAnimations)
    bpy.utils.register_class(OBJECT_OT_AddRootNLA)
    bpy.utils.register_class(MixamorootPanel)
    '''

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.utils.unregister_class(MixamoPropertyGroup)    
    '''
    bpy.utils.unregister_class(MixamoPropertyGroup)
    bpy.utils.uregister_class(OBJECT_OT_ImportAnimations)
    bpy.utils.uregister_class(OBJECT_OT_ApplyAnimations)
    bpy.utils.unregister_class(OBJECT_OT_AddRootNLA)
    bpy.utils.unregister_class(MixamorootPanel)
    '''
    del bpy.types.Scene.mixamo_control_rig


if __name__ == "__main__":
    register()