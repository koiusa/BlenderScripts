"""
Debug utilities for Auto Light Camera Setup.
Provides comprehensive logging and state verification for troubleshooting position drift issues.
"""

import bpy
from mathutils import Vector
from typing import Dict, List, Any, Optional
from datetime import datetime


class ALCSDebugger:
    """Centralized debug logging for ALCS operations."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.log_entries = []
    
    def log(self, level: str, message: str, context: Dict[str, Any] = None):
        """Log a debug message with context."""
        if not self.enabled:
            return
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            'context': context or {}
        }
        self.log_entries.append(entry)
        
        # Print to console for immediate feedback
        context_str = f" | {context}" if context else ""
        print(f"[ALCS-{level}] {message}{context_str}")
    
    def info(self, message: str, context: Dict[str, Any] = None):
        self.log('INFO', message, context)
    
    def warning(self, message: str, context: Dict[str, Any] = None):
        self.log('WARNING', message, context)
    
    def error(self, message: str, context: Dict[str, Any] = None):
        self.log('ERROR', message, context)
    
    def dump_logs(self) -> str:
        """Return all logs as formatted string."""
        return '\n'.join([
            f"{entry['timestamp']} [{entry['level']}] {entry['message']}"
            + (f" | {entry['context']}" if entry['context'] else "")
            for entry in self.log_entries
        ])


# Global debugger instance
debugger = ALCSDebugger()


def log_object_state(obj: bpy.types.Object, operation: str = "", phase: str = ""):
    """Log comprehensive object state for debugging."""
    if not obj:
        debugger.warning(f"Null object in log_object_state", {'operation': operation, 'phase': phase})
        return
    
    world_pos = obj.matrix_world.translation
    local_pos = obj.location
    parent_name = obj.parent.name if obj.parent else "None"
    
    context = {
        'operation': operation,
        'phase': phase,
        'object': obj.name,
        'type': obj.type,
        'world_pos': f"({world_pos.x:.3f}, {world_pos.y:.3f}, {world_pos.z:.3f})",
        'local_pos': f"({local_pos.x:.3f}, {local_pos.y:.3f}, {local_pos.z:.3f})",
        'parent': parent_name,
        'has_constraints': len(obj.constraints) > 0,
        'constraint_count': len(obj.constraints)
    }
    
    debugger.info(f"Object state: {obj.name}", context)


def log_rig_state(operation: str = "", phase: str = ""):
    """Log complete rig state for debugging."""
    from . import util_rig
    
    rig_objects = util_rig.get_rig_objects()
    rig_exists = util_rig.rig_exists()
    
    context = {
        'operation': operation,
        'phase': phase,
        'rig_exists': rig_exists,
        'focus_exists': rig_objects['focus'] is not None,
        'curve_exists': rig_objects['curve'] is not None,
        'control_exists': rig_objects['control'] is not None,
        'cam_rig_exists': rig_objects['cam_rig'] is not None,
        'light_rigs_count': len(rig_objects['light_rigs'])
    }
    
    if rig_objects['focus']:
        focus_pos = rig_objects['focus'].matrix_world.translation
        context['focus_position'] = f"({focus_pos.x:.3f}, {focus_pos.y:.3f}, {focus_pos.z:.3f})"
    
    debugger.info(f"Rig state", context)


def log_bounds_info(bounds_info: Dict[str, Any], operation: str = "", phase: str = ""):
    """Log bounds information for debugging."""
    if not bounds_info:
        debugger.warning(f"Null bounds_info", {'operation': operation, 'phase': phase})
        return
    
    center = bounds_info.get('center')
    context = {
        'operation': operation,
        'phase': phase,
        'object_count': len(bounds_info.get('objects', [])),
        'max_dimension': bounds_info.get('max_dimension', 0),
        'center': f"({center.x:.3f}, {center.y:.3f}, {center.z:.3f})" if center else "None"
    }
    
    debugger.info(f"Bounds info", context)


def verify_rig_consistency(phase: str = "") -> bool:
    """Verify rig consistency and return True if consistent.
    
    Args:
        phase: Description of current phase for logging
        
    Returns:
        bool: True if rig is consistent, False if issues found
    """
    from . import util_rig
    
    issues = []
    
    if not util_rig.rig_exists():
        # No rig present; treat as consistent for this phase
        debugger.info(f"No rig present in phase '{phase}' — treating as consistent")
        return True
    
    rig_objects = util_rig.get_rig_objects()
    
    # Check rig component existence
    required_components = ['focus', 'curve', 'control', 'cam_rig']
    for component in required_components:
        if rig_objects[component] is None:
            issues.append(f"Missing rig component: {component}")
    
    # Check camera rig consistency
    if rig_objects['cam_rig']:
        rigged_cameras = []
        for obj in bpy.context.scene.objects:
            if obj.type == 'CAMERA' and obj.name.startswith("AutoSetup_Camera"):
                if util_rig.is_camera_rigged(obj):
                    rigged_cameras.append(obj)
                    # Check for conflicting constraints
                    autosetup_constraints = [c for c in obj.constraints 
                                           if c.type == 'TRACK_TO' and c.name.startswith("AutoSetup")]
                    if autosetup_constraints:
                        issues.append(f"Camera {obj.name} has conflicting AutoSetup constraints while rigged")
        
        debugger.info(f"Found {len(rigged_cameras)} rigged cameras")
    
    # Check light rig consistency
    for obj in bpy.context.scene.objects:
        if obj.type == 'LIGHT' and obj.name.startswith("AutoSetup_"):
            if util_rig.is_light_rigged(obj):
                # Check for conflicting constraints
                autosetup_constraints = [c for c in obj.constraints 
                                       if c.type == 'TRACK_TO' and c.name.startswith("AutoSetup")]
                if autosetup_constraints:
                    issues.append(f"Light {obj.name} has conflicting AutoSetup constraints while rigged")
    
    # Check for orphaned track targets
    orphaned_targets = []
    for obj in bpy.context.scene.objects:
        if obj.type == 'EMPTY' and obj.name.endswith('_TrackTarget'):
            owner_name = obj.name.replace('_TrackTarget', '')
            owner = bpy.data.objects.get(owner_name)
            
            if owner is None:
                orphaned_targets.append(obj.name)
            elif ((owner.type == 'CAMERA' and util_rig.is_camera_rigged(owner)) or
                  (owner.type == 'LIGHT' and util_rig.is_light_rigged(owner))):
                orphaned_targets.append(obj.name)
    
    if orphaned_targets:
        issues.append(f"Found orphaned track targets: {', '.join(orphaned_targets)}")
    
    if issues:
        debugger.warning(f"Rig consistency issues found in phase '{phase}'", {
            'phase': phase,
            'issue_count': len(issues),
            'issues': issues
        })
        return False
    else:
        debugger.info(f"Rig consistency verified in phase '{phase}'", {'phase': phase})
        return True


def log_coordinate_change(obj: bpy.types.Object, operation: str, old_world: Vector, new_world: Vector):
    """Log coordinate changes for debugging position drift."""
    delta = new_world - old_world
    
    context = {
        'operation': operation,
        'object': obj.name,
        'old_world': f"({old_world.x:.3f}, {old_world.y:.3f}, {old_world.z:.3f})",
        'new_world': f"({new_world.x:.3f}, {new_world.y:.3f}, {new_world.z:.3f})",
        'delta': f"({delta.x:.3f}, {delta.y:.3f}, {delta.z:.3f})",
        'delta_magnitude': f"{delta.length:.3f}"
    }
    
    if delta.length > 0.001:  # Only log significant changes
        debugger.info(f"Coordinate change: {obj.name}", context)


def enable_debug_logging():
    """Enable debug logging."""
    debugger.enabled = True
    debugger.info("Debug logging enabled")


def disable_debug_logging():
    """Disable debug logging."""
    debugger.enabled = False


def get_debug_report() -> str:
    """Generate comprehensive debug report."""
    from . import util_rig
    
    report = ["=== ALCS Debug Report ==="]
    report.append(f"Generated: {datetime.now().isoformat()}")
    report.append("")
    
    # Rig state
    report.append("=== Rig State ===")
    is_consistent = verify_rig_consistency("debug_report")
    if not is_consistent:
        report.append("Rig consistency issues detected (see logs for details)")
    else:
        report.append("No rig consistency issues found")
    report.append("")
    
    # Object inventory
    report.append("=== Object Inventory ===")
    cameras = [obj for obj in bpy.context.scene.objects 
              if obj.type == 'CAMERA' and obj.name.startswith("AutoSetup_Camera")]
    lights = [obj for obj in bpy.context.scene.objects 
             if obj.type == 'LIGHT' and obj.name.startswith("AutoSetup_")]
    targets = [obj for obj in bpy.context.scene.objects 
              if obj.type == 'EMPTY' and obj.name.endswith("_TrackTarget")]
    
    report.append(f"AutoSetup Cameras: {len(cameras)}")
    for cam in cameras:
        rigged = util_rig.is_camera_rigged(cam)
        constraints = len([c for c in cam.constraints if c.name.startswith("AutoSetup")])
        report.append(f"  - {cam.name}: rigged={rigged}, constraints={constraints}")
    
    report.append(f"AutoSetup Lights: {len(lights)}")
    for light in lights:
        rigged = util_rig.is_light_rigged(light)
        constraints = len([c for c in light.constraints if c.name.startswith("AutoSetup")])
        report.append(f"  - {light.name}: rigged={rigged}, constraints={constraints}")
    
    report.append(f"Track Targets: {len(targets)}")
    for target in targets:
        report.append(f"  - {target.name}")
    
    report.append("")
    
    # Recent logs
    report.append("=== Recent Debug Logs ===")
    report.append(debugger.dump_logs())
    
    return '\n'.join(report)