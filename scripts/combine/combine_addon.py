bl_info = {
    "name": "Combine Collections",
    "author": "koiusa",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Object > Combine Collections",
    "description": "カーブをメッシュ化し、モディファイア適用、コレクション結合を一括実行",
    "category": "Object",
}

import bpy
import sys
import os

# 既存のcombine.pyの主要処理を関数化

def run_combine():
    def get_script_dirpath():
        script_filename = os.path.basename(__file__)
        try:
            script_filepath = bpy.data.texts[script_filename].filepath
        except Exception:
            return ""
        if script_filepath == "":
            return ""
        script_dirpath = os.path.dirname(script_filepath)
        return script_dirpath

    sys.path.append(get_script_dirpath())
    import sub.joincollections as joincollections
    import sub.applymodifier as applymodifier
    import sub.curvetomesh as curvetomesh
    import sub.common as common

    bpy.ops.object.select_all(action='DESELECT')
    selected_collection = bpy.context.view_layer.active_layer_collection.collection
    objects_in_collection = common.get_objects_in_collection(selected_collection)
    for obj in objects_in_collection:
        curvetomesh.curve_to_mesh(obj)
    for obj in objects_in_collection:
        applymodifier.apply_modifier(obj)
    collection_names = common.get_selected_collection_names(selected_collection)
    for name in collection_names:
        joincollections.join_collections(name)

class OBJECT_OT_combine_collections(bpy.types.Operator):
    bl_idname = "object.combine_collections"
    bl_label = "Combine Collections"
    bl_description = "カーブをメッシュ化し、モディファイア適用、コレクション結合を一括実行"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        run_combine()
        self.report({'INFO'}, "Combine Collections 完了")
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_combine_collections.bl_idname)

def register():
    bpy.utils.register_class(OBJECT_OT_combine_collections)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.utils.unregister_class(OBJECT_OT_combine_collections)

if __name__ == "__main__":
    register()
