import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.models import VectorizableTextQuery, VectorizedQuery
from azure.search.documents.indexes import SearchIndexClient


class AzureSearchClient:

    def __init__(self, index_name: str = None):

        # 各種設定値を環境変数から取得
        endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        key = os.getenv("AZURE_SEARCH_QUERY_KEY")
        api_version = os.getenv("AZURE_SEARCH_API_VERSION", "2024-03-01-preview")
        index_name = index_name or os.getenv("AZURE_SEARCH_INDEX_NAME")
        self.use_semantic_search = True if os.getenv("AZURE_SEARCH_USE_SEMANTIC_SEARCH") == "true" else False
        self.vector_field_names = os.getenv("AZURE_SEARCH_VECTOR_FIELD_NAMES", "")
        self.vector_field_names = self.vector_field_names.split(",") if self.vector_field_names else []

        # Azure AI Search にアクセスするためのクライアントの初期化
        index_client = SearchIndexClient(endpoint=endpoint, credential=AzureKeyCredential(key), api_version=api_version)
        self.search_client = index_client.get_search_client(index_name)

    # インデックスを検索する
    def search(self, query: str = None, query_vector: list[float] = None, top: int = 10, skip: int = 0, filter: str = None) -> list[dict]:
        """
        Azure AI Search によるドキュメント検索を実行する

        Args:
            query (str): 検索クエリ
            query_vector (list[float]): 検索ベクトル
            top (int): 取得する検索結果の最大数
            skip (int): 検索結果のオフセット
            filter (str): フィルタ条件

        Returns:
            list[dict]: 検索結果のドキュメント一覧
        """
        docs = self.search_client.search(
            search_text=query,
            query_type="semantic" if self.use_semantic_search else "full",
            filter=filter,
            top=top,
            skip=skip,
            vector_queries=(
                [
                    (
                        VectorizableTextQuery(
                            k_nearest_neighbors=top,
                            fields=field_name,
                            text=query,
                        )
                        if query_vector is None
                        else VectorizedQuery(
                            k_nearest_neighbors=top,
                            fields=field_name,
                            vector=query_vector,
                        )
                    )
                    for field_name in self.vector_field_names
                ]
            ),
        )
        return [d for d in docs]  # Paged item -> list
