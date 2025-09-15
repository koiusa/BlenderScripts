"""
UI Panel for Auto Light Camera Setup.
Provides the Blender interface for the add-on.
"""

import bpy
from bpy.types import Panel
from . import presets

class ALCS_PT_auto_setup_panel(Panel):
    """Main panel for Auto Light Camera Setup"""
    bl_label = "Auto Light Camera Setup"
    bl_idname = "ALCS_PT_auto_setup_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Auto Setup"
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.auto_setup_props
        
        # Presets section
        self.draw_presets_section(layout, props)
        
        layout.separator()
        
        # Target Configuration
        self.draw_target_section(layout, props)
        
        layout.separator()
        
        # Main Setup Controls
        self.draw_main_controls(layout)
        
        layout.separator()
        
        # Camera Settings
        self.draw_camera_section(layout, props)
        
        layout.separator()
        
        # Lighting Settings
        self.draw_lighting_section(layout, props)
        
        layout.separator()
        
        # Environment Settings
        self.draw_environment_section(layout, props)
        
        layout.separator()
        
        # Multi-shot and Batch
        self.draw_batch_section(layout, props)
        
        layout.separator()
        
        # Utilities
        self.draw_utilities_section(layout)
    
    def draw_presets_section(self, layout, props):
        """Draw presets section"""
        box = layout.box()
        box.label(text="Presets", icon='PRESET')
        
        # Preset buttons in a grid
        col = box.column()
        
        row = col.row()
        row.operator("alcs.apply_preset", text="Product").preset_name = "PRODUCT"
        row.operator("alcs.apply_preset", text="Character").preset_name = "CHARACTER"
        
        row = col.row()
        row.operator("alcs.apply_preset", text="Small Prop").preset_name = "SMALL_PROP"
        row.operator("alcs.apply_preset", text="Flat Art").preset_name = "FLAT_ART"
        
        row = col.row()
        row.operator("alcs.apply_preset", text="Architectural").preset_name = "ARCHITECTURAL"
    
    def draw_target_section(self, layout, props):
        """Draw target configuration section"""
        box = layout.box()
        box.label(text="Target Configuration", icon='OBJECT_DATA')
        
        col = box.column()
        col.prop(props, "use_selection")
        
        if not props.use_selection:
            col.prop_search(props, "target_collection", bpy.data, "collections")
    
    def draw_main_controls(self, layout):
        """Draw main control buttons"""
        box = layout.box()
        box.label(text="Main Controls", icon='TOOL_SETTINGS')
        
        col = box.column(align=True)
        col.operator("alcs.auto_setup", text="Auto Setup", icon='AUTO')
        col.operator("alcs.generate_multi_shots", text="Generate Multi-Shots", icon='CAMERA_DATA')
        
        row = box.row(align=True)
        row.operator("alcs.create_studio_setup", text="Studio Setup", icon='LIGHT')
        row.operator("alcs.cleanup_auto_objects", text="Cleanup", icon='TRASH')
    
    def draw_camera_section(self, layout, props):
        """Draw camera settings section"""
        box = layout.box()
        box.label(text="Camera Settings", icon='CAMERA_DATA')
        
        col = box.column()
        col.prop(props, "camera_distance_factor")
        col.prop(props, "camera_lens")
        
        col.separator()
        col.prop(props, "enable_dof")
        if props.enable_dof:
            col.prop(props, "dof_fstop")
    
    def draw_lighting_section(self, layout, props):
        """Draw lighting settings section"""
        box = layout.box()
        box.label(text="Lighting Settings", icon='LIGHT')
        
        col = box.column()
        col.prop(props, "light_key_intensity")
        col.prop(props, "light_fill_intensity")
        col.prop(props, "light_rim_intensity")
    
    def draw_environment_section(self, layout, props):
        """Draw environment settings section"""
        box = layout.box()
        box.label(text="Environment", icon='WORLD')
        
        col = box.column()
        
        # Floor settings
        col.prop(props, "add_floor")
        if props.add_floor:
            col.prop(props, "floor_material_color")
        
        col.separator()
        
        # World/HDRI settings
        col.prop(props, "use_hdri")
        if props.use_hdri:
            col.prop(props, "hdri_path")
            col.prop(props, "hdri_strength")
        else:
            col.prop(props, "world_strength")
        
        col.separator()
        
        # Render settings
        col.prop(props, "enable_filmic")
        col.prop(props, "exposure")
    
    def draw_batch_section(self, layout, props):
        """Draw batch processing section"""
        box = layout.box()
        box.label(text="Multi-Shot & Batch", icon='RENDER_ANIMATION')
        
        col = box.column()
        col.prop(props, "shot_types")
        col.prop(props, "render_shots")
        
        col.separator()
        
        col.prop(props, "batch_mode")
        if props.batch_mode:
            col.prop(props, "collection_filter")
            col.prop(props, "render_per_collection")
        
        col.separator()
        col.prop(props, "output_path")
        
        # Batch operations
        col.separator()
        col.operator("alcs.batch_process", text="Batch Process Collections", icon='PLAY')
        col.operator("alcs.batch_render_all_cameras", text="Render All Cameras", icon='RENDER_STILL')
    
    def draw_utilities_section(self, layout):
        """Draw utilities section"""
        box = layout.box()
        box.label(text="Utilities", icon='TOOL_SETTINGS')
        
        col = box.column(align=True)
        col.operator("alcs.focus_camera_on_selection", text="Focus on Selection", icon='ZOOM_SELECTED')
        col.operator("alcs.quick_render_current", text="Quick Render", icon='RENDER_STILL')
        
        col.separator()
        col.operator("alcs.export_batch_config", text="Export Config", icon='EXPORT')

class ALCS_PT_advanced_panel(Panel):
    """Advanced settings panel"""
    bl_label = "Advanced Settings"
    bl_idname = "ALCS_PT_advanced_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Auto Setup"
    bl_parent_id = "ALCS_PT_auto_setup_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.auto_setup_props
        
        # Advanced camera settings
        box = layout.box()
        box.label(text="Advanced Camera", icon='CAMERA_DATA')
        col = box.column()
        
        # Custom shot configuration could go here
        col.label(text="Custom shots coming soon...")
        
        # Advanced lighting settings
        box = layout.box()
        box.label(text="Advanced Lighting", icon='LIGHT')
        col = box.column()
        
        col.label(text="Advanced lighting controls coming soon...")
        
        # Performance settings
        box = layout.box()
        box.label(text="Performance", icon='PREFERENCES')
        col = box.column()
        
        col.label(text="Performance options coming soon...")

class ALCS_PT_info_panel(Panel):
    """Information and help panel"""
    bl_label = "Info & Help"
    bl_idname = "ALCS_PT_info_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Auto Setup"
    bl_parent_id = "ALCS_PT_auto_setup_panel"
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        
        # Quick usage guide
        box = layout.box()
        box.label(text="Quick Start", icon='INFO')
        col = box.column(align=True)
        col.label(text="1. Select objects or choose collection")
        col.label(text="2. Choose a preset or configure manually")
        col.label(text="3. Click 'Auto Setup' to begin")
        col.label(text="4. Use 'Generate Multi-Shots' for multiple angles")
        
        # Preset descriptions
        box = layout.box()
        box.label(text="Presets", icon='PRESET')
        col = box.column(align=True)
        
        for preset_key, preset_data in presets.PRESETS.items():
            row = col.row()
            row.label(text=f"{preset_data['name']}:")
            row = col.row()
            row.label(text=f"  {preset_data['description']}")
            col.separator()
        
        # Tips
        box = layout.box()
        box.label(text="Tips", icon='LIGHTBULB')
        col = box.column(align=True)
        col.label(text="• Use 'Focus on Selection' to adjust camera")
        col.label(text="• 'Cleanup' removes all auto-generated objects")
        col.label(text="• Batch mode processes multiple collections")
        col.label(text="• HDRI files improve lighting quality")

def draw_collection_list(layout, collection_filter=""):
    """Draw a list of available collections for batch processing"""
    from . import ops_batch
    
    box = layout.box()
    box.label(text="Available Collections", icon='OUTLINER_COLLECTION')
    
    collections = ops_batch.get_collections_for_batch(collection_filter)
    
    if not collections:
        box.label(text="No collections found", icon='ERROR')
        return
    
    col = box.column()
    for collection_name in collections[:10]:  # Limit to first 10
        row = col.row()
        row.label(text=collection_name, icon='COLLECTION_COLOR_01')
        op = row.operator("alcs.setup_collection_shots", text="Setup", icon='AUTO')
        op.collection_name = collection_name
    
    if len(collections) > 10:
        box.label(text=f"... and {len(collections) - 10} more")

# Register UI classes
classes = (
    ALCS_PT_auto_setup_panel,
    ALCS_PT_advanced_panel,
    ALCS_PT_info_panel,
)