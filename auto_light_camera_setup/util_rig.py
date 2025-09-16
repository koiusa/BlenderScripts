"""
Rig/Locator utilities for Auto Light Camera Setup.
Creates a common locator (Empty) and parents auto-generated cameras/lights to it
so the whole setup can be manipulated together.
"""

import bpy
from mathutils import Vector
from . import util_collections
from .debug_utils import debugger, log_object_state, log_rig_state, log_coordinate_change


RIG_NAMES = {
    'curve': "AutoSetup_Rig_Curve",
    'control': "AutoSetup_Rig_Control",
    'cam_rig': "AutoSetup_Camera_Rig",
    'focus': "AutoSetup_Rig_Focus",
}


def is_camera_rigged(camera: bpy.types.Object) -> bool:
    """Check if camera is under AutoSetup rig control."""
    cam_rig = bpy.data.objects.get(RIG_NAMES['cam_rig'])
    return cam_rig is not None and camera.parent == cam_rig


def is_light_rigged(light: bpy.types.Object) -> bool:
    """Check if light is under AutoSetup light rig control."""
    return (light.parent is not None and 
            light.parent.name.startswith("AutoSetup_LightRig_"))


def rig_exists() -> bool:
    """Check if any AutoSetup rig components exist."""
    rig_objects = [bpy.data.objects.get(name) for name in RIG_NAMES.values()]
    light_rigs = [o for o in bpy.data.objects if o.name.startswith("AutoSetup_LightRig_")]
    return any(rig_objects) or len(light_rigs) > 0


def get_rig_objects() -> dict:
    """Get all rig objects in a structured dict."""
    rig_objects = {name: bpy.data.objects.get(obj_name) for name, obj_name in RIG_NAMES.items()}
    rig_objects['light_rigs'] = [o for o in bpy.data.objects if o.name.startswith("AutoSetup_LightRig_")]
    return rig_objects


def safe_execute(func, *args, **kwargs):
    """Execute function with error handling."""
    try:
        return func(*args, **kwargs)
    except Exception:
        return None


def normalize_object_transform(obj: bpy.types.Object):
    """Reset object's local position and rotation to zero."""
    safe_execute(setattr, obj, 'location', (0.0, 0.0, 0.0))
    safe_execute(setattr, obj, 'rotation_euler', (0.0, 0.0, 0.0))


def setup_camera_for_rig(camera: bpy.types.Object, focus_obj: bpy.types.Object):
    """Configure camera for rig control: remove individual tracking, set DOF focus."""
    _remove_autosetup_trackto_and_target(camera)
    normalize_object_transform(camera)
    # Set DOF focus to rig focus
    safe_execute(lambda: setattr(camera.data.dof, 'focus_object', focus_obj) 
                 if hasattr(camera.data, 'dof') and hasattr(camera.data.dof, 'focus_object') else None)
    safe_execute(lambda: setattr(camera.data.dof, 'focus_subtarget', "") 
                 if hasattr(camera.data, 'dof') and hasattr(camera.data.dof, 'focus_subtarget') else None)


def setup_light_for_rig(light: bpy.types.Object):
    """Configure light for rig control: remove individual tracking, reset transform."""
    _remove_autosetup_trackto_and_target(light)
    normalize_object_transform(light)


def _remove_autosetup_trackto_and_target(obj: bpy.types.Object):
    """Remove AutoSetup Track To constraints from object and delete its *_TrackTarget empty if present."""
    safe_execute(lambda: [obj.constraints.remove(c) for c in list(obj.constraints) 
                         if c.type == 'TRACK_TO' and c.name.startswith("AutoSetup")])
    # Delete per-object track target empty
    target_name = f"{obj.name}_TrackTarget"
    tgt = bpy.data.objects.get(target_name)
    if tgt is not None:
        safe_execute(lambda: bpy.data.objects.remove(tgt, do_unlink=True))


def _find_autosetup_camera() -> bpy.types.Object:
    """Find AutoSetup camera, preferring active camera."""
    cam = bpy.context.scene.camera
    if cam and cam.type == 'CAMERA' and cam.name.startswith("AutoSetup_Camera"):
        return cam
    
    for obj in bpy.context.scene.objects:
        if obj.type == 'CAMERA' and obj.name.startswith("AutoSetup_Camera"):
            return obj
    return None


def create_or_get_locator(name: str = "AutoSetup_Locator") -> bpy.types.Object:
    """
    Create or get the common locator (Empty) used to group cameras/lights.
    """
    locator = bpy.data.objects.get(name)
    if locator is None:
        locator = bpy.data.objects.new(name, None)
        locator.empty_display_type = 'PLAIN_AXES'
        # Link safely (avoid context.collection)
        try:
            bpy.context.scene.collection.objects.link(locator)
        except RuntimeError:
            pass
        # Also ensure it's part of the AutoSetup root collection for organization
        try:
            root_col = util_collections.get_or_create_collection("AutoSetup")
            util_collections.link_object_to_collection(locator, root_col)
        except Exception:
            pass
    return locator


def _reposition_locator_without_affecting_children(locator: bpy.types.Object, new_center: Vector):
    """Move locator to new_center while preserving children's world transforms.

    This ensures we can keep the locator aligned to the current target center
    on re-runs without dragging cameras/lights/rig objects and causing drift.
    """
    if locator is None or new_center is None:
        return
    try:
        old_center = locator.matrix_world.translation.copy()
    except Exception:
        old_center = None

    # Cache children's world matrices
    children = list(locator.children)
    child_world = {c.name: c.matrix_world.copy() for c in children}

    # Reposition locator (log inside safe_set_world_position)
    safe_set_world_position(locator, new_center, "locator_reposition")

    # Restore children world matrices to cancel parent's move
    for c in children:
        try:
            c.matrix_world = child_world[c.name]
        except Exception:
            pass

    if old_center is not None:
        delta = new_center - old_center
        debugger.info("Repositioned locator without affecting children", {
            'old_center': f"({old_center.x:.3f}, {old_center.y:.3f}, {old_center.z:.3f})",
            'new_center': f"({new_center.x:.3f}, {new_center.y:.3f}, {new_center.z:.3f})",
            'delta_magnitude': f"{delta.length:.6f}"
        })

def safe_set_world_position(obj: bpy.types.Object, new_position: Vector, operation: str = "unknown"):
    """Safely set object world position with debug logging."""
    if obj is None:
        debugger.warning(f"Attempted to set position on null object", {'operation': operation})
        return
    
    old_position = obj.matrix_world.translation.copy()
    obj.matrix_world.translation = new_position
    log_coordinate_change(obj, operation, old_position, new_position)


def safe_set_local_position(obj: bpy.types.Object, new_position: tuple, operation: str = "unknown"):
    """Safely set object local position with debug logging."""
    if obj is None:
        debugger.warning(f"Attempted to set local position on null object", {'operation': operation})
        return
    
    old_world = obj.matrix_world.translation.copy()
    obj.location = new_position
    new_world = obj.matrix_world.translation.copy()
    log_coordinate_change(obj, f"{operation}_local", old_world, new_world)


def _parent_keep_world_transform(obj: bpy.types.Object, parent: bpy.types.Object):
    """Parent obj to parent while keeping the world transform unchanged."""
    if obj.parent == parent:
        return
    
    old_world = obj.matrix_world.translation.copy()
    world = obj.matrix_world.copy()
    old_parent_name = obj.parent.name if obj.parent else 'None'
    obj.parent = parent
    obj.matrix_world = world
    new_world = obj.matrix_world.translation.copy()
    
    log_coordinate_change(obj, "parent_keep_world_transform", old_world, new_world)
    debugger.info(f"Parented {obj.name} to {parent.name}", {
        'old_parent': old_parent_name,
        'new_parent': parent.name
    })


def parent_autosetup_objects_to_locator(bounds_info: dict | None = None,
                                        include_track_targets: bool = True,
                                        locator_name: str = "AutoSetup_Locator") -> bpy.types.Object:
    """Parent AutoSetup objects to locator with rig-aware logic."""
    debugger.info("Starting parent_autosetup_objects_to_locator")
    log_rig_state("parent_autosetup_objects_to_locator", "start")
    
    locator = create_or_get_locator(locator_name)
    
    # Keep locator aligned to bounds center on every run, without dragging children
    if bounds_info and 'center' in bounds_info and isinstance(bounds_info['center'], Vector):
        _reposition_locator_without_affecting_children(locator, bounds_info['center'])
    
    if rig_exists():
        _parent_rig_to_locator(locator, bounds_info, include_track_targets)
    else:
        _parent_objects_to_locator(locator, include_track_targets)
    
    return locator


def _parent_rig_to_locator(locator: bpy.types.Object, bounds_info: dict | None, include_track_targets: bool):
    """Parent rig components to locator and re-center preserving user edits."""
    rig_objs = get_rig_objects()
    
    # Clean up orphaned track targets from rigged cameras/lights
    _cleanup_orphaned_track_targets()
    
    # Parent rig components
    for obj in [rig_objs['curve'], rig_objs['control'], rig_objs['cam_rig'], rig_objs['focus']]:
        if obj is not None:
            _parent_keep_world_transform(obj, locator)
    
    for light_rig in rig_objs['light_rigs']:
        _parent_keep_world_transform(light_rig, locator)
    
    # Parent orphaned track targets
    if include_track_targets:
        for obj in bpy.context.scene.objects:
            if (obj.type == 'EMPTY' and obj.name.startswith("AutoSetup_") and 
                obj.name.endswith("_TrackTarget") and obj.parent is None):
                _parent_keep_world_transform(obj, locator)
    
    # Re-center rig preserving relative positions
    if bounds_info and 'center' in bounds_info and rig_objs['focus'] is not None:
        _recenter_rig_preserving_layout(rig_objs, bounds_info['center'])


def _parent_objects_to_locator(locator: bpy.types.Object, include_track_targets: bool):
    """Parent cameras/lights directly to locator (no rig mode)."""
    to_parent = []
    for obj in bpy.context.scene.objects:
        if obj.type == 'CAMERA' and obj.name.startswith("AutoSetup_Camera"):
            to_parent.append(obj)
        elif obj.type == 'LIGHT' and obj.name.startswith("AutoSetup_"):
            to_parent.append(obj)
        elif (include_track_targets and obj.type == 'EMPTY' and 
              obj.name.startswith("AutoSetup_") and obj.name.endswith("_TrackTarget")):
            to_parent.append(obj)
    
    for obj in to_parent:
        _parent_keep_world_transform(obj, locator)


def _cleanup_orphaned_track_targets():
    """Remove TrackTarget empties for cameras/lights that are now rigged."""
    targets_to_remove = []
    
    for obj in bpy.context.scene.objects:
        if obj.type == 'EMPTY' and obj.name.endswith('_TrackTarget'):
            # Find the associated camera/light
            owner_name = obj.name.replace('_TrackTarget', '')
            owner = bpy.data.objects.get(owner_name)
            
            if owner is not None:
                # If owner is rigged, remove its track target
                if ((owner.type == 'CAMERA' and is_camera_rigged(owner)) or
                    (owner.type == 'LIGHT' and is_light_rigged(owner))):
                    targets_to_remove.append(obj)
            else:
                # Owner doesn't exist, remove orphaned target
                targets_to_remove.append(obj)
    
    for target in targets_to_remove:
        safe_execute(lambda t=target: bpy.data.objects.remove(t, do_unlink=True))


def _recenter_rig_preserving_layout(rig_objs: dict, new_center: Vector):
    """Move focus to new center and translate other rig parts by same delta."""
    focus = rig_objs['focus']
    if focus is None:
        debugger.warning("Cannot recenter rig: focus object is None")
        return
    
    old_focus = safe_execute(lambda: focus.matrix_world.translation.copy())
    if old_focus is None:
        debugger.warning("Cannot get old focus position")
        return
    
    # Only recenter if the distance is significant (prevent micro-adjustments from accumulating)
    delta = new_center - old_focus
    debugger.info(f"Rig recenter delta: {delta.length:.6f}", {
        'old_focus': f"({old_focus.x:.3f}, {old_focus.y:.3f}, {old_focus.z:.3f})",
        'new_center': f"({new_center.x:.3f}, {new_center.y:.3f}, {new_center.z:.3f})",
        'delta_magnitude': f"{delta.length:.6f}"
    })
    
    if delta.length < 0.01:  # 1cm threshold
        debugger.info("Skipping rig recenter: delta below threshold")
        return
    
    debugger.info("Executing rig recenter")
    # Move focus to new center
    safe_set_world_position(focus, new_center, "rig_recenter_focus")
    
    # Calculate delta and apply to other rig components
    delta = new_center - old_focus
    rig_components = [rig_objs['curve'], rig_objs['control'], rig_objs['cam_rig']] + rig_objs['light_rigs']
    
    for obj in rig_components:
        if obj is not None:
            safe_execute(lambda o=obj: setattr(o.matrix_world, 'translation', o.matrix_world.translation + delta))


def _add_driver(id_data, data_path: str, expression: str, vars: list[tuple[str, bpy.types.ID, str]]):
    """Add a simple driver to id_data at data_path with variables.

    vars: list of tuples (name, id, data_path)
    """
    try:
        fcurve = id_data.driver_add(data_path)
        drv = fcurve.driver
        drv.type = 'SCRIPTED'
        drv.expression = expression
        # Clear existing vars
        while drv.variables:
            drv.variables.remove(drv.variables[0])
        for name, target_id, target_path in vars:
            v = drv.variables.new()
            v.name = name
            t = v.targets[0]
            t.id = target_id
            t.data_path = target_path
        return fcurve
    except Exception:
        return None


def get_control_objects():
    curve = bpy.data.objects.get(RIG_NAMES['curve'])
    control = bpy.data.objects.get(RIG_NAMES['control'])
    cam_rig = bpy.data.objects.get(RIG_NAMES['cam_rig'])
    focus = bpy.data.objects.get(RIG_NAMES['focus'])
    return curve, control, cam_rig, focus


def delete_control_rig():
    """Delete spline-based control rig objects (curve, control, cam rig, focus)."""
    # Detach children before removal to avoid cascading issues
    targets = []
    for name in RIG_NAMES.values():
        obj = bpy.data.objects.get(name)
        if obj:
            targets.append(obj)
    # Also collect light rig empties
    for obj in list(bpy.data.objects):
        if obj.name.startswith("AutoSetup_LightRig_"):
            targets.append(obj)
    # Clear parents of attached cameras/lights
    for obj in bpy.context.scene.objects:
        if obj.parent in targets:
            obj.parent = None
    # Remove targets
    for obj in targets:
        try:
            bpy.data.objects.remove(obj, do_unlink=True)
        except Exception:
            pass


def create_spline_control_rig(bounds_info: dict) -> dict:
    """Create a spline-based control rig to manipulate camera and lights.

    Returns dict with created objects.
    """
    center = bounds_info.get('center')
    max_dim = bounds_info.get('max_dimension', 1.0)

    # Focus empty at center
    focus = bpy.data.objects.get(RIG_NAMES['focus'])
    if focus is None:
        focus = bpy.data.objects.new(RIG_NAMES['focus'], None)
        focus.empty_display_type = 'SPHERE'
        try:
            bpy.context.scene.collection.objects.link(focus)
        except RuntimeError:
            pass
    # Use world-space placement to avoid double offset when parented
    focus.matrix_world.translation = center

    # Bezier circle as orbit curve
    curve_obj = bpy.data.objects.get(RIG_NAMES['curve'])
    if curve_obj is None:
        curve_data = bpy.data.curves.new(RIG_NAMES['curve'] + "_Data", type='CURVE')
        curve_data.dimensions = '3D'
        # Create a circle spline
        spline = curve_data.splines.new(type='BEZIER')
        spline.bezier_points.add(3)  # 4 points total
        # Define a unit circle in XY
        import math
        pts = [
            (1, 0, 0),
            (0, 1, 0),
            (-1, 0, 0),
            (0, -1, 0),
        ]
        for i, co in enumerate(pts):
            bp = spline.bezier_points[i]
            bp.co = (*co,)
            bp.handle_left_type = 'AUTO'
            bp.handle_right_type = 'AUTO'
        spline.use_cyclic_u = True
        curve_obj = bpy.data.objects.new(RIG_NAMES['curve'], curve_data)
        try:
            bpy.context.scene.collection.objects.link(curve_obj)
        except RuntimeError:
            pass
        # Enable path evaluation (duration must be int)
        try:
            curve_data.path_duration = 100
        except Exception:
            # Some versions use different defaults; ignore if not settable
            pass
        curve_data.use_path = True
    # Use world-space placement to avoid double offset when parented
    curve_obj.matrix_world.translation = center

    # Set initial radius by scaling the curve
    desired_radius = max_dim * 1.0  # base radius ~ object size
    curve_obj.scale = (desired_radius, desired_radius, desired_radius)
    curve_obj["base_scale"] = desired_radius

    # Control empty
    control = bpy.data.objects.get(RIG_NAMES['control'])
    if control is None:
        control = bpy.data.objects.new(RIG_NAMES['control'], None)
        control.empty_display_type = 'ARROWS'
        safe_execute(lambda: bpy.context.scene.collection.objects.link(control))
    control.matrix_world.translation = center

    # Camera rig empty following the path
    cam_rig = bpy.data.objects.get(RIG_NAMES['cam_rig'])
    if cam_rig is None:
        cam_rig = bpy.data.objects.new(RIG_NAMES['cam_rig'], None)
        cam_rig.empty_display_type = 'PLAIN_AXES'
        try:
            bpy.context.scene.collection.objects.link(cam_rig)
        except RuntimeError:
            pass

    # Follow Path on cam_rig
    follow = None
    for c in cam_rig.constraints:
        if c.type == 'FOLLOW_PATH' and c.target == curve_obj:
            follow = c
            break
    if follow is None:
        follow = cam_rig.constraints.new(type='FOLLOW_PATH')
    follow.name = "ALCS_FollowPath"
    follow.target = curve_obj
    # Some builds may not expose use_fixed_position/offset_factor until curve has path settings; guard attributes
    if hasattr(follow, 'use_fixed_position'):
        try:
            follow.use_fixed_position = True
        except Exception:
            pass
    # Set axes with guards
    if hasattr(follow, 'forward_axis'):
        follow.forward_axis = 'FORWARD_Y'
    if hasattr(follow, 'up_axis'):
        follow.up_axis = 'UP_Z'

    # Drive path position by control rotation around Z (wrap 0..1)
    data_path = "constraints[\"ALCS_FollowPath\"].offset_factor"
    if not hasattr(follow, 'offset_factor') and hasattr(follow, 'offset'):
        data_path = "constraints[\"ALCS_FollowPath\"].offset"
    expr = "rz/6.283185307179586 - floor(rz/6.283185307179586)"
    _add_driver(cam_rig, data_path, expr, [("rz", control, "rotation_euler[2]")])

    # Track To focus
    tto = None
    for c in cam_rig.constraints:
        if c.type == 'TRACK_TO' and c.target == focus:
            tto = c
            break
    if tto is None:
        tto = cam_rig.constraints.new(type='TRACK_TO')
    tto.name = "ALCS_TrackTo"
    tto.target = focus
    tto.track_axis = 'TRACK_NEGATIVE_Z'
    tto.up_axis = 'UP_Y'

    # Drive curve scale by control scale X/Y (average) times base scale
    _add_driver(curve_obj, "scale[0]", "((sx+sy)/2)*b", [("sx", control, "scale[0]"), ("sy", control, "scale[1]"), ("b", curve_obj, "[\"base_scale\"]")])
    _add_driver(curve_obj, "scale[1]", "((sx+sy)/2)*b", [("sx", control, "scale[0]"), ("sy", control, "scale[1]"), ("b", curve_obj, "[\"base_scale\"]")])

    # Parent control objects under AutoSetup root collection for organization
    try:
        root_col = util_collections.get_or_create_collection("AutoSetup")
        util_collections.link_object_to_collection(focus, root_col)
        util_collections.link_object_to_collection(curve_obj, root_col)
        util_collections.link_object_to_collection(control, root_col)
        util_collections.link_object_to_collection(cam_rig, root_col)
    except Exception:
        pass

    # Attach existing AutoSetup camera to the rig
    cam = _find_autosetup_camera()
    if cam:
        setup_camera_for_rig(cam, focus)
        _parent_keep_world_transform(cam, cam_rig)
        _add_driver(cam, "location[2]", "lz", [("lz", control, "location[2]")])

    # Optionally, attach AutoSetup lights to the curve via helper empties
    lights = [obj for obj in bpy.context.scene.objects if obj.type == 'LIGHT' and obj.name.startswith("AutoSetup_")]
    offsets = [0.0, 0.33, 0.66]
    for idx, light in enumerate(lights[:3]):
        rig_name = f"AutoSetup_LightRig_{idx+1}"
        rig = bpy.data.objects.get(rig_name)
        if rig is None:
            rig = bpy.data.objects.new(rig_name, None)
            rig.empty_display_type = 'CUBE'
            try:
                bpy.context.scene.collection.objects.link(rig)
            except RuntimeError:
                pass
            try:
                util_collections.link_object_to_collection(rig, root_col)
            except Exception:
                pass
        # Follow Path
        f = None
        for c in rig.constraints:
            if c.type == 'FOLLOW_PATH' and c.target == curve_obj:
                f = c
                break
        if f is None:
            f = rig.constraints.new(type='FOLLOW_PATH')
        f.name = f"ALCS_FollowPath_{idx+1}"
        f.target = curve_obj
        if hasattr(f, 'use_fixed_position'):
            try:
                f.use_fixed_position = True
            except Exception:
                pass
        if hasattr(f, 'forward_axis'):
            f.forward_axis = 'FORWARD_Y'
        if hasattr(f, 'up_axis'):
            f.up_axis = 'UP_Z'
        # offset = rotZ + const, wrapped 0..1
        k = offsets[idx]
        dpath = f"constraints[\"ALCS_FollowPath_{idx+1}\"].offset_factor"
        if not hasattr(f, 'offset_factor') and hasattr(f, 'offset'):
            dpath = f"constraints[\"ALCS_FollowPath_{idx+1}\"].offset"
        _add_driver(rig, dpath, f"(rz/6.283185307179586+{k})-floor(rz/6.283185307179586+{k})", [("rz", control, "rotation_euler[2]")])
        # Track to focus
        tt = None
        for c in rig.constraints:
            if c.type == 'TRACK_TO' and c.target == focus:
                tt = c
                break
        if tt is None:
            tt = rig.constraints.new(type='TRACK_TO')
        tt.target = focus
        tt.track_axis = 'TRACK_NEGATIVE_Z'
        tt.up_axis = 'UP_Y'
        # Setup light for rig control
        setup_light_for_rig(light)
        _parent_keep_world_transform(light, rig)

    return {
        'focus': focus,
        'curve': curve_obj,
        'control': control,
        'cam_rig': cam_rig,
    }
