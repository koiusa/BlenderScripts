param(
    [string]$BlenderExe = "C:\\Program Files (x86)\\Steam\\steamapps\\common\\Blender\\blender.exe",
    # Path to the add-on folder (should be the folder that contains __init__.py)
    [string]$AddonFolder = "..\", 
    # Output zip path (default one level up from tools)
    [string]$ZipOut = "..\\auto_light_camera_setup.zip",
    # Run Blender with factory startup to avoid other addons interfering
    [switch]$FactoryStartup
)

$ErrorActionPreference = 'Stop'

# Resolve paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..")
# Resolve $AddonFolder relative to the script directory
$AddonRoot = Resolve-Path (Join-Path $ScriptDir $AddonFolder)
$ZipPath = Resolve-Path -LiteralPath (Join-Path $RepoRoot $ZipOut) -ErrorAction SilentlyContinue
if ($ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}
$ZipPath = Join-Path $RepoRoot $ZipOut

Write-Host "Zipping add-on from: $AddonRoot"

# Ensure __init__.py exists (sanity check)
if (-not (Test-Path (Join-Path $AddonRoot "__init__.py"))) {
    Write-Error "__init__.py not found in $AddonRoot. Run this from the add-on folder."
}

# Create ZIP. We include the folder itself so the zip root contains 'auto_light_camera_setup' directory.
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path $AddonRoot -DestinationPath $ZipPath -Force

Write-Host "ZIP created: $ZipPath"

# Blender install script (Python code) to install/enable the add-on
$InstallPy = @'
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
zip_path = Path(r"{ZIP}")
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
'@

$InstallPyFile = Join-Path $RepoRoot "tools\\install_addon_temp.py"
$InstallPyContent = $InstallPy.Replace("{ZIP}", $ZipPath.Replace("\\", "\\\\"))
Set-Content -LiteralPath $InstallPyFile -Value $InstallPyContent -Encoding UTF8

Write-Host "Running Blender to install the add-on..."
$argsList = @()
if ($FactoryStartup) { $argsList += '--factory-startup' }
$argsList += @('-b','-P',"$InstallPyFile")
& "$BlenderExe" @argsList | Write-Host

Write-Host "Done. You can remove the temp script if you like: $InstallPyFile"
