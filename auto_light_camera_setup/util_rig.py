"""
Rig/Locator utilities for Auto Light Camera Setup.
Creates a common locator (Empty) and parents auto-generated cameras/lights to it
so the whole setup can be manipulated together.
"""

import bpy
from mathutils import Vector
from . import util_collections


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


def _parent_keep_world_transform(obj: bpy.types.Object, parent: bpy.types.Object):
    """Parent obj to parent while keeping the world transform unchanged."""
    if obj.parent == parent:
        return
    world = obj.matrix_world.copy()
    obj.parent = parent
    obj.matrix_world = world


def parent_autosetup_objects_to_locator(bounds_info: dict | None = None,
                                        include_track_targets: bool = True,
                                        locator_name: str = "AutoSetup_Locator") -> bpy.types.Object:
    """
    Find AutoSetup cameras/lights (and optionally track target empties) and parent them to a common locator.

    Args:
        bounds_info: If provided, the locator will be moved to bounds center.
        include_track_targets: Whether to also parent *_TrackTarget empties.
        locator_name: Name of the locator object.

    Returns:
        The locator object used.
    """
    locator = create_or_get_locator(locator_name)

    # Optionally place the locator at the target center for intuitive manipulation
    if bounds_info and 'center' in bounds_info:
        center = bounds_info['center']
        if isinstance(center, Vector):
            locator.location = center

    # Collect targets
    to_parent: list[bpy.types.Object] = []
    for obj in bpy.context.scene.objects:
        if obj.type == 'CAMERA' and obj.name.startswith("AutoSetup_Camera"):
            to_parent.append(obj)
        elif obj.type == 'LIGHT' and obj.name.startswith("AutoSetup_"):
            to_parent.append(obj)
        elif include_track_targets and obj.type == 'EMPTY' and obj.name.startswith("AutoSetup_") and obj.name.endswith("_TrackTarget"):
            to_parent.append(obj)

    # Parent with transform preserved
    for obj in to_parent:
        _parent_keep_world_transform(obj, locator)

    return locator
