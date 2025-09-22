"""
Collection utilities for Auto Light Camera Setup.
Creates/gets dedicated collections and links auto-generated objects into them
for easier management.
"""

import bpy


def get_or_create_collection(name: str) -> bpy.types.Collection:
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
    # Ensure linked to current scene (root) if not already
    if not any(child.name == col.name for child in bpy.context.scene.collection.children):
        try:
            bpy.context.scene.collection.children.link(col)
        except RuntimeError:
            # Already linked somewhere in scene hierarchy
            pass
    return col


def get_or_create_nested_collection(name: str, parent_name: str) -> bpy.types.Collection:
    parent = get_or_create_collection(parent_name)
    col = bpy.data.collections.get(name)
    if col is None:
        col = bpy.data.collections.new(name)
    # Link under parent
    if not any(child.name == col.name for child in parent.children):
        try:
            parent.children.link(col)
        except RuntimeError:
            pass
    return col


def ensure_autosetup_collections() -> tuple[bpy.types.Collection, bpy.types.Collection]:
    """Ensure the root and sub collections for AutoSetup exist and return (cams, lights)."""
    root_name = "AutoSetup"
    cams_name = "AutoSetup_Cameras"
    lights_name = "AutoSetup_Lights"
    cams = get_or_create_nested_collection(cams_name, root_name)
    lights = get_or_create_nested_collection(lights_name, root_name)
    return cams, lights


def link_object_to_collection(obj: bpy.types.Object, collection: bpy.types.Collection):
    """Link object to collection if not already linked."""
    # Prefer checking from the object's perspective (compare by name)
    users_cols = getattr(obj, 'users_collection', [])
    if not any(c.name == collection.name for c in users_cols):
        try:
            collection.objects.link(obj)
        except RuntimeError:
            # Already linked somewhere; ignore
            pass
