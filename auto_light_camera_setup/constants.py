"""
Constants and default values for Auto Light Camera Setup.
Centralizes magic numbers and configuration defaults.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Tuple


class ShotType(Enum):
    """Available camera shot types."""
    ALL = "ALL"
    FRONT = "FRONT"
    THREE_QUARTER = "3Q"
    CUSTOM = "CUSTOM"


class LightType(Enum):
    """Blender light types."""
    AREA = "AREA"
    POINT = "POINT"
    SPOT = "SPOT"
    SUN = "SUN"


@dataclass(frozen=True)
class CameraSettings:
    """Default camera configuration values."""
    DEFAULT_DISTANCE_FACTOR: float = 2.5
    DEFAULT_LENS: float = 50.0
    DEFAULT_DOF_FSTOP: float = 2.8
    
    # Shot positioning constants
    FRONT_ROTATION_X: float = 90.0  # degrees
    THREE_QUARTER_ANGLE: float = 45.0  # degrees
    THREE_QUARTER_HEIGHT_FACTOR: float = 0.3
    LOW_ANGLE_HEIGHT_FACTOR: float = -0.3
    LOW_ANGLE_DISTANCE_FACTOR: float = 1.2


@dataclass(frozen=True)
class LightingSettings:
    """Default lighting configuration values."""
    DEFAULT_KEY_INTENSITY: float = 5.0
    DEFAULT_FILL_INTENSITY: float = 2.0
    DEFAULT_RIM_INTENSITY: float = 3.0
    
    # Light positioning
    LIGHT_DISTANCE_FACTOR: float = 2.0
    LIGHT_HEIGHT_FACTOR: float = 1.5
    KEY_LIGHT_SIZE_FACTOR: float = 0.5
    FILL_LIGHT_SIZE_FACTOR: float = 0.8
    RIM_LIGHT_SIZE_FACTOR: float = 0.3
    
    # Studio lighting factors
    STUDIO_KEY_ENERGY_FACTOR: float = 1.5
    STUDIO_FILL_ENERGY_FACTOR: float = 0.8
    STUDIO_RIM_ENERGY_FACTOR: float = 2.0


@dataclass(frozen=True)
class FloorSettings:
    """Default floor configuration values."""
    DEFAULT_COLOR: Tuple[float, float, float] = (0.8, 0.8, 0.8)
    SIZE_MULTIPLIER: float = 3.0
    Z_OFFSET: float = -0.01
    DEFAULT_ROUGHNESS: float = 0.8
    DEFAULT_SPECULAR: float = 0.1


@dataclass(frozen=True)
class WorldSettings:
    """Default world/environment settings."""
    DEFAULT_STRENGTH: float = 1.0
    DEFAULT_HDRI_STRENGTH: float = 1.0
    DEFAULT_EXPOSURE: float = 0.0
    DARK_GRAY_COLOR: Tuple[float, float, float, float] = (0.05, 0.05, 0.05, 1.0)


@dataclass(frozen=True)
class RenderSettings:
    """Default render configuration."""
    DEFAULT_SAMPLES: int = 128
    DEFAULT_RESOLUTION_X: int = 1920
    DEFAULT_RESOLUTION_Y: int = 1080


@dataclass(frozen=True)
class ObjectNames:
    """Standard names for auto-generated objects."""
    # Cameras
    CAMERA_PREFIX: str = "AutoSetup_Camera"
    TRACK_TARGET_SUFFIX: str = "_TrackTarget"
    
    # Lights
    KEY_LIGHT: str = "AutoSetup_KeyLight"
    FILL_LIGHT: str = "AutoSetup_FillLight"
    RIM_LIGHT: str = "AutoSetup_RimLight"
    STUDIO_KEY: str = "AutoSetup_StudioKey"
    STUDIO_FILL: str = "AutoSetup_StudioFill"
    STUDIO_RIM: str = "AutoSetup_StudioRim"
    
    # Collections
    ROOT_COLLECTION: str = "AutoSetup"
    CAMERAS_COLLECTION: str = "AutoSetup_Cameras"
    LIGHTS_COLLECTION: str = "AutoSetup_Lights"
    
    # Floor
    FLOOR_OBJECT: str = "AutoSetup_Floor"
    INFINITE_FLOOR: str = "AutoSetup_InfiniteFloor"
    FLOOR_MATERIAL: str = "AutoSetup_FloorMaterial"
    INFINITE_FLOOR_MATERIAL: str = "AutoSetup_InfiniteFloorMaterial"
    
    # World
    WORLD: str = "AutoSetup_World"
    STUDIO_WORLD: str = "AutoSetup_StudioWorld"
    
    # Locator
    LOCATOR: str = "AutoSetup_Locator"


# Constraint names
TRACK_TO_CONSTRAINT: str = "AutoSetup_TrackTo"

# Collections that should be excluded from targeting
AUTOSETUP_FLOOR_NAMES = {ObjectNames.FLOOR_OBJECT, ObjectNames.INFINITE_FLOOR}

# File extensions for HDRI validation
VALID_HDRI_EXTENSIONS = {'.hdr', '.exr', '.hdri', '.jpg', '.jpeg', '.png', '.tiff', '.tif'}