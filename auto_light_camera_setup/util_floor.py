"""
Floor utilities for Auto Light Camera Setup.
Handles automatic floor plane creation and material setup.
"""

import bpy
import bmesh
from mathutils import Vector
from . import util_collections

def create_or_get_floor(name: str = "AutoSetup_Floor") -> bpy.types.Object:
    """
    Create a new floor plane or get existing one by name.
    
    Args:
        name: Floor object name
        
    Returns:
        Floor object
    """
    floor_obj = bpy.data.objects.get(name)
    
    if floor_obj is None:
        # Create new floor mesh
        mesh = bpy.data.meshes.new(name + "_Mesh")
        floor_obj = bpy.data.objects.new(name, mesh)
        # Link to AutoSetup root collection to avoid context.collection dependency
        root_col, _ = util_collections.ensure_autosetup_collections()
        # ensure_autosetup_collections returns (cams, lights); we only need root existence, so link to scene root too
        try:
            bpy.context.scene.collection.objects.link(floor_obj)
        except RuntimeError:
            pass
    
    return floor_obj

def setup_floor(props, bounds_info: dict) -> bpy.types.Object:
    """
    Set up floor plane beneath target objects.
    
    Args:
        props: AutoSetupProperties instance
        bounds_info: Bounds information from util_bounds
        
    Returns:
        Floor object
    """
    if not props.add_floor:
        return None
    
    floor_obj = create_or_get_floor()
    
    # Calculate floor dimensions and position
    center = bounds_info['center']
    size = bounds_info['size']
    min_coord = bounds_info['min_coord']
    
    # Make floor larger than target bounds
    floor_size = max(size.x, size.y) * 3.0
    floor_z = min_coord.z - 0.01  # Slightly below lowest point
    
    # Create floor mesh
    create_floor_mesh(floor_obj, floor_size, Vector((center.x, center.y, floor_z)))
    
    # Create and assign material
    create_floor_material(floor_obj, props)
    
    return floor_obj

def create_floor_mesh(floor_obj: bpy.types.Object, size: float, location: Vector):
    """
    Create or update floor mesh geometry.
    
    Args:
        floor_obj: Floor object
        size: Size of the floor plane
        location: Center location of the floor
    """
    mesh = floor_obj.data
    # スケールをリセットして累積拡大を防ぐ
    floor_obj.scale = (1, 1, 1)
    
    # Clear existing mesh
    mesh.clear_geometry()
    
    # Create new mesh using bmesh
    bm = bmesh.new()
    
    # Create a plane
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size/2)
    
    # Update mesh
    bm.to_mesh(mesh)
    bm.free()
    
    # Set object location
    floor_obj.location = location
    
    # Update mesh
    mesh.update()

def create_floor_material(floor_obj: bpy.types.Object, props):
    """
    Create and assign material to floor object.
    
    Args:
        floor_obj: Floor object
        props: AutoSetupProperties instance
    """
    material_name = "AutoSetup_FloorMaterial"
    material = bpy.data.materials.get(material_name)
    
    if material is None:
        material = bpy.data.materials.new(material_name)
        material.use_nodes = True
        
        # Clear default nodes
        material.node_tree.nodes.clear()
        
        # Create nodes
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        
        # Output node
        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        output_node.location = (300, 0)
        
        # Principled BSDF
        principled_node = nodes.new(type='ShaderNodeBsdf')
        principled_node.location = (0, 0)
        
        # Set base color
        principled_node.inputs['Base Color'].default_value = (*props.floor_material_color, 1.0)
        
        # Make it slightly rough
        principled_node.inputs['Roughness'].default_value = 0.8
        
        # Connect nodes
        links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])
    
    else:
        # Update existing material color
        nodes = material.node_tree.nodes
        principled_node = None
        for node in nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled_node = node
                break
        
        if principled_node:
            principled_node.inputs['Base Color'].default_value = (*props.floor_material_color, 1.0)
    
    # Assign material to object
    if len(floor_obj.data.materials) == 0:
        floor_obj.data.materials.append(material)
    else:
        floor_obj.data.materials[0] = material

def remove_auto_floor():
    """
    Remove auto-setup floor from the scene.
    """
    floor_obj = bpy.data.objects.get("AutoSetup_Floor")
    if floor_obj:
        bpy.data.objects.remove(floor_obj, do_unlink=True)

def create_infinite_floor(props, bounds_info: dict) -> bpy.types.Object:
    """
    Create an infinite floor using a large plane with appropriate material.
    
    Args:
        props: AutoSetupProperties instance
        bounds_info: Bounds information from util_bounds
        
    Returns:
        Floor object
    """
    if not props.add_floor:
        return None
    
    floor_obj = create_or_get_floor("AutoSetup_InfiniteFloor")
    
    # Calculate position
    center = bounds_info['center']
    min_coord = bounds_info['min_coord']
    floor_z = min_coord.z - 0.01
    
    # Create very large floor
    floor_size = 1000.0  # Large enough to appear infinite
    create_floor_mesh(floor_obj, floor_size, Vector((center.x, center.y, floor_z)))
    
    # Create material with infinite appearance
    create_infinite_floor_material(floor_obj, props)
    
    return floor_obj

def create_infinite_floor_material(floor_obj: bpy.types.Object, props):
    """
    Create material for infinite floor with subtle grid or solid color.
    
    Args:
        floor_obj: Floor object
        props: AutoSetupProperties instance
    """
    material_name = "AutoSetup_InfiniteFloorMaterial"
    material = bpy.data.materials.get(material_name)
    
    if material is None:
        material = bpy.data.materials.new(material_name)
        material.use_nodes = True
        
        # Clear default nodes
        material.node_tree.nodes.clear()
        
        # Create nodes
        nodes = material.node_tree.nodes
        links = material.node_tree.links
        
        # Output node
        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        output_node.location = (600, 0)
        
        # Principled BSDF
        principled_node = nodes.new(type='ShaderNodeBsdf')
        principled_node.location = (300, 0)
        
        # Texture coordinate node
        tex_coord_node = nodes.new(type='ShaderNodeTexCoord')
        tex_coord_node.location = (-300, 0)
        
        # Mapping node
        mapping_node = nodes.new(type='ShaderNodeMapping')
        mapping_node.location = (-100, 0)
        mapping_node.inputs['Scale'].default_value = (10, 10, 1)  # Scale for subtle grid
        
        # Checker texture for subtle floor pattern
        checker_node = nodes.new(type='ShaderNodeTexChecker')
        checker_node.location = (0, 100)
        checker_node.inputs['Scale'].default_value = 20.0
        checker_node.inputs['Color1'].default_value = (*props.floor_material_color, 1.0)
        # Slightly darker for checker pattern
        darker_color = [c * 0.95 for c in props.floor_material_color]
        checker_node.inputs['Color2'].default_value = (*darker_color, 1.0)
        
        # ColorRamp to make the pattern very subtle
        colorramp_node = nodes.new(type='ShaderNodeValToRGB')
        colorramp_node.location = (150, 100)
        colorramp_node.color_ramp.elements[0].color = (*props.floor_material_color, 1.0)
        colorramp_node.color_ramp.elements[1].color = (*props.floor_material_color, 1.0)
        
        # Set material properties
        principled_node.inputs['Roughness'].default_value = 0.9
        principled_node.inputs['Specular'].default_value = 0.1
        
        # Connect nodes
        links.new(tex_coord_node.outputs['Generated'], mapping_node.inputs['Vector'])
        links.new(mapping_node.outputs['Vector'], checker_node.inputs['Vector'])
        links.new(checker_node.outputs['Color'], colorramp_node.inputs['Fac'])
        links.new(colorramp_node.outputs['Color'], principled_node.inputs['Base Color'])
        links.new(principled_node.outputs['BSDF'], output_node.inputs['Surface'])
    
    # Assign material to object
    if len(floor_obj.data.materials) == 0:
        floor_obj.data.materials.append(material)
    else:
        floor_obj.data.materials[0] = material