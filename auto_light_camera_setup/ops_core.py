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
from . import util_rig
from . import util_collections
from .utils import resolve_output_path, get_timestamp
from .debug_utils import debugger, verify_rig_consistency, get_debug_report

class ALCS_OT_auto_setup(Operator):
    """Automatically set up lighting, camera, and environment"""
    bl_idname = "alcs.auto_setup"
    bl_label = "Auto Setup"
    bl_description = "Automatically configure lighting, camera, and environment"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.auto_setup_props
        
        debugger.info("=== Auto Setup Started ===")
        # Pre-execution rig state verification（シンプル化）
        initial_state = verify_rig_consistency("auto_setup_start")
        
        try:
            # Ensure collections exist up-front and sync depsgraph
            util_collections.ensure_autosetup_collections()
            try:
                bpy.context.view_layer.update()
            except Exception:
                pass
            # Validate targets
            if not util_bounds.validate_targets(props):
                self.report({'ERROR'}, "No valid target objects found")
                return {'CANCELLED'}
            
            # Get bounds information
            bounds_info = util_bounds.get_bounds_info(props)
            debugger.info(f"Bounds info: center={bounds_info.get('center')}, max_dimension={bounds_info.get('max_dimension')}")

            # Lighting
            util_lighting.setup_three_point_lighting(props, bounds_info)
            try:
                bpy.context.view_layer.update()
            except Exception:
                pass

            # Camera(s)
            if props.shot_types == 'FRONT':
                camera = util_camera.position_camera_auto(props, bounds_info, "FRONT")
                util_camera.set_active_camera(camera)
            else:
                cameras = util_camera.generate_multi_shots(props, bounds_info)
                if cameras:
                    util_camera.set_active_camera(cameras[0])
            try:
                bpy.context.view_layer.update()
            except Exception:
                pass
            
            # Floor
            if props.add_floor:
                util_floor.setup_floor(props, bounds_info)
            
            # World and render settings
            util_world.setup_world_environment(props)
            util_world.setup_render_settings(props)

            # Parent under locator
            util_rig.parent_autosetup_objects_to_locator(bounds_info)
            
            # Post-execution rig state verification
            final_state = verify_rig_consistency("auto_setup_end")
            
            # Generate debug report if there are inconsistencies
            if not initial_state or not final_state:
                debugger.warning("Rig consistency issues detected. Generating debug report.")
                report = get_debug_report()
                debugger.info(f"Debug report length: {len(report)} characters")
            
            debugger.info("=== Auto Setup Completed ===")
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
        
        debugger.info("=== Multi-Shot Generation Started ===")
        
        # Pre-execution rig state verification
        initial_state = verify_rig_consistency("multi_shot_start")
        
        try:
            # Validate targets
            if not util_bounds.validate_targets(props):
                self.report({'ERROR'}, "No valid target objects found")
                return {'CANCELLED'}
            
            # Get bounds information
            bounds_info = util_bounds.get_bounds_info(props)
            debugger.info(f"Multi-shot bounds: center={bounds_info.get('center')}, max_dimension={bounds_info.get('max_dimension')}")
            
            # Generate multiple camera shots
            cameras = util_camera.generate_multi_shots(props, bounds_info)
            
            if not cameras:
                self.report({'ERROR'}, "No cameras were generated")
                return {'CANCELLED'}
            
            # Render shots if requested
            if props.render_shots:
                self.render_multiple_shots(context, cameras, props)

            # Ensure cameras (and lights if present) are parented under the locator
            util_rig.parent_autosetup_objects_to_locator(bounds_info)
            
            # Post-execution rig state verification
            final_state = verify_rig_consistency("multi_shot_end")
            
            # Generate debug report if there are inconsistencies
            if not initial_state or not final_state:
                debugger.warning("Rig consistency issues detected during multi-shot generation.")
                report = get_debug_report()
                debugger.info(f"Multi-shot debug report length: {len(report)} characters")
            
            debugger.info("=== Multi-Shot Generation Completed ===")
            self.report({'INFO'}, f"Generated {len(cameras)} camera shots")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"Multi-shot generation failed: {str(e)}")
            return {'CANCELLED'}
    
    def render_multiple_shots(self, context, cameras, props):
        """Render all generated camera shots"""
        import os

        base_path = resolve_output_path(props.output_path)
        if not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)

        ts = get_timestamp()
        for i, camera in enumerate(cameras):
            # Extract shot type from camera name
            shot_type = camera.name.split('_')[-1] if '_' in camera.name else f"shot_{i+1}"
            
            # Generate output filename
            filename = f"shot_{shot_type}_{ts}.png"
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

class ALCS_OT_reload_addon(Operator):
    """Reload this add-on without restarting Blender"""
    bl_idname = "alcs.reload_addon"
    bl_label = "Reload Add-on"
    bl_description = "Reload Auto Light Camera Setup in-place (unregister -> reload modules -> register)"
    bl_options = {'REGISTER'}

    def execute(self, context):
        import sys
        import importlib
        try:
            # Package name (folder name of the add-on)
            pkg_name = __name__.split('.')[0]

            # Unregister if available (ignore failures)
            pkg = sys.modules.get(pkg_name)
            try:
                if pkg and hasattr(pkg, 'unregister'):
                    pkg.unregister()
            except Exception:
                pass

            # Reload submodules (deepest first)
            module_names = [m for m in list(sys.modules.keys()) if m == pkg_name or m.startswith(pkg_name + ".")]
            module_names.sort(key=len, reverse=True)
            for mod_name in module_names:
                mod = sys.modules.get(mod_name)
                if mod is None:
                    continue
                try:
                    importlib.reload(mod)
                except Exception as e:
                    print(f"[ALCS] Failed to reload {mod_name}: {e}")

            # Ensure top-level is imported and register again
            pkg = sys.modules.get(pkg_name)
            if pkg is None:
                pkg = importlib.import_module(pkg_name)
            if hasattr(pkg, 'register'):
                pkg.register()

            self.report({'INFO'}, "Add-on reloaded successfully")
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Reload failed: {e}")
            return {'CANCELLED'}

