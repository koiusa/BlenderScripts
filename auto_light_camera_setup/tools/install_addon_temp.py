import bpy, sys
from pathlib import Path

zip_path = Path(r"D:\Work\koiusa\BlenderScripts\auto_light_camera_setup\..\\\\auto_light_camera_setup.zip")
print("Installing add-on:", zip_path)
# Install or upgrade (do not rely on default_set)
bpy.ops.preferences.addon_install(filepath=str(zip_path), overwrite=True)

# Enable by exact module name (matches folder name inside the zip)
MODULE = 'auto_light_camera_setup'
try:
    bpy.ops.preferences.addon_enable(module=MODULE)
    print("Enabled:", MODULE)
except Exception as e:
    print("Enable failed:", MODULE, e)

# Save preferences so it's enabled next launch
try:
    bpy.ops.wm.save_userpref()
except Exception:
    pass
