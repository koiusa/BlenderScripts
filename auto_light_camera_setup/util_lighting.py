"""
Lighting utilities for Auto Light Camera Setup.
Handles three-point lighting setup with automatic positioning.
"""

import bpy
from mathutils import Vector
import math
from . import util_collections
from . import util_rig
from .debug_utils import debugger, log_object_state

def create_or_get_light(name: str, light_type: str = 'AREA') -> bpy.types.Object:
    """Create a new light or get existing one by name."""
    light = bpy.data.objects.get(name)
    
    if light is None:
        # Create new light
        light_data = bpy.data.lights.new(name + "_Data", light_type)
        light = bpy.data.objects.new(name, light_data)
        # Link to AutoSetup light collection
        _, lights_col = util_collections.ensure_autosetup_collections()
        util_collections.link_object_to_collection(light, lights_col)
    elif light.data.type != light_type:
        # Update existing light type if different
        old_data = light.data
        light_data = bpy.data.lights.new(name + "_Data", light_type)
        light.data = light_data
        # Remove old data if no other users
        if old_data.users == 0:
            bpy.data.lights.remove(old_data)
    
    return light

def setup_three_point_lighting(props, bounds_info: dict):
    """
    Set up three-point lighting system (key, fill, rim).
    """
    debugger.info("Starting setup_three_point_lighting")
    
    center = bounds_info['center']
    max_dimension = bounds_info['max_dimension']
    
    # Calculate lighting distance
    light_distance = max_dimension * 2.0
    light_height = max_dimension * 1.5
    
    # Light rig detection: if light is rigged, skip position reset
    def _is_rigged(obj: bpy.types.Object) -> bool:
        return util_rig.is_light_rigged(obj)

    # Key Light (main light)
    key_light = create_or_get_light("AutoSetup_KeyLight", 'AREA')
    log_object_state(key_light, "setup_three_point_lighting", "key_light_initial")
    if not _is_rigged(key_light):
        target_pos = center + Vector((-light_distance * 0.7, -light_distance, light_height))
        util_rig.safe_set_world_position(key_light, target_pos, "key_light_position")
        point_light_at_target(key_light, center)
    else:
        debugger.info(f"Skipping position for rigged light {key_light.name}")
    key_light.data.energy = props.light_key_intensity
    key_light.data.size = max_dimension * 0.5
    
    # Fill Light (softer, opposite side)
    fill_light = create_or_get_light("AutoSetup_FillLight", 'AREA')
    log_object_state(fill_light, "setup_three_point_lighting", "fill_light_initial")
    if not _is_rigged(fill_light):
        target_pos = center + Vector((light_distance * 0.5, -light_distance * 0.3, light_height * 0.8))
        util_rig.safe_set_world_position(fill_light, target_pos, "fill_light_position")
        point_light_at_target(fill_light, center)
    else:
        debugger.info(f"Skipping position for rigged light {fill_light.name}")
    fill_light.data.energy = props.light_fill_intensity
    fill_light.data.size = max_dimension * 0.8
    
    # Rim Light (back light for edge definition)
    rim_side = determine_rim_light_side(bounds_info)
    rim_x = light_distance * rim_side
    rim_light = create_or_get_light("AutoSetup_RimLight", 'AREA')
    log_object_state(rim_light, "setup_three_point_lighting", "rim_light_initial")
    if not _is_rigged(rim_light):
        target_pos = center + Vector((rim_x, light_distance * 0.8, light_height * 1.2))
        util_rig.safe_set_world_position(rim_light, target_pos, "rim_light_position")
        point_light_at_target(rim_light, center)
    else:
        debugger.info(f"Skipping position for rigged light {rim_light.name}")
    rim_light.data.energy = props.light_rim_intensity
    rim_light.data.size = max_dimension * 0.3
    
    debugger.info("Completed setup_three_point_lighting")

def point_light_at_target(light: bpy.types.Object, target_location: Vector):
    """
    Point light at target location using track-to constraint.
    """
    # If light is under a light rig, use rig's tracking system
    if util_rig.is_light_rigged(light):
        return
    
    # Create empty at target location for tracking
    track_target_name = f"{light.name}_TrackTarget"
    track_target = bpy.data.objects.get(track_target_name)
    
    if track_target is None:
        track_target = bpy.data.objects.new(track_target_name, None)
        # Put track target into lights collection for grouping (avoid context.collection)
        _, lights_col = util_collections.ensure_autosetup_collections()
        util_collections.link_object_to_collection(track_target, lights_col)
    
    # Place target at world-space center (avoid accumulating parent offsets)
    track_target.matrix_world.translation = target_location
    
    # Add track-to constraint
    constraint = None
    for const in light.constraints:
        if const.type == 'TRACK_TO' and const.name.startswith("AutoSetup"):
            constraint = const
            break
    
    if constraint is None:
        constraint = light.constraints.new(type='TRACK_TO')
        constraint.name = "AutoSetup_TrackTo"
    
    constraint.target = track_target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'

def determine_rim_light_side(bounds_info: dict) -> float:
    """
    Automatically determine which side to place rim light based on object bounds.
    
    Args:
        bounds_info: Bounds information from util_bounds
        
    Returns:
        Side multiplier (-1 for left, 1 for right)
    """
    # Simple heuristic: use the side with more space
    center = bounds_info['center']
    min_coord = bounds_info['min_coord']
    max_coord = bounds_info['max_coord']
    
    left_space = abs(center.x - min_coord.x)
    right_space = abs(max_coord.x - center.x)
    
    # Place rim light on the side with more space
    return 1.0 if right_space > left_space else -1.0

def cleanup_auto_lights():
    """
    Remove all auto-setup lights from the scene.
    """
    lights_to_remove = []
    for obj in bpy.context.scene.objects:
        if obj.type == 'LIGHT' and obj.name.startswith("AutoSetup_"):
            lights_to_remove.append(obj)
    
    for light in lights_to_remove:
        bpy.data.objects.remove(light, do_unlink=True)

def adjust_light_intensity(light_name: str, intensity: float):
    """
    Adjust the intensity of a specific light.
    
    Args:
        light_name: Name of the light object
        intensity: New intensity value
    """
    light = bpy.data.objects.get(light_name)
    if light and light.type == 'LIGHT':
        light.data.energy = intensity

def create_studio_lighting(props, bounds_info: dict):
    """
    Create a more complex studio lighting setup.
    
    Args:
        props: AutoSetupProperties instance
        bounds_info: Bounds information from util_bounds
    """
    center = bounds_info['center']
    max_dimension = bounds_info['max_dimension']
    
    # Main key light (large softbox equivalent)
    key_light = create_or_get_light("AutoSetup_StudioKey", 'AREA')
    key_light.location = center + Vector((-max_dimension * 1.5, -max_dimension * 2.0, max_dimension * 1.8))
    key_light.data.energy = props.light_key_intensity * 1.5
    key_light.data.size = max_dimension
    key_light.data.shape = 'RECTANGLE'
    key_light.data.size_y = max_dimension * 0.7
    point_light_at_target(key_light, center)
    
    # Fill light (opposite side, softer)
    fill_light = create_or_get_light("AutoSetup_StudioFill", 'AREA')
    fill_light.location = center + Vector((max_dimension * 1.2, -max_dimension * 1.5, max_dimension * 1.2))
    fill_light.data.energy = props.light_fill_intensity * 0.8
    fill_light.data.size = max_dimension * 1.2
    point_light_at_target(fill_light, center)
    
    # Rim light (back)
    rim_light = create_or_get_light("AutoSetup_StudioRim", 'SPOT')
    rim_light.location = center + Vector((0, max_dimension * 1.5, max_dimension * 2.0))
    rim_light.data.energy = props.light_rim_intensity * 2.0
    rim_light.data.spot_size = math.radians(45)
    rim_light.data.spot_blend = 0.3
    point_light_at_target(rim_light, center)