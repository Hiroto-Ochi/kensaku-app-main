import os
import uuid
from azure.cosmos import PartitionKey
from azure.cosmos.cosmos_client import CosmosClient
from azure.cosmos.exceptions import CosmosResourceNotFoundError


class CosmosContainer:

    def __init__(self):

        # 各種設定値を環境変数から取得
        db_name = os.getenv("AZURE_COSMOS_DB_NAME")
        container_name = os.getenv("AZURE_COSMOS_CONTAINER_NAME")
        connection_string = os.getenv("AZURE_COSMOS_CONNECTION_STRING")

        # Azure Cosmos DB アカウントを参照する
        client = CosmosClient.from_connection_string(connection_string)

        # データベースを参照する (存在しない場合は作成する)
        client.create_database_if_not_exists(id=db_name)
        database = client.get_database_client(db_name)

        # コンテナを参照する (存在しない場合は作成する)
        database.create_container_if_not_exists(id=container_name, partition_key=PartitionKey(path="/id"))
        self.container = database.get_container_client(container_name)

    def query_items(self, query: str, parameters: list[dict] = None) -> list[dict]:
        """
        Azure Cosmos DB にクエリを実行する

        Args:
            query (str): クエリ文字列
            parameters (list[dict]): クエリパラメータ

        Returns:
            list[dict]: クエリ結果
        """
        items = self.container.query_items(query, parameters=parameters, enable_cross_partition_query=True)
        return [i for i in items]

    def get_item(self, id: str) -> dict:
        """
        Azure Cosmos DB から指定されたIDのアイテムを取得する

        Args:
            id (str): アイテムID
        """
        try:
            return self.container.read_item(item=id, partition_key=id)
        except CosmosResourceNotFoundError:
            return None

    def upsert_item(self, item: dict):
        """
        Azure Cosmos DB にアイテムを追加または更新する

        Args:
            item (dict): 追加または更新するアイテム
        """
        try:
            if "id" not in item:  # 新規作成の場合はIDを生成して設定
                item["id"] = str(uuid.uuid4())
            item = self.container.upsert_item(item)
            return item
        except CosmosResourceNotFoundError:
            return None

    def delete_item(self, id: str):
        """
        Azure Cosmos DB から指定されたIDのアイテムを削除する

        Args:
            id (str): アイテムID
        """
        try:
            self.container.delete_item(item=id, partition_key=id)
        except CosmosResourceNotFoundError:
            pass
