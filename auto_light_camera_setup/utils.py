"""
Common utilities for Auto Light Camera Setup.
Provides consistent error handling, logging, and helper functions.
"""

import bpy
from typing import Optional, Any, Callable, TypeVar, Union
import traceback
from .constants import ObjectNames
import os
import time

T = TypeVar('T')


class ALCSLogger:
    """Centralized logging for ALCS operations."""
    
    @staticmethod
    def info(message: str) -> None:
        """Log an info message."""
        print(f"[ALCS INFO] {message}")
    
    @staticmethod
    def warning(message: str) -> None:
        """Log a warning message."""
        print(f"[ALCS WARNING] {message}")
    
    @staticmethod
    def error(message: str, exception: Optional[Exception] = None) -> None:
        """Log an error message with optional exception details."""
        print(f"[ALCS ERROR] {message}")
        if exception:
            print(f"[ALCS ERROR] Exception: {str(exception)}")
            print(f"[ALCS ERROR] Traceback: {traceback.format_exc()}")


def safe_execute(
    operation: Callable[[], T], 
    error_message: str,
    default_return: Optional[T] = None,
    log_errors: bool = True
) -> Optional[T]:
    """
    Safely execute an operation with consistent error handling.
    
    Args:
        operation: Function to execute
        error_message: Message to log on error
        default_return: Value to return on error
        log_errors: Whether to log errors
        
    Returns:
        Result of operation or default_return on error
    """
    try:
        return operation()
    except Exception as e:
        if log_errors:
            ALCSLogger.error(error_message, e)
        return default_return


def get_or_create_object(
    name: str, 
    create_func: Callable[[], bpy.types.Object],
    object_type: Optional[str] = None
) -> Optional[bpy.types.Object]:
    """
    Get existing object by name or create new one.
    
    Args:
        name: Object name to search for
        create_func: Function to create new object
        object_type: Optional type filter for existing object
        
    Returns:
        Object instance or None on error
    """
    def _get_or_create():
        obj = bpy.data.objects.get(name)
        
        if obj is None:
            obj = create_func()
            ALCSLogger.info(f"Created new object: {name}")
        else:
            # Validate object type if specified
            if object_type and obj.type != object_type:
                ALCSLogger.warning(f"Object {name} exists but has wrong type: {obj.type} != {object_type}")
                # Could recreate here if needed
            else:
                ALCSLogger.info(f"Using existing object: {name}")
        
        return obj
    
    return safe_execute(
        _get_or_create,
        f"Failed to get or create object: {name}"
    )


def ensure_scene_update() -> None:
    """Force scene/view layer update to sync dependencies."""
    def _update():
        bpy.context.view_layer.update()
    
    safe_execute(
        _update,
        "Failed to update view layer",
        log_errors=False  # This can fail in background mode
    )


def validate_bounds_info(bounds_info: dict) -> bool:
    """
    Validate that bounds_info contains required keys.
    
    Args:
        bounds_info: Dictionary from util_bounds.get_bounds_info()
        
    Returns:
        True if valid, False otherwise
    """
    required_keys = {'objects', 'center', 'max_dimension', 'min_coord', 'max_coord', 'size'}
    missing_keys = required_keys - set(bounds_info.keys())
    
    if missing_keys:
        ALCSLogger.error(f"Invalid bounds_info, missing keys: {missing_keys}")
        return False
    
    if not bounds_info['objects']:
        ALCSLogger.warning("bounds_info contains no objects")
        return False
    
    return True


def cleanup_autosetup_objects() -> int:
    """
    Remove all auto-generated objects from the scene.
    
    Returns:
        Number of objects removed
    """
    def _cleanup():
        objects_to_remove = []
        
        # Find all AutoSetup objects
        for obj in bpy.context.scene.objects:
            if (obj.name.startswith("AutoSetup_") or 
                obj.name.endswith("_TrackTarget")):
                objects_to_remove.append(obj)
        
        # Remove them
        for obj in objects_to_remove:
            try:
                bpy.data.objects.remove(obj, do_unlink=True)
            except Exception as e:
                ALCSLogger.warning(f"Failed to remove object {obj.name}: {e}")
        
        ALCSLogger.info(f"Cleaned up {len(objects_to_remove)} AutoSetup objects")
        return len(objects_to_remove)
    
    return safe_execute(_cleanup, "Failed to cleanup AutoSetup objects", 0) or 0


def report_to_user(operator: bpy.types.Operator, message: str, level: str = 'INFO') -> None:
    """
    Report message to user through operator interface.
    
    Args:
        operator: Blender operator instance
        message: Message to display
        level: Message level ('INFO', 'WARNING', 'ERROR')
    """
    if hasattr(operator, 'report'):
        operator.report({level}, message)
    else:
        # Fallback to console
        if level == 'ERROR':
            ALCSLogger.error(message)
        elif level == 'WARNING':
            ALCSLogger.warning(message)
        else:
            ALCSLogger.info(message)


def get_autosetup_objects() -> dict:
    """
    Get all AutoSetup objects organized by type.
    
    Returns:
        Dictionary with 'cameras', 'lights', 'empties', 'other' lists
    """
    result = {
        'cameras': [],
        'lights': [],
        'empties': [],
        'other': []
    }
    
    for obj in bpy.context.scene.objects:
        if obj.name.startswith("AutoSetup_"):
            if obj.type == 'CAMERA':
                result['cameras'].append(obj)
            elif obj.type == 'LIGHT':
                result['lights'].append(obj)
            elif obj.type == 'EMPTY':
                result['empties'].append(obj)
            else:
                result['other'].append(obj)
    
    return result


def is_autosetup_object(obj: bpy.types.Object) -> bool:
    """Check if object is managed by AutoSetup."""
    return (obj.name.startswith("AutoSetup_") or 
            obj.name.endswith("_TrackTarget"))


def format_vector(vector) -> str:
    """Format a vector for logging/display."""
    try:
        return f"({vector.x:.2f}, {vector.y:.2f}, {vector.z:.2f})"
    except (AttributeError, TypeError):
        return str(vector)


# ----------------------------
# Output path helpers
# ----------------------------
def get_default_output_dir(create: bool = False) -> str:
    """Return default renders output directory under user's Pictures.

    Windows: %USERPROFILE%\\Pictures\\ALCS_Renders
    Others:  ~/Pictures/ALCS_Renders (fallback to home if Pictures missing)

    Args:
        create: When True, ensure the directory exists.

    Returns:
        Absolute path string to the default output directory.
    """
    try:
        user_home = os.environ.get('USERPROFILE') or os.path.expanduser('~')
        pics = os.path.join(user_home, 'Pictures')
        # If Pictures doesn't exist, fall back to home
        base = pics if os.path.isdir(pics) else user_home
        path = os.path.join(base, 'ALCS_Renders')
        if create:
            os.makedirs(path, exist_ok=True)
        return os.path.normpath(path)
    except Exception:
        # Final fallback to Blender-relative renders
        return bpy.path.abspath("//renders/")


def resolve_output_path(path: Optional[str]) -> str:
    """Resolve user-configured output path to an absolute directory.

    Rules:
        - Empty/None -> default Pictures/ALCS_Renders (auto-created)
    - Otherwise: expand ~ and env vars, use Blender abspath for // paths,
      then auto-create the directory.
    """
    if not path or not str(path).strip():
        return get_default_output_dir(create=True)

    # Expand environment variables and ~
    expanded = os.path.expandvars(os.path.expanduser(path))
    # Let Blender resolve '//' relative paths (keeps absolute paths as-is)
    abs_path = bpy.path.abspath(expanded)
    try:
        os.makedirs(abs_path, exist_ok=True)
    except Exception:
        pass
    return os.path.normpath(abs_path)


# ----------------------------
# Filename helpers
# ----------------------------
def get_timestamp() -> str:
    """Return a compact timestamp string like YYYYMMDD_HHMMSS."""
    try:
        return time.strftime("%Y%m%d_%H%M%S")
    except Exception:
        # Fallback to epoch seconds if strftime fails
        return str(int(time.time()))