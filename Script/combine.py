import sys
import os
import bpy

def get_script_dirpath() -> str:
    """実行中のスクリプトが存在するディレクトリパスを取得する
    未保存のスクリプト上で実行すると、空文字が返る

    Returns:
        str: スクリプトディレクトリパス
    """

    # 実行中のスクリプト名を取得する
    script_filename = os.path.basename(__file__)

    # スクリプトファイルのパスを取得
    script_filepath = bpy.data.texts[script_filename].filepath

    # 空文字が返った場合は処理せず終了する
    if script_filepath == "":
        return ""

    # ディレクトリパスを取得する
    script_dirpath = os.path.dirname(script_filepath)

    return script_dirpath

# プロジェクトのルートパスを取得する
sys.path.append(get_script_dirpath())

import sub.joincollections as joincollections
import sub.applymodifier as applymodifier
import sub.curvetomesh as curvetomesh
import sub.common as common

# 全てのオブジェクトを非選択状態にする
bpy.ops.object.select_all(action='DESELECT')

selected_collection = bpy.context.view_layer.active_layer_collection.collection
objects_in_collection = common.get_objects_in_collection(selected_collection)

# カーブをメッシュ化
for obj in objects_in_collection:
    curvetomesh.curve_to_mesh(obj)

# モデファイアを適用
for obj in objects_in_collection:
    applymodifier.apply_modifier(obj)

# コレクションを結合
collection_names = common.get_selected_collection_names(selected_collection)
for name in collection_names:
    joincollections.join_collections(name)
