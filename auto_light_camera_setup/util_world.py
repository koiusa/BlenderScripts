"""
World and HDRI utilities for Auto Light Camera Setup.
Handles environment lighting and world shader configuration.
"""

import bpy
import os

def setup_world_environment(props):
    """
    Set up world environment based on props configuration.
    
    Args:
        props: AutoSetupProperties instance
    """
    world = bpy.context.scene.world
    
    if world is None:
        # Create new world
        world = bpy.data.worlds.new("AutoSetup_World")
        bpy.context.scene.world = world
    
    # Enable nodes
    world.use_nodes = True
    
    if props.use_hdri and props.hdri_path and os.path.exists(props.hdri_path):
        setup_hdri_environment(world, props)
    else:
        setup_basic_world(world, props)

def setup_hdri_environment(world: bpy.types.World, props):
    """
    Set up HDRI environment lighting.
    
    Args:
        world: World object
        props: AutoSetupProperties instance
    """
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    
    # Clear existing nodes
    nodes.clear()
    
    # Create nodes
    output_node = nodes.new(type='ShaderNodeOutputWorld')
    output_node.location = (600, 0)
    
    background_node = nodes.new(type='ShaderNodeBackground')
    background_node.location = (300, 0)
    background_node.inputs['Strength'].default_value = props.hdri_strength
    
    # Environment texture node
    env_tex_node = nodes.new(type='ShaderNodeTexEnvironment')
    env_tex_node.location = (0, 0)
    
    # Texture coordinate node
    tex_coord_node = nodes.new(type='ShaderNodeTexCoord')
    tex_coord_node.location = (-300, 0)
    
    # Mapping node for rotation control
    mapping_node = nodes.new(type='ShaderNodeMapping')
    mapping_node.location = (-150, 0)
    
    # Load HDRI image
    try:
        hdri_image = bpy.data.images.load(props.hdri_path)
        env_tex_node.image = hdri_image
    except:
        print(f"Warning: Could not load HDRI from {props.hdri_path}")
        # Fall back to basic world
        setup_basic_world(world, props)
        return
    
    # Connect nodes
    links.new(tex_coord_node.outputs['Generated'], mapping_node.inputs['Vector'])
    links.new(mapping_node.outputs['Vector'], env_tex_node.inputs['Vector'])
    links.new(env_tex_node.outputs['Color'], background_node.inputs['Color'])
    links.new(background_node.outputs['Background'], output_node.inputs['Surface'])

def setup_basic_world(world: bpy.types.World, props):
    """
    Set up basic world with solid color background.
    
    Args:
        world: World object
        props: AutoSetupProperties instance
    """
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    
    # Clear existing nodes
    nodes.clear()
    
    # Create nodes
    output_node = nodes.new(type='ShaderNodeOutputWorld')
    output_node.location = (300, 0)
    
    background_node = nodes.new(type='ShaderNodeBackground')
    background_node.location = (0, 0)
    background_node.inputs['Color'].default_value = (0.05, 0.05, 0.05, 1.0)  # Dark gray
    background_node.inputs['Strength'].default_value = props.world_strength
    
    # Connect nodes
    links.new(background_node.outputs['Background'], output_node.inputs['Surface'])

def setup_render_settings(props):
    """
    Configure render settings for optimal results.
    
    Args:
        props: AutoSetupProperties instance
    """
    scene = bpy.context.scene
    
    # Set render engine to Cycles for better quality
    scene.render.engine = 'CYCLES'
    
    # Configure color management
    if props.enable_filmic:
        scene.view_settings.view_transform = 'Filmic'
        scene.view_settings.look = 'None'
    else:
        scene.view_settings.view_transform = 'Standard'
    
    # Set exposure
    scene.view_settings.exposure = props.exposure
    
    # Configure Cycles settings for quality
    cycles_prefs = scene.cycles
    cycles_prefs.samples = 128  # Good balance of quality and speed
    cycles_prefs.use_denoising = True
    
    # Set resolution to reasonable default if not set
    if scene.render.resolution_x < 100:
        scene.render.resolution_x = 1920
        scene.render.resolution_y = 1080

def reset_world_to_default():
    """
    Reset world to Blender default state.
    """
    world = bpy.context.scene.world
    
    if world and world.use_nodes:
        nodes = world.node_tree.nodes
        links = world.node_tree.links
        
        # Clear all nodes
        nodes.clear()
        
        # Create default background setup
        output_node = nodes.new(type='ShaderNodeOutputWorld')
        background_node = nodes.new(type='ShaderNodeBackground')
        
        # Set default color and strength
        background_node.inputs['Color'].default_value = (0.05, 0.05, 0.05, 1.0)
        background_node.inputs['Strength'].default_value = 1.0
        
        # Connect nodes
        links.new(background_node.outputs['Background'], output_node.inputs['Surface'])

def validate_hdri_path(hdri_path: str) -> bool:
    """
    Validate that HDRI path exists and is a valid image file.
    
    Args:
        hdri_path: Path to HDRI file
        
    Returns:
        True if valid, False otherwise
    """
    if not hdri_path:
        return False
    
    if not os.path.exists(hdri_path):
        return False
    
    # Check file extension
    valid_extensions = {'.hdr', '.exr', '.hdri', '.jpg', '.jpeg', '.png', '.tiff', '.tif'}
    file_ext = os.path.splitext(hdri_path)[1].lower()
    
    return file_ext in valid_extensions

def get_hdri_rotation_for_lighting(hdri_path: str) -> float:
    """
    Get optimal HDRI rotation based on the image (placeholder implementation).
    
    Args:
        hdri_path: Path to HDRI file
        
    Returns:
        Rotation angle in radians
    """
    # This is a placeholder - in a real implementation you might analyze
    # the HDRI to find the best lighting direction
    return 0.0