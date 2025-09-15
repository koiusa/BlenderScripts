"""
Core operations for Auto Light Camera Setup.
Main operators for single setup and multi-shot generation.
"""

import bpy
from bpy.types import Operator
from . import util_bounds
from . import util_camera
from . import util_lighting
from . import util_floor
from . import util_world

class ALCS_OT_auto_setup(Operator):
    """Automatically set up lighting, camera, and environment"""
    bl_idname = "alcs.auto_setup"
    bl_label = "Auto Setup"
    bl_description = "Automatically configure lighting, camera, and environment"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.auto_setup_props
        
        try:
            # Validate targets
            if not util_bounds.validate_targets(props):
                self.report({'ERROR'}, "No valid target objects found")
                return {'CANCELLED'}
            
            # Get bounds information
            bounds_info = util_bounds.get_bounds_info(props)
            
            # Set up lighting
            util_lighting.setup_three_point_lighting(props, bounds_info)
            
            # Set up camera
            camera = util_camera.position_camera_auto(props, bounds_info, "FRONT")
            util_camera.set_active_camera(camera)
            
            # Set up floor if enabled
            if props.add_floor:
                util_floor.setup_floor(props, bounds_info)
            
            # Set up world environment
            util_world.setup_world_environment(props)
            
            # Configure render settings
            util_world.setup_render_settings(props)
            
            self.report({'INFO'}, "Auto setup completed successfully")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Auto setup failed: {str(e)}")
            return {'CANCELLED'}

class ALCS_OT_generate_multi_shots(Operator):
    """Generate multiple camera shots"""
    bl_idname = "alcs.generate_multi_shots"
    bl_label = "Generate Multi-Shots"
    bl_description = "Generate multiple camera angles and optionally render them"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.auto_setup_props
        
        try:
            # Validate targets
            if not util_bounds.validate_targets(props):
                self.report({'ERROR'}, "No valid target objects found")
                return {'CANCELLED'}
            
            # Get bounds information
            bounds_info = util_bounds.get_bounds_info(props)
            
            # Generate multiple camera shots
            cameras = util_camera.generate_multi_shots(props, bounds_info)
            
            if not cameras:
                self.report({'ERROR'}, "No cameras were generated")
                return {'CANCELLED'}
            
            # Render shots if requested
            if props.render_shots:
                self.render_multiple_shots(context, cameras, props)
            
            self.report({'INFO'}, f"Generated {len(cameras)} camera shots")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Multi-shot generation failed: {str(e)}")
            return {'CANCELLED'}
    
    def render_multiple_shots(self, context, cameras, props):
        """Render all generated camera shots"""
        import os
        
        base_path = bpy.path.abspath(props.output_path)
        if not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)
        
        for i, camera in enumerate(cameras):
            # Extract shot type from camera name
            shot_type = camera.name.split('_')[-1] if '_' in camera.name else f"shot_{i+1}"
            
            # Generate output filename
            filename = f"shot_{shot_type}.png"
            output_path = os.path.join(base_path, filename)
            
            # Render shot
            try:
                util_camera.render_camera_shot(camera, output_path)
                print(f"Rendered shot: {output_path}")
            except Exception as e:
                print(f"Failed to render shot {shot_type}: {e}")

class ALCS_OT_cleanup_auto_objects(Operator):
    """Clean up all auto-generated objects"""
    bl_idname = "alcs.cleanup_auto_objects"
    bl_label = "Cleanup Auto Objects"
    bl_description = "Remove all auto-generated cameras, lights, and other objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            # Remove auto-generated objects
            objects_to_remove = []
            for obj in bpy.context.scene.objects:
                if obj.name.startswith("AutoSetup_"):
                    objects_to_remove.append(obj)
            
            for obj in objects_to_remove:
                bpy.data.objects.remove(obj, do_unlink=True)
            
            # Clean up track targets
            track_targets = []
            for obj in bpy.context.scene.objects:
                if obj.name.endswith("_TrackTarget"):
                    track_targets.append(obj)
            
            for obj in track_targets:
                bpy.data.objects.remove(obj, do_unlink=True)
            
            # Reset world to default
            util_world.reset_world_to_default()
            
            self.report({'INFO'}, f"Cleaned up {len(objects_to_remove)} auto-generated objects")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Cleanup failed: {str(e)}")
            return {'CANCELLED'}

class ALCS_OT_focus_camera_on_selection(Operator):
    """Focus active camera on selected objects"""
    bl_idname = "alcs.focus_camera_on_selection"
    bl_label = "Focus on Selection"
    bl_description = "Point active camera at selected objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            if not context.selected_objects:
                self.report({'ERROR'}, "No objects selected")
                return {'CANCELLED'}
            
            camera = context.scene.camera
            if not camera or camera.type != 'CAMERA':
                self.report({'ERROR'}, "No active camera in scene")
                return {'CANCELLED'}
            
            # Calculate center of selected objects
            props = context.scene.auto_setup_props
            props.use_selection = True  # Temporarily use selection
            
            bounds_info = util_bounds.get_bounds_info(props)
            center = bounds_info['center']
            
            # Point camera at center
            util_camera.point_camera_at_target(camera, center)
            
            self.report({'INFO'}, "Camera focused on selection")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Focus operation failed: {str(e)}")
            return {'CANCELLED'}

class ALCS_OT_quick_render_current(Operator):
    """Quick render from current camera"""
    bl_idname = "alcs.quick_render_current"
    bl_label = "Quick Render"
    bl_description = "Render current view to output path"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        try:
            props = context.scene.auto_setup_props
            camera = context.scene.camera
            
            if not camera:
                self.report({'ERROR'}, "No active camera in scene")
                return {'CANCELLED'}
            
            # Generate output path
            import os
            import time
            
            base_path = bpy.path.abspath(props.output_path)
            if not os.path.exists(base_path):
                os.makedirs(base_path, exist_ok=True)
            
            timestamp = int(time.time())
            filename = f"quick_render_{timestamp}.png"
            output_path = os.path.join(base_path, filename)
            
            # Render
            util_camera.render_camera_shot(camera, output_path)
            
            self.report({'INFO'}, f"Rendered to: {filename}")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Render failed: {str(e)}")
            return {'CANCELLED'}

class ALCS_OT_create_studio_setup(Operator):
    """Create a more advanced studio lighting setup"""
    bl_idname = "alcs.create_studio_setup"
    bl_label = "Studio Setup"
    bl_description = "Create advanced studio lighting with multiple area lights"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.auto_setup_props
        
        try:
            # Validate targets
            if not util_bounds.validate_targets(props):
                self.report({'ERROR'}, "No valid target objects found")
                return {'CANCELLED'}
            
            # Get bounds information
            bounds_info = util_bounds.get_bounds_info(props)
            
            # Set up studio lighting
            util_lighting.create_studio_lighting(props, bounds_info)
            
            # Set up studio world
            util_world.setup_studio_world(props)
            
            # Configure render settings for studio
            util_world.setup_render_settings(props)
            
            self.report({'INFO'}, "Studio setup completed")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Studio setup failed: {str(e)}")
            return {'CANCELLED'}