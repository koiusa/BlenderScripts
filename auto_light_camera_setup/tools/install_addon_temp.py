import bpy, sys, importlib
from pathlib import Path

MODULE = 'auto_light_camera_setup'

# 1) Disable if already enabled
try:
    if MODULE in bpy.context.preferences.addons:
        bpy.ops.preferences.addon_disable(module=MODULE)
        print('Disabled existing module:', MODULE)
except Exception as e:
    print('Disable failed:', e)

# 2) Purge module caches to avoid stale code
purged = []
for key in list(sys.modules.keys()):
    if key == MODULE or key.startswith(MODULE + '.'):
        sys.modules.pop(key, None)
        purged.append(key)
if purged:
    print('Purged modules:', purged)
importlib.invalidate_caches()

# 3) Install or upgrade from zip
zip_path = Path(r"D:\Work\koiusa\BlenderScripts\auto_light_camera_setup\..\\\\auto_light_camera_setup.zip")
print("Installing add-on:", zip_path)
bpy.ops.preferences.addon_install(filepath=str(zip_path), overwrite=True)

# 4) Enable freshly
try:
    bpy.ops.preferences.addon_enable(module=MODULE)
    print("Enabled:", MODULE)
except Exception as e:
    print("Enable failed:", MODULE, e)

# 5) Save preferences so it's enabled next launch
try:
    bpy.ops.wm.save_userpref()
except Exception:
    pass
