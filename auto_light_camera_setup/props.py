"""
Properties module for Auto Light Camera Setup add-on.
Defines all the configuration properties used by the add-on.
"""

import bpy
from bpy.props import (
    BoolProperty, FloatProperty, IntProperty, 
    StringProperty, EnumProperty, FloatVectorProperty
)

# Static preset items to avoid registration-time errors
PRESET_ITEMS = (
    ('PRODUCT', 'Product', 'Optimized for product visualization'),
    ('CHARACTER', 'Character/Portrait', 'Optimized for character and portrait rendering'),
    ('SMALL_PROP', 'Small Prop', 'Close-up shots for small objects and details'),
    ('FLAT_ART', 'Flat Art/Technical', 'Flat, even lighting for technical documentation'),
    ('ARCHITECTURAL', 'Architectural', 'Wide shots for architectural visualization'),
)

class AutoSetupProperties(bpy.types.PropertyGroup):
    """Main property group for auto setup configuration"""
    
    # Preset selection
    preset_name: EnumProperty(
        name="Preset",
        description="Preset configuration to apply",
        items=PRESET_ITEMS,
        default='PRODUCT'
    )

    # Target Configuration
    use_selection: BoolProperty(
        name="Use Selection",
        description="Use selected objects as target (overrides collection)",
        default=True
    )
    
    target_collection: StringProperty(
        name="Target Collection",
        description="Collection to process (if no selection)",
        default=""
    )
    
    # Camera Settings
    camera_distance_factor: FloatProperty(
        name="Distance Factor",
        description="Multiplier for camera distance from bounds",
        default=2.5,
        min=0.5,
        max=10.0
    )
    
    camera_lens: FloatProperty(
        name="Lens (mm)",
        description="Camera lens focal length in mm (0 = use current)",
        default=50.0,
        min=0.0,
        max=300.0
    )
    
    enable_dof: BoolProperty(
        name="Enable DOF",
        description="Enable depth of field",
        default=False
    )
    
    dof_fstop: FloatProperty(
        name="F-Stop",
        description="Depth of field F-Stop value",
        default=2.8,
        min=0.1,
        max=22.0
    )
    
    # Lighting Settings
    light_key_intensity: FloatProperty(
        name="Key Light",
        description="Key light intensity",
        default=5.0,
        min=0.0,
        max=50.0
    )
    
    light_fill_intensity: FloatProperty(
        name="Fill Light",
        description="Fill light intensity",
        default=2.0,
        min=0.0,
        max=50.0
    )
    
    light_rim_intensity: FloatProperty(
        name="Rim Light",
        description="Rim light intensity",
        default=3.0,
        min=0.0,
        max=50.0
    )
    
    # Floor Settings
    add_floor: BoolProperty(
        name="Add Floor",
        description="Add a floor plane beneath the target",
        default=False
    )
    
    floor_material_color: FloatVectorProperty(
        name="Floor Color",
        description="Floor material color",
        default=(0.8, 0.8, 0.8),
        min=0.0,
        max=1.0,
        subtype='COLOR'
    )
    
    # World/HDRI Settings
    use_hdri: BoolProperty(
        name="Use HDRI",
        description="Use HDRI environment lighting",
        default=False
    )
    
    hdri_path: StringProperty(
        name="HDRI Path",
        description="Path to HDRI file",
        default="",
        subtype='FILE_PATH'
    )
    
    hdri_strength: FloatProperty(
        name="HDRI Strength",
        description="HDRI environment strength",
        default=1.0,
        min=0.0,
        max=10.0
    )
    
    world_strength: FloatProperty(
        name="World Strength",
        description="Basic world background strength",
        default=1.0,
        min=0.0,
        max=10.0
    )
    
    # Render Settings
    enable_filmic: BoolProperty(
        name="Enable Filmic",
        description="Enable Filmic color management",
        default=True
    )
    
    exposure: FloatProperty(
        name="Exposure",
        description="Scene exposure adjustment",
        default=0.0,
        min=-10.0,
        max=10.0
    )
    
    # Multi-shot Settings
    shot_types: EnumProperty(
        name="Shot Types",
        description="Types of shots to generate",
        items=[
            ('ALL', "All Shots", "Generate all shot types"),
            ('FRONT', "Front Only", "Generate front shot only"),
            ('3Q', "3/4 Views", "Generate 3/4 left and right shots"),
            ('CUSTOM', "Custom", "Select specific shots"),
        ],
        default='ALL'
    )
    
    render_shots: BoolProperty(
        name="Render Shots",
        description="Immediately render generated shots",
        default=False
    )
    
    # Batch Processing
    batch_mode: BoolProperty(
        name="Batch Mode",
        description="Process multiple collections",
        default=False
    )
    
    collection_filter: StringProperty(
        name="Collection Filter",
        description="Filter collections by name (empty = all)",
        default=""
    )

    def batch_collection_items(self, context):
        import bpy
        items = []
        for c in bpy.data.collections:
            items.append((c.name, c.name, ""))
        if not items:
            items = [("", "No collections found", "")]
        return items

    batch_target_collection: EnumProperty(
        name="Batch Target Collection",
        description="Collection to process in batch mode",
        items=batch_collection_items
    )
    
    render_per_collection: BoolProperty(
        name="Render Per Collection",
        description="Render after processing each collection",
        default=False
    )
    
    output_path: StringProperty(
        name="Output Path",
        description="Base output path for batch rendering",
        # Default is user's Pictures\ALCS_Renders when empty (see utils.resolve_output_path)
        default="",
        subtype='DIR_PATH'
    )