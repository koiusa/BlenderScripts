import bpy


def get_objects_in_collection(collection):
    objects = []
    for obj in collection.objects:
        objects.append(obj)
    for child_collection in collection.children:
        objects += get_objects_in_collection(child_collection)
    return objects


def get_selected_collection_names(args_collection):
    """指定されたコレクション配下のコレクションを再帰的に取得

    Returns:
        選択中のコレクション配下のコレクション名の配列
        選択されていない場合は空の配列
    """

    if not args_collection:
        print("No collection selected")
        return []

    collections = get_subcollections(args_collection)

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
