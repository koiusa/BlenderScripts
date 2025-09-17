"""
Camera utilities for Auto Light Camera Setup.
Handles camera positioning, configuration, and multi-shot generation.
"""

import bpy
from mathutils import Vector, Euler
import math
from typing import List, Optional, Dict, Any
from . import util_bounds
from . import util_collections
from . import util_rig
from .debug_utils import debugger, log_object_state
from .constants import (
    CameraSettings, ObjectNames, ShotType, TRACK_TO_CONSTRAINT
)
from .utils import ALCSLogger, safe_execute, get_or_create_object, ensure_scene_update

def create_or_get_camera(name: str = ObjectNames.CAMERA_PREFIX) -> Optional[bpy.types.Object]:
    """
    Create a new camera or get existing one by name.
    
    Args:
        name: Camera object name
        
    Returns:
        Camera object or None on error
    """
    def _create_camera():
        camera_data = bpy.data.cameras.new(name + "_Data")
        camera = bpy.data.objects.new(name, camera_data)
        # Link to AutoSetup camera collection
        cams_col, _ = util_collections.ensure_autosetup_collections()
        util_collections.link_object_to_collection(camera, cams_col)
        return camera
    
    camera = get_or_create_object(name, _create_camera, 'CAMERA')
    
    if camera:
        # Ensure existing camera is organized under AutoSetup_Cameras
        cams_col, _ = util_collections.ensure_autosetup_collections()
        util_collections.link_object_to_collection(camera, cams_col)
    
    return camera

def position_camera_auto(props, bounds_info: dict, shot_type: str = "FRONT") -> bpy.types.Object:
    """
    Automatically position camera based on target bounds and shot type.
    """
    debugger.info(f"Starting position_camera_auto for {shot_type}")
    
    camera_name = f"AutoSetup_Camera_{shot_type}"
    camera = create_or_get_camera(camera_name)
    
    log_object_state(camera, "position_camera_auto", "initial")
    
    center = bounds_info['center']
    max_dimension = bounds_info['max_dimension']
    distance = max_dimension * props.camera_distance_factor
    
    # Check if camera is already rigged
    already_rigged = util_rig.is_camera_rigged(camera)
    debugger.info(f"Camera {camera.name} rigged status: {already_rigged}")

    # Shot-specific positioning（リグ済カメラは位置決めを完全スキップ）
    if not already_rigged:
        def calc_pos_and_rot(shot: str):
            if shot == "FRONT":
                return center + Vector((0, -distance, 0)), Euler((math.radians(90), 0, 0), 'XYZ')
            if shot == "3Q_L":
                ang = math.radians(45)
                return center + Vector((-distance * math.sin(ang), -distance * math.cos(ang), distance * 0.3)), Euler((math.radians(75), 0, math.radians(-45)), 'XYZ')
            if shot == "3Q_R":
                ang = math.radians(45)
                return center + Vector((distance * math.sin(ang), -distance * math.cos(ang), distance * 0.3)), Euler((math.radians(75), 0, math.radians(45)), 'XYZ')
            if shot == "TOP":
                return center + Vector((0, 0, distance)), Euler((0, 0, 0), 'XYZ')
            if shot == "LOW":
                return center + Vector((0, -distance * 1.2, -max_dimension * 0.3)), Euler((math.radians(100), 0, 0), 'XYZ')
            # default fallback (front-like)
            return center + Vector((0, -distance, 0)), Euler((math.radians(90), 0, 0), 'XYZ')

        target_pos, target_rot = calc_pos_and_rot(shot_type)
        util_rig.safe_set_world_position(camera, target_pos, f"camera_position_{shot_type}")
        camera.rotation_euler = target_rot
    else:
        debugger.info(f"Skipping position for rigged camera {camera.name}")
    
    # Point camera at target center (skip for rigged cameras)
    if not already_rigged:
        point_camera_at_target(camera, center)
    
    # Configure camera settings
    configure_camera(camera, props)
    
    return camera

def point_camera_at_target(camera: bpy.types.Object, target_location: Vector):
    """
    Point camera at target location using track-to constraint.
    """
    # If camera is rigged, use rig's focus system
    if util_rig.is_camera_rigged(camera):
        util_rig.setup_camera_for_rig(camera, bpy.data.objects.get("AutoSetup_Rig_Focus"))
        return
    
    # Non-rigged path: Create per-camera track target and Track To
    track_target_name = f"{camera.name}_TrackTarget"
    track_target = bpy.data.objects.get(track_target_name)
    
    if track_target is None:
        track_target = bpy.data.objects.new(track_target_name, None)
        cams_col, _ = util_collections.ensure_autosetup_collections()
        util_collections.link_object_to_collection(track_target, cams_col)
    
    track_target.matrix_world.translation = target_location
    
    # Add/update track-to constraint
    constraint = None
    for const in camera.constraints:
        if const.type == 'TRACK_TO' and const.name.startswith("AutoSetup"):
            constraint = const
            break
    
    if constraint is None:
        constraint = camera.constraints.new(type='TRACK_TO')
        constraint.name = TRACK_TO_CONSTRAINT
    
    constraint.target = track_target
    constraint.track_axis = 'TRACK_NEGATIVE_Z'
    constraint.up_axis = 'UP_Y'
    
    # Set DOF focus
    util_rig.safe_execute(lambda: setattr(camera.data.dof, 'focus_object', track_target) 
                         if hasattr(camera.data, 'dof') and hasattr(camera.data.dof, 'focus_object') else None)
    util_rig.safe_execute(lambda: setattr(camera.data.dof, 'focus_subtarget', "") 
                         if hasattr(camera.data, 'dof') and hasattr(camera.data.dof, 'focus_subtarget') else None)
    
    # Set initial orientation
    util_rig.safe_execute(lambda: _set_camera_orientation(camera, target_location))


def _set_camera_orientation(camera: bpy.types.Object, target_location: Vector):
    """Set camera orientation to face target."""
    cam_world = camera.matrix_world.translation
    direction = (target_location - cam_world)
    if direction.length > 0:
        quat = direction.to_track_quat('-Z', 'Y')
        camera.rotation_euler = quat.to_euler('XYZ')

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

        # Prefer focus_object if available; otherwise use Track To target; if rigged, use rig focus
        focus_distance = None
        target_obj = util_rig.safe_execute(lambda: camera_data.dof.focus_object 
                                          if hasattr(camera_data.dof, 'focus_object') and camera_data.dof.focus_object else None)
        
        if target_obj is None:
            # Try to get from Track To constraint
            for const in camera.constraints:
                if const.type == 'TRACK_TO' and getattr(const, 'target', None) is not None:
                    target_obj = const.target
                    break
            # If rigged, fall back to rig focus
            if target_obj is None and util_rig.is_camera_rigged(camera):
                target_obj = bpy.data.objects.get("AutoSetup_Rig_Focus")
                util_rig.safe_execute(lambda: setattr(camera_data.dof, 'focus_object', target_obj) 
                                     if hasattr(camera_data.dof, 'focus_object') and target_obj else None)
        
        if target_obj is not None:
            cam_pos = camera.matrix_world.translation
            tgt_pos = target_obj.matrix_world.translation
            focus_distance = (tgt_pos - cam_pos).length

        # Fallback: keep current distance if target not found
        if focus_distance is None or focus_distance <= 0:
            focus_distance = camera_data.dof.focus_distance if hasattr(camera_data.dof, 'focus_distance') else 0.0

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