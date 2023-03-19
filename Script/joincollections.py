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


def get_selected_collection_names():
    """指定されたコレクション配下のコレクションを再帰的に取得

    Returns:
        選択中のコレクション配下のコレクション名の配列
        選択されていない場合は空の配列
    """

    selected_collections = bpy.context.view_layer.active_layer_collection.collection
    if not selected_collections:
        print("No collection selected")
        return []

    collections = get_subcollections(selected_collections)

    collection_names = []
    for collection in collections:
        collection_names.append(collection.name)

    return list(set(collection_names))


def get_subcollections(collection):
    """指定されたコレクション配下のコレクションを再帰的に取得

    Keyword Arguments:
        collection (bpy.context.collection): 指定オブジェクト

    Returns:
        subcollections -- 指定されたコレクション配下のコレクション配列
    """

    subcollections = []
    for subcollection in collection.children:
        subcollections.append(subcollection)
        subcollections.extend(get_subcollections(subcollection))
    return subcollections


# 全てのオブジェクトを非選択状態にする
bpy.ops.object.select_all(action='DESELECT')

# 関数の実行
collection_names = get_selected_collection_names()
for name in collection_names:
    join_collections(name)
