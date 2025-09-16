#!/usr/bin/env python3
"""
Headless batch runner for Auto Light Camera Setup.
Enables command-line automation for CI/CD pipelines.

Usage:
    blender --background --python batch_runner.py -- [options]

Options:
    --input-file BLEND_FILE     Input .blend file to process
    --output-dir OUTPUT_DIR     Output directory for renders
    --preset PRESET_NAME        Preset to apply (PRODUCT, CHARACTER, etc.)
    --collections COLLECTION    Collections to process (comma-separated)
    --shots SHOT_TYPES          Shot types to generate (ALL, FRONT, 3Q)
    --render                    Render shots after setup
    --config CONFIG_FILE        JSON configuration file
    --verbose                   Enable verbose output

Examples:
    # Basic setup with rendering
    blender --background scene.blend --python batch_runner.py -- --preset PRODUCT --render
    
    # Process specific collections
    blender --background scene.blend --python batch_runner.py -- --collections "Objects,Props" --shots ALL
    
    # Use configuration file
    blender --background scene.blend --python batch_runner.py -- --config config.json
"""

import bpy
import sys
import os
import argparse
import json
from pathlib import Path

# Add the add-on directory to path
addon_dir = Path(__file__).parent
if str(addon_dir) not in sys.path:
    sys.path.append(str(addon_dir))

# Import add-on modules
try:
    from . import props
    from . import presets
    from . import util_bounds
    from . import util_camera
    from . import util_lighting
    from . import util_floor
    from . import util_world
    from . import ops_batch
    from .utils import get_default_output_dir, resolve_output_path, get_timestamp
except ImportError:
    # Direct import for standalone execution
    import props
    import presets
    import util_bounds
    import util_camera
    import util_lighting
    import util_floor
    import util_world
    import ops_batch
    from utils import get_default_output_dir, resolve_output_path, get_timestamp

class BatchRunner:
    """Headless batch processing runner"""
    
    def __init__(self):
        self.verbose = False
        self.config = {}
        self.setup_props()
    
    def setup_props(self):
        """Set up property system for headless mode"""
        if not hasattr(bpy.types.Scene, 'auto_setup_props'):
            # Register properties if not already registered
            bpy.utils.register_class(props.AutoSetupProperties)
            bpy.types.Scene.auto_setup_props = bpy.props.PointerProperty(
                type=props.AutoSetupProperties
            )
    
    def log(self, message):
        """Log message if verbose mode is enabled"""
        if self.verbose:
            print(f"[BatchRunner] {message}")
    
    def load_config(self, config_file):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                self.config = json.load(f)
            self.log(f"Loaded configuration from {config_file}")
            return True
        except Exception as e:
            print(f"Error loading config file {config_file}: {e}")
            return False
    
    def apply_config_to_props(self, props_obj):
        """Apply loaded configuration to properties"""
        if not self.config:
            return
        
        # Apply camera settings
        if 'camera_settings' in self.config:
            cam_settings = self.config['camera_settings']
            for key, value in cam_settings.items():
                if hasattr(props_obj, key):
                    setattr(props_obj, key, value)
        
        # Apply lighting settings
        if 'lighting_settings' in self.config:
            light_settings = self.config['lighting_settings']
            for key, value in light_settings.items():
                if hasattr(props_obj, key):
                    setattr(props_obj, key, value)
        
        # Apply render settings
        if 'render_settings' in self.config:
            render_settings = self.config['render_settings']
            for key, value in render_settings.items():
                if hasattr(props_obj, key):
                    setattr(props_obj, key, value)
        
        # Apply world settings
        if 'world_settings' in self.config:
            world_settings = self.config['world_settings']
            for key, value in world_settings.items():
                if hasattr(props_obj, key):
                    setattr(props_obj, key, value)
        
        # Apply batch settings
        if 'batch_settings' in self.config:
            batch_settings = self.config['batch_settings']
            for key, value in batch_settings.items():
                if hasattr(props_obj, key):
                    setattr(props_obj, key, value)
    
    def process_collection(self, collection_name, props_obj, output_dir, render=False):
        """Process a single collection"""
        self.log(f"Processing collection: {collection_name}")
        
        collection = bpy.data.collections.get(collection_name)
        if not collection:
            print(f"Warning: Collection '{collection_name}' not found")
            return False
        
        # Configure properties for this collection
        props_obj.use_selection = False
        props_obj.target_collection = collection_name
        
        # Get bounds information
        bounds_info = util_bounds.get_bounds_info(props_obj)
        if not bounds_info['objects']:
            print(f"Warning: No objects found in collection '{collection_name}'")
            return False
        
        # Set up lighting
        util_lighting.setup_three_point_lighting(props_obj, bounds_info)
        self.log("Set up lighting")
        
        # Generate cameras
        if props_obj.shot_types == 'ALL':
            cameras = util_camera.generate_multi_shots(props_obj, bounds_info)
        else:
            camera = util_camera.position_camera_auto(props_obj, bounds_info, "FRONT")
            cameras = [camera]
            util_camera.set_active_camera(camera)
        
        self.log(f"Generated {len(cameras)} cameras")
        
        # Set up floor if enabled
        if props_obj.add_floor:
            util_floor.setup_floor(props_obj, bounds_info)
            self.log("Set up floor")
        
        # Set up world environment
        util_world.setup_world_environment(props_obj)
        util_world.setup_render_settings(props_obj)
        self.log("Set up world environment")
        
        # Render if requested
        if render:
            self.render_collection_shots(collection_name, cameras, output_dir)
        
        return True
    
    def render_collection_shots(self, collection_name, cameras, output_dir):
        """Render all shots for a collection"""
        collection_dir = os.path.join(output_dir, collection_name)
        os.makedirs(collection_dir, exist_ok=True)
        ts = get_timestamp()
        for camera in cameras:
            # Extract shot type from camera name
            shot_type = camera.name.split('_')[-1] if '_' in camera.name else "shot"
            
            # Generate filename
            filename = f"{collection_name}_{shot_type}_{ts}.png"
            output_path = os.path.join(collection_dir, filename)
            
            try:
                util_camera.render_camera_shot(camera, output_path)
                self.log(f"Rendered: {output_path}")
            except Exception as e:
                print(f"Error rendering {filename}: {e}")
    
    def run_batch_process(self, args):
        """Run the main batch processing"""
        self.verbose = args.verbose
        props_obj = bpy.context.scene.auto_setup_props
        
        # Load configuration if specified
        if args.config:
            if not self.load_config(args.config):
                return False
            self.apply_config_to_props(props_obj)
        
        # Apply preset if specified
        if args.preset:
            if not presets.apply_preset_to_props(args.preset, props_obj):
                print(f"Error: Invalid preset '{args.preset}'")
                return False
            self.log(f"Applied preset: {args.preset}")
        
        # Configure output directory
        output_dir = args.output_dir or get_default_output_dir(create=True)
        # Resolve and ensure exists; also store back to props for consistency
        output_dir = resolve_output_path(output_dir)
        props_obj.output_path = output_dir
        
        # Set up shot types
        if args.shots:
            props_obj.shot_types = args.shots
        
        # Get collections to process
        if args.collections:
            collection_names = [name.strip() for name in args.collections.split(',')]
        else:
            # Process all collections with mesh objects
            collection_names = ops_batch.get_collections_for_batch()
        
        if not collection_names:
            print("No collections found to process")
            return False
        
        self.log(f"Processing {len(collection_names)} collections")
        
        # Process each collection
        success_count = 0
        for collection_name in collection_names:
            try:
                if self.process_collection(collection_name, props_obj, output_dir, args.render):
                    success_count += 1
            except Exception as e:
                print(f"Error processing collection '{collection_name}': {e}")
        
        self.log(f"Successfully processed {success_count}/{len(collection_names)} collections")
        return success_count > 0

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Headless batch runner for Auto Light Camera Setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  blender --background scene.blend --python batch_runner.py -- --preset PRODUCT --render
  blender --background scene.blend --python batch_runner.py -- --collections "Objects,Props"
  blender --background scene.blend --python batch_runner.py -- --config config.json
        """
    )
    
    parser.add_argument('--output-dir', type=str, default="",
                       help='Output directory for renders (empty = user Pictures/ALCS_Renders)')
    
    parser.add_argument('--preset', type=str, choices=list(presets.PRESETS.keys()),
                       help='Preset to apply')
    
    parser.add_argument('--collections', type=str,
                       help='Collections to process (comma-separated)')
    
    parser.add_argument('--shots', type=str, choices=['ALL', 'FRONT', '3Q'],
                       default='ALL', help='Shot types to generate')
    
    parser.add_argument('--render', action='store_true',
                       help='Render shots after setup')
    
    parser.add_argument('--config', type=str,
                       help='JSON configuration file')
    
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    
    # Parse only the arguments after --
    if '--' in sys.argv:
        args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    else:
        args = parser.parse_args([])
    
    return args

def main():
    """Main entry point"""
    try:
        args = parse_arguments()
        runner = BatchRunner()
        
        if runner.run_batch_process(args):
            print("Batch processing completed successfully")
            sys.exit(0)
        else:
            print("Batch processing failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()