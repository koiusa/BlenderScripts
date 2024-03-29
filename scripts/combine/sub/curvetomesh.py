import bpy


def curve_to_mesh(arg_object: bpy.types.Object) -> bool:
    """カーブをメッシュに変換

    Keyword Arguments:
        arg_object (bpy.types.Object): 指定オブジェクト

    Returns:
        bool -- 実行成否
    """
    # 対象のオブジェクトをアクティブオブジェクトにする
    bpy.context.view_layer.objects.active = arg_object

    # カーブをメッシュに変換
    if arg_object.type == 'CURVE':
        arg_object.select_set(True)
        bpy.ops.object.convert(target='MESH')

    return True
