"""
Camera utilities for Auto Light Camera Setup.
Handles camera positioning, configuration, and multi-shot generation.
"""

import bpy
import bmesh
from mathutils import Vector, Euler
import math
from . import util_bounds

def create_or_get_camera(name: str = "AutoSetup_Camera") -> bpy.types.Object:
    """
    Create a new camera or get existing one by name.
    
    Args:
        name: Camera object name
        
    Returns:
        Camera object
    """
    camera = bpy.data.objects.get(name)
    
    if camera is None:
        # Create new camera
        camera_data = bpy.data.cameras.new(name + "_Data")
        camera = bpy.data.objects.new(name, camera_data)
        bpy.context.collection.objects.link(camera)
    
    return camera

def position_camera_auto(props, bounds_info: dict, shot_type: str = "FRONT") -> bpy.types.Object:
    """
    Automatically position camera based on target bounds and shot type.
    
    Args:
        props: AutoSetupProperties instance
        bounds_info: Bounds information from util_bounds
        shot_type: Type of shot (FRONT, 3Q_L, 3Q_R, TOP, LOW)
        
    Returns:
        Positioned camera object
    """
    camera_name = f"AutoSetup_Camera_{shot_type}"
    camera = create_or_get_camera(camera_name)
    
    center = bounds_info['center']
    max_dimension = bounds_info['max_dimension']
    distance = max_dimension * props.camera_distance_factor
    
    # Shot-specific positioning
    if shot_type == "FRONT":
        # Front view
        camera.location = center + Vector((0, -distance, 0))
        camera.rotation_euler = Euler((math.radians(90), 0, 0), 'XYZ')
        
    elif shot_type == "3Q_L":
        # Three-quarter left view
        angle = math.radians(45)
        camera.location = center + Vector((
            -distance * math.sin(angle),
            -distance * math.cos(angle),
            distance * 0.3
        ))
        camera.rotation_euler = Euler((math.radians(75), 0, math.radians(-45)), 'XYZ')
        
    elif shot_type == "3Q_R":
        # Three-quarter right view
        angle = math.radians(45)
        camera.location = center + Vector((
            distance * math.sin(angle),
            -distance * math.cos(angle),
            distance * 0.3
        ))
        camera.rotation_euler = Euler((math.radians(75), 0, math.radians(45)), 'XYZ')
        
    elif shot_type == "TOP":
        # Top view
        camera.location = center + Vector((0, 0, distance))
        camera.rotation_euler = Euler((0, 0, 0), 'XYZ')
        
    elif shot_type == "LOW":
        # Low angle view
        camera.location = center + Vector((0, -distance * 1.2, -max_dimension * 0.3))
        camera.rotation_euler = Euler((math.radians(100), 0, 0), 'XYZ')
    
    # Point camera at target center
    point_camera_at_target(camera, center)
    
    # Configure camera settings
    configure_camera(camera, props)
    
    return camera

def point_camera_at_target(camera: bpy.types.Object, target_location: Vector):
    """
    Point camera at target location using track-to constraint.
    
    Args:
        camera: Camera object
        target_location: Location to point at
    """
    # Create empty at target location for tracking
    track_target_name = f"{camera.name}_TrackTarget"
    track_target = bpy.data.objects.get(track_target_name)
    
    if track_target is None:
        track_target = bpy.data.objects.new(track_target_name, None)
        bpy.context.collection.objects.link(track_target)
    
    track_target.location = target_location
    
    # Add track-to constraint
    constraint = None
    for const in camera.constraints:
        if const.type == 'TRACK_TO' and const.name.startswith("AutoSetup"):
            constraint = const
            break
    
    if constraint is None:
        constraint = camera.constraints.new(type='TRACK_TO')
        constraint.name = "AutoSetup_TrackTo"
    
    constraint.target = track_target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'

def configure_camera(camera: bpy.types.Object, props):
    """
    Configure camera settings based on properties.
    
    Args:
        camera: Camera object
        props: AutoSetupProperties instance
    """
    camera_data = camera.data
    
    # Set lens if specified
    if props.camera_lens > 0:
        camera_data.lens = props.camera_lens
    
    # Configure depth of field
    if props.enable_dof:
        camera_data.dof.use_dof = True
        camera_data.dof.aperture_fstop = props.dof_fstop
        
        # Set focus distance to camera location distance from origin
        focus_distance = camera.location.length
        camera_data.dof.focus_distance = focus_distance
    else:
        camera_data.dof.use_dof = False

def set_active_camera(camera: bpy.types.Object):
    """
    Set camera as the active scene camera.
    
    Args:
        camera: Camera object to set as active
    """
    bpy.context.scene.camera = camera

def generate_multi_shots(props, bounds_info: dict) -> list:
    """
    Generate multiple camera shots based on configuration.
    
    Args:
        props: AutoSetupProperties instance
        bounds_info: Bounds information from util_bounds
        
    Returns:
        List of created camera objects
    """
    cameras = []
    
    if props.shot_types == 'ALL':
        shot_types = ['FRONT', '3Q_L', '3Q_R', 'TOP', 'LOW']
    elif props.shot_types == 'FRONT':
        shot_types = ['FRONT']
    elif props.shot_types == '3Q':
        shot_types = ['3Q_L', '3Q_R']
    else:
        # Custom - for now default to all
        shot_types = ['FRONT', '3Q_L', '3Q_R', 'TOP', 'LOW']
    
    for shot_type in shot_types:
        camera = position_camera_auto(props, bounds_info, shot_type)
        cameras.append(camera)
    
    # Set first camera as active
    if cameras:
        set_active_camera(cameras[0])
    
    return cameras

def render_camera_shot(camera: bpy.types.Object, output_path: str):
    """
    Render a single camera shot.
    
    Args:
        camera: Camera to render from
        output_path: Output file path
    """
    # Set as active camera
    set_active_camera(camera)
    
    # Set output path
    bpy.context.scene.render.filepath = output_path
    
    # Render
    bpy.ops.render.render(write_still=True)