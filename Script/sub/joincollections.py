import bpy


def join_collections(arg_collectionname) -> bool:
    """指定されたコレクション配下のコレクションを結合

    Keyword Arguments:
        arg_collectionname (string): 指定オブジェクト

    Returns:
        Returns: bool -- 実行成否
    """

    # 対象のコレクションを取得
    collection = bpy.data.collections[arg_collectionname]

    # コレクション内のすべてのオブジェクトを結合するためのリストを作成
    objects_to_join = []
    for obj in collection.objects:
        objects_to_join.append(obj)

    # 新しいオブジェクトを作成して、リスト内のすべてのオブジェクトを結合する
    for obj in objects_to_join:
        obj.select_set(True)
        bpy.context.view_layer.objects.active = objects_to_join[0]
        bpy.ops.object.join()

    return True
