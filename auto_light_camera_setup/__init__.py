"""
Auto Light Camera Setup - Blender Add-on
Provides automatic lighting, camera positioning, and batch rendering capabilities.
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
    ops_core.ALCS_OT_cleanup_auto_objects,
    ops_core.ALCS_OT_focus_camera_on_selection,
    ops_core.ALCS_OT_quick_render_current,
    ops_core.ALCS_OT_create_studio_setup,
    ops_batch.ALCS_OT_batch_process,
    ops_batch.ALCS_OT_batch_render_all_cameras,
    ops_batch.ALCS_OT_setup_collection_shots,
    ops_batch.ALCS_OT_export_batch_config,
    ui_panel.ALCS_PT_auto_setup_panel,
    ui_panel.ALCS_PT_advanced_panel,
    ui_panel.ALCS_PT_info_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.auto_setup_props = bpy.props.PointerProperty(
        type=props.AutoSetupProperties
    )

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    del bpy.types.Scene.auto_setup_props

if __name__ == "__main__":
    register()