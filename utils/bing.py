import os
import requests


class BingSearchClient:

    def __init__(self):
        self.api_key = os.environ.get("BING_SEARCH_API_KEY")

    def search_web_pages(self, query: str, mkt: str = "ja-JP", count: int = 10, offset: int = 0) -> list[dict]:
        """
        Bing Web検索APIを利用して、指定されたクエリに一致するWebページを検索する。

        Args:
            query (str): 検索クエリ
            mkt (str): マーケットコード
            count (int): 取得する検索結果の最大数
            offset (int): 検索結果のオフセット

        Returns:
            list[dict]: 検索結果のリスト
        """
        params = {"q": query, "mkt": mkt, "count": count, "offset": offset, "sortby": "date"}
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        resp = requests.get(f"https://api.bing.microsoft.com/v7.0/search", params=params, headers=headers)
        resp.raise_for_status()
        resp = resp.json()
        return resp["webPages"]["value"] if "webPages" in resp else []

    def search_news(
        self,
        query: str,
        mkt: str = "ja-JP",
        count: int = 10,
        offset: int = 0,
        sortby: str = "date",  # relevance,
        freshness: str = "month",  # day, week, month
    ) -> list[dict]:
        """
        Bing News検索APIを利用して、指定されたクエリに一致するニュース記事を検索する。

        Args:
            query (str): 検索クエリ
            mkt (str): マーケットコード
            count (int): 取得する検索結果の最大数
            offset (int): 検索結果のオフセット
            sortby (str): ソート方法
            freshness (str): 検索対象の期間

        Returns:
            list[dict]: 検索結果のリスト
        """
        params = {"q": query, "mkt": mkt, "count": count, "offset": offset, "sortby": sortby, "freshness": freshness}
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}
        resp = requests.get(f"https://api.bing.microsoft.com/v7.0//news/search", params=params, headers=headers)
        resp.raise_for_status()
        return resp.json()["value"]
