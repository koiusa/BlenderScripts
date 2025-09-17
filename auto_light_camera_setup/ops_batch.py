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
from . import util_rig
from .utils import resolve_output_path, get_timestamp
import subprocess
import tempfile
from pathlib import Path

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
        # If a specific batch target collection is chosen, prioritize it
        if hasattr(props, 'batch_target_collection') and props.batch_target_collection:
            chosen = bpy.data.collections.get(props.batch_target_collection)
            return [chosen] if chosen else []

        collections = []
        for collection in bpy.data.collections:
            # Skip if collection has no (direct or nested) mesh objects
            if not self.collection_has_mesh_objects(collection):
                continue
            # Apply filter if specified (case-insensitive, substring)
            if props.collection_filter and props.collection_filter.lower() not in collection.name.lower():
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
            
            # Parent under locator for unified manipulation
            util_rig.parent_autosetup_objects_to_locator(bounds_info)

            # Render if requested
            if props.render_per_collection:
                self.render_collection_shots(context, collection, cameras, props)
            
        finally:
            # Restore original settings
            props.use_selection = original_use_selection
            props.target_collection = original_target_collection
    
    def render_collection_shots(self, context, collection, cameras, props):
        """Render all shots for a collection"""
        base_path = resolve_output_path(props.output_path)
        collection_path = os.path.join(base_path, collection.name)
        
        # Create collection directory
        os.makedirs(collection_path, exist_ok=True)
        ts = get_timestamp()
        for camera in cameras:
            # Extract shot type from camera name
            shot_type = camera.name.split('_')[-1] if '_' in camera.name else "shot"
            
            # Generate filename
            filename = f"{collection.name}_{shot_type}_{ts}.png"
            output_path = os.path.join(collection_path, filename)
            
            try:
                util_camera.render_camera_shot(camera, output_path)
                print(f"Rendered: {output_path}")
            except Exception as e:
                print(f"Failed to render {filename}: {e}")

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

            # Parent under locator for unified manipulation
            util_rig.parent_autosetup_objects_to_locator(bounds_info)
            
        finally:
            # Restore original settings
            props.use_selection = original_use_selection
            props.target_collection = original_target_collection