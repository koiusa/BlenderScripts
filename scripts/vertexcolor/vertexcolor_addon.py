bl_info = {
    "name": "Attach Vertex Color",
    "author": "koiusa",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "View3D > Object > Attach Vertex Color",
    "description": "全コレクションのメッシュに頂点カラーを割り当てる",
    "category": "Object",
}

import bpy

def attachvertexcolor(obj):
    if obj is None or obj.type != "MESH":
        return
    name = obj.data.name
    mesh = obj.data
    if name not in mesh.materials:
        return
    nodes = mesh.materials[name].node_tree.nodes
    links = mesh.materials[name].node_tree.links
    colorattribute = nodes.new(type='ShaderNodeVertexColor')
    shader = nodes.get('Principled BSDF')
    if shader:
        links.new(colorattribute.outputs['Color'], shader.inputs['Base Color'])

def run_vertexcolor():
    if len(bpy.data.collections) > 0:
        for col in bpy.data.collections:
            if len(col.objects) > 0:
                for obj in col.objects:
                    attachvertexcolor(obj)

class OBJECT_OT_attach_vertex_color(bpy.types.Operator):
    bl_idname = "object.attach_vertex_color"
    bl_label = "Attach Vertex Color"
    bl_description = "全コレクションのメッシュに頂点カラーを割り当てる"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        run_vertexcolor()
        self.report({'INFO'}, "頂点カラー割り当て完了")
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(OBJECT_OT_attach_vertex_color.bl_idname)

def register():
    bpy.utils.register_class(OBJECT_OT_attach_vertex_color)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    bpy.types.VIEW3D_MT_object.remove(menu_func)
    bpy.utils.unregister_class(OBJECT_OT_attach_vertex_color)

if __name__ == "__main__":
    register()
