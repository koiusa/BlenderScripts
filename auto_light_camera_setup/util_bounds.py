"""
Bounds detection utilities for Auto Light Camera Setup.
Handles automatic detection of object bounds for camera and lighting positioning.
"""

import bpy
import bmesh
from mathutils import Vector
from typing import List, Tuple, Optional, Dict, Any
from .constants import AUTOSETUP_FLOOR_NAMES
from .utils import ALCSLogger, safe_execute

def get_target_objects(props) -> List[bpy.types.Object]:
    """
    Get target objects based on current selection or specified collection.
    
    Args:
        props: AutoSetupProperties instance
        
    Returns:
        List of mesh objects to target (excludes AutoSetup floors)
    """
    def _get_objects():
        objects = []
        
        if props.use_selection and bpy.context.selected_objects:
            # Use selected objects (exclude AutoSetup floors)
            objects = [obj for obj in bpy.context.selected_objects
                      if obj.type == 'MESH' and obj.name not in AUTOSETUP_FLOOR_NAMES]
            ALCSLogger.info(f"Using {len(objects)} selected objects as targets")
        elif props.target_collection:
            # Use specified collection
            collection = bpy.data.collections.get(props.target_collection)
            if collection:
                objects = get_objects_in_collection(collection)
                ALCSLogger.info(f"Using {len(objects)} objects from collection '{props.target_collection}'")
            else:
                ALCSLogger.warning(f"Collection '{props.target_collection}' not found")
        else:
            # Use all visible mesh objects in scene
            objects = [obj for obj in bpy.context.scene.objects
                      if obj.type == 'MESH' and obj.visible_get() and obj.name not in AUTOSETUP_FLOOR_NAMES]
            ALCSLogger.info(f"Using {len(objects)} visible mesh objects from scene")
        
        return objects
    
    return safe_execute(_get_objects, "Failed to get target objects", []) or []

def get_objects_in_collection(collection) -> List[bpy.types.Object]:
    """
    Recursively get all mesh objects in a collection and its children.
    
    Args:
        collection: Blender collection
        
    Returns:
        List of mesh objects
    """
    objects = []
    
    # Add objects from current collection
    for obj in collection.objects:
        if obj.type == 'MESH' and obj.name not in AUTOSETUP_FLOOR_NAMES:
            objects.append(obj)
    
    # Recursively add objects from child collections
    for child_collection in collection.children:
        objects.extend(get_objects_in_collection(child_collection))
    
    return objects

def calculate_bounds(objects: List[bpy.types.Object]) -> Tuple[Vector, Vector, Vector]:
    """
    Calculate combined bounding box for multiple objects.
    
    Args:
        objects: List of objects to calculate bounds for
        
    Returns:
        Tuple of (min_coord, max_coord, center)
    """
    if not objects:
        # Default bounds if no objects
        return Vector((-1, -1, -1)), Vector((1, 1, 1)), Vector((0, 0, 0))
    
    # Initialize with first object's bounds
    first_obj = objects[0]
    
    # Get world matrix transformed bounding box
    bbox_corners = [first_obj.matrix_world @ Vector(corner) 
                    for corner in first_obj.bound_box]
    
    min_x = min(corner.x for corner in bbox_corners)
    max_x = max(corner.x for corner in bbox_corners)
    min_y = min(corner.y for corner in bbox_corners)
    max_y = max(corner.y for corner in bbox_corners)
    min_z = min(corner.z for corner in bbox_corners)
    max_z = max(corner.z for corner in bbox_corners)
    
    # Extend bounds with remaining objects
    for obj in objects[1:]:
        bbox_corners = [obj.matrix_world @ Vector(corner) 
                       for corner in obj.bound_box]
        
        min_x = min(min_x, min(corner.x for corner in bbox_corners))
        max_x = max(max_x, max(corner.x for corner in bbox_corners))
        min_y = min(min_y, min(corner.y for corner in bbox_corners))
        max_y = max(max_y, max(corner.y for corner in bbox_corners))
        min_z = min(min_z, min(corner.z for corner in bbox_corners))
        max_z = max(max_z, max(corner.z for corner in bbox_corners))
    
    min_coord = Vector((min_x, min_y, min_z))
    max_coord = Vector((max_x, max_y, max_z))
    center = (min_coord + max_coord) / 2
    
    return min_coord, max_coord, center

def get_bounds_info(props) -> Dict[str, Any]:
    """
    Get comprehensive bounds information for target objects.
    
    Args:
        props: AutoSetupProperties instance
        
    Returns:
        Dictionary with bounds information including:
        - objects: List of target objects
        - min_coord, max_coord: Bounding box corners
        - center: Center point
        - size: Dimensions vector
        - max_dimension: Largest dimension
    """
    def _calculate_bounds():
        objects = get_target_objects(props)
        
        if not objects:
            ALCSLogger.warning("No target objects found, using default bounds")
            return {
                'objects': [],
                'min_coord': Vector((-1, -1, -1)),
                'max_coord': Vector((1, 1, 1)),
                'center': Vector((0, 0, 0)),
                'size': Vector((2, 2, 2)),
                'max_dimension': 2.0
            }
        
        min_coord, max_coord, center = calculate_bounds(objects)
        size = max_coord - min_coord
        max_dimension = max(size.x, size.y, size.z)
        
        ALCSLogger.info(f"Calculated bounds for {len(objects)} objects: "
                       f"center={center}, max_dim={max_dimension:.2f}")
        
        return {
            'objects': objects,
            'min_coord': min_coord,
            'max_coord': max_coord,
            'center': center,
            'size': size,
            'max_dimension': max_dimension
        }
    
    return safe_execute(_calculate_bounds, "Failed to calculate bounds info", {}) or {}

def validate_targets(props) -> bool:
    """
    Validate that target objects exist and are valid.
    
    Args:
        props: AutoSetupProperties instance
        
    Returns:
        True if valid targets found, False otherwise
    """
    objects = get_target_objects(props)
    is_valid = len(objects) > 0
    
    if not is_valid:
        ALCSLogger.error("No valid target objects found")
    else:
        ALCSLogger.info(f"Validated {len(objects)} target objects")
    
    return is_valid