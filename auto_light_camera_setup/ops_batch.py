"""
Batch operations for Auto Light Camera Setup.
Handles processing multiple collections and batch rendering.
"""

import bpy
import os
from bpy.types import Operator
from . import util_bounds
from . import util_camera
from . import util_lighting
from . import util_floor
from . import util_world

class ALCS_OT_batch_process(Operator):
    """Process multiple collections in batch mode"""
    bl_idname = "alcs.batch_process"
    bl_label = "Batch Process Collections"
    bl_description = "Process multiple collections with auto setup and optional rendering"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.auto_setup_props
        
        try:
            # Get collections to process
            collections = self.get_target_collections(props)
            
            if not collections:
                self.report({'ERROR'}, "No collections found to process")
                return {'CANCELLED'}
            
            processed_count = 0
            failed_count = 0
            
            # Process each collection
            for collection in collections:
                try:
                    self.process_collection(context, collection, props)
                    processed_count += 1
                    print(f"Processed collection: {collection.name}")
                    
                except Exception as e:
                    failed_count += 1
                    print(f"Failed to process collection {collection.name}: {e}")
            
            message = f"Processed {processed_count} collections"
            if failed_count > 0:
                message += f", {failed_count} failed"
            
            self.report({'INFO'}, message)
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Batch processing failed: {str(e)}")
            return {'CANCELLED'}
    
    def get_target_collections(self, props):
        """Get list of collections to process based on filter"""
        collections = []
        
        for collection in bpy.data.collections:
            # Skip if collection has no objects
            if not self.collection_has_mesh_objects(collection):
                continue
            
            # Apply filter if specified
            if props.collection_filter:
                if props.collection_filter.lower() not in collection.name.lower():
                    continue
            
            collections.append(collection)
        
        return collections
    
    def collection_has_mesh_objects(self, collection):
        """Check if collection contains mesh objects"""
        for obj in collection.objects:
            if obj.type == 'MESH':
                return True
        
        # Check child collections
        for child_collection in collection.children:
            if self.collection_has_mesh_objects(child_collection):
                return True
        
        return False
    
    def process_collection(self, context, collection, props):
        """Process a single collection"""
        # Store original settings
        original_use_selection = props.use_selection
        original_target_collection = props.target_collection
        
        try:
            # Configure to use this collection
            props.use_selection = False
            props.target_collection = collection.name
            
            # Get bounds info for this collection
            bounds_info = util_bounds.get_bounds_info(props)
            
            if not bounds_info['objects']:
                print(f"No objects found in collection: {collection.name}")
                return
            
            # Set up lighting
            util_lighting.setup_three_point_lighting(props, bounds_info)
            
            # Generate cameras if multi-shot is enabled
            if props.shot_types != 'FRONT':
                cameras = util_camera.generate_multi_shots(props, bounds_info)
            else:
                camera = util_camera.position_camera_auto(props, bounds_info, "FRONT")
                cameras = [camera]
                util_camera.set_active_camera(camera)
            
            # Set up floor if enabled
            if props.add_floor:
                util_floor.setup_floor(props, bounds_info)
            
            # Set up world environment
            util_world.setup_world_environment(props)
            
            # Render if requested
            if props.render_per_collection:
                self.render_collection_shots(context, collection, cameras, props)
            
        finally:
            # Restore original settings
            props.use_selection = original_use_selection
            props.target_collection = original_target_collection
    
    def render_collection_shots(self, context, collection, cameras, props):
        """Render all shots for a collection"""
        base_path = bpy.path.abspath(props.output_path)
        collection_path = os.path.join(base_path, collection.name)
        
        # Create collection directory
        os.makedirs(collection_path, exist_ok=True)
        
        for camera in cameras:
            # Extract shot type from camera name
            shot_type = camera.name.split('_')[-1] if '_' in camera.name else "shot"
            
            # Generate filename
            filename = f"{collection.name}_{shot_type}.png"
            output_path = os.path.join(collection_path, filename)
            
            try:
                util_camera.render_camera_shot(camera, output_path)
                print(f"Rendered: {output_path}")
            except Exception as e:
                print(f"Failed to render {filename}: {e}")

class ALCS_OT_batch_render_all_cameras(Operator):
    """Render from all cameras in the scene"""
    bl_idname = "alcs.batch_render_all_cameras"
    bl_label = "Render All Cameras"
    bl_description = "Render from all cameras in the scene"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.auto_setup_props
        
        try:
            # Get all cameras in scene
            cameras = [obj for obj in context.scene.objects if obj.type == 'CAMERA']
            
            if not cameras:
                self.report({'ERROR'}, "No cameras found in scene")
                return {'CANCELLED'}
            
            # Set up output directory
            base_path = bpy.path.abspath(props.output_path)
            render_path = os.path.join(base_path, "all_cameras")
            os.makedirs(render_path, exist_ok=True)
            
            rendered_count = 0
            
            for camera in cameras:
                filename = f"{camera.name}.png"
                output_path = os.path.join(render_path, filename)
                
                try:
                    util_camera.render_camera_shot(camera, output_path)
                    rendered_count += 1
                    print(f"Rendered camera: {camera.name}")
                except Exception as e:
                    print(f"Failed to render camera {camera.name}: {e}")
            
            self.report({'INFO'}, f"Rendered {rendered_count} cameras")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Batch render failed: {str(e)}")
            return {'CANCELLED'}

class ALCS_OT_setup_collection_shots(Operator):
    """Set up shots for specific collection"""
    bl_idname = "alcs.setup_collection_shots"
    bl_label = "Setup Collection Shots"
    bl_description = "Set up lighting and cameras for a specific collection"
    bl_options = {'REGISTER', 'UNDO'}
    
    collection_name: bpy.props.StringProperty(
        name="Collection Name",
        description="Name of collection to set up"
    )
    
    def execute(self, context):
        props = context.scene.auto_setup_props
        
        try:
            if not self.collection_name:
                self.report({'ERROR'}, "No collection name specified")
                return {'CANCELLED'}
            
            collection = bpy.data.collections.get(self.collection_name)
            if not collection:
                self.report({'ERROR'}, f"Collection '{self.collection_name}' not found")
                return {'CANCELLED'}
            
            # Process this specific collection
            self.process_collection(context, collection, props)
            
            self.report({'INFO'}, f"Set up shots for collection: {self.collection_name}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Collection setup failed: {str(e)}")
            return {'CANCELLED'}
    
    def process_collection(self, context, collection, props):
        """Process a single collection (same as batch process)"""
        # Store original settings
        original_use_selection = props.use_selection
        original_target_collection = props.target_collection
        
        try:
            # Configure to use this collection
            props.use_selection = False
            props.target_collection = collection.name
            
            # Get bounds info
            bounds_info = util_bounds.get_bounds_info(props)
            
            if not bounds_info['objects']:
                raise Exception(f"No objects found in collection: {collection.name}")
            
            # Set up lighting
            util_lighting.setup_three_point_lighting(props, bounds_info)
            
            # Generate cameras
            cameras = util_camera.generate_multi_shots(props, bounds_info)
            
            # Set up floor if enabled
            if props.add_floor:
                util_floor.setup_floor(props, bounds_info)
            
            # Set up world environment
            util_world.setup_world_environment(props)
            
            # Configure render settings
            util_world.setup_render_settings(props)
            
        finally:
            # Restore original settings
            props.use_selection = original_use_selection
            props.target_collection = original_target_collection

class ALCS_OT_export_batch_config(Operator):
    """Export batch processing configuration"""
    bl_idname = "alcs.export_batch_config"
    bl_label = "Export Batch Config"
    bl_description = "Export current settings as batch configuration file"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: bpy.props.StringProperty(
        name="File Path",
        description="Path to save configuration file",
        subtype='FILE_PATH'
    )
    
    def execute(self, context):
        try:
            props = context.scene.auto_setup_props
            
            # Create configuration dictionary
            config = {
                'camera_settings': {
                    'distance_factor': props.camera_distance_factor,
                    'lens': props.camera_lens,
                    'enable_dof': props.enable_dof,
                    'dof_fstop': props.dof_fstop,
                },
                'lighting_settings': {
                    'key_intensity': props.light_key_intensity,
                    'fill_intensity': props.light_fill_intensity,
                    'rim_intensity': props.light_rim_intensity,
                },
                'render_settings': {
                    'enable_filmic': props.enable_filmic,
                    'exposure': props.exposure,
                    'shot_types': props.shot_types,
                },
                'world_settings': {
                    'use_hdri': props.use_hdri,
                    'hdri_path': props.hdri_path,
                    'hdri_strength': props.hdri_strength,
                    'world_strength': props.world_strength,
                },
                'batch_settings': {
                    'collection_filter': props.collection_filter,
                    'render_per_collection': props.render_per_collection,
                    'output_path': props.output_path,
                }
            }
            
            # Save configuration
            import json
            with open(self.filepath, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.report({'INFO'}, f"Configuration exported to: {self.filepath}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Export failed: {str(e)}")
            return {'CANCELLED'}
    
    def invoke(self, context, event):
        # Set default filename
        import time
        timestamp = int(time.time())
        self.filepath = f"//batch_config_{timestamp}.json"
        
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

def get_collections_for_batch(collection_filter: str = "") -> list:
    """
    Get list of collections suitable for batch processing.
    
    Args:
        collection_filter: Optional filter string
        
    Returns:
        List of collection names
    """
    collections = []
    
    for collection in bpy.data.collections:
        # Check if collection has mesh objects
        has_mesh = False
        for obj in collection.objects:
            if obj.type == 'MESH':
                has_mesh = True
                break
        
        if not has_mesh:
            continue
        
        # Apply filter
        if collection_filter and collection_filter.lower() not in collection.name.lower():
            continue
        
        collections.append(collection.name)
    
    return collections