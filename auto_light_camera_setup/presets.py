"""
Presets module for Auto Light Camera Setup.
Defines preset configurations for different types of objects and scenes.
"""

import bpy
from bpy.types import Operator

# Preset definitions
PRESETS = {
    'PRODUCT': {
        'name': 'Product Photography',
        'description': 'Optimized for product visualization',
        'camera_distance_factor': 2.0,
        'camera_lens': 85.0,
        'enable_dof': True,
        'dof_fstop': 5.6,
        'light_key_intensity': 8.0,
        'light_fill_intensity': 3.0,
        'light_rim_intensity': 4.0,
        'add_floor': True,
        'floor_material_color': (0.9, 0.9, 0.9),
        'use_hdri': False,
        'world_strength': 0.5,
        'enable_filmic': True,
        'exposure': 0.5,
        'shot_types': 'ALL'
    },
    
    'CHARACTER': {
        'name': 'Character/Portrait',
        'description': 'Optimized for character and portrait rendering',
        'camera_distance_factor': 3.0,
        'camera_lens': 75.0,
        'enable_dof': True,
        'dof_fstop': 2.8,
        'light_key_intensity': 6.0,
        'light_fill_intensity': 2.5,
        'light_rim_intensity': 5.0,
        'add_floor': False,
        'floor_material_color': (0.5, 0.5, 0.5),
        'use_hdri': True,
        'world_strength': 1.0,
        'enable_filmic': True,
        'exposure': 0.0,
        'shot_types': '3Q'
    },
    
    'SMALL_PROP': {
        'name': 'Small Props/Details',
        'description': 'Close-up shots for small objects and details',
        'camera_distance_factor': 1.5,
        'camera_lens': 100.0,
        'enable_dof': True,
        'dof_fstop': 4.0,
        'light_key_intensity': 12.0,
        'light_fill_intensity': 4.0,
        'light_rim_intensity': 6.0,
        'add_floor': True,
        'floor_material_color': (1.0, 1.0, 1.0),
        'use_hdri': False,
        'world_strength': 0.3,
        'enable_filmic': True,
        'exposure': 1.0,
        'shot_types': 'FRONT'
    },
    
    'FLAT_ART': {
        'name': 'Flat Art/Technical',
        'description': 'Flat, even lighting for technical documentation',
        'camera_distance_factor': 2.5,
        'camera_lens': 50.0,
        'enable_dof': False,
        'dof_fstop': 8.0,
        'light_key_intensity': 5.0,
        'light_fill_intensity': 5.0,
        'light_rim_intensity': 1.0,
        'add_floor': False,
        'floor_material_color': (0.8, 0.8, 0.8),
        'use_hdri': False,
        'world_strength': 2.0,
        'enable_filmic': False,
        'exposure': 0.0,
        'shot_types': 'FRONT'
    },
    
    'ARCHITECTURAL': {
        'name': 'Architectural',
        'description': 'Wide shots for architectural visualization',
        'camera_distance_factor': 4.0,
        'camera_lens': 24.0,
        'enable_dof': False,
        'dof_fstop': 11.0,
        'light_key_intensity': 3.0,
        'light_fill_intensity': 2.0,
        'light_rim_intensity': 1.0,
        'add_floor': True,
        'floor_material_color': (0.6, 0.6, 0.6),
        'use_hdri': True,
        'world_strength': 1.5,
        'enable_filmic': True,
        'exposure': -0.5,
        'shot_types': 'ALL'
    }
}

class ALCS_OT_apply_preset(Operator):
    """Apply a preset configuration to auto setup properties"""
    bl_idname = "alcs.apply_preset"
    bl_label = "Apply Preset"
    bl_description = "Apply preset configuration"
    bl_options = {'REGISTER', 'UNDO'}
    
    preset_name: bpy.props.StringProperty(
        name="Preset Name",
        description="Name of preset to apply"
    )
    
    def execute(self, context):
        if self.preset_name not in PRESETS:
            self.report({'ERROR'}, f"Preset '{self.preset_name}' not found")
            return {'CANCELLED'}
        
        preset = PRESETS[self.preset_name]
        props = context.scene.auto_setup_props
        
        # Apply all preset values to properties
        for key, value in preset.items():
            if key in ['name', 'description']:
                continue  # Skip metadata
            
            if hasattr(props, key):
                setattr(props, key, value)
        
        self.report({'INFO'}, f"Applied preset: {preset['name']}")
        return {'FINISHED'}

def get_preset_items():
    """Get preset items for EnumProperty"""
    items = []
    for key, preset in PRESETS.items():
        items.append((key, preset['name'], preset['description']))
    return items

def apply_preset_to_props(preset_name: str, props):
    """
    Apply preset configuration to properties object.
    
    Args:
        preset_name: Name of preset to apply
        props: AutoSetupProperties instance
    """
    if preset_name not in PRESETS:
        print(f"Warning: Preset '{preset_name}' not found")
        return False
    
    preset = PRESETS[preset_name]
    
    # Apply preset values
    for key, value in preset.items():
        if key in ['name', 'description']:
            continue
        
        if hasattr(props, key):
            setattr(props, key, value)
    
    return True

def create_custom_preset(name: str, description: str, props) -> dict:
    """
    Create a custom preset from current property values.
    
    Args:
        name: Name for the custom preset
        description: Description for the preset
        props: AutoSetupProperties instance
        
    Returns:
        Dictionary containing preset configuration
    """
    preset = {
        'name': name,
        'description': description,
    }
    
    # Extract relevant properties
    property_names = [
        'camera_distance_factor', 'camera_lens', 'enable_dof', 'dof_fstop',
        'light_key_intensity', 'light_fill_intensity', 'light_rim_intensity',
        'add_floor', 'floor_material_color', 'use_hdri', 'world_strength',
        'enable_filmic', 'exposure', 'shot_types'
    ]
    
    for prop_name in property_names:
        if hasattr(props, prop_name):
            preset[prop_name] = getattr(props, prop_name)
    
    return preset

def save_custom_preset(preset: dict, filepath: str):
    """
    Save custom preset to file.
    
    Args:
        preset: Preset dictionary
        filepath: Path to save preset file
    """
    import json
    
    try:
        with open(filepath, 'w') as f:
            json.dump(preset, f, indent=2, default=str)
        return True
    except Exception as e:
        print(f"Error saving preset: {e}")
        return False

def load_custom_preset(filepath: str) -> dict:
    """
    Load custom preset from file.
    
    Args:
        filepath: Path to preset file
        
    Returns:
        Preset dictionary or None if failed
    """
    import json
    
    try:
        with open(filepath, 'r') as f:
            preset = json.load(f)
        return preset
    except Exception as e:
        print(f"Error loading preset: {e}")
        return None

def get_preset_description(preset_name: str) -> str:
    """
    Get description for a preset.
    
    Args:
        preset_name: Name of preset
        
    Returns:
        Preset description or empty string
    """
    if preset_name in PRESETS:
        return PRESETS[preset_name]['description']
    return ""

def list_available_presets() -> list:
    """
    Get list of available preset names.
    
    Returns:
        List of preset names
    """
    return list(PRESETS.keys())

def validate_preset(preset: dict) -> bool:
    """
    Validate that a preset contains required fields.
    
    Args:
        preset: Preset dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_fields = ['name', 'description']
    
    for field in required_fields:
        if field not in preset:
            return False
    
    return True