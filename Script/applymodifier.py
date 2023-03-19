import bpy


def apply_modifier_targettype(arg_object: bpy.types.Object) -> bool:
    """指定オブジェクトのモディファイアを適用する
       ※アーマチュア以外

    Keyword Arguments:
        arg_object (bpy.types.Object): 指定オブジェクト

    Returns:
        bool -- 実行成否
    """

    # 対象のオブジェクトをアクティブオブジェクトにする
    bpy.context.view_layer.objects.active = arg_object

    # オブジェクト内の全てのモディファイアを走査する
    for modifier in arg_object.modifiers:
        if modifier.type != 'ARMATURE':
            bpy.ops.object.modifier_apply(modifier=modifier.name)

    return True


# 関数の実行
objects = bpy.context.scene.objects
for obj in objects:
    apply_modifier_targettype(obj)
