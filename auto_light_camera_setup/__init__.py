"""
Auto Light Camera Setup - Blender Add-on
Provides automatic lighting, camera positioning, and batch rendering capabilities.

Version 1.0.1 - Refactored for improved maintainability and reliability.
"""

bl_info = {
    "name": "Auto Light Camera Setup",
    "author": "Blender Scripts",
    "version": (1, 0, 1),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Auto Setup",
    "description": "Automatic lighting, camera setup, multi-shot generation, and batch processing",
    "category": "Render",
}

import bpy
from . import props
from . import presets
from . import ops_core
from . import ops_batch
from . import ui_panel

classes = (
    props.AutoSetupProperties,
    presets.ALCS_OT_apply_preset,
    ops_core.ALCS_OT_auto_setup,
    ops_core.ALCS_OT_generate_multi_shots,
    ops_core.ALCS_OT_render_shots_now,
    ops_core.ALCS_OT_cleanup_auto_objects,
    ops_core.ALCS_OT_focus_camera_on_selection,
    ops_core.ALCS_OT_reload_addon,
    ops_batch.ALCS_OT_batch_process,
    ops_batch.ALCS_OT_setup_collection_shots,
    ui_panel.ALCS_PT_auto_setup_panel,
    ui_panel.ALCS_PT_advanced_panel,
    ui_panel.ALCS_PT_info_panel,
)

def _safe_register_class(cls):
    import bpy
    try:
        bpy.utils.register_class(cls)
    except ValueError:
        # Already registered: try to unregister then register again
        try:
            bpy.utils.unregister_class(cls)
        except Exception:
            pass
        bpy.utils.register_class(cls)

def _safe_unregister_class(cls):
    import bpy
    try:
        bpy.utils.unregister_class(cls)
    except Exception:
        # Ignore if not registered
        pass

def register():
    # Register classes safely (handle re-registration)
    for cls in classes:
        _safe_register_class(cls)

    # (Re)define Scene pointer property safely
    if hasattr(bpy.types.Scene, 'auto_setup_props'):
        try:
            del bpy.types.Scene.auto_setup_props
        except Exception:
            pass
    bpy.types.Scene.auto_setup_props = bpy.props.PointerProperty(type=props.AutoSetupProperties)

def unregister():
    # Remove Scene pointer property if present
    if hasattr(bpy.types.Scene, 'auto_setup_props'):
        try:
            del bpy.types.Scene.auto_setup_props
        except Exception:
            pass

    # Unregister classes safely
    for cls in reversed(classes):
        _safe_unregister_class(cls)

if __name__ == "__main__":
    register()