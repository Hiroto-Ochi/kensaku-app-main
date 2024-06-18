import os
import json
import base64
from typing import Generator
from dotenv import load_dotenv
from flask import Flask, Response, request
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from utils.logger import logger
from utils.openai import OpenAIClient
from utils.cosmos import CosmosContainer

# .envファイルから環境変数を読み込む
load_dotenv(override=True)
ASSISTANT_INITIAL_MESSAGE = os.getenv("ASSISTANT_INITIAL_MESSAGE", "こんにちは！何かお手伝いできることはありますか？")

# Flask の初期化
app = Flask(__name__)

# デバッグ実行かどうかを判定
debug = True if os.getenv("DEBUG") == "true" else False

# デバッグ実行でない場合のみ、Azure Application Insights によるログ出力とトレースを有効化
if not debug:
    configure_azure_monitor()
    FlaskInstrumentor().instrument_app(app)

# Azure OpenAI Service にアクセスするためのクライアントの初期化
openai_client = OpenAIClient()

# Azure Cosmos DB にアクセスするためのクライアントの初期化
cosmos_client = CosmosContainer()


@app.route("/", defaults={"path": "index.html"})
@app.route("/<path:path>")
def static_file(path: str) -> Response:
    return app.send_static_file(path)


@app.route("/talks", methods=["GET"])
def list_talks() -> tuple[dict, int]:
    """
    ユーザが作成したチャット一覧を取得する
    """

    # ログインユーザ情報を取得
    user_id, _ = get_user_info()

    # ユーザが作成したチャット一覧を取得
    query = "SELECT c.id, c.title, c.messages FROM c WHERE c.userId = @userId ORDER BY c._ts ASC"
    parameters = [{"name": "@userId", "value": user_id}]
    items = cosmos_client.query_items(query, parameters=parameters)

    # チャット一覧を返す
    return items, 200


@app.route("/talks", methods=["POST"])
def add_talk() -> tuple[dict, int]:
    """
    新しいチャットを作成する
    """

    # リクエストボディからチャットタイトルを取得
    if "title" not in request.json:
        return "title is required", 400
    title = request.json["title"]

    # ログインユーザ情報を取得
    user_id, _ = get_user_info()

    # 新しいチャットを作成
    item = cosmos_client.upsert_item(
        {
            "title": title,
            "userId": user_id,
            "messages": [{"role": "assistant", "content": ASSISTANT_INITIAL_MESSAGE}],
        }
    )

    # 作成したチャット情報を返す
    return {key: item[key] for key in ["id", "title", "userId", "messages"]}, 200


@app.route("/talks/<talk_id>", methods=["DELETE"])
def delete_talk(talk_id: str) -> tuple[str, int]:
    """
    指定したチャットを削除する

    Args:
        talk_id (str): チャットID
    """

    # ログインユーザ情報を取得
    user_id, _ = get_user_info()

    # 対象の会話情報を削除する権限があるか確認
    talk = cosmos_client.get_item(talk_id)
    if talk is None or talk["userId"] != user_id:
        return "", 404

    # 会話情報を削除
    cosmos_client.delete_item(talk_id)

    return "", 204


@app.route("/talks/<talk_id>/message", methods=["POST"])
def add_message(talk_id: str):
    """
    ユーザメッセージを受け取り、Azure OpenAI Service で回答を生成する

    Args:
        talk_id (str): チャットID
    """
    try:

        # リクエストボディからメッセージを取得
        if "message" not in request.json:
            return "message is required", 400
        message = request.json["message"]

        # ログインユーザ情報を取得
        user_id, _ = get_user_info()

        # 対象の会話情報を取得
        talk = cosmos_client.get_item(talk_id)
        if talk is None or talk["userId"] != user_id:
            return "", 404

        # ユーザメッセージを会話情報に追加
        talk["messages"].append({"role": "user", "content": message})

        # Azure OpenAI Service で回答を生成する
        chunks = openai_client.get_completion_with_tools([m for m in talk["messages"]])  # Deep Copy

        # 回答をストリーミング形式で返却する
        return Response(to_stream_resp(talk, chunks), mimetype="text/event-stream")

    except Exception as e:
        logger.exception(e)
        return "", 500


def to_stream_resp(talk: dict, chunks: Generator) -> Generator:
    """
    Azure OpenAI Service で生成した回答をクライアントへストリーミング形式で返却する

    Args:
        talk (dict): チャット情報
        chunks (Generator): 生成された回答
    """

    # Azure OpenAI Service で生成した回答をストリーミング形式で返却する
    content = ""
    for chunk in chunks:
        if not chunk or chunk == "[DONE]":
            continue
        content += chunk
        yield json.dumps({"content": content}).replace("\n", "\\n") + "\n"

    # 返却しきったら、会話情報を更新する
    talk["messages"].append({"role": "assistant", "content": content})
    cosmos_client.upsert_item(talk)


@app.route("/talk/<talk_id>/title", methods=["PUT"])
def update_talk_title(talk_id: str) -> tuple[str, int]:
    """
    チャットのタイトルを更新する

    Args:
        talk_id (str): チャットID
    """

    # リクエストボディからメッセージを取得
    if "title" not in request.json:
        return "title is required", 400
    title = request.json["title"]

    # ログインユーザ情報を取得
    user_id, _ = get_user_info()

    # 対象の会話情報を取得
    talk = cosmos_client.get_item(talk_id)
    if talk is None or talk["userId"] != user_id:
        return "", 404

    # 会話情報を更新
    talk["title"] = title
    cosmos_client.upsert_item(talk)

    return "", 204


@app.route("/talk/<talk_id>/title/gen", methods=["POST"])
def generate_talk_title(talk_id: str) -> tuple[str, int]:
    """
    会話履歴からチャットのタイトルを生成する

    Args:
        talk_id (str): チャットID
    """

    # ログインユーザ情報を取得
    user_id, _ = get_user_info()

    # 対象の会話情報を取得
    talk = cosmos_client.get_item(talk_id)
    if talk is None or talk["userId"] != user_id:
        return "", 404

    # 今までの会話からチャットタイトルを生成
    messages = [m for m in talk["messages"]]  # deep copy
    user_message = """
    今までの会話履歴を元に、タイトルを生成してください。
    タイトルは15文字以下で、以下のJSONフォーマットで出力してください。

    # 出力フォーマット
    {"title": "{生成したタイトル}"}
    """
    messages.append({"role": "user", "content": user_message})
    completion = openai_client.get_completion(messages, json_mode=True)
    title = completion["title"]

    # 会話情報を更新
    talk["title"] = title
    cosmos_client.upsert_item(talk)

    return title, 200


def get_user_info() -> tuple[str, str]:
    """
    ログイン中のユーザ情報を取得する

    Returns:
        tuple[str, str]: ログインユーザのIDと名前
    """

    # ヘッダーに付与されているEntra認証に関するプリンシパル情報を取得する
    # 参考: http://schemas.microsoft.com/identity/claims/objectidentifier
    principal = request.headers.get("X-Ms-Client-Principal", "")

    # プリンシパルが設定されていない場合のユーザIDとユーザ名を定義
    user_id = "00000000-0000-0000-0000-000000000000"
    user_name = ""

    if principal:

        # プリンシパルをBase64デコードする
        principal = base64.b64decode(principal).decode("utf-8")
        principal = json.loads(principal)

        # プリンシパルから特定のキーの値を取得する関数を定義
        def get_princival_value(key, default):
            claims = [c["val"] for c in principal["claims"] if c["typ"] == key]
            return claims[0] if claims else default

        # ユーザーIDとユーザー名を取得する
        user_id = get_princival_value("http://schemas.microsoft.com/identity/claims/objectidentifier", "00000000-0000-0000-0000-000000000000")
        user_name = get_princival_value("http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress", "unknown")

    return (user_id, user_name)


if __name__ == "__main__":
    app.run(debug=debug)
