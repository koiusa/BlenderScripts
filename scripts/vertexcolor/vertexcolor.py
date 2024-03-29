import bpy

def attachvertexcolor(obj):
    if obj is None or obj.type != "MESH":
        return
    name = obj.data.name
    mesh = obj.data   
    nodes = mesh.materials[name].node_tree.nodes
    links = mesh.materials[name].node_tree.links

    colorattribute = nodes.new(type='ShaderNodeVertexColor')
    shader=nodes.get('Principled BSDF')
    links.new(colorattribute.outputs['Color'], shader.inputs['Base Color'])

def main():
    if len(bpy.data.collections) > 0:
        print('COLLECTIONS')
        for col in bpy.data.collections:
            if len(col.objects) > 0:
                for obj in col.objects:
                    attachvertexcolor(obj)
    else:
        print('NO_COLLECTIONS')

if __name__ == "__main__":
    main()
