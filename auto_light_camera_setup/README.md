# Auto Light Camera Setup - Blender Add-on

A comprehensive Blender 4.x add-on for automatic lighting, camera positioning, multi-shot generation, and batch processing. Designed for product visualization, character rendering, and automated pipeline workflows.

## Features

### 🎬 Automatic Setup
- **Bounds Detection**: Automatically detects object bounds from selection, specific collection, or entire scene
- **Three-Point Lighting**: Professional key/fill/rim lighting with configurable intensities
- **Camera Positioning**: Auto-positions camera based on target bounds with distance factor control
- **Floor Generation**: Optional floor plane with customizable materials
- **Environment Lighting**: HDRI support or basic world configuration

### 🎯 Multi-Shot Generation
- **Front View**: Standard front-facing shot
- **Three-Quarter Views**: Left and right 3/4 angle shots
- **Top View**: Overhead shot for plan views
- **Low Angle**: Dynamic low-angle perspective
- **Custom Configurations**: Extensible shot system

### 🔄 Batch Processing
- **Collection Processing**: Automatically process multiple collections
- **Filtering**: Filter collections by name patterns
- **Batch Rendering**: Render all shots for each collection
- **Headless Support**: Command-line automation for CI/CD

### 🎨 Presets System
- **Product Photography**: Optimized for product visualization
- **Character/Portrait**: Ideal for character and portrait rendering
- **Small Props**: Close-up shots for detailed objects
- **Flat Art/Technical**: Even lighting for technical documentation
- **Architectural**: Wide shots for architectural visualization

### ⚙️ Advanced Features
- **Depth of Field**: Automatic DOF configuration with F-Stop control
- **Filmic Color Management**: Professional color pipeline setup
- **Exposure Control**: Scene exposure adjustment
- **Studio Lighting**: Advanced multi-area light setup
- **Material Configuration**: Automatic material setup for floors

## Installation

1. Download the `auto_light_camera_setup` folder
2. Copy to your Blender add-ons directory:
   - **Windows**: `%APPDATA%\Blender Foundation\Blender\4.x\scripts\addons\`
   - **macOS**: `~/Library/Application Support/Blender/4.x/scripts/addons/`
   - **Linux**: `~/.config/blender/4.x/scripts/addons/`
3. Open Blender and go to Edit > Preferences > Add-ons
4. Search for "Auto Light Camera Setup" and enable it
5. The panel will appear in the 3D Viewport sidebar under "Auto Setup"

## Quick Start

### Basic Usage
1. **Select Target Objects** or choose a collection
2. **Choose a Preset** that matches your scene type
3. **Click "Auto Setup"** to configure lighting, camera, and environment
4. **Use "Generate Multi-Shots"** for multiple camera angles
5. **Enable "Render Shots"** to automatically render all generated views

### Preset Guidelines
- **Product**: Use for commercial product shots, jewelry, electronics
- **Character**: Best for character models, portraits, figurines
- **Small Prop**: Ideal for detailed close-ups, small objects
- **Flat Art**: Perfect for technical drawings, flat artwork
- **Architectural**: For buildings, rooms, large environments

## Interface Guide

### Main Panel Sections

#### Presets
Quick-access buttons for common setup configurations:
- Product, Character, Small Prop, Flat Art, Architectural

#### Target Configuration
- **Use Selection**: Target currently selected objects
- **Target Collection**: Specify a collection to process

#### Main Controls
- **Auto Setup**: Complete automatic setup
- **Generate Multi-Shots**: Create multiple camera angles
- **Studio Setup**: Advanced lighting with area lights
- **Cleanup**: Remove all auto-generated objects

#### Camera Settings
- **Distance Factor**: Multiplier for camera distance (1.0-10.0)
- **Lens (mm)**: Camera focal length (0 = keep current)
- **Enable DOF**: Depth of field with F-Stop control

#### Lighting Settings
- **Key Light**: Main light intensity
- **Fill Light**: Secondary light intensity
- **Rim Light**: Edge/back light intensity

#### Environment
- **Add Floor**: Generate floor plane with material
- **Use HDRI**: Environment lighting from HDRI file
- **World Strength**: Basic world background intensity
- **Filmic/Exposure**: Color management settings

#### Multi-Shot & Batch
- **Shot Types**: ALL, FRONT, 3Q (three-quarter views)
- **Render Shots**: Automatically render generated cameras
- **Batch Mode**: Process multiple collections
- **Output Path**: Base directory for rendered images

## Batch Processing

### Interactive Batch Mode
1. Enable "Batch Mode" in the panel
2. Set collection filter (optional)
3. Configure output path
4. Click "Batch Process Collections"

### Collections will be processed with:
- Automatic lighting setup
- Multi-shot camera generation
- Optional floor and environment
- Per-collection rendering (if enabled)

## Headless/CLI Usage

The `batch_runner.py` script enables command-line automation:

### Basic Usage
```bash
blender --background scene.blend --python batch_runner.py -- --preset PRODUCT --render
```

### Advanced Usage
```bash
# Process specific collections
blender --background scene.blend --python batch_runner.py -- \
  --collections "Objects,Props,Furniture" \
  --shots ALL \
  --output-dir "/path/to/renders" \
  --render

# Use configuration file
blender --background scene.blend --python batch_runner.py -- \
  --config config.json \
  --verbose
```

### Command Line Options
- `--preset`: Apply preset (PRODUCT, CHARACTER, SMALL_PROP, FLAT_ART, ARCHITECTURAL)
- `--collections`: Comma-separated collection names
- `--shots`: Shot types (ALL, FRONT, 3Q)
- `--render`: Render shots after setup
- `--output-dir`: Output directory for renders
- `--config`: JSON configuration file
- `--verbose`: Enable detailed logging

### Configuration File Format
```json
{
  "camera_settings": {
    "distance_factor": 2.5,
    "lens": 50.0,
    "enable_dof": true,
    "dof_fstop": 5.6
  },
  "lighting_settings": {
    "key_intensity": 8.0,
    "fill_intensity": 3.0,
    "rim_intensity": 4.0
  },
  "render_settings": {
    "enable_filmic": true,
    "exposure": 0.5,
    "shot_types": "ALL"
  },
  "world_settings": {
    "use_hdri": true,
    "hdri_path": "/path/to/studio.hdr",
    "hdri_strength": 1.0
  },
  "batch_settings": {
    "collection_filter": "",
    "render_per_collection": true,
    "output_path": "//renders/"
  }
}
```

## Technical Details

### Architecture
The add-on is built with a modular architecture:

- **`props.py`**: Property definitions and UI data
- **`presets.py`**: Preset configurations and management
- **`util_bounds.py`**: Object bounds detection and calculation
- **`util_camera.py`**: Camera positioning and multi-shot generation
- **`util_lighting.py`**: Three-point and studio lighting setup
- **`util_floor.py`**: Floor plane creation and materials
- **`util_world.py`**: World/HDRI environment configuration
- **`ops_core.py`**: Main operators for setup and generation
- **`ops_batch.py`**: Batch processing and collection iteration
- **`ui_panel.py`**: Blender UI panel and interface
- **`batch_runner.py`**: Headless CLI automation script

### Object Naming Convention
Auto-generated objects use the prefix `AutoSetup_`:
- Cameras: `AutoSetup_Camera_FRONT`, `AutoSetup_Camera_3Q_L`, etc.
- Lights: `AutoSetup_KeyLight`, `AutoSetup_FillLight`, `AutoSetup_RimLight`
- Floor: `AutoSetup_Floor`
- Track Targets: `AutoSetup_Camera_FRONT_TrackTarget`

### Bounds Detection Priority
1. **Selected Objects** (if "Use Selection" enabled)
2. **Specified Collection** (if collection name provided)
3. **All Visible Mesh Objects** (fallback)

## Workflows

### Product Photography Workflow
1. Import/create product model
2. Apply "Product" preset
3. Adjust camera distance and lighting intensity
4. Enable floor with white material
5. Generate multi-shots (ALL)
6. Render shots for different angles

### Character Rendering Workflow
1. Load character model
2. Apply "Character" preset
3. Enable DOF with appropriate F-Stop
4. Set up HDRI environment lighting
5. Generate 3/4 views
6. Focus camera on character face/center

### Batch Production Workflow
1. Organize models in collections
2. Configure batch settings
3. Set output directory structure
4. Run batch processing
5. Review generated renders
6. Export configuration for reuse

## Troubleshooting

### Common Issues

**No target objects found**
- Ensure objects are selected or collection contains mesh objects
- Check that objects are visible in the viewport

**Camera too close/far**
- Adjust "Distance Factor" in camera settings
- Check object bounds and scale

**Lighting too bright/dim**
- Modify individual light intensities
- Try different presets for your object type
- Adjust world/HDRI strength

**HDRI not loading**
- Verify HDRI file path exists
- Check file format (HDR, EXR supported)
- Ensure file is not corrupted

**Batch processing fails**
- Check collection names and filters
- Verify output directory permissions
- Enable verbose mode for detailed error messages

### Performance Tips
- Use "Cleanup" to remove unused auto objects
- Process collections individually for large scenes
- Use lower sample counts for preview renders
- Consider HDRI file size for memory usage

## Extending the Add-on

### Adding Custom Presets
```python
# In presets.py, add to PRESETS dictionary
'CUSTOM_PRESET': {
    'name': 'Custom Setup',
    'description': 'Your custom configuration',
    'camera_distance_factor': 3.0,
    'light_key_intensity': 10.0,
    # ... other settings
}
```

### Custom Shot Types
Extend the shot generation in `util_camera.py`:
```python
def position_camera_auto(props, bounds_info, shot_type="FRONT"):
    # Add new shot type
    elif shot_type == "CUSTOM_ANGLE":
        # Custom positioning logic
        camera.location = center + Vector((x, y, z))
        camera.rotation_euler = Euler((rx, ry, rz), 'XYZ')
```

### Integration with Other Add-ons
The modular design allows integration with:
- Material libraries (automatic material assignment)
- Animation tools (turntable generation)
- Render farms (batch job submission)
- Asset browsers (automated preview generation)

## Version History

### v1.0.0 (Initial Release)
- Complete automatic setup system
- Five built-in presets
- Multi-shot generation (5 shot types)
- Batch collection processing
- Headless CLI automation
- Comprehensive UI panel
- HDRI environment support
- Studio lighting setup
- Floor generation with materials
- DOF and exposure controls

## License

This add-on is released under the same license as the parent BlenderScripts repository. See the main repository LICENSE file for details.

## Contributing

This add-on is part of the BlenderScripts project. Contributions are welcome through the main repository:
- Bug reports and feature requests
- Code improvements and optimizations
- Documentation updates
- Additional presets and shot types
- Integration examples

## Credits

Developed as part of the BlenderScripts collection for automated Blender workflows and pipeline integration.